# core/langgraph/node/semantic_grounding_node.py
"""
🧠 VSGS Semantic Grounding Node
Sacred Order: Discourse (Semantic Context Enrichment)

Transforms Gemma Embedding from passive vector service to active memory layer.
Enriches LangGraph state with semantic context from historical conversations.

Pipeline:
1. Generate embedding for user_input (via Gemma/MiniLM-L6-v2)
2. Query Qdrant semantic_states collection (top-k similar contexts)
3. Store results in state["semantic_matches"]
4. Audit log to PostgreSQL + publish Memory Orders event
5. Update Prometheus metrics

Feature Flag:
- VSGS_ENABLED=0: Node returns immediately (no-op, bootstrap phase)
- VSGS_ENABLED=1: Full semantic grounding active

Environment Variables:
- VSGS_ENABLED: Master feature flag (0/1)
- VSGS_GROUNDING_TOPK: Number of top matches (default: 3)
- VSGS_COLLECTION_NAME: Qdrant collection (default: semantic_states)

State Updates:
- semantic_matches: List[Dict] - Top-k similar contexts from Qdrant
- vsgs_status: str - "enabled", "disabled", "error"
- vsgs_elapsed_ms: float - Processing time

Integration:
- Placement: After babel_emotion_node, before exec_node/llm_soft_node
- Memory Orders: Publishes 'semantic.grounding.completed' event
- Audit: Logs to log_agent table via audit()
- Metrics: Updates vsgs_grounding_requests_total, vsgs_grounding_hits_total

Usage in graph_flow.py:
    from core.langgraph.node.semantic_grounding_node import semantic_grounding_node
    
    g.add_node("semantic_grounding", semantic_grounding_node)
    g.add_edge("babel_emotion", "semantic_grounding")
    g.add_edge("semantic_grounding", "exec")
"""

import os
import time
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx
from dotenv import load_dotenv
from qdrant_client import models

# VSGS Infrastructure
# from core.logging.audit import audit, audit_error, audit_performance  # TODO: Not available in vitruvyan-os
# from core.leo.qdrant_agent import QdrantAgent  # DEPRECATED path

# Correct imports for vitruvyan-os
try:
    from core.monitoring.vsgs_metrics import (
        record_grounding_request,
        record_grounding_hit,
        record_embedding_latency,
        record_qdrant_latency,
        record_error
    )
except ImportError:
    # Stubs if monitoring not available
    def record_grounding_request(*args, **kwargs): pass
    def record_grounding_hit(*args, **kwargs): pass
    def record_embedding_latency(*args, **kwargs): pass
    def record_qdrant_latency(*args, **kwargs): pass
    def record_error(*args, **kwargs): pass

from core.foundation.persistence.qdrant_agent import QdrantAgent

# Stub audit functions
def audit(*args, **kwargs):
    pass

def audit_error(*args, **kwargs):
    pass

def audit_performance(*args, **kwargs):
    pass

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================
# Configuration (Feature Flags + Hyperparameters)
# ============================================================

VSGS_ENABLED = int(os.getenv("VSGS_ENABLED", "0"))  # ✅ DEFAULT: OFF (bootstrap phase)
VSGS_GROUNDING_TOPK = int(os.getenv("VSGS_GROUNDING_TOPK", "3"))
VSGS_COLLECTION_NAME = os.getenv("VSGS_COLLECTION_NAME", "semantic_states")
from config.api_config import get_embedding_url

EMBEDDING_API_URL = get_embedding_url()

# ============================================================
# Global Embedding Client (initialized once, reused)
# ============================================================

_EMBEDDING_CLIENT = None
_QDRANT_CLIENT = None

def _get_embedding_client():
    """Lazy-load embedding API client with timeout"""
    global _EMBEDDING_CLIENT
    if _EMBEDDING_CLIENT is None:
        # 🚀 OPTIMIZATION (Nov 20, 2025): Reduce timeout to prevent hangs
        _EMBEDDING_CLIENT = httpx.Client(timeout=5.0)  # Was 10.0
    return _EMBEDDING_CLIENT

