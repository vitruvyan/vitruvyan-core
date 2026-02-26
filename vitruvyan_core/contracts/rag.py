"""
RAG Governance Contract — Python Interface
===========================================

Defines the programmatic interfaces for RAG collection governance.

These are the types and validators that enforce the RAG Governance Contract V1.
Services and Sacred Orders import these to declare and validate their collections.

Usage:
    from contracts.rag import CollectionDeclaration, CollectionTier, RAGPayload

Author: vitruvyan-core
Date: February 21, 2026
Contract Version: 1.1.0

Changelog:
    1.1.0 (Phase 4): Multi-model support, collection versioning,
           stale detection utilities, RAG effectiveness metrics.
"""

from __future__ import annotations

import re
import uuid
import hashlib
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Collection Tier Enum ─────────────────────────────────────────────────────

class CollectionTier(str, Enum):
    """
    Collection tier classification.

    CORE:      OS-level, domain-agnostic, permanent
    ORDER:     Sacred Order operational data
    DOMAIN:    Vertical/domain-specific
    EPHEMERAL: Test, migration, temporary
    """
    CORE = "core"
    ORDER = "order"
    DOMAIN = "domain"
    EPHEMERAL = "ephemeral"


# ── Distance Metric Enum ─────────────────────────────────────────────────────

class DistanceMetric(str, Enum):
    """Supported vector distance metrics."""
    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"


# ── Embedding Model Registry ─────────────────────────────────────────────────

@dataclass(frozen=True)
class EmbeddingModel:
    """
    Immutable descriptor for a supported embedding model.

    Each model defines a name and its output vector dimension.
    The registry enforces that collection vector_size matches the model dimension.
    """
    name: str           # e.g., "all-MiniLM-L6-v2"
    dimension: int      # e.g., 384
    family: str = ""    # e.g., "sentence-transformers", "openai"

    def __str__(self) -> str:
        return f"{self.name} (dim={self.dimension})"


# Canonical model registry — extend when adding new models
EMBEDDING_MODELS: Dict[str, EmbeddingModel] = {
    "all-MiniLM-L6-v2": EmbeddingModel(
        name="all-MiniLM-L6-v2",
        dimension=384,
        family="sentence-transformers",
    ),
    "all-mpnet-base-v2": EmbeddingModel(
        name="all-mpnet-base-v2",
        dimension=768,
        family="sentence-transformers",
    ),
    "text-embedding-3-small": EmbeddingModel(
        name="text-embedding-3-small",
        dimension=1536,
        family="openai",
    ),
    "text-embedding-3-large": EmbeddingModel(
        name="text-embedding-3-large",
        dimension=3072,
        family="openai",
    ),
}

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_embedding_model(name: str) -> Optional[EmbeddingModel]:
    """Look up an embedding model by name."""
    return EMBEDDING_MODELS.get(name)


def register_embedding_model(model: EmbeddingModel) -> None:
    """Register a new embedding model at runtime (for domain extensions)."""
    EMBEDDING_MODELS[model.name] = model


# ── Collection Declaration ───────────────────────────────────────────────────

@dataclass(frozen=True)
class CollectionDeclaration:
    """
    Immutable declaration of a Qdrant collection.

    Every collection in a Vitruvyan deployment MUST have a corresponding
    CollectionDeclaration. The init script is the runtime manifestation;
    this dataclass is the programmatic contract.

    Phase 4 additions:
        model_name: Embedding model that produced these vectors (multi-model support).
                    Enables dimension validation and future model migrations.
        version:    Collection schema version (monotonic integer).
                    Supports side-by-side versioned collections (e.g., v1 → v2).
    """
    name: str
    vector_size: int
    distance: DistanceMetric
    tier: CollectionTier
    owner: str          # Sacred Order or domain name
    purpose: str        # Human-readable purpose
    domain: str = "generic"  # Domain tag (e.g., "finance", "mercator")
    model_name: str = DEFAULT_EMBEDDING_MODEL  # Embedding model name
    version: int = 1    # Collection schema version (monotonic)

    def __post_init__(self):
        _validate_collection_name(self.name, self.tier)
        # Validate model_name → vector_size consistency
        model = get_embedding_model(self.model_name)
        if model and model.dimension != self.vector_size:
            raise ValueError(
                f"Collection '{self.name}': vector_size={self.vector_size} "
                f"does not match model '{self.model_name}' dimension={model.dimension}. "
                f"Either fix vector_size or register a custom model."
            )
        if self.version < 1:
            raise ValueError(f"Collection '{self.name}': version must be >= 1, got {self.version}")

    @property
    def description(self) -> str:
        """Format description for init script: '<TIER>: <Owner> — <Purpose>'"""
        return f"{self.tier.value.upper()}: {self.owner} — {self.purpose}"

    @property
    def versioned_name(self) -> str:
        """Collection name with version suffix (v1+ only adds suffix for v2+)."""
        if self.version <= 1:
            return self.name
        return f"{self.name}_v{self.version}"

    def to_init_dict(self) -> Dict[str, Any]:
        """Convert to init script entry format."""
        return {
            "name": self.name,
            "vector_size": self.vector_size,
            "distance": self.distance.value,
            "description": self.description,
            "model_name": self.model_name,
            "version": self.version,
        }


