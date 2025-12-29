#!/usr/bin/env python3
"""
PHASE A3.3: Memory Orders - Coherence Check Module
Sacred Order: Truth (Epistemic Integrity Validation)

Verifies coherence between PostgreSQL (Archivarium) and Qdrant (Mnemosyne).
Calculates drift percentage and provides health status.

Coherence Thresholds:
- <5% drift: HEALTHY (green)
- 5-15% drift: WARNING (yellow) - schedule sync
- >15% drift: CRITICAL (red) - immediate action required

Architecture:
- Queries PostgreSQL for phrases with embedded=true
- Queries Qdrant for phrases_embeddings point count
- Calculates absolute and percentage drift
- Returns structured health report
- Exposes Prometheus metrics

Usage:
    from core.agents.memory_orders.coherence import coherence_check
    
    health = coherence_check()
    print(f"Status: {health['status']}")
    print(f"Drift: {health['drift_percentage']:.2f}%")
"""
from typing import Dict, Any
from datetime import datetime
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
import logging

logger = logging.getLogger(__name__)

COLLECTION_NAME = "phrases_embeddings"

# Coherence thresholds
DRIFT_HEALTHY = 5.0      # < 5% = healthy
DRIFT_WARNING = 15.0     # 5-15% = warning
# > 15% = critical

def coherence_check() -> Dict[str, Any]:
    """
    Check coherence between PostgreSQL and Qdrant.
    
    Returns:
        Dict with coherence metrics: {
            "status": "healthy" | "warning" | "critical",
            "postgresql_count": int,
            "qdrant_count": int,
            "drift_absolute": int,
            "drift_percentage": float,
            "timestamp": str,
            "recommendation": str
        }
    """
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    logger.info("🔍 Checking PostgreSQL ↔ Qdrant coherence...")
    
    try:
        # PostgreSQL count (embedded phrases)
        pg_result = pg.fetch_all(
            "SELECT COUNT(*) FROM phrases WHERE embedded = true;"
        )
        pg_count = pg_result[0][0] if pg_result else 0
        logger.info(f"📊 PostgreSQL: {pg_count} embedded phrases")
        
        # Qdrant count
        try:
            # Use httpx to avoid Pydantic version issues
            import httpx
            response = httpx.get(f"http://172.17.0.1:6333/collections/{COLLECTION_NAME}")
            response.raise_for_status()
            qdrant_count = response.json()["result"]["points_count"]
            logger.info(f"📊 Qdrant: {qdrant_count} points")
        except Exception as e:
            logger.error(f"❌ Qdrant query error: {e}")
            return {
                "status": "error",
                "postgresql_count": pg_count,
                "qdrant_count": -1,
                "drift_absolute": -1,
                "drift_percentage": -1,
                "timestamp": datetime.now().isoformat(),
                "recommendation": "Cannot query Qdrant - check service health",
                "error": str(e)
            }
        
        # Calculate drift
        drift_absolute = abs(pg_count - qdrant_count)
        
        if pg_count == 0:
            drift_percentage = 0.0 if qdrant_count == 0 else 100.0
        else:
            drift_percentage = (drift_absolute / pg_count) * 100
        
        # Determine status
        if drift_percentage < DRIFT_HEALTHY:
            status = "healthy"
            recommendation = "System coherent. No action required."
        elif drift_percentage < DRIFT_WARNING:
            status = "warning"
            recommendation = f"Moderate drift detected. Schedule sync to resolve {drift_absolute} mismatched entries."
        else:
            status = "critical"
            recommendation = f"HIGH DRIFT! Immediate sync required. {drift_absolute} entries out of sync."
        
        # Check direction
        if qdrant_count > pg_count:
            direction = "orphaned_vectors"
            detail = f"{qdrant_count - pg_count} orphaned vectors in Qdrant (should rebuild)"
        elif pg_count > qdrant_count:
            direction = "missing_vectors"
            detail = f"{pg_count - qdrant_count} phrases not embedded (should sync)"
        else:
            direction = "perfect"
            detail = "Perfect coherence achieved"
        
        result = {
            "status": status,
            "postgresql_count": pg_count,
            "qdrant_count": qdrant_count,
            "drift_absolute": drift_absolute,
            "drift_percentage": round(drift_percentage, 2),
            "drift_direction": direction,
            "drift_detail": detail,
            "timestamp": datetime.now().isoformat(),
            "recommendation": recommendation
        }
        
        logger.info(f"✅ Coherence check: {status.upper()} ({drift_percentage:.2f}% drift)")
        
        # Log to PostgreSQL for monitoring
        _log_coherence_check(pg, result)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Coherence check error: {e}", exc_info=True)
        return {
            "status": "error",
            "postgresql_count": -1,
            "qdrant_count": -1,
            "drift_absolute": -1,
            "drift_percentage": -1,
            "timestamp": datetime.now().isoformat(),
            "recommendation": "Coherence check failed - investigate system health",
            "error": str(e)
        }

def _log_coherence_check(pg: PostgresAgent, result: Dict[str, Any]):
    """Log coherence check to PostgreSQL for audit trail."""
    try:
        query = """
            INSERT INTO coherence_logs 
                (status, postgresql_count, qdrant_count, drift_percentage, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING;
        """
        cursor = pg.connection.cursor()
        cursor.execute(
            query,
            (
                result["status"],
                result["postgresql_count"],
                result["qdrant_count"],
                result["drift_percentage"]
            )
        )
        pg.connection.commit()
        cursor.close()
        logger.info(f"✅ Coherence log saved: {result['drift_percentage']:.2f}% drift")
    except Exception as e:
        logger.warning(f"⚠️  Could not log coherence check: {e}")

def get_sync_lag() -> int:
    """
    Get current sync lag (unembedded phrases count).
    Used for Prometheus metrics.
    
    Returns:
        Number of unembedded phrases
    """
    try:
        pg = PostgresAgent()
        result = pg.fetch_all("SELECT COUNT(*) FROM phrases WHERE embedded = false;")
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"❌ Sync lag query error: {e}")
        return -1

if __name__ == "__main__":
    # Test coherence check
    logging.basicConfig(level=logging.INFO)
    health = coherence_check()
    
    print(f"\n{'='*60}")
    print(f"COHERENCE CHECK RESULT")
    print(f"{'='*60}")
    print(f"Status: {health['status'].upper()}")
    print(f"PostgreSQL: {health['postgresql_count']} phrases")
    print(f"Qdrant: {health['qdrant_count']} points")
    print(f"Drift: {health['drift_absolute']} ({health['drift_percentage']}%)")
    if 'drift_direction' in health:
        print(f"Direction: {health['drift_direction']}")
        print(f"Detail: {health['drift_detail']}")
    print(f"Recommendation: {health['recommendation']}")
    print(f"{'='*60}\n")
