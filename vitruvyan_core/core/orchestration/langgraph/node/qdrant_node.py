from typing import Dict, Any
import os
import httpx
from core.agents.qdrant_agent import QdrantAgent

# Init Qdrant agent once
_agent = QdrantAgent()

# Embedding API endpoint (configurable via env var)
EMBEDDING_API = os.getenv("EMBEDDING_API_URL", "http://embedding:8010/v1/embeddings/batch")

def _get_embedding(text: str):
    """Generate embedding via localhost API (avoid loading SentenceTransformer)."""
    try:
        response = httpx.post(EMBEDDING_API, json={"texts": [text]}, timeout=10.0)
        response.raise_for_status()
        return response.json()["embeddings"][0]
    except Exception as e:
        raise RuntimeError(f"Embedding API error: {e}")


def qdrant_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic search node with configurable domain filtering.
    
    Strategy:
    1. Try conversations_embeddings first (user chat history)
    2. Fallback to phrases_embeddings with domain filtering (QDRANT_FILTER_DOMAIN env)
    3. Save results in state["result"]["hits"]
    """
    text = (state.get("input_text") or "").strip()
    if not text:
        state["error"] = "qdrant_query_empty"
        return state

    try:
        # Generate embedding
        vec = _get_embedding(text)

        # 1️⃣ Try conversations_embeddings first (conversational memory)
        res = _agent.search("conversations_embeddings", vec, top_k=5)
        hits = res.get("results", []) if isinstance(res, dict) else (res or [])

        # 2️⃣ Fallback to phrases_embeddings with SMART FILTERING
        if not hits:
            # Domain-agnostic source filtering via env var (comma-separated list)
            _raw_sources = os.getenv("QDRANT_SOURCE_FILTER", "").strip()
            _source_filter = [s.strip() for s in _raw_sources.split(",") if s.strip()] or None
            res = _agent.search_phrases(
                query_vector=vec,
                top_k=5,
                source_filter=_source_filter
            )
            
            # Convert search_phrases format to legacy format (for backwards compatibility)
            if res.get("status") == "ok":
                hits = [
                    {
                        "id": idx,  # Dummy ID for compatibility
                        "score": r["score"],
                        "payload": {
                            "phrase_text": r["phrase_text"],
                            "phrase": r["phrase_text"],  # Legacy field
                            "source": r["source"],
                            "context_type": r["context_type"],
                            "language": r["language"]
                        }
                    }
                    for idx, r in enumerate(res.get("results", []))
                ]

        # 3️⃣ Save hits inside result (graph already expects this)
        state["result"] = {
            "route": "semantic_fallback",
            "semantic_fallback": True,  # ✅ Flag for compose_node
            "summary": f"Semantic search for: {text}",
            "hits": hits,
            "filtered": len(hits) > 0  # Indicates filtering was applied
        }

        return state

    except Exception as e:
        state["error"] = f"qdrant_search_error:{e}"
        return state
