"""
VSGS Engine — Vitruvyan Semantic Grounding System

Reusable semantic grounding pipeline:
  1. Generate embedding for text (via embedding API)
  2. Search Qdrant for top-k similar contexts
  3. Classify match quality
  4. Return structured GroundingResult

This engine is callable from ANY context — LangGraph node, API endpoint,
batch job, REPL. The LangGraph node is a thin adapter over this engine.

Infrastructure dependencies (QdrantAgent, httpx) are injected or
lazy-loaded — no imports at module level except types.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from .types import GroundingConfig, SemanticMatch, GroundingResult

logger = logging.getLogger(__name__)


class VSGSEngine:
    """Semantic grounding engine. Embed → Search → Classify → Return.

    Args:
        config: GroundingConfig with thresholds and parameters
        embedding_url: URL for embedding API (e.g., "http://gemma:8003")
        qdrant_agent: Optional pre-initialized QdrantAgent (lazy-loaded if None)
    """

    def __init__(self, config: GroundingConfig,
                 embedding_url: str = "",
                 qdrant_agent=None):
        self.config = config
        self.embedding_url = embedding_url
        self._qdrant = qdrant_agent
        self._http_client = None
        logger.info("VSGS Engine initialized (collection=%s, top_k=%d)",
                     config.collection, config.top_k)

    # ── Public API ───────────────────────────────────────────────────────────

    def ground(self, text: str, user_id: str = "demo",
               intent: str = "unknown",
               language: str = "en",
               tenant_id: str = "") -> GroundingResult:
        """Run full semantic grounding pipeline.

        Args:
            text: Input text to ground semantically
            user_id: User filter for Qdrant search
            intent: Detected intent (for metrics)
            language: Detected language (for metrics)
            tenant_id: Optional tenant for data isolation

        Returns:
            GroundingResult with matches, status, and timing
        """
        if not self.config.enabled:
            return GroundingResult([], "disabled")

        if not text or not text.strip():
            return GroundingResult([], "skipped")

        start = time.time()
        try:
            # Phase 1: Generate embedding
            embedding = self._embed(text)

            # Phase 2: Search Qdrant
            raw_results = self._search(embedding, user_id, tenant_id=tenant_id)

            # Phase 3: Classify and format
            matches = self._format_matches(raw_results)

            elapsed = (time.time() - start) * 1000
            logger.debug("VSGS grounding: %d matches in %.1fms (top=%.3f)",
                         len(matches), elapsed,
                         matches[0].score if matches else 0.0)

            return GroundingResult(matches, "enabled", elapsed)

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error("VSGS grounding failed: %s", e)
            return GroundingResult([], "error", elapsed, str(e))

    def embed_only(self, text: str) -> List[float]:
        """Generate embedding without searching. Useful for ingestion."""
        return self._embed(text)

    # ── Phase 1: Embedding ───────────────────────────────────────────────────

    def _embed(self, text: str) -> List[float]:
        """Generate embedding via external API (Gemma/MiniLM)."""
        import httpx

        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self.config.embedding_timeout)

        response = self._http_client.post(
            f"{self.embedding_url}/v1/embeddings/batch",
            json={"texts": [text]},
            timeout=self.config.embedding_timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Embedding API {response.status_code}: {response.text}")

        return response.json()["embeddings"][0]

    # ── Phase 2: Qdrant search ───────────────────────────────────────────────

    def _search(self, embedding: List[float],
                user_id: str,
                tenant_id: str = "") -> List[Dict[str, Any]]:
        """Query Qdrant for top-k semantic matches.

        If tenant_id is provided, applies a payload filter for data isolation.
        Without tenant_id, behaviour is unchanged (backward compatible).
        """
        qdrant = self._get_qdrant()

        # Build tenant filter if tenant_id is provided
        qfilter = None
        if tenant_id:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                qfilter = Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                )
            except ImportError:
                logger.warning("qdrant_client.models not available — tenant filter skipped")

        results = qdrant.search(
            collection=self.config.collection,
            query_vector=embedding,
            top_k=self.config.top_k,
            qfilter=qfilter,
        )

        if results.get("status") != "ok":
            logger.error("Qdrant search failed: %s", results.get("error"))
            return []

        return results.get("results", [])

    # ── Phase 3: Classify & format ───────────────────────────────────────────

    def _format_matches(self,
                        raw_results: List[Dict[str, Any]]) -> List[SemanticMatch]:
        """Convert raw Qdrant results to SemanticMatch objects."""
        matches = []
        for r in raw_results:
            score = r.get("score", 0.0)
            payload = r.get("payload", {})
            matches.append(SemanticMatch(
                text=payload.get("text", "") or payload.get("query_text", ""),
                score=score,
                quality=self._classify(score),
                intent=payload.get("intent"),
                language=payload.get("language"),
                timestamp=payload.get("timestamp"),
                trace_id=payload.get("trace_id"),
                metadata=payload,
            ))
        return matches

    def _classify(self, score: float) -> str:
        """Classify match quality based on configurable thresholds."""
        if score > self.config.high_threshold:
            return "high"
        elif score > self.config.medium_threshold:
            return "medium"
        return "low"

    # ── Infrastructure ───────────────────────────────────────────────────────

    def _get_qdrant(self):
        """Lazy-load QdrantAgent."""
        if self._qdrant is None:
            from core.agents.qdrant_agent import QdrantAgent
            self._qdrant = QdrantAgent()
        return self._qdrant

    def close(self):
        """Clean up HTTP client."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None
