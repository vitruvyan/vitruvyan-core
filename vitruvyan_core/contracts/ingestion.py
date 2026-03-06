"""
Vitruvyan Contracts — Ingestion Contract V1
============================================
Defines the canonical interface for the Perception / Ingestion layer.

All sources (web, files, APIs, streams) that feed the Epistemic OS MUST
conform to this contract when normalising raw content into NormalizedChunks.

Channels (emitted by Codex Hunters / Perception order):
    CHANNEL_INGESTION_ACQUIRED    — raw source acquired, not yet normalised
    CHANNEL_INGESTION_NORMALIZED  — chunk normalised and ready for embedding
    CHANNEL_INGESTION_DUPLICATE   — duplicate detected, chunk discarded
    CHANNEL_INGESTION_REJECTED    — chunk failed validation / quality gate

Author: Vitruvyan Core Team
Created: March 2026
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import uuid
from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field

from .base import BaseContract, IContractPlugin

# ---------------------------------------------------------------------------
# Channel constants
# ---------------------------------------------------------------------------

CHANNEL_INGESTION_ACQUIRED   = "ingestion.acquired"
CHANNEL_INGESTION_NORMALIZED = "ingestion.normalized"
CHANNEL_INGESTION_DUPLICATE  = "ingestion.duplicate"
CHANNEL_INGESTION_REJECTED   = "ingestion.rejected"


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SourceType(str, Enum):
    WEB         = "web"
    FILE        = "file"
    API         = "api"
    STREAM      = "stream"
    DATABASE    = "database"
    MANUAL      = "manual"
    SYNTHETIC   = "synthetic"


class IngestionQuality(str, Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

class SourceDescriptor(BaseContract):
    """Identifies a content source."""

    CONTRACT_NAME:    ClassVar[str] = "ingestion.source_descriptor"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "perception"

    source_id:   str         = Field(..., description="Canonical source identifier")
    source_type: SourceType  = Field(..., description="Source category")
    uri:         str         = Field(..., description="Canonical URI of the source")
    metadata:    Dict[str, Any] = Field(default_factory=dict)


class NormalizedChunk(BaseContract):
    """
    A single normalised unit of content ready for embedding / storage.

    Every chunk MUST have:
        - chunk_id  — stable deterministic ID (use build_chunk_id)
        - source_id — links back to SourceDescriptor
        - content   — plain-text content (after pre-processing)
        - content_hash — SHA-256 of content (use compute_content_hash)
    """

    CONTRACT_NAME:    ClassVar[str] = "ingestion.normalized_chunk"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "perception"

    chunk_id:      str             = Field(..., description="Deterministic chunk ID")
    source_id:     str             = Field(..., description="Parent source ID")
    content:       str             = Field(..., description="Normalised text content")
    content_hash:  str             = Field(..., description="SHA-256 of content")
    quality:       IngestionQuality = Field(default=IngestionQuality.UNKNOWN)
    language:      Optional[str]   = Field(default=None)
    position:      Optional[int]   = Field(default=None, description="Chunk order within source")
    metadata:      Dict[str, Any]  = Field(default_factory=dict)
    tags:          List[str]       = Field(default_factory=list)


class IngestionPayload(BaseContract):
    """
    Event payload emitted on CHANNEL_INGESTION_NORMALIZED.
    Carries one or more NormalizedChunks from a single ingestion run.
    """

    CONTRACT_NAME:    ClassVar[str] = "ingestion.payload"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER:   ClassVar[str] = "perception"

    ingestion_id:  str                  = Field(default_factory=lambda: str(uuid.uuid4()))
    source:        SourceDescriptor
    chunks:        List[NormalizedChunk] = Field(default_factory=list)
    total_chunks:  int                  = Field(default=0)
    metadata:      Dict[str, Any]       = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Plugin interface
# ---------------------------------------------------------------------------

class IIngestionPlugin(IContractPlugin):
    """
    Interface for Perception-layer ingestion plugins.

    Implement ingest() to normalise a raw source into NormalizedChunks.
    """

    PLUGIN_CONTRACT_NAME:    ClassVar[str] = "ingestion_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    PLUGIN_CONTRACT_OWNER:   ClassVar[str] = "perception"

    @abstractmethod
    def ingest(self, source: SourceDescriptor, raw: Any) -> List[NormalizedChunk]:
        """Normalise raw content from source into chunks."""
        ...

    @abstractmethod
    def can_handle(self, source_type: SourceType) -> bool:
        """Return True if this plugin handles the given source type."""
        ...


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def compute_content_hash(content: str) -> str:
    """Return SHA-256 hex digest of content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_source_id(source_type: SourceType, uri: str) -> str:
    """
    Build a stable source ID from type + URI.
    Format: <type>:<sha256[:16] of uri>
    """
    uri_hash = hashlib.sha256(uri.encode("utf-8")).hexdigest()[:16]
    return f"{source_type.value}:{uri_hash}"


def build_chunk_id(source_id: str, content_hash: str, position: int = 0) -> str:
    """
    Build a stable chunk ID from source_id + content_hash + position.
    Deterministic: same inputs → same ID.
    """
    raw = f"{source_id}:{content_hash}:{position}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