# ── RAG Payload Schema ───────────────────────────────────────────────────────

@dataclass
class RAGPayload:
    """
    Standard payload schema for Qdrant point metadata.

    Every upserted point MUST include `source` and `created_at`.
    `text`, `version`, and `domain` are SHOULD-level fields.
    Additional domain-specific fields can be added via `extra`.
    """
    source: str                     # MUST: origin identifier
    created_at: str = ""            # MUST: ISO 8601 timestamp
    text: Optional[str] = None      # SHOULD: original embedded text
    version: str = "1.0"            # SHOULD: payload schema version
    domain: str = "generic"         # SHOULD: domain tag
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.source:
            raise ValueError("RAGPayload.source is REQUIRED (contract Section 5.2)")

    def to_dict(self) -> Dict[str, Any]:
        """Flatten to Qdrant payload dict."""
        payload = {
            "source": self.source,
            "created_at": self.created_at,
            "version": self.version,
            "domain": self.domain,
        }
        if self.text is not None:
            payload["text"] = self.text
        payload.update(self.extra)
        return payload


# ── Point ID Generation ──────────────────────────────────────────────────────

# Namespace UUID for deterministic point IDs (Vitruvyan RAG namespace)
RAG_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def deterministic_point_id(content: str, collection: str = "") -> str:
    """
    Generate a deterministic UUID v5 point ID from content + collection.

    This ensures upsert idempotency: the same content always gets the same ID,
    preventing duplicates on re-ingestion.

    Args:
        content: The text content being embedded
        collection: Optional collection name for namespace isolation

    Returns:
        UUID string (deterministic, reproducible)
    """
    key = f"{collection}:{content}" if collection else content
    return str(uuid.uuid5(RAG_NAMESPACE, key))


def content_hash_id(content: str) -> str:
    """
    Generate a short hash ID from content (alternative to UUID).

    Returns:
        Hex string (32 chars, MD5-based — NOT for security, only dedup)
    """
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ── Collection Name Validation ───────────────────────────────────────────────

# Name pattern: lowercase letters, digits, underscores, dots (for domain prefix)
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.]{1,62}[a-z0-9]$")
_EPHEMERAL_PREFIXES = ("test_", "tmp_", "migration_")


def _validate_collection_name(name: str, tier: CollectionTier) -> None:
    """Validate collection name against contract rules."""
    if not _NAME_PATTERN.match(name):
        raise ValueError(
            f"Collection name '{name}' violates naming convention: "
            f"must be lowercase, 3-64 chars, start with letter, "
            f"only [a-z0-9_.] allowed"
        )

    if tier == CollectionTier.EPHEMERAL:
        if not any(name.startswith(p) for p in _EPHEMERAL_PREFIXES):
            raise ValueError(
                f"EPHEMERAL collection '{name}' must start with "
                f"one of: {_EPHEMERAL_PREFIXES}"
            )

    if tier == CollectionTier.DOMAIN and "." not in name:
        # Domain collections SHOULD use dot notation, but grandfathered names are OK
        pass  # Warning only — not enforced in V1 for backward compatibility


def validate_collection_name(name: str) -> bool:
    """
    Check if a collection name is valid (without tier check).

    Returns:
        True if valid, False otherwise
    """
    return bool(_NAME_PATTERN.match(name))


# ── Collection Registry ──────────────────────────────────────────────────────