def _get_qdrant_client():
    """Lazy-load Qdrant agent"""
    global _QDRANT_CLIENT
    if _QDRANT_CLIENT is None:
        _QDRANT_CLIENT = QdrantAgent()
    return _QDRANT_CLIENT


# ============================================================
# Core Functions
# ============================================================

def _generate_embedding(text: str) -> List[float]:
    """
    Generate 384-dim embedding via Gemma/MiniLM-L6-v2.
    
    Args:
        text: User query text
    
    Returns:
        List of 384 floats (embedding vector)
    
    Raises:
        Exception: If embedding API fails
    """
    start_time = time.time()
    
    try:
        client = _get_embedding_client()
        
        response = client.post(
            f"{EMBEDDING_API_URL}/v1/embeddings/batch",
            json={"texts": [text]},
            timeout=3.0  # 🚀 OPTIMIZATION: Tighter timeout (was 5.0)
        )
        
        if response.status_code != 200:
            raise Exception(f"Embedding API returned {response.status_code}: {response.text}")
        
        result = response.json()
        embedding = result["embeddings"][0]
        
        elapsed_ms = (time.time() - start_time) * 1000
        record_embedding_latency(elapsed_ms, model="minilm")
        
        logger.debug(f"✅ [VSGS] Generated embedding ({len(embedding)}d) in {elapsed_ms:.2f}ms")
        
        return embedding
        
    except Exception as e:
        logger.error(f"❌ [VSGS] Embedding generation failed: {e}")
        record_error("embedding_failed", "semantic_grounding")
        raise


