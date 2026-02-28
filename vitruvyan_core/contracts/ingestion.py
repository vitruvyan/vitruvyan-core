"""
Ingestion Contract — Data Acquisition & Normalization
======================================================

Governs the boundary between external data sources and the Vitruvyan
epistemic kernel.  ALL data entering the system MUST pass through this
contract.

Sacred Order: Perception (Babel Gardens + Codex Hunters)
Downstream consumers: Memory Orders, Vault Keepers, Pattern Weavers

Contract guarantees:
  1. Source identity  — every ingested item has a deterministic source_id
  2. Provenance       — full chain from raw source to normalised payload
  3. Quality gate     — minimum quality_score before Memory acceptance
  4. Schema stability — consumers can depend on field presence
  5. Idempotency      — re-ingesting same source_id is safe (dedup by hash)

LIVELLO 1: Pure Python + Pydantic. No I/O, no external dependencies.

> **Last updated**: February 28, 2026 19:30 UTC

Author: Vitruvyan Core Team
Contract Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import uuid
from abc import abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseContract, IContractPlugin


# ─────────────────────────────────────────────────────────────
# Stream channel constants (Synaptic Conclave dot notation)
# ─────────────────────────────────────────────────────────────

CHANNEL_INGESTION_ACQUIRED   = "perception.ingestion.acquired"    # SourceDescriptor ready
CHANNEL_INGESTION_NORMALIZED = "perception.ingestion.normalized"  # IngestionPayload ready
CHANNEL_INGESTION_REJECTED   = "perception.ingestion.rejected"    # quality gate failed
CHANNEL_INGESTION_DUPLICATE  = "perception.ingestion.duplicate"   # dedup detected


# ─────────────────────────────────────────────────────────────
# SourceType — classification of ingestion sources
# ─────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    """Classification of ingestion sources."""

    FILE       = "file"         # Local/remote file (PDF, CSV, TXT, MD, …)
    API        = "api"          # External API response
    STREAM     = "stream"       # Real-time stream (Redis, Kafka, WebSocket)
    DATABASE   = "database"     # External database query result
    USER_INPUT = "user_input"   # Direct user-provided text
    CRAWL      = "crawl"        # Web crawler output
    SYNTHETIC  = "synthetic"    # System-generated (test, simulation)


# ─────────────────────────────────────────────────────────────
# SourceDescriptor — immutable source identity
# ─────────────────────────────────────────────────────────────

class SourceDescriptor(BaseContract):
    """
    Immutable descriptor for a data source.

    Every piece of data entering Vitruvyan MUST have a SourceDescriptor.
    ``source_id`` is deterministic: same (uri + content) → same id (dedup key).
    """

    CONTRACT_NAME: ClassVar[str]    = "ingestion.source"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "perception"

    source_id: str = Field(description="Deterministic id: hash(uri + content_hash)")
    source_type: SourceType = Field(description="Origin category of this source")
    uri: str = Field(default="", description="Original location (file path, URL, …)")
    content_hash: str = Field(
        default="",
        description="SHA-256 of raw content bytes — primary dedup key",
    )
    mime_type: str = Field(default="text/plain", description="MIME type of raw content")
    language: str = Field(default="auto", description="ISO 639-1 or 'auto' for LLM detection")
    encoding: str = Field(default="utf-8", description="Character encoding of raw content")
    size_bytes: int = Field(default=0, ge=0, description="Raw content size in bytes")
    acquired_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the source was acquired",
    )
    acquired_by: str = Field(
        default="",
        description="Service or Sacred Order that acquired this source",
    )

    # Provenance chain
    parent_source_id: Optional[str] = Field(
        default=None,
        description="source_id of parent document (if derived/chunked)",
    )
    provenance_chain: List[str] = Field(
        default_factory=list,
        description="Ordered list of source_ids from root to this descriptor",
    )

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if not self.source_id:
            violations.append("source_id must not be empty")
        if self.size_bytes < 0:
            violations.append(f"size_bytes must be >= 0, got {self.size_bytes}")
        return violations


# ─────────────────────────────────────────────────────────────
# IngestionQuality — quality gate assessment
# ─────────────────────────────────────────────────────────────

class IngestionQuality(BaseContract):
    """
    Quality assessment of ingested data.

    Populated by Perception BEFORE handoff to Memory Orders.
    Memory Orders MAY reject payloads where ``gate_passed=False``.

    Invariants:
      - gate_passed=True  requires  quality_score >= gate_threshold
      - gate_passed=True  is forbidden when  duplicate_of is set
    """

    CONTRACT_NAME: ClassVar[str]    = "ingestion.quality"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "perception"

    completeness: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction of expected fields that are present",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Extraction/parsing confidence",
    )
    noise_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction of content classified as noise/irrelevant",
    )
    language_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Confidence in detected language",
    )
    encoding_valid: bool = Field(
        default=True,
        description="False if content could not be decoded with declared encoding",
    )
    duplicate_of: Optional[str] = Field(
        default=None,
        description="source_id of canonical duplicate, if dedup detected",
    )
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Composite quality score (0=unusable, 1=perfect)",
    )
    gate_passed: bool = Field(
        default=False,
        description="True when quality_score >= gate_threshold and not a duplicate",
    )
    gate_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Minimum quality_score required to pass the gate",
    )
    assessment_method: str = Field(
        default="auto",
        description="How quality was assessed (auto, manual, heuristic, …)",
    )

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if self.gate_passed and self.quality_score < self.gate_threshold:
            violations.append(
                f"gate_passed=True but quality_score ({self.quality_score:.3f}) "
                f"< gate_threshold ({self.gate_threshold:.3f})"
            )
        if self.gate_passed and self.duplicate_of is not None:
            violations.append(
                f"gate_passed=True for a detected duplicate (duplicate_of='{self.duplicate_of}')"
            )
        return violations


# ─────────────────────────────────────────────────────────────
# NormalizedChunk — single text chunk ready for embedding
# ─────────────────────────────────────────────────────────────

class NormalizedChunk(BaseModel):
    """
    A single normalised text chunk ready for embedding.

    Sub-model of IngestionPayload — does NOT inherit BaseContract because
    it is nested; only top-level contracts register with ContractRegistry.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(
        description="Deterministic id: hash(source_id + chunk_index)",
    )
    chunk_index: int = Field(
        default=0, ge=0,
        description="Zero-based position within the source document",
    )
    text: str = Field(description="Normalised text content of this chunk")
    token_count: int = Field(
        default=0, ge=0,
        description="Approximate token count (model-dependent)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk-level metadata (page, section, heading, …)",
    )


