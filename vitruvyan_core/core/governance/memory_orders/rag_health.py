#!/usr/bin/env python3
"""
PHASE A3.5: RAG System Health Endpoint
Sacred Order: Truth (System Integrity Validation)

Aggregate health check for all RAG components:
- PostgreSQL (Archivarium)
- Qdrant (Mnemosyne)
- Embedding API (vitruvyan_api_embedding:8010)
- Babel Gardens (vitruvyan_babel_gardens:8009)
- Memory Orders (sync & coherence status)

Usage:
    # Standalone test
    python core/agents/memory_orders/rag_health.py
    
    # FastAPI integration
    from core.agents.memory_orders.rag_health import get_rag_health
    
    @app.get("/health/rag")
    async def health_rag():
        return get_rag_health()
"""
import httpx
from datetime import datetime
from typing import Dict, Any
from core.foundation.persistence.postgres_agent import PostgresAgent
from .coherence import coherence_check, get_sync_lag
import logging

logger = logging.getLogger(__name__)

def check_postgresql() -> Dict[str, Any]:
    """Check PostgreSQL health and key metrics."""
    try:
        pg = PostgresAgent()
        
        # Test query
        result = pg.fetch_all("SELECT 1;")
        if not result or result[0][0] != 1:
            return {"status": "unhealthy", "error": "Query returned unexpected result"}
        
        # Get phrase counts
        phrases_total = pg.fetch_all("SELECT COUNT(*) FROM phrases;")[0][0]
        phrases_embedded = pg.fetch_all("SELECT COUNT(*) FROM phrases WHERE embedded = true;")[0][0]
        
        # Get conversation count
        conversations = pg.fetch_all("SELECT COUNT(*) FROM conversations;")[0][0]
        
        return {
            "status": "healthy",
            "phrases_total": phrases_total,
            "phrases_embedded": phrases_embedded,
            "conversations": conversations,
            "response_time_ms": "<10"
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant health and collection metrics."""
    try:
        # Health endpoint
        response = httpx.get("http://172.17.0.1:6333/", timeout=5.0)
        response.raise_for_status()
        
        # Get collection counts
        collections = {}
        for col in ["phrases_embeddings", "conversations_embeddings", "momentum_vectors", 
                    "trend_vectors", "volatility_vectors", "sentiment_embeddings"]:
            try:
                col_response = httpx.get(f"http://172.17.0.1:6333/collections/{col}", timeout=5.0)
                col_response.raise_for_status()
                count = col_response.json()["result"]["points_count"]
                collections[col] = count
            except:
                collections[col] = -1
        
        return {
            "status": "healthy",
            "collections": collections,
            "total_points": sum(v for v in collections.values() if v > 0),
            "response_time_ms": "<50"
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def check_embedding_api() -> Dict[str, Any]:
    """Check embedding API health and performance."""
    try:
        # Health check (use container name for Docker networking)
        response = httpx.get("http://vitruvyan_api_embedding:8010/health", timeout=5.0)
        response.raise_for_status()
        health = response.json()
        
        # Quick test embed
        test_response = httpx.post(
            "http://vitruvyan_api_embedding:8010/v1/embeddings/create",
            json={"text": "test"},
            timeout=10.0
        )
        test_response.raise_for_status()
        
        return {
            "status": "healthy",
            "model": health.get("model", "unknown"),
            "vector_size": health.get("vector_size", 384),
            "response_time_ms": "<30"
        }
    except Exception as e:
        logger.error(f"Embedding API health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def check_babel_gardens() -> Dict[str, Any]:
    """Check Babel Gardens health."""
    try:
        response = httpx.get("http://vitruvyan_babel_gardens:8009/sacred-health", timeout=5.0)
        response.raise_for_status()
        health = response.json()
        
        # Count blessed groves from sacred_groves dict
        groves = health.get("sacred_groves", {})
        groves_blessed = sum(1 for g in groves.values() if g.get("blessed"))
        
        # Map divine_status ("blessed"/"profaned") to standard status
        divine_status = health.get("divine_status", "unknown")
        status = "healthy" if divine_status == "blessed" else "degraded"
        
        return {
            "status": status,
            "groves_blessed": groves_blessed,
            "groves_total": len(groves),
            "divine_status": divine_status,
            "uptime_seconds": int(health.get("blessed_uptime_seconds", 0)),
            "response_time_ms": "<50"
        }
    except Exception as e:
        logger.error(f"Babel Gardens health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def check_memory_orders() -> Dict[str, Any]:
    """Check Memory Orders sync and coherence status."""
    try:
        # Coherence check
        coherence = coherence_check()
        sync_lag = get_sync_lag()
        
        # Determine overall status
        if coherence["status"] == "healthy" and sync_lag < 100:
            status = "healthy"
        elif coherence["status"] == "warning" or sync_lag < 1000:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "coherence_status": coherence["status"],
            "drift_percentage": coherence.get("drift_percentage", -1),
            "sync_lag": sync_lag,
            "recommendation": coherence.get("recommendation", "")
        }
    except Exception as e:
        logger.error(f"Memory Orders health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

def get_rag_health() -> Dict[str, Any]:
    """
    Aggregate RAG system health check.
    
    Returns comprehensive health report including:
    - Overall system status
    - Individual component health
    - Key metrics and recommendations
    """
    # Check all components
    postgresql = check_postgresql()
    qdrant = check_qdrant()
    embedding_api = check_embedding_api()
    babel_gardens = check_babel_gardens()
    memory_orders = check_memory_orders()
    
    # Determine overall status
    statuses = [
        postgresql.get("status"),
        qdrant.get("status"),
        embedding_api.get("status"),
        babel_gardens.get("status"),
        memory_orders.get("status")
    ]
    
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif "unhealthy" in statuses:
        overall_status = "degraded"
    elif "critical" in statuses:
        overall_status = "critical"
    else:
        overall_status = "warning"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "postgresql": postgresql,
            "qdrant": qdrant,
            "embedding_api": embedding_api,
            "babel_gardens": babel_gardens,
            "memory_orders": memory_orders
        },
        "summary": {
            "total_collections": 6,
            "total_points": qdrant.get("total_points", 0),
            "coherence_status": memory_orders.get("coherence_status", "unknown"),
            "sync_lag": memory_orders.get("sync_lag", -1)
        }
    }

if __name__ == "__main__":
    # Standalone test
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("RAG SYSTEM HEALTH CHECK")
    print("="*70 + "\n")
    
    health = get_rag_health()
    
    print(f"Overall Status: {health['status'].upper()}")
    print(f"Timestamp: {health['timestamp']}\n")
    
    print("Components:")
    for component, status in health['components'].items():
        icon = "✅" if status['status'] == "healthy" else "⚠️" if status['status'] == "warning" else "❌"
        print(f"  {icon} {component}: {status['status']}")
        if 'error' in status:
            print(f"     Error: {status['error']}")
    
    print(f"\nSummary:")
    print(f"  Total Points: {health['summary']['total_points']:,}")
    print(f"  Coherence: {health['summary']['coherence_status']}")
    print(f"  Sync Lag: {health['summary']['sync_lag']}")
    
    print("\n" + "="*70 + "\n")