def _query_semantic_context(
    embedding: List[float],
    user_id: str,
    top_k: int = VSGS_GROUNDING_TOPK
) -> List[Dict[str, Any]]:
    """
    Query Qdrant for top-k similar semantic contexts.
    
    Args:
        embedding: 384-dim query vector
        user_id: User context filter
        top_k: Number of results to return
    
    Returns:
        List of dicts: [{"text": "...", "score": 0.87, "metadata": {...}}, ...]
    
    Raises:
        Exception: If Qdrant query fails
    """
    start_time = time.time()
    
    try:
        qdrant = _get_qdrant_client()
        
        # Query Qdrant semantic_states collection
        results = qdrant.search(
            collection=VSGS_COLLECTION_NAME,
            query_vector=embedding,
            top_k=top_k,  # ✅ Already limited to 3 by default
            qfilter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        record_qdrant_latency(elapsed_ms, collection=VSGS_COLLECTION_NAME, operation="search")
        
        # Check if search was successful
        if results.get("status") != "ok":
            logger.error(f"❌ [VSGS] Qdrant search failed: {results.get('error')}")
            return []
        
        # Format results
        matches = []
        for result in results.get("results", []):
            score = result.get("score", 0)
            payload = result.get("payload", {})
            
            match_quality = "high" if score > 0.8 else ("medium" if score > 0.6 else "low")
            record_grounding_hit(user_id=user_id, collection=VSGS_COLLECTION_NAME, match_quality=match_quality)
            
            matches.append({
                "text": payload.get("query_text", ""),
                "score": score,
                "intent": payload.get("intent"),
                "language": payload.get("language"),
                "timestamp": payload.get("timestamp"),
                "trace_id": payload.get("trace_id"),
                "metadata": payload
            })
        
        top_score = matches[0]['score'] if matches else 0.0
        logger.debug(
            f"✅ [VSGS] Found {len(matches)} semantic matches in {elapsed_ms:.2f}ms "
            f"(top_score={top_score:.3f})"
        )
        
        return matches
        
    except Exception as e:
        logger.error(f"❌ [VSGS] Qdrant query failed: {e}")
        record_error("qdrant_query_failed", "semantic_grounding")
        raise


# ============================================================
# Main Node Function
# ============================================================

def semantic_grounding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🧠 VSGS Semantic Grounding Node
    
    Enriches state with semantic context from historical conversations.
    
    Args:
        state: LangGraph state dict
    
    Returns:
        Updated state with:
        - semantic_matches: List[Dict] (top-k similar contexts)
        - vsgs_status: str ("enabled", "disabled", "error")
        - vsgs_elapsed_ms: float
    
    Feature Flag:
        VSGS_ENABLED=0 → Returns immediately (no-op)
        VSGS_ENABLED=1 → Full semantic grounding
    
    Example:
        state = semantic_grounding_node({
            "input_text": "analizza AAPL trend",
            "user_id": "demo",
            "trace_id": "a1b2c3d4-...",
            "intent": "trend",
            "language": "it"
        })
        
        # state now contains:
        # {
        #   "semantic_matches": [
        #     {"text": "analizza NVDA momentum", "score": 0.87, "intent": "momentum"},
        #     {"text": "AAPL breve termine", "score": 0.82, "intent": "trend"},
        #     ...
        #   ],
        #   "vsgs_status": "enabled",
        #   "vsgs_elapsed_ms": 23.5
        # }
    """
    
    start_time = time.time()
    
    # Extract state fields
    input_text = state.get("input_text", "")
    user_id = state.get("user_id", "demo")
    trace_id = state.get("trace_id", "unknown")
    intent = state.get("intent", "unknown")
    language = state.get("language", "en")
    
    # ============================================================
    # FEATURE FLAG CHECK (Bootstrap Phase Default: OFF)
    # ============================================================
    
    if VSGS_ENABLED == 0:
        logger.debug("⚠️ [VSGS] Feature flag OFF (VSGS_ENABLED=0), skipping semantic grounding")
        state["vsgs_status"] = "disabled"
        state["semantic_matches"] = []
        state["vsgs_elapsed_ms"] = 0.0
        return state
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    if not input_text or not input_text.strip():
        logger.warning(f"⚠️ [VSGS] No input_text provided (trace_id={trace_id[:8]}...)")
        state["vsgs_status"] = "skipped"
        state["semantic_matches"] = []
        state["vsgs_elapsed_ms"] = 0.0
        return state
    
    # ============================================================
    # SEMANTIC GROUNDING PIPELINE
    # ============================================================
    
    try:
        # Record metrics
        record_grounding_request(user_id=user_id, intent=intent, language=language)
        
        # 1. Generate embedding
        logger.info(f"🧠 [VSGS] Grounding query: '{input_text[:50]}...' (user={user_id}, trace={trace_id[:8]}...)")
        embedding = _generate_embedding(input_text)
        
        # 2. Query Qdrant for semantic context
        semantic_matches = _query_semantic_context(
            embedding=embedding,
            user_id=user_id,
            top_k=VSGS_GROUNDING_TOPK
        )
        
        # 3. Update state
        state["semantic_matches"] = semantic_matches
        state["vsgs_status"] = "enabled"
        
        elapsed_ms = (time.time() - start_time) * 1000
        state["vsgs_elapsed_ms"] = elapsed_ms
        
        # ============================================================
        # 🧠 VSGS PR-B: DUAL WRITE (PostgreSQL + Qdrant)
        # Save the NEW user query (not the matches!) for future retrieval
        # ============================================================
        
        # Always save new query (even if no matches found)
        try:
            import hashlib
            import numpy as np
            import psycopg2
            from core.leo.postgres_agent import save_grounding_event
            from core.leo.qdrant_agent import QdrantAgent
            from core.monitoring.vsgs_metrics import vsgs_ingest_total
            
            # Generate phrase_hash for deduplication
            phrase_hash = hashlib.sha256(
                f"{user_id}:{input_text}:{language}".encode()
            ).hexdigest()
            
            # Calculate grounding confidence (mean of match scores, or 0 if no matches)
            if semantic_matches:
                grounding_confidence = float(np.mean([m["score"] for m in semantic_matches]))
            else:
                grounding_confidence = 0.0
            
            # Get affective state from state (if available from babel_emotion_node)
            affective_state = state.get("emotion", None)
            
            # Save to PostgreSQL (Archivarium)
            pg_conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            
            grounding_id = save_grounding_event(
                pg_conn,
                user_id=user_id,
                trace_id=trace_id,
                query_text=input_text,
                language=language,
                affective_state=affective_state,
                semantic_context=semantic_matches,
                grounding_confidence=grounding_confidence,
                phrase_hash=phrase_hash,
                phase="ingest"
            )
            
            pg_conn.close()
            
            if grounding_id:
                logger.info(f"✅ [VSGS PR-B] Saved grounding event to PostgreSQL (id={grounding_id})")
            else:
                logger.warning(f"⚠️ [VSGS PR-B] Grounding event already exists (phrase_hash={phrase_hash[:16]}...)")
            
            # Upsert NEW USER QUERY to Qdrant (Mnemosyne) - for future retrieval
            # 🐛 FIX (Dec 27, 2025): Save the NEW query with embedding, not old matches
            qdrant = QdrantAgent()
            
            from qdrant_client.models import PointStruct
            import uuid
            
            # Create point for the NEW user query
            new_query_point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,  # The embedding we generated for THIS query
                payload={
                    "user_id": user_id,
                    "query_text": input_text,
                    "text": input_text,  # Alias for compatibility
                    "intent": intent,
                    "language": language,
                    "entity_ids": state.get("entity_ids", []),
                    "horizon": state.get("horizon", "medium"),
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat(),
                    "phase": "ingest",
                    "grounding_confidence": grounding_confidence
                }
            )
            
            try:
                qdrant.client.upsert(
                    collection_name="semantic_states",
                    points=[new_query_point]
                )
                logger.info(f"✅ [VSGS PR-B] Saved new query to Qdrant (id={new_query_point.id[:8]}...)")
            except Exception as qdrant_err:
                logger.error(f"❌ [VSGS PR-B] Qdrant upsert failed: {qdrant_err}")
            
            # Update Prometheus metrics (source = semantic_grounding_node)
            vsgs_ingest_total.labels(user_id=user_id, source="semantic_grounding").inc()
            
            # Audit dual write (now saving NEW query, not old matches)
            audit(
                agent="semantic_ingestion",
                payload={
                    "grounding_id": grounding_id,
                    "new_query_saved": True,
                    "matches_found": len(semantic_matches),
                    "phase": "ingest",
                    "phrase_hash": phrase_hash[:16],
                    "grounding_confidence": grounding_confidence
                },
                trace_id=trace_id,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"❌ [VSGS PR-B] Dual write failed: {e}", exc_info=True)
            
            # Audit error (non-blocking, grounding still succeeded)
            audit(
                agent="semantic_ingestion",
                payload={
                    "error": str(e),
                    "phase": "ingest",
                    "status": "failed"
                },
                trace_id=trace_id,
                user_id=user_id
            )
        
        # ============================================================
        # END DUAL WRITE
        # ============================================================
        
        # 4. Audit log (original)
        top_score = semantic_matches[0]["score"] if semantic_matches and len(semantic_matches) > 0 else 0.0
        audit(
            agent="semantic_grounding",
            payload={
                "query": input_text[:100],
                "matches_found": len(semantic_matches),
                "top_score": top_score,
                "elapsed_ms": elapsed_ms,
                "intent": intent,
                "language": language
            },
            trace_id=trace_id,
            user_id=user_id
        )
        
        # 5. Performance audit
        audit_performance(
            agent="semantic_grounding",
            operation="grounding_query",
            elapsed_ms=elapsed_ms,
            metadata={
                "matches": len(semantic_matches),
                "top_k": VSGS_GROUNDING_TOPK,
                "collection": VSGS_COLLECTION_NAME
            },
            trace_id=trace_id,
            user_id=user_id
        )
        
        top_score_log = semantic_matches[0]['score'] if semantic_matches and len(semantic_matches) > 0 else 0.0
        logger.info(
            f"✅ [VSGS] Grounding complete: {len(semantic_matches)} matches in {elapsed_ms:.2f}ms "
            f"(top_score={top_score_log:.3f})"
        )
        
        return state
        
    except Exception as e:
        logger.error(f"❌ [VSGS] Semantic grounding failed: {e}", exc_info=True)
        
        # Audit error
        audit_error(
            agent="semantic_grounding",
            error=e,
            context={"input_text": input_text[:100], "user_id": user_id},
            trace_id=trace_id,
            user_id=user_id
        )
        
        # Graceful degradation: return empty matches
        state["vsgs_status"] = "error"
        state["semantic_matches"] = []
        state["vsgs_elapsed_ms"] = (time.time() - start_time) * 1000
        state["vsgs_error"] = str(e)
        
        return state