# ─────────────────────────────────────────────────────────────
# IngestionPayload — canonical output from Perception to Memory
# ─────────────────────────────────────────────────────────────

class IngestionPayload(BaseContract):
    """
    Canonical ingestion output — what Perception hands to Memory Orders.

    Contract guarantees:
      - ``source``  is always present (provenance)
      - ``quality`` is always present (gate decision)
      - ``chunks``  contains at least 1 NormalizedChunk (empty = error)
      - ``total_chunks == len(chunks)`` (consistency invariant)
      - ``quality.gate_passed == True`` (only gated payloads reach Memory)

    Downstream consumers (Memory Orders, Vault Keepers) depend on this schema.
    """

    CONTRACT_NAME: ClassVar[str]    = "ingestion.payload"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "perception"

    # Identity
    ingestion_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID for this specific ingestion event",
    )

    # Provenance
    source: SourceDescriptor = Field(description="Source identity and provenance")

    # Quality gate
    quality: IngestionQuality = Field(description="Quality assessment and gate result")

    # Normalised output
    chunks: List[NormalizedChunk] = Field(
        default_factory=list,
        description="Ordered list of normalised text chunks",
    )
    total_chunks: int = Field(
        default=0, ge=0,
        description="Must equal len(chunks) — consistency check",
    )
    total_tokens: int = Field(
        default=0, ge=0,
        description="Sum of token_count across all chunks",
    )

    # Extracted domain-agnostic metadata
    extracted_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Domain-agnostic metadata extracted from source "
            "(title, author, date, tags, …)"
        ),
    )

    # Processing provenance
    processing_pipeline: List[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of processing steps "
            "(e.g. 'codex_hunters.discover', 'babel_gardens.comprehend')"
        ),
    )
    processing_time_ms: float = Field(
        default=0.0, ge=0.0,
        description="Total end-to-end processing time in milliseconds",
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when this payload was assembled",
    )

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if not self.chunks:
            violations.append("IngestionPayload must contain at least 1 NormalizedChunk")
        if self.total_chunks != len(self.chunks):
            violations.append(
                f"total_chunks ({self.total_chunks}) != len(chunks) ({len(self.chunks)})"
            )
        if not self.source.source_id:
            violations.append("source.source_id must not be empty")
        if not self.quality.gate_passed:
            violations.append(
                f"quality gate not passed "
                f"(score={self.quality.quality_score:.3f}, "
                f"threshold={self.quality.gate_threshold:.3f})"
            )
        return violations


