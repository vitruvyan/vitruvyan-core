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
Contract Version: 1.0.0
"""

from __future__ import annotations

import re
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


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


# ── Collection Declaration ───────────────────────────────────────────────────

@dataclass(frozen=True)
class CollectionDeclaration:
    """
    Immutable declaration of a Qdrant collection.

    Every collection in a Vitruvyan deployment MUST have a corresponding
    CollectionDeclaration. The init script is the runtime manifestation;
    this dataclass is the programmatic contract.
    """
    name: str
    vector_size: int
    distance: DistanceMetric
    tier: CollectionTier
    owner: str          # Sacred Order or domain name
    purpose: str        # Human-readable purpose
    domain: str = "generic"  # Domain tag (e.g., "finance", "mercator")

    def __post_init__(self):
        _validate_collection_name(self.name, self.tier)

    @property
    def description(self) -> str:
        """Format description for init script: '<TIER>: <Owner> — <Purpose>'"""
        return f"{self.tier.value.upper()}: {self.owner} — {self.purpose}"

    def to_init_dict(self) -> Dict[str, Any]:
        """Convert to init script entry format."""
        return {
            "name": self.name,
            "vector_size": self.vector_size,
            "distance": self.distance.value,
            "description": self.description,
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


# ── Exports ──────────────────────────────────────────────────────────────────

__all__ = [
    "CollectionTier",
    "CollectionDeclaration",
    "DistanceMetric",
    "RAGPayload",
    "RAG_NAMESPACE",
    "deterministic_point_id",
    "content_hash_id",
    "validate_collection_name",
    "CORE_COLLECTIONS",
    "ORDER_COLLECTIONS",
    "ALL_DECLARED_COLLECTIONS",
    "get_collection_declaration",
    "is_declared_collection",
]