# Canonical core collections (grandfathered names)
CORE_COLLECTIONS: List[CollectionDeclaration] = [
    CollectionDeclaration(
        name="semantic_states",
        vector_size=384,
        distance=DistanceMetric.COSINE,
        tier=CollectionTier.CORE,
        owner="VSGS Engine",
        purpose="Semantic grounding contexts",
    ),
    CollectionDeclaration(
        name="phrases_embeddings",
        vector_size=384,
        distance=DistanceMetric.COSINE,
        tier=CollectionTier.CORE,
        owner="Embedding Service",
        purpose="NLP phrase embeddings (general-purpose RAG)",
    ),
    CollectionDeclaration(
        name="conversations_embeddings",
        vector_size=384,
        distance=DistanceMetric.COSINE,
        tier=CollectionTier.CORE,
        owner="LangGraph",
        purpose="Conversational memory for RAG retrieval",
    ),
]

ORDER_COLLECTIONS: List[CollectionDeclaration] = [
    CollectionDeclaration(
        name="entity_embeddings",
        vector_size=384,
        distance=DistanceMetric.COSINE,
        tier=CollectionTier.ORDER,
        owner="Codex Hunters",
        purpose="Ingested entity semantic embeddings",
    ),
    CollectionDeclaration(
        name="weave_embeddings",
        vector_size=384,
        distance=DistanceMetric.COSINE,
        tier=CollectionTier.ORDER,
        owner="Pattern Weavers",
        purpose="Ontological pattern result embeddings",
    ),
]

# All declared collections (core + order)
ALL_DECLARED_COLLECTIONS: List[CollectionDeclaration] = CORE_COLLECTIONS + ORDER_COLLECTIONS


def get_collection_declaration(name: str) -> Optional[CollectionDeclaration]:
    """Look up a collection declaration by name."""
    for decl in ALL_DECLARED_COLLECTIONS:
        if decl.name == name:
            return decl
    return None


def is_declared_collection(name: str) -> bool:
    """Check if a collection name is declared in the registry."""
    return get_collection_declaration(name) is not None


# ── Stale Detection ──────────────────────────────────────────────────────────

import os

# Default: 30 days (configurable via env)
STALE_THRESHOLD_DAYS = int(os.getenv("RAG_STALE_THRESHOLD_DAYS", "30"))


@dataclass
class StaleReport:
    """Result of stale detection analysis for a single collection."""
    collection: str
    total_points: int
    newest_created_at: Optional[str] = None
    age_days: Optional[float] = None
    is_stale: bool = False
    has_zero_points: bool = False

    @property
    def status(self) -> str:
        if self.has_zero_points:
            return "EMPTY"
        if self.is_stale:
            return f"STALE ({self.age_days:.0f}d)"
        if self.newest_created_at:
            return f"ACTIVE ({self.age_days:.0f}d)"
        return "UNKNOWN"  # no created_at metadata


def check_stale_collection(
    agent: Any,
    collection: str,
    threshold_days: int = STALE_THRESHOLD_DAYS,
    sample_size: int = 10,
) -> StaleReport:
    """
    Check if a collection is stale by sampling its most recent points.

    Queries the collection with a zero-vector to get recent points,
    looks at `created_at` payload field to determine freshness.

    Args:
        agent: QdrantAgent instance (typed as Any to avoid circular imports)
        collection: Collection name to check
        threshold_days: Days without writes to consider stale
        sample_size: Number of points to sample for timestamp

    Returns:
        StaleReport with freshness analysis
    """
    report = StaleReport(collection=collection, total_points=0)

    try:
        count = agent.count_points(collection)
        report.total_points = count

        if count == 0:
            report.has_zero_points = True
            report.is_stale = True
            return report

        # Get collection dimension for zero-vector query
        decl = get_collection_declaration(collection)
        dim = decl.vector_size if decl else 384

        # Search with zero-vector to get a sample of points with payloads
        result = agent.search(
            collection=collection,
            query_vector=[0.0] * dim,
            top_k=sample_size,
            with_payload=True,
        )

        if result.get("status") != "ok" or not result.get("results"):
            return report

        # Find the most recent created_at across sampled points
        # Check multiple timestamp fields (legacy data may use different names)
        _TS_FIELDS = ("created_at", "migrated_at", "synced_at", "timestamp", "updated_at")
        timestamps = []
        for r in result["results"]:
            payload = r.get("payload", {})
            for ts_field in _TS_FIELDS:
                created_at = payload.get(ts_field)
                if not created_at:
                    continue
                try:
                    if isinstance(created_at, (int, float)):
                        # Unix epoch (from time.time())
                        timestamps.append(datetime.fromtimestamp(created_at, tz=timezone.utc))
                    else:
                        # ISO 8601 string
                        ts = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        timestamps.append(ts)
                except (ValueError, TypeError):
                    pass

        if timestamps:
            newest = max(timestamps)
            report.newest_created_at = newest.isoformat()
            age = datetime.now(timezone.utc) - newest
            report.age_days = age.total_seconds() / 86400
            report.is_stale = report.age_days > threshold_days

    except Exception as e:
        logger.warning(f"Stale check failed for '{collection}': {e}")

    return report