# ─────────────────────────────────────────────────────────────
# IIngestionPlugin — domain extension point
# ─────────────────────────────────────────────────────────────

class IIngestionPlugin(IContractPlugin):
    """
    Domain plugin for ingestion customisation.

    Domains implement this to:
      - Declare accepted source types
      - Extract domain-specific metadata from raw text
      - Customise quality gates (e.g. finance may require ticker validation)
      - Apply domain-specific normalisation rules
    """

    PLUGIN_CONTRACT_NAME: ClassVar[str]    = "ingestion_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    PLUGIN_CONTRACT_OWNER: ClassVar[str]   = "perception"

    @abstractmethod
    def get_domain_name(self) -> str:
        """Return the domain identifier (e.g. 'finance', 'energy')."""

    @abstractmethod
    def get_accepted_source_types(self) -> List[SourceType]:
        """Return the list of SourceType values this domain accepts."""

    @abstractmethod
    def extract_domain_metadata(
        self,
        raw_text: str,
        source: SourceDescriptor,
    ) -> Dict[str, Any]:
        """Extract domain-specific metadata from raw text + source descriptor."""

    @abstractmethod
    def get_quality_threshold(self) -> float:
        """Return the minimum quality_score for this domain (default 0.3)."""

    def validate_source(self, source: SourceDescriptor) -> List[str]:
        """
        Optional domain-specific source validation.

        Returns:
            List of violation messages. Empty = source accepted.
        """
        return []

    def normalize_text(self, raw_text: str) -> str:
        """
        Optional domain-specific text normalisation.

        Default implementation returns the text unchanged.
        """
        return raw_text


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────

def compute_content_hash(content: bytes) -> str:
    """
    Return the SHA-256 hex digest of raw content bytes.

    Args:
        content: Raw bytes of the source document.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(content).hexdigest()


def build_source_id(uri: str, content_hash: str) -> str:
    """
    Derive a deterministic source_id from URI + content hash.

    Same (uri, content_hash) always produces the same source_id —
    safe to use as a dedup key.

    Args:
        uri:          Original source location (file path, URL, …).
        content_hash: SHA-256 hex digest of raw content bytes.

    Returns:
        32-character lowercase hex string.
    """
    raw = f"{uri}|{content_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def build_chunk_id(source_id: str, chunk_index: int) -> str:
    """
    Derive a deterministic chunk_id from source_id + chunk index.

    Args:
        source_id:   Deterministic id of the parent source.
        chunk_index: Zero-based position of this chunk in the source.

    Returns:
        32-character lowercase hex string.
    """
    raw = f"{source_id}|{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ─────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────

__all__ = [
    # Channels
    "CHANNEL_INGESTION_ACQUIRED",
    "CHANNEL_INGESTION_NORMALIZED",
    "CHANNEL_INGESTION_REJECTED",
    "CHANNEL_INGESTION_DUPLICATE",
    # Enums
    "SourceType",
    # Contracts
    "SourceDescriptor",
    "IngestionQuality",
    "NormalizedChunk",
    "IngestionPayload",
    # Plugin
    "IIngestionPlugin",
    # Helpers
    "compute_content_hash",
    "build_source_id",
    "build_chunk_id",
]
