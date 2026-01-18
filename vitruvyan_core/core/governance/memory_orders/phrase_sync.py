#!/usr/bin/env python3
"""
PHASE A3.3: Memory Orders - Entity Sync Module
Sacred Order: Memory (PostgreSQL ↔ Qdrant Coherence)

Synchronizes unembedded entities from PostgreSQL to Qdrant.
Ensures dual-memory coherence via scheduled sync jobs.

Architecture:
- Reads entities with embedded=false from PostgreSQL (configurable)
- Generates embeddings via vitruvyan_api_embedding:8010
- Writes to Qdrant entities_embeddings collection (configurable)
- Marks entities as embedded=true in PostgreSQL
- Logs sync metrics to PostgreSQL
- Exposes Prometheus metrics

Usage:
    from core.agents.memory_orders.phrase_sync import sync_entities_to_qdrant
    
    # Sync next 1000 unembedded entities
    result = sync_entities_to_qdrant(limit=1000)
    print(f"Synced {result['synced']} entities in {result['duration']:.2f}s")
"""
import httpx
import uuid
from datetime import datetime
from typing import Dict, List, Any
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
import logging
import time

logger = logging.getLogger(__name__)

EMBEDDING_API_URL = "http://localhost:8010"
DEFAULT_COLLECTION_NAME = "entities_embeddings"
VECTOR_SIZE = 384

def sync_entities_to_qdrant(
    pg_table: str = "entities",
    pg_id_column: str = "id",
    pg_text_column: str = "text",
    pg_metadata_columns: List[str] = None,
    pg_embedded_column: str = "embedded",
    qdrant_collection: str = DEFAULT_COLLECTION_NAME,
    embedding_api_url: str = EMBEDDING_API_URL,
    limit: int = 1000
) -> Dict[str, Any]:
    """
    Sync unembedded entities from PostgreSQL to Qdrant.
    
    Args:
        pg_table: PostgreSQL table name (default: "entities")
        pg_id_column: ID column name (default: "id")
        pg_text_column: Text column to embed (default: "text")
        pg_metadata_columns: Additional columns to include in payload (default: None)
        pg_embedded_column: Embedded status column (default: "embedded")
        qdrant_collection: Qdrant collection name (default: "entities_embeddings")
        embedding_api_url: Embedding API URL (default: "http://localhost:8010")
        limit: Maximum number of entities to sync in one run
        
    Returns:
        Dict with sync results: {
            "status": "success" | "error",
            "synced": int,
            "failed": int,
            "duration": float,
            "lag": int,  # Total unembedded entities remaining
            "timestamp": str
        }
    """
    start_time = time.time()
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    logger.info(f"🔄 Starting entity sync (table={pg_table}, limit={limit})...")
    
    try:
        # Build column list for SELECT
        select_columns = [pg_id_column, pg_text_column]
        if pg_metadata_columns:
            select_columns.extend(pg_metadata_columns)
        
        # Fetch unembedded entities
        columns_str = ", ".join(select_columns)
        query = f"""
            SELECT {columns_str}
            FROM {pg_table} 
            WHERE {pg_embedded_column} = false 
            ORDER BY created_at ASC
            LIMIT %s;
        """
        entities = pg.fetch_all(query, (limit,))
        
        if not entities:
            logger.info("✅ No unembedded entities found. System coherent.")
            return {
                "status": "success",
                "synced": 0,
                "failed": 0,
                "duration": time.time() - start_time,
                "lag": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"📊 Found {len(entities)} unembedded entities")
        
        # Batch embed entities (API limit: 100 per batch)
        texts = [e[1] for e in entities]  # pg_text_column is index 1
        entity_ids = [e[0] for e in entities]  # pg_id_column is index 0
        
        logger.info(f"🧠 Generating {len(texts)} embeddings...")
        
        # Call embedding API in chunks of 100
        embeddings = []
        BATCH_SIZE = 100
        
        try:
            for i in range(0, len(texts), BATCH_SIZE):
                batch_texts = texts[i:i+BATCH_SIZE]
                logger.info(f"   Processing batch {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1} ({len(batch_texts)} texts)")
                
                response = httpx.post(
                    f"{embedding_api_url}/v1/embeddings/batch",
                    json={"texts": batch_texts},
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()
                
                if not result.get("success") or not result.get("embeddings"):
                    raise Exception(f"API returned success=False or null embeddings: {result.get('error', 'unknown error')}")
                
                embeddings.extend(result["embeddings"])
                
        except Exception as e:
            logger.error(f"❌ Embedding API error: {e}")
            return {
                "status": "error",
                "synced": 0,
                "failed": len(entities),
                "duration": time.time() - start_time,
                "lag": _count_unembedded(pg, pg_table, pg_embedded_column),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Prepare Qdrant points
        points = []
        for entity, embedding in zip(entities, embeddings):
            entity_id = entity[0]  # pg_id_column
            
            # Build payload dynamically
            payload = {
                pg_text_column: entity[1],  # pg_text_column
                "synced_at": datetime.now().isoformat()
            }
            
            # Add metadata columns if specified
            if pg_metadata_columns:
                for i, col in enumerate(pg_metadata_columns):
                    payload[col] = entity[i + 2]  # After id and text
            
            point = {
                "id": entity_id,  # Use PostgreSQL ID as integer (Qdrant accepts int or UUID)
                "vector": embedding,
                "payload": payload
            }
            points.append(point)
        
        # Upsert to Qdrant
        logger.info(f"💾 Upserting {len(points)} points to {qdrant_collection}...")
        try:
            qdrant.upsert(qdrant_collection, points)
        except Exception as e:
            logger.error(f"❌ Qdrant upsert error: {e}")
            return {
                "status": "error",
                "synced": 0,
                "failed": len(phrases),
                "duration": time.time() - start_time,
                "lag": _count_unembedded(pg),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Mark as embedded in PostgreSQL
        logger.info(f"✏️  Marking {len(entity_ids)} entities as embedded...")
        try:
            with pg.connection.cursor() as cur:
                update_query = f"""
                    UPDATE {pg_table} 
                    SET {pg_embedded_column} = true
                    WHERE {pg_id_column} = ANY(%s);
                """
                cur.execute(update_query, (entity_ids,))
                pg.connection.commit()
        except Exception as e:
            logger.error(f"❌ PostgreSQL update error: {e}")
            # Embeddings are in Qdrant but not marked in PG - will retry next sync
            return {
                "status": "partial",
                "synced": len(entities),
                "failed": 0,
                "duration": time.time() - start_time,
                "lag": _count_unembedded(pg, pg_table, pg_embedded_column),
                "timestamp": datetime.now().isoformat(),
                "warning": "Embeddings created but PostgreSQL update failed"
            }
        
        # Log sync event
        _log_sync_event(pg, len(entities), time.time() - start_time)
        
        elapsed = time.time() - start_time
        remaining = _count_unembedded(pg, pg_table, pg_embedded_column)
        
        logger.info(f"✅ Sync complete: {len(entities)} entities in {elapsed:.2f}s ({remaining} remaining)")
        
        return {
            "status": "success",
            "synced": len(entities),
            "failed": 0,
            "duration": elapsed,
            "lag": remaining,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Sync error: {e}", exc_info=True)
        return {
            "status": "error",
            "synced": 0,
            "failed": 0,
            "duration": time.time() - start_time,
            "lag": _count_unembedded(pg, pg_table, pg_embedded_column),
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _count_unembedded(pg: PostgresAgent, pg_table: str, pg_embedded_column: str) -> int:
    """Count remaining unembedded entities."""
    try:
        result = pg.fetch_all(f"SELECT COUNT(*) FROM {pg_table} WHERE {pg_embedded_column} = false;")
        return result[0][0] if result else 0
    except:
        return -1

def _log_sync_event(pg: PostgresAgent, count: int, duration: float):
    """Log sync event to PostgreSQL for audit trail."""
    try:
        query = """
            INSERT INTO memory_sync_logs (sync_type, items_synced, duration_seconds, timestamp)
            VALUES ('entities', %s, %s, NOW())
            ON CONFLICT DO NOTHING;
        """
        pg.execute_query(query, (count, duration))
        pg.connection.commit()
    except Exception as e:
        logger.warning(f"⚠️  Could not log sync event: {e}")

if __name__ == "__main__":
    # Test sync
    logging.basicConfig(level=logging.INFO)
    result = sync_entities_to_qdrant(limit=10)
    print(f"\n{'='*60}")
    print(f"SYNC TEST RESULT")
    print(f"{'='*60}")
    for key, value in result.items():
        print(f"{key}: {value}")
    print(f"{'='*60}\n")