# ── RAG Effectiveness Metrics ────────────────────────────────────────────────

@dataclass
class SearchMetrics:
    """
    Metrics for a single RAG search operation.

    Captures score distribution, hit quality, and empty-result tracking.
    Aggregated over time, these reveal retrieval effectiveness trends.
    """
    collection: str
    query_dim: int
    top_k_requested: int
    results_returned: int
    scores: List[float] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def hit_rate(self) -> float:
        """Fraction of top_k slots filled (1.0 = full, 0.0 = empty)."""
        if self.top_k_requested <= 0:
            return 0.0
        return min(1.0, self.results_returned / self.top_k_requested)

    @property
    def avg_score(self) -> float:
        """Mean relevance score of returned results."""
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def max_score(self) -> float:
        """Best (highest) relevance score."""
        return max(self.scores) if self.scores else 0.0

    @property
    def min_score(self) -> float:
        """Worst (lowest) relevance score among returned results."""
        return min(self.scores) if self.scores else 0.0

    @property
    def is_empty(self) -> bool:
        """True if search returned zero results."""
        return self.results_returned == 0

    @property
    def quality_tier(self) -> str:
        """
        Classify search quality into tiers.
        
        - EXCELLENT: avg_score > 0.85
        - GOOD:      avg_score > 0.70
        - FAIR:      avg_score > 0.50
        - POOR:      avg_score > 0.30
        - MISS:      no results or avg < 0.30
        """
        if self.is_empty:
            return "MISS"
        avg = self.avg_score
        if avg > 0.85:
            return "EXCELLENT"
        if avg > 0.70:
            return "GOOD"
        if avg > 0.50:
            return "FAIR"
        if avg > 0.30:
            return "POOR"
        return "MISS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "top_k": self.top_k_requested,
            "returned": self.results_returned,
            "hit_rate": round(self.hit_rate, 3),
            "avg_score": round(self.avg_score, 4),
            "max_score": round(self.max_score, 4),
            "min_score": round(self.min_score, 4),
            "quality": self.quality_tier,
            "timestamp": self.timestamp,
        }


