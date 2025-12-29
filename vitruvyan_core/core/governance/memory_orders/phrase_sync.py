#!/usr/bin/env python3
"""
PHASE A3.3: Memory Orders - Phrase Sync Module
Sacred Order: Memory (PostgreSQL ↔ Qdrant Coherence)

Synchronizes unembedded phrases from PostgreSQL to Qdrant.
Ensures dual-memory coherence via scheduled sync jobs.

Architecture:
- Reads phrases with embedded=false from PostgreSQL
- Generates embeddings via vitruvyan_api_embedding:8010
- Writes to Qdrant phrases_embeddings collection
- Marks phrases as embedded=true in PostgreSQL
- Logs sync metrics to PostgreSQL
- Exposes Prometheus metrics

Usage:
    from core.agents.memory_orders.phrase_sync import sync_phrases_to_qdrant
    
    # Sync next 1000 unembedded phrases
    result = sync_phrases_to_qdrant(limit=1000)
    print(f"Synced {result['synced']} phrases in {result['duration']:.2f}s")
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
COLLECTION_NAME = "phrases_embeddings"
VECTOR_SIZE = 384

def sync_phrases_to_qdrant(limit: int = 1000) -> Dict[str, Any]:
    """
    Sync unembedded phrases from PostgreSQL to Qdrant.
    
    Args:
        limit: Maximum number of phrases to sync in one run
        
    Returns:
        Dict with sync results: {
            "status": "success" | "error",
            "synced": int,
            "failed": int,
            "duration": float,
            "lag": int,  # Total unembedded phrases remaining
            "timestamp": str
        }
    """
    start_time = time.time()
    pg = PostgresAgent()
    qdrant = QdrantAgent()
    
    logger.info(f"🔄 Starting phrase sync (limit={limit})...")
    
    try:
        # Fetch unembedded phrases
        query = """
            SELECT id, phrase_text, context_type, language, source, sentiment
            FROM phrases 
            WHERE embedded = false 
            ORDER BY created_at ASC
            LIMIT %s;
        """
        phrases = pg.fetch_all(query, (limit,))
        
        if not phrases:
            logger.info("✅ No unembedded phrases found. System coherent.")
            return {
                "status": "success",
                "synced": 0,
                "failed": 0,
                "duration": time.time() - start_time,
                "lag": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"📊 Found {len(phrases)} unembedded phrases")
        
        # Batch embed phrases (API limit: 100 per batch)
        texts = [p[1] for p in phrases]  # phrase_text
        phrase_ids = [p[0] for p in phrases]
        
        logger.info(f"🧠 Generating {len(texts)} embeddings...")
        
        # Call embedding API in chunks of 100
        embeddings = []
        BATCH_SIZE = 100
        
        try:
            for i in range(0, len(texts), BATCH_SIZE):
                batch_texts = texts[i:i+BATCH_SIZE]
                logger.info(f"   Processing batch {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1} ({len(batch_texts)} texts)")
                
                response = httpx.post(
                    f"{EMBEDDING_API_URL}/v1/embeddings/batch",
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
                "failed": len(phrases),
                "duration": time.time() - start_time,
                "lag": _count_unembedded(pg),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Prepare Qdrant points
        points = []
        for phrase, embedding in zip(phrases, embeddings):
            phrase_id, phrase_text, context_type, language, source, sentiment = phrase
            
            point = {
                "id": phrase_id,  # Use PostgreSQL ID as integer (Qdrant accepts int or UUID)
                "vector": embedding,
                "payload": {
                    "phrase_text": phrase_text,
                    "context_type": context_type,
                    "language": language or "en",
                    "source": source,
                    "sentiment": sentiment,
                    "synced_at": datetime.now().isoformat()
                }
            }
            points.append(point)
        
        # Upsert to Qdrant
        logger.info(f"💾 Upserting {len(points)} points to Qdrant...")
        try:
            qdrant.upsert(COLLECTION_NAME, points)
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
        logger.info(f"✏️  Marking {len(phrase_ids)} phrases as embedded...")
        try:
            with pg.connection.cursor() as cur:
                update_query = """
                    UPDATE phrases 
                    SET embedded = true
                    WHERE id = ANY(%s);
                """
                cur.execute(update_query, (phrase_ids,))
                pg.connection.commit()
        except Exception as e:
            logger.error(f"❌ PostgreSQL update error: {e}")
            # Embeddings are in Qdrant but not marked in PG - will retry next sync
            return {
                "status": "partial",
                "synced": len(phrases),
                "failed": 0,
                "duration": time.time() - start_time,
                "lag": _count_unembedded(pg),
                "timestamp": datetime.now().isoformat(),
                "warning": "Embeddings created but PostgreSQL update failed"
            }
        
        # Log sync event
        _log_sync_event(pg, len(phrases), time.time() - start_time)
        
        elapsed = time.time() - start_time
        remaining = _count_unembedded(pg)
        
        logger.info(f"✅ Sync complete: {len(phrases)} phrases in {elapsed:.2f}s ({remaining} remaining)")
        
        return {
            "status": "success",
            "synced": len(phrases),
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
            "lag": _count_unembedded(pg),
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _count_unembedded(pg: PostgresAgent) -> int:
    """Count remaining unembedded phrases."""
    try:
        result = pg.fetch_all("SELECT COUNT(*) FROM phrases WHERE embedded = false;")
        return result[0][0] if result else 0
    except:
        return -1

def _log_sync_event(pg: PostgresAgent, count: int, duration: float):
    """Log sync event to PostgreSQL for audit trail."""
    try:
        query = """
            INSERT INTO memory_sync_logs (sync_type, items_synced, duration_seconds, timestamp)
            VALUES ('phrases', %s, %s, NOW())
            ON CONFLICT DO NOTHING;
        """
        pg.execute_query(query, (count, duration))
        pg.connection.commit()
    except Exception as e:
        logger.warning(f"⚠️  Could not log sync event: {e}")

if __name__ == "__main__":
    # Test sync
    logging.basicConfig(level=logging.INFO)
    result = sync_phrases_to_qdrant(limit=10)
    print(f"\n{'='*60}")
    print(f"SYNC TEST RESULT")
    print(f"{'='*60}")
    for key, value in result.items():
        print(f"{key}: {value}")
    print(f"{'='*60}\n")
