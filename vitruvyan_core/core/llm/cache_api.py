# Cache Management API and Utilities
# core/llm/cache_api.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from .cache_manager import get_cache_manager, CacheEntry

router = APIRouter(prefix="/cache", tags=["LLM Cache"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_cache_statistics(days: int = 7) -> Dict[str, Any]:
    """Get cache performance statistics"""
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_cache_statistics(days)
        
        # Add some derived metrics
        if "total_requests" in stats and stats["total_requests"] > 0:
            stats["cache_efficiency"] = {
                "hit_rate_percentage": round(stats["hit_rate"] * 100, 2),
                "miss_rate_percentage": round((1 - stats["hit_rate"]) * 100, 2),
                "avg_tokens_per_request": round(
                    (stats["tokens_used"] + stats["tokens_saved"]) / stats["total_requests"], 1
                ),
                "cost_efficiency": round(
                    stats["tokens_saved"] / (stats["tokens_used"] + stats["tokens_saved"]) * 100, 2
                ) if (stats["tokens_used"] + stats["tokens_saved"]) > 0 else 0
            }
        
        return {
            "status": "success",
            "data": stats,
            "period_days": days,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_entries() -> Dict[str, Any]:
    """Manually trigger cleanup of expired cache entries"""
    try:
        cache_manager = get_cache_manager()
        cleaned_count = cache_manager.cleanup_expired_entries()
        
        return {
            "status": "success",
            "message": f"Cleaned up {cleaned_count} expired entries",
            "cleaned_count": cleaned_count,
            "cleaned_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate")
async def invalidate_cache_for_entities(entity_ids: List[str]) -> Dict[str, Any]:
    """Invalidate cache entries for specific entity_ids"""
    try:
        if not entity_ids:
            raise HTTPException(status_code=400, detail="EntityIds list cannot be empty")
        
        cache_manager = get_cache_manager()
        cache_manager.invalidate_cache_for_entities(entity_ids)
        
        return {
            "status": "success",
            "message": f"Invalidated cache for entity_ids: {', '.join(entity_ids)}",
            "entity_ids": entity_ids,
            "invalidated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def cache_health_check() -> Dict[str, Any]:
    """Check cache system health"""
    try:
        cache_manager = get_cache_manager()
        
        # Test Redis connection
        test_key = "health_check_test"
        test_value = datetime.now().isoformat()
        
        # Write test
        cache_manager.redis_client.set(test_key, test_value, ex=60)
        
        # Read test  
        retrieved_value = cache_manager.redis_client.get(test_key)
        
        # Cleanup
        cache_manager.redis_client.delete(test_key)
        
        redis_healthy = retrieved_value == test_value
        
        # Get current cache size (approximate)
        cache_keys = cache_manager.redis_client.keys("llm_cache:*")
        cache_size = len(cache_keys)
        
        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "redis_connection": "ok" if redis_healthy else "failed",
            "cache_entries": cache_size,
            "max_cache_size": cache_manager.max_cache_size,
            "utilization": round(cache_size / cache_manager.max_cache_size * 100, 2),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }


@router.get("/similar/{query}")
async def find_similar_queries(query: str, limit: int = 5) -> Dict[str, Any]:
    """Find similar cached queries for debugging/analysis"""
    try:
        # Simulate state for similarity search
        state = {
            "input_text": query,
            "language": "it",
            "entity_ids": [],
            "intent": "analysis"
        }
        
        cache_manager = get_cache_manager()
        similar_entries = cache_manager.find_similar_cached_responses(state, limit)
        
        # Convert to serializable format
        results = []
        for entry in similar_entries:
            results.append({
                "cache_key": entry.cache_key,
                "timestamp": entry.timestamp.isoformat(),
                "hit_count": entry.hit_count,
                "tokens_used": entry.tokens_used,
                "model": entry.model,
                "similarity_score": getattr(entry, 'similarity_score', 0.0),
                "response_preview": entry.response[:200] + "..." if len(entry.response) > 200 else entry.response
            })
        
        return {
            "status": "success",
            "query": query,
            "similar_entries": results,
            "found_count": len(results),
            "searched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Similar queries search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-analysis")
async def get_cost_analysis(days: int = 30) -> Dict[str, Any]:
    """Detailed cost analysis and projections"""
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_cache_statistics(days)
        
        # Cost calculations (approximate)
        cost_per_token = 0.0001  # $0.0001 per token for GPT-4o-mini
        
        analysis = {
            "period_days": days,
            "total_tokens_used": stats.get("tokens_used", 0),
            "total_tokens_saved": stats.get("tokens_saved", 0),
            "actual_cost": stats.get("tokens_used", 0) * cost_per_token,
            "cost_saved": stats.get("tokens_saved", 0) * cost_per_token,
            "cost_without_cache": (stats.get("tokens_used", 0) + stats.get("tokens_saved", 0)) * cost_per_token,
        }
        
        if analysis["cost_without_cache"] > 0:
            analysis["savings_percentage"] = round(
                analysis["cost_saved"] / analysis["cost_without_cache"] * 100, 2
            )
        else:
            analysis["savings_percentage"] = 0
        
        # Projections
        daily_avg_requests = stats.get("total_requests", 0) / max(days, 1)
        daily_avg_cost = analysis["actual_cost"] / max(days, 1)
        
        analysis["projections"] = {
            "monthly_requests": round(daily_avg_requests * 30),
            "monthly_cost": round(daily_avg_cost * 30, 2),
            "yearly_cost": round(daily_avg_cost * 365, 2),
            "yearly_savings": round(analysis["cost_saved"] / max(days, 1) * 365, 2)
        }
        
        return {
            "status": "success",
            "cost_analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cost analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preload")
async def preload_common_queries() -> Dict[str, Any]:
    """Preload cache with common queries (domain-configurable)"""
    try:
        # Common queries to preload (domain-agnostic examples)
        common_queries = [
            {"input_text": "Analyze recent data overview", "intent": "trend"},
            {"input_text": "Show recommendations", "intent": "recommendation"},
            {"input_text": "Collection risk analysis", "intent": "collection"},
            {"input_text": "Sector trend analysis", "intent": "sector_analysis"},
            {"input_text": "Long-term opportunities", "intent": "soft"}
        ]
        
        preloaded_count = 0
        
        for query_data in common_queries:
            # Create mock state
            state = {
                "input_text": query_data["input_text"],
                "intent": query_data["intent"],
                "language": "it",
                "entity_ids": [],
                "user_id": "preload_system"
            }
            
            # Check if already cached
            cache_manager = get_cache_manager()
            cache_key = cache_manager.generate_cache_key(state, query_data["intent"])
            
            if not cache_manager.get_cached_response(cache_key):
                # Generate and cache response
                # Note: This would require actual LLM call in production
                mock_response = f"Analisi precaricata per: {query_data['input_text']}"
                
                cache_manager.cache_response(
                    cache_key, mock_response, state,
                    "gpt-4o-mini", 150  # Mock token count
                )
                
                preloaded_count += 1
        
        return {
            "status": "success",
            "message": f"Preloaded {preloaded_count} common queries",
            "preloaded_count": preloaded_count,
            "preloaded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cache preload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))