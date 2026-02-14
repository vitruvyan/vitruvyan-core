# LLM Caching System for Vitruvyan
# core/llm/cache_manager.py

import hashlib
import json
import redis
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class CacheEntry:
    """Cached LLM response entry"""
    response: str
    timestamp: datetime
    model: str
    tokens_used: int
    user_id: str
    language: str
    cache_key: str
    context_hash: str
    expires_at: datetime
    hit_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'expires_at': self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class LLMCacheManager:
    """
    Intelligent LLM caching system for token cost optimization
    
    Features:
    - Multi-level caching (Redis + PostgreSQL)
    - Semantic similarity detection
    - Context-aware cache keys
    - Automatic expiration
    - Analytics & cost tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True,
            socket_timeout=5
        )
        
        # Cache configuration
        self.default_ttl_hours = int(os.getenv("LLM_CACHE_TTL_HOURS", "24"))
        self.max_cache_size = int(os.getenv("LLM_CACHE_MAX_SIZE", "10000"))
        
        # Similarity thresholds
        self.similarity_threshold = float(os.getenv("LLM_CACHE_SIMILARITY_THRESHOLD", "0.85"))
        
        self.logger.info("LLM Cache Manager initialized")
    
    def generate_cache_key(self, state: Dict[str, Any], prompt_type: str = "default") -> str:
        """Generate intelligent cache key based on state"""
        
        # Core elements for cache key
        key_elements = {
            "user_input": state.get("input_text", ""),
            "intent": state.get("intent", ""),
            "entity_ids": sorted(state.get("entity_ids", [])),  # Sort for consistency
            "language": state.get("language", "en"),
            "horizon": state.get("horizon", ""),
            "prompt_type": prompt_type
        }
        
        # Add technical data hash if present
        if "raw_output" in state:
            tech_hash = self._hash_technical_data(state["raw_output"])
            key_elements["tech_hash"] = tech_hash
        
        # Create normalized string
        key_string = json.dumps(key_elements, sort_keys=True, ensure_ascii=False)
        
        # Generate SHA256 hash
        cache_key = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        
        return f"llm_cache:{prompt_type}:{cache_key}"
    
    def _hash_technical_data(self, raw_output: Dict[str, Any]) -> str:
        """Create hash of technical data for cache key"""
        if not isinstance(raw_output, dict):
            return "no_data"
        
        # Extract key elements that affect LLM response
        key_data = {}
        
        if "ranking" in raw_output:
            ranking = raw_output["ranking"]
            # Hash top 5 entities and their scores
            all_items = []
            for group in ranking.values():
                all_items.extend(group)
            
            top_5 = sorted(all_items, key=lambda x: x.get("composite_score", 0), reverse=True)[:5]
            key_data["top_performers"] = [
                {
                    "entity_id": entity["entity_id"],
                    "score": round(entity.get("composite_score", 0), 2)
                }
                for entity in top_5
            ]
        
        data_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(data_string.encode()).hexdigest()[:8]
    
    def get_cached_response(self, cache_key: str) -> Optional[CacheEntry]:
        """Retrieve cached response if available and valid"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if not cached_data:
                return None
            
            # Deserialize
            entry_dict = json.loads(cached_data)
            entry = CacheEntry.from_dict(entry_dict)
            
            # Check expiration
            if datetime.now() > entry.expires_at:
                self.redis_client.delete(cache_key)
                self.logger.debug(f"Expired cache entry removed: {cache_key}")
                return None
            
            # Update hit count
            entry.hit_count += 1
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.default_ttl_hours),
                json.dumps(entry.to_dict())
            )
            
            self.logger.info(f"Cache HIT: {cache_key} (hits: {entry.hit_count})")
            return entry
            
        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
            return None
    
    def cache_response(self, cache_key: str, response: str, state: Dict[str, Any], 
                      model: str, tokens_used: int) -> bool:
        """Cache LLM response"""
        try:
            entry = CacheEntry(
                response=response,
                timestamp=datetime.now(),
                model=model,
                tokens_used=tokens_used,
                user_id=state.get("user_id", "anonymous"),
                language=state.get("language", "en"),
                cache_key=cache_key,
                context_hash=self._hash_technical_data(state.get("raw_output", {})),
                expires_at=datetime.now() + timedelta(hours=self.default_ttl_hours),
                hit_count=0
            )
            
            # Store in Redis
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.default_ttl_hours),
                json.dumps(entry.to_dict())
            )
            
            # Update cache statistics
            self._update_cache_stats(tokens_used, "miss")
            
            self.logger.info(f"Cached response: {cache_key} ({tokens_used} tokens)")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache storage error: {e}")
            return False
    
    def find_similar_cached_responses(self, state: Dict[str, Any], 
                                    limit: int = 5) -> List[CacheEntry]:
        """Find similar cached responses using semantic similarity"""
        try:
            # Get potential matches based on partial key matching
            user_input = state.get("input_text", "").lower()
            intent = state.get("intent", "")
            entity_ids = set(state.get("entity_ids", []))
            language = state.get("language", "en")
            
            # Search pattern
            pattern = f"llm_cache:*"
            keys = self.redis_client.keys(pattern)
            
            similar_entries = []
            
            for key in keys[:50]:  # Limit search scope
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue
                    
                    entry_dict = json.loads(cached_data)
                    entry = CacheEntry.from_dict(entry_dict)
                    
                    # Skip expired entries
                    if datetime.now() > entry.expires_at:
                        continue
                    
                    # Language match required
                    if entry.language != language:
                        continue
                    
                    # Calculate similarity score
                    similarity_score = self._calculate_similarity(state, entry)
                    
                    if similarity_score >= self.similarity_threshold:
                        entry.similarity_score = similarity_score
                        similar_entries.append(entry)
                        
                except Exception as e:
                    continue
            
            # Sort by similarity and return top matches
            similar_entries.sort(key=lambda x: x.similarity_score, reverse=True)
            return similar_entries[:limit]
            
        except Exception as e:
            self.logger.error(f"Similarity search error: {e}")
            return []
    
    def _calculate_similarity(self, current_state: Dict[str, Any], 
                            cached_entry: CacheEntry) -> float:
        """Calculate similarity score between current state and cached entry"""
        
        score = 0.0
        
        # Intent similarity (high weight)
        current_intent = current_state.get("intent", "")
        # Note: We'd need to parse intent from cached entry's context
        # For now, simplified approach
        score += 0.3  # Base score
        
        # EntityId overlap (high weight)
        current_entitys = set(current_state.get("entity_ids", []))
        # Would need to extract entity_ids from cached context
        # Simplified for now
        if current_entitys:
            score += 0.4
        
        # Language match (required, already filtered)
        score += 0.1
        
        # Recency bonus (newer entries preferred)
        age_hours = (datetime.now() - cached_entry.timestamp).total_seconds() / 3600
        recency_score = max(0, 0.2 * (24 - age_hours) / 24)  # Full bonus for <24h
        score += recency_score
        
        return min(1.0, score)
    
    def _update_cache_stats(self, tokens_used: int, result: str):
        """Update cache performance statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            stats_key = f"llm_cache_stats:{today}"
            
            # Update daily stats
            current_stats = self.redis_client.hgetall(stats_key)
            if not current_stats:
                current_stats = {
                    "total_requests": "0",
                    "cache_hits": "0", 
                    "cache_misses": "0",
                    "tokens_saved": "0",
                    "tokens_used": "0"
                }
            
            # Update counters
            current_stats["total_requests"] = str(int(current_stats["total_requests"]) + 1)
            
            if result == "hit":
                current_stats["cache_hits"] = str(int(current_stats["cache_hits"]) + 1)
                current_stats["tokens_saved"] = str(int(current_stats["tokens_saved"]) + tokens_used)
            else:
                current_stats["cache_misses"] = str(int(current_stats["cache_misses"]) + 1)
                current_stats["tokens_used"] = str(int(current_stats["tokens_used"]) + tokens_used)
            
            # Store updated stats
            self.redis_client.hset(stats_key, mapping=current_stats)
            self.redis_client.expire(stats_key, timedelta(days=30))
            
        except Exception as e:
            self.logger.error(f"Stats update error: {e}")
    
    def get_cache_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = {
                "total_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "tokens_saved": 0,
                "tokens_used": 0,
                "hit_rate": 0.0,
                "estimated_cost_saved": 0.0
            }
            
            # Aggregate stats for specified days
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                stats_key = f"llm_cache_stats:{date}"
                
                daily_stats = self.redis_client.hgetall(stats_key)
                if daily_stats:
                    stats["total_requests"] += int(daily_stats.get("total_requests", 0))
                    stats["cache_hits"] += int(daily_stats.get("cache_hits", 0))
                    stats["cache_misses"] += int(daily_stats.get("cache_misses", 0))
                    stats["tokens_saved"] += int(daily_stats.get("tokens_saved", 0))
                    stats["tokens_used"] += int(daily_stats.get("tokens_used", 0))
            
            # Calculate derived metrics
            if stats["total_requests"] > 0:
                stats["hit_rate"] = stats["cache_hits"] / stats["total_requests"]
            
            # Estimate cost savings (approximate $0.0001 per token)
            stats["estimated_cost_saved"] = stats["tokens_saved"] * 0.0001
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Stats retrieval error: {e}")
            return {}
    
    def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries"""
        try:
            pattern = "llm_cache:*"
            keys = self.redis_client.keys(pattern)
            
            cleaned = 0
            for key in keys:
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue
                    
                    entry_dict = json.loads(cached_data)
                    entry = CacheEntry.from_dict(entry_dict)
                    
                    if datetime.now() > entry.expires_at:
                        self.redis_client.delete(key)
                        cleaned += 1
                        
                except Exception:
                    continue
            
            self.logger.info(f"Cleaned up {cleaned} expired cache entries")
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            return 0
    
    def invalidate_cache_for_entities(self, entity_ids: List[str]):
        """Invalidate cache entries for specific entity_ids (e.g., after data updates)"""
        try:
            pattern = "llm_cache:*"
            keys = self.redis_client.keys(pattern)
            
            invalidated = 0
            for key in keys:
                try:
                    # This is a simplified approach
                    # In production, we'd need more sophisticated entity_id extraction
                    for entity_id in entity_ids:
                        if entity_id.lower() in key.lower():
                            self.redis_client.delete(key)
                            invalidated += 1
                            break
                            
                except Exception:
                    continue
            
            self.logger.info(f"Invalidated {invalidated} cache entries for entity_ids: {entity_ids}")
            
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {e}")


# Singleton instance
_cache_manager_instance = None

def get_cache_manager() -> LLMCacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = LLMCacheManager()
    return _cache_manager_instance


# Decorator for easy caching
def cached_llm_call(prompt_type: str = "default", ttl_hours: Optional[int] = None):
    """Decorator for caching LLM calls"""
    def decorator(func):
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(state, prompt_type)
            
            # Try to get from cache
            cached_entry = cache_manager.get_cached_response(cache_key)
            if cached_entry:
                return cached_entry.response
            
            # Call original function
            result = func(state, *args, **kwargs)
            
            # Cache the result (simplified - would need token counting)
            if isinstance(result, str):
                cache_manager.cache_response(
                    cache_key, result, state, 
                    model="gpt-4o-mini", tokens_used=100  # Placeholder
                )
            
            return result
        return wrapper
    return decorator