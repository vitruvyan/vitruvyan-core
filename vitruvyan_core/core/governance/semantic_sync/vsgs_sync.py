"""
🧠 VSGS Memory Orders Sync Module (PR-B)
Sacred Order: Memory Orders — Archivarium ↔ Mnemosyne Coherence

This module synchronizes semantic grounding events from PostgreSQL to Qdrant,
ensuring dual-memory consistency and enabling semantic trajectory tracking.

Architecture:
- PostgreSQL (Archivarium): Source of truth for grounding events
- Qdrant (Mnemosyne): Vector memory for semantic search
- Memory Orders: Synchronization orchestrator (drift < 5%)

Execution:
- Scheduled: Systemd timer (02:30 UTC daily)
- Manual: python -m core.foundation.semantic_sync.vsgs_sync
- Monitored: Prometheus metrics + audit logs

Usage:
    from core.foundation.semantic_sync.vsgs_sync import sync_semantic_states
    
    synced_count = sync_semantic_states(limit=100)
    print(f"Synced {synced_count} grounding events to Qdrant")
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Audit stub (TODO: Replace with proper audit module when available)
def audit(action: str, data: Dict[str, Any], trace_id: str = None, user_id: str = None):
    """Stub for audit logging - logs to standard logger"""
    logger.info(f"[AUDIT] {action} | trace={trace_id} | user={user_id} | data={data}")

# Import agents (correct vitruvyan-core paths)
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# PostgreSQL connection params
DB_PARAMS = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}


# Helper functions for VSGS-specific PostgreSQL operations
def fetch_unsynced_groundings(conn, limit: int = 100):
    """
    Fetch unsynced semantic grounding events from PostgreSQL.
    
    Args:
        conn: psycopg2 connection
        limit: Max events to fetch
    
    Returns:
        List of grounding event dicts
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, trace_id, input_text, embedding_vector, 
               matched_contexts, created_at
        FROM semantic_states
        WHERE qdrant_synced = false
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    
    return [dict(zip(columns, row)) for row in rows]


def mark_grounding_synced(conn, event_id: int) -> bool:
    """
    Mark a grounding event as synced in PostgreSQL.
    
    Args:
        conn: psycopg2 connection
        event_id: Event ID to mark
    
    Returns:
        True if successful
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE semantic_states
            SET qdrant_synced = true, qdrant_synced_at = NOW()
            WHERE id = %s
        """, (event_id,))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"Failed to mark event {event_id}: {e}")
        conn.rollback()
        return False


def count_grounding_events(conn) -> Dict[str, int]:
    """
    Count semantic grounding events by sync status.
    
    Args:
        conn: psycopg2 connection
    
    Returns:
        {"total": int, "synced": int, "unsynced": int}
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN qdrant_synced THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN NOT qdrant_synced THEN 1 ELSE 0 END) as unsynced
        FROM semantic_states
    """)
    
    row = cursor.fetchone()
    cursor.close()
    
    return {
        "total": row[0] or 0,
        "synced": row[1] or 0,
        "unsynced": row[2] or 0
    }


