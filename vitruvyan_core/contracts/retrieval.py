"""
Retrieval Contracts — Query Transformation, Re-Ranking, Citations
=================================================================

Domain-agnostic interfaces for retrieval quality hooks.

The core provides:
- Interfaces (ABC) with sensible pass-through defaults
- Data structures (frozen dataclasses) for ranked results and citations

Verticals provide:
- Concrete implementations (HyDE, cross-encoder, domain re-rankers)
- Registration at service startup

Author: vitruvyan-core
Date: March 10, 2026
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Query Transformation ─────────────────────────────────────────────────────

class IQueryTransformer(ABC):
    """
    Interface for pre-retrieval query transformation.

    Takes a user query and returns one or more search variants.
    Multiple variants trigger parallel searches whose results are merged
    and deduplicated before ranking.

    Verticals implement this to add HyDE, multi-query expansion,
    synonym injection, etc.
    """

    @abstractmethod
    def transform(self, query: str, context: Dict[str, Any]) -> List[str]:
        """
        Transform a query into one or more retrieval variants.

        Args:
            query: Original user query text.
            context: Ambient state (language, intent, domain, tenant_id, etc.)

        Returns:
            List of query strings to search with. Must contain at least
            the original query.
        """
        ...


class DefaultQueryTransformer(IQueryTransformer):
    """Pass-through: returns the original query unchanged."""

    def transform(self, query: str, context: Dict[str, Any]) -> List[str]:
        return [query]


# ── Ranked Result ─────────────────────────────────────────────────────────────

@dataclass
class RankedResult:
    """
    A single retrieval result enriched with ranking metadata.

    Used as the shared currency between retrieval, re-ranking, and citation.
    """

    chunk_id: str
    text: str
    original_score: float
    collection: str = ""
    reranked_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def effective_score(self) -> float:
        """Return reranked score if available, otherwise original."""
        return self.reranked_score if self.reranked_score is not None else self.original_score


# ── Re-Ranking ────────────────────────────────────────────────────────────────

class IReranker(ABC):
    """
    Interface for post-retrieval re-ranking.

    Takes the raw top-K results from Qdrant and re-orders them using
    a more expensive relevance signal (cross-encoder, LLM-as-judge, etc.).

    Verticals implement this; the core provides a no-op default.
    """

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[RankedResult],
        top_k: int = 3,
    ) -> List[RankedResult]:
        """
        Re-rank retrieval results.

        Args:
            query: Original user query.
            results: Raw results from vector search (ordered by cosine).
            top_k: Maximum results to return after re-ranking.

        Returns:
            Re-ordered (and possibly truncated) list of RankedResult,
            with ``reranked_score`` populated.
        """
        ...


class DefaultReranker(IReranker):
    """No-op: returns results in original Qdrant order, truncated to top_k."""

    def rerank(
        self,
        query: str,
        results: List[RankedResult],
        top_k: int = 3,
    ) -> List[RankedResult]:
        return results[:top_k]


# ── Citation ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CitationRef:
    """
    Attribution reference linking a response segment to its source chunk.

    Populated by the CAN/compose layer from the chunks that were actually
    injected into the LLM prompt. Channels decide how (or whether) to
    render citations.
    """

    chunk_id: str
    source_name: str
    text_excerpt: str                 # First 200 chars of the chunk
    relevance_score: float
    collection: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Context Routing (for Phase 3 — inline vs RAG) ────────────────────────────

class ContextRouting(str, Enum):
    """Routing decision for incoming content."""

    INLINE = "inline"       # Inject directly into the prompt
    EMBED = "embed"         # Chunk → embed → Qdrant
    BOTH = "both"           # Inline for current session + persist in RAG


class IContextRouter(ABC):
    """
    Interface that decides whether content goes inline or into RAG.

    The core provides a size-based default. Verticals override with
    domain logic (e.g. "PDFs always go to RAG, short messages inline").
    """

    @abstractmethod
    def route(self, content: str, metadata: Dict[str, Any]) -> ContextRouting:
        """
        Decide how to handle incoming content.

        Args:
            content: The text content to route.
            metadata: Context (file type, size, user preference, etc.)

        Returns:
            ContextRouting decision.
        """
        ...


class DefaultContextRouter(IContextRouter):
    """Size-based routing: small content inline, large content to RAG."""

    def __init__(self, inline_threshold_chars: int = 15_000):
        self.threshold = inline_threshold_chars

    def route(self, content: str, metadata: Dict[str, Any]) -> ContextRouting:
        if len(content) <= self.threshold:
            return ContextRouting.INLINE
        return ContextRouting.EMBED
