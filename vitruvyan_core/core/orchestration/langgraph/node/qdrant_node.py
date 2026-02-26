from typing import Dict, Any, List
import os
import logging
import httpx
from core.agents.qdrant_agent import QdrantAgent

logger = logging.getLogger(__name__)

# Init Qdrant agent once
_agent = QdrantAgent()

# Embedding API endpoint (configurable via env var)
EMBEDDING_API = os.getenv("EMBEDDING_API_URL", "http://embedding:8010/v1/embeddings/batch")


def _get_embedding(text: str) -> List[float]:
    """Generate embedding via localhost API (avoid loading SentenceTransformer)."""
    try:
        response = httpx.post(EMBEDDING_API, json={"texts": [text]}, timeout=10.0)
        response.raise_for_status()
        return response.json()["embeddings"][0]
    except Exception as e:
        raise RuntimeError(f"Embedding API error: {e}")


def qdrant_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic search node — 3-tier RAG cascade with explicit collection names.

    Strategy (RAG Contract V1 compliant — no hardcoded defaults):
    1. conversations_embeddings  — conversational memory (user chat history)
    2. phrases_embeddings        — NLP seed phrases (general-purpose RAG)
    3. weave_embeddings          — ontological patterns (Pattern Weavers)
    4. Save results in state["result"]["hits"]
    """
    text = (state.get("input_text") or "").strip()
    if not text:
        state["error"] = "qdrant_query_empty"
        return state

    try:
        # Generate embedding
        vec = _get_embedding(text)

        # 1️⃣ conversations_embeddings — conversational memory
        res = _agent.search("conversations_embeddings", vec, top_k=5)
        hits = res.get("results", []) if isinstance(res, dict) else (res or [])

        # 2️⃣ phrases_embeddings — NLP seed phrases (explicit collection)
        if not hits:
            _raw_sources = os.getenv("QDRANT_SOURCE_FILTER", "").strip()
            _source_filter = [s.strip() for s in _raw_sources.split(",") if s.strip()] or None
            res = _agent.search_phrases(
                query_vector=vec,
                top_k=5,
                source_filter=_source_filter,
                collection="phrases_embeddings",
            )

            if res.get("status") == "ok":
                hits = [
                    {
                        "id": idx,
                        "score": r["score"],
                        "payload": {
                            "phrase_text": r["phrase_text"],
                            "phrase": r["phrase_text"],  # Legacy field
                            "source": r["source"],
                            "context_type": r["context_type"],
                            "language": r["language"],
                        },
                    }
                    for idx, r in enumerate(res.get("results", []))
                ]

        # 3️⃣ weave_embeddings — ontological patterns (Pattern Weavers)
        if not hits:
            res = _agent.search("weave_embeddings", vec, top_k=5)
            weave_hits = res.get("results", []) if isinstance(res, dict) else (res or [])
            if weave_hits:
                hits = [
                    {
                        "id": h.get("id", idx),
                        "score": h.get("score", 0.0),
                        "payload": {
                            **h.get("payload", {}),
                            "source": "weave_embeddings",
                            "context_type": "ontological_pattern",
                        },
                    }
                    for idx, h in enumerate(weave_hits)
                ]
                logger.info(f"🕸️ [qdrant_node] weave_embeddings fallback: {len(hits)} hits")

        # 4️⃣ Save hits inside result (graph already expects this)
        state["result"] = {
            "route": "semantic_fallback",
            "semantic_fallback": True,
            "summary": f"Semantic search for: {text}",
            "hits": hits,
            "filtered": len(hits) > 0,
        }

        return state

    except Exception as e:
        state["error"] = f"qdrant_search_error:{e}"
        return state