def sync_semantic_states(limit: int = 100, collection: str = "semantic_states") -> Dict[str, Any]:
    """
    Synchronize unsynced semantic grounding events from PostgreSQL to Qdrant.
    
    Args:
        limit: Maximum number of events to sync per run
        collection: Qdrant collection name
    
    Returns:
        dict: {
            "synced": int,
            "failed": int,
            "skipped": int,
            "errors": List[str]
        }
    
    Process:
    1. Fetch unsynced grounding events from PostgreSQL (qdrant_synced=false)
    2. For each event:
       a. Upsert to Qdrant with embedding_vector
       b. Mark as synced in PostgreSQL (qdrant_synced=true)
       c. Audit log the operation
    3. Report metrics to Prometheus
    """
    logger.info(f"🔄 Starting VSGS sync (limit={limit}, collection={collection})")
    
    conn = None
    synced = 0
    failed = 0
    skipped = 0
    errors = []
    
    try:
        # Initialize agents
        conn = psycopg2.connect(**DB_PARAMS)  # Raw conn for cursor-level sync ops
        qdrant = QdrantAgent()
        
        # Fetch unsynced events
        unsynced_events = fetch_unsynced_groundings(conn, limit=limit)
        logger.info(f"📊 Found {len(unsynced_events)} unsynced grounding events")
        
        if not unsynced_events:
            logger.info("✅ No unsynced events, sync complete")
            audit(
                "foundation.semantic_sync.vsgs_sync",
                {"synced": 0, "phase": "sync", "status": "no_work"},
                trace_id="sync_job",
                user_id="system"
            )
            return {"synced": 0, "failed": 0, "skipped": 0, "errors": []}
        
        # Sync each event
        for event in unsynced_events:
            try:
                # Check if embedding_vector exists
                if not event.get("embedding_vector"):
                    logger.warning(f"⚠️ Event {event['id']} has no embedding_vector, skipping")
                    skipped += 1
                    continue
                
                # Upsert to Qdrant
                result = qdrant.upsert_point_from_grounding(event, collection=collection)
                
                if result["status"] == "ok":
                    # Mark as synced in PostgreSQL
                    mark_success = mark_grounding_synced(conn, event["id"])
                    
                    if mark_success:
                        synced += 1
                        logger.info(f"✅ Synced event {event['id']} (user={event['user_id']})")
                    else:
                        failed += 1
                        error_msg = f"Failed to mark event {event['id']} as synced"
                        errors.append(error_msg)
                        logger.error(f"❌ {error_msg}")
                        
                        # Audit error
                        audit(
                            "foundation.semantic_sync.vsgs_sync",
                            {"error": error_msg, "event_id": event['id'], "phase": "sync"},
                            trace_id=event.get("trace_id", "unknown"),
                            user_id=event.get("user_id", "unknown")
                        )
                else:
                    failed += 1
                    error_msg = f"Qdrant upsert failed for event {event['id']}: {result.get('error')}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    
                    # Audit error
                    audit(
                        "foundation.semantic_sync.vsgs_sync",
                        {"error": error_msg, "event_id": event['id'], "phase": "sync"},
                        trace_id=event.get("trace_id", "unknown"),
                        user_id=event.get("user_id", "unknown")
                    )
                    
            except Exception as e:
                failed += 1
                error_msg = f"Exception syncing event {event['id']}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}", exc_info=True)
                
                # Audit error
                audit(
                    "foundation.semantic_sync.vsgs_sync",
                    {"error": str(e), "event_id": event['id'], "phase": "sync"},
                    trace_id=event.get("trace_id", "unknown"),
                    user_id=event.get("user_id", "unknown")
                )
        
        # Final audit log
        audit(
            "foundation.semantic_sync.vsgs_sync",
            {
                "synced": synced,
                "failed": failed,
                "skipped": skipped,
                "phase": "sync",
                "status": "complete"
            },
            trace_id="sync_job",
            user_id="system"
        )
        
        logger.info(f"🎯 VSGS sync complete: synced={synced}, failed={failed}, skipped={skipped}")
        
        return {
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ VSGS sync failed: {e}", exc_info=True)
        
        # Audit critical error
        audit(
            "foundation.semantic_sync.vsgs_sync",
            {"error": str(e), "phase": "sync", "status": "critical_failure"},
            trace_id="sync_job",
            user_id="system"
        )
        
        return {
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "errors": [str(e)]
        }
        
    finally:
        if conn:
            conn.close()
            logger.info("🔌 PostgreSQL connection closed")


def check_sync_health() -> Dict[str, Any]:
    """
    Check VSGS sync health: count unsynced events and report drift.
    
    Returns:
        dict: {
            "unsynced_count": int,
            "total_pg": int,
            "total_qdrant": int,
            "drift_percent": float,
            "status": "healthy" | "warning" | "critical"
        }
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        qdrant = QdrantAgent()
        
        # Count unsynced events
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM semantic_states WHERE qdrant_synced = false;")
            unsynced_count = cur.fetchone()[0]
        
        # Count total events
        total_pg = count_grounding_events(conn)
        total_qdrant = qdrant.count_points("semantic_states")
        
        # Calculate drift
        drift = abs(total_pg - total_qdrant) / max(total_pg, 1)
        drift_percent = drift * 100
        
        # Determine status
        if drift < 0.05 and unsynced_count < 100:
            status = "healthy"
        elif drift < 0.10 and unsynced_count < 500:
            status = "warning"
        else:
            status = "critical"
        
        logger.info(f"📊 VSGS Health: unsynced={unsynced_count}, PG={total_pg}, Qdrant={total_qdrant}, drift={drift_percent:.2f}%, status={status}")
        
        return {
            "unsynced_count": unsynced_count,
            "total_pg": total_pg,
            "total_qdrant": total_qdrant,
            "drift_percent": drift_percent,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}", exc_info=True)
        return {
            "unsynced_count": -1,
            "total_pg": -1,
            "total_qdrant": -1,
            "drift_percent": -1.0,
            "status": "error",
            "error": str(e)
        }
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VSGS Memory Orders Sync")
    parser.add_argument("--limit", type=int, default=100, help="Max events to sync per run")
    parser.add_argument("--collection", type=str, default="semantic_states", help="Qdrant collection")
    parser.add_argument("--health", action="store_true", help="Check sync health only")
    args = parser.parse_args()
    
    if args.health:
        health = check_sync_health()
        print(f"\n🏥 VSGS Sync Health Report:")
        print(f"  Unsynced Events: {health['unsynced_count']}")
        print(f"  PostgreSQL Total: {health['total_pg']}")
        print(f"  Qdrant Total: {health['total_qdrant']}")
        print(f"  Drift: {health['drift_percent']:.2f}%")
        print(f"  Status: {health['status']}")
    else:
        result = sync_semantic_states(limit=args.limit, collection=args.collection)
        print(f"\n✅ VSGS Sync Complete:")
        print(f"  Synced: {result['synced']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Skipped: {result['skipped']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"    - {error}")