class RAGMetricsCollector:
    """
    In-memory collector for RAG search metrics.

    Accumulates SearchMetrics per collection and provides
    summary statistics for monitoring dashboards and alerting.

    Thread-safe by design: append-only list, read snapshots.
    
    Usage:
        collector = RAGMetricsCollector()
        metrics = collector.record_search("conversations_embeddings", 384, 10, results)
        summary = collector.summary("conversations_embeddings")
    """

    def __init__(self, max_history: int = 1000):
        self._history: List[SearchMetrics] = []
        self._max_history = max_history

    def record_search(
        self,
        collection: str,
        query_dim: int,
        top_k: int,
        results: List[Dict[str, Any]],
    ) -> SearchMetrics:
        """
        Record a search operation's metrics.

        Args:
            collection: Collection searched
            query_dim: Query vector dimension
            top_k: Requested result count
            results: List of result dicts (each must have 'score' key)

        Returns:
            The recorded SearchMetrics instance
        """
        scores = [r.get("score", 0.0) for r in results if "score" in r]
        metrics = SearchMetrics(
            collection=collection,
            query_dim=query_dim,
            top_k_requested=top_k,
            results_returned=len(results),
            scores=scores,
        )
        self._history.append(metrics)

        # Trim history to prevent unbounded memory growth
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return metrics

    def summary(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregate summary of recorded search metrics.

        Args:
            collection: Filter by collection name (None = all)

        Returns:
            Dict with total_searches, empty_rate, avg_hit_rate,
            avg_score, quality_distribution, per_collection breakdown
        """
        entries = self._history
        if collection:
            entries = [e for e in entries if e.collection == collection]

        if not entries:
            return {
                "total_searches": 0,
                "empty_rate": 0.0,
                "avg_hit_rate": 0.0,
                "avg_score": 0.0,
                "quality_distribution": {},
            }

        total = len(entries)
        empty_count = sum(1 for e in entries if e.is_empty)
        avg_hit = sum(e.hit_rate for e in entries) / total
        all_scores = [s for e in entries for s in e.scores]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        # Quality tier distribution
        quality_dist: Dict[str, int] = {}
        for e in entries:
            tier = e.quality_tier
            quality_dist[tier] = quality_dist.get(tier, 0) + 1

        # Per-collection breakdown
        collections: Dict[str, int] = {}
        for e in entries:
            collections[e.collection] = collections.get(e.collection, 0) + 1

        return {
            "total_searches": total,
            "empty_rate": round(empty_count / total, 3),
            "avg_hit_rate": round(avg_hit, 3),
            "avg_score": round(avg_score, 4),
            "quality_distribution": quality_dist,
            "per_collection": collections,
        }

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self._history.clear()


# Global RAG metrics collector (singleton for process-wide metrics)
_rag_metrics: Optional[RAGMetricsCollector] = None


def get_rag_metrics() -> RAGMetricsCollector:
    """Get or create the global RAG metrics collector singleton."""
    global _rag_metrics
    if _rag_metrics is None:
        max_history = int(os.getenv("RAG_METRICS_HISTORY", "1000"))
        _rag_metrics = RAGMetricsCollector(max_history=max_history)
    return _rag_metrics


# ── Collection Version Migration Utilities ───────────────────────────────────

@dataclass
class MigrationPlan:
    """
    Plan for migrating a collection from one version/model to another.

    This is a data structure, not an executor. The actual migration
    requires orchestration (re-embedding, dual-write, cutover).
    """
    source_collection: str
    target_collection: str
    source_version: int
    target_version: int
    source_model: str
    target_model: str
    source_dim: int
    target_dim: int
    requires_reembedding: bool
    estimated_points: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_collection,
            "target": self.target_collection,
            "version": f"v{self.source_version} → v{self.target_version}",
            "model": f"{self.source_model} → {self.target_model}",
            "dimensions": f"{self.source_dim} → {self.target_dim}",
            "requires_reembedding": self.requires_reembedding,
            "estimated_points": self.estimated_points,
        }


def plan_collection_migration(
    current: CollectionDeclaration,
    target_model: str = DEFAULT_EMBEDDING_MODEL,
    target_version: Optional[int] = None,
) -> MigrationPlan:
    """
    Generate a migration plan for upgrading a collection.

    Args:
        current: Current collection declaration
        target_model: New embedding model name
        target_version: New version number (default: current + 1)

    Returns:
        MigrationPlan describing the required changes
    """
    target_ver = target_version or (current.version + 1)
    target_model_info = get_embedding_model(target_model)

    if not target_model_info:
        raise ValueError(
            f"Unknown target model '{target_model}'. "
            f"Register it first with register_embedding_model()."
        )

    target_dim = target_model_info.dimension
    needs_reembed = (target_model != current.model_name)

    # Target collection name: original_name_v{N} for v2+
    target_name = current.name if target_ver == 1 else f"{current.name}_v{target_ver}"

    return MigrationPlan(
        source_collection=current.name,
        target_collection=target_name,
        source_version=current.version,
        target_version=target_ver,
        source_model=current.model_name,
        target_model=target_model,
        source_dim=current.vector_size,
        target_dim=target_dim,
        requires_reembedding=needs_reembed,
    )


# ── Exports ──────────────────────────────────────────────────────────────────

__all__ = [
    # Enums
    "CollectionTier",
    "DistanceMetric",
    # Core types
    "CollectionDeclaration",
    "RAGPayload",
    # Embedding model registry
    "EmbeddingModel",
    "EMBEDDING_MODELS",
    "DEFAULT_EMBEDDING_MODEL",
    "get_embedding_model",
    "register_embedding_model",
    # Point ID generation
    "RAG_NAMESPACE",
    "deterministic_point_id",
    "content_hash_id",
    # Name validation
    "validate_collection_name",
    # Collection registry
    "CORE_COLLECTIONS",
    "ORDER_COLLECTIONS",
    "ALL_DECLARED_COLLECTIONS",
    "get_collection_declaration",
    "is_declared_collection",
    # Stale detection
    "StaleReport",
    "STALE_THRESHOLD_DAYS",
    "check_stale_collection",
    # RAG effectiveness metrics
    "SearchMetrics",
    "RAGMetricsCollector",
    "get_rag_metrics",
    # Migration
    "MigrationPlan",
    "plan_collection_migration",
]
