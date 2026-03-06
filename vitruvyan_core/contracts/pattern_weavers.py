"""
Pattern Weavers v3 — Semantic Compilation Contracts
====================================================

Canonical output contract for the Pattern Weavers semantic compiler.
Consumed by intent_detection_node, entity_resolver_node, compose_node,
and any downstream node that needs structured ontology context.

Schema: strict (extra="forbid") — any LLM hallucination of extra fields
is rejected at parse time.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Vitruvyan Core Team
Version: 3.0.0
"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseContract, IContractPlugin


# ─────────────────────────────────────────────────────────────
# Gate — Is the query in-domain?
# ─────────────────────────────────────────────────────────────

class GateVerdict(str, Enum):
    """Domain gate verdict."""
    IN_DOMAIN = "in_domain"
    OUT_OF_DOMAIN = "out_of_domain"
    AMBIGUOUS = "ambiguous"


class DomainGate(BaseModel):
    """Domain gate result."""
    model_config = ConfigDict(extra="forbid")

    verdict: GateVerdict = GateVerdict.AMBIGUOUS
    domain: str = "generic"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""


# ─────────────────────────────────────────────────────────────
# Entities — Resolved domain objects from the query
# ─────────────────────────────────────────────────────────────

class OntologyEntity(BaseModel):
    """A single resolved entity."""
    model_config = ConfigDict(extra="forbid")

    raw: str                    # What appeared in the query
    canonical: str              # Normalized / resolved form
    entity_type: str            # Domain-defined type (e.g. "ticker", "concept")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# ─────────────────────────────────────────────────────────────
# OntologyPayload — The semantic compilation output
# ─────────────────────────────────────────────────────────────

class OntologyPayload(BaseContract):
    """
    The semantic compilation contract.

    Produced by Pattern Weavers /compile endpoint.
    Consumed by intent_detection and all downstream graph nodes.

    Invariant: ``extra="forbid"`` — unknown fields cause ValidationError.
    """

    CONTRACT_NAME: ClassVar[str]    = "pattern_weavers.ontology"
    CONTRACT_VERSION: ClassVar[str] = "3.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "pattern_weavers"

    schema_version: str = "3.0.0"  # kept for backward compatibility

    # Gate
    gate: DomainGate = Field(default_factory=DomainGate)

    # Entities extracted from query
    entities: List[OntologyEntity] = Field(default_factory=list)

    # Semantic classification
    intent_hint: str = "unknown"
    topics: List[str] = Field(default_factory=list)
    sentiment_hint: str = "neutral"          # positive|negative|neutral|mixed
    temporal_context: str = "real_time"      # real_time|historical|forward_looking
    language: str = "en"
    complexity: str = "simple"               # simple|compound|multi_intent

    # Source
    raw_query: str = ""

    # Processing metadata (latency, model, method, etc.)
    compile_metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Service-level request / response (HTTP contract)
# ─────────────────────────────────────────────────────────────

class CompileRequest(BaseModel):
    """POST /compile request body."""
    query: str = Field(..., min_length=1, description="User query text")
    user_id: str = "anonymous"
    language: str = "auto"
    domain: str = "auto"  # "auto" = detect, or force a domain
    context: Dict[str, Any] = Field(default_factory=dict)


class CompileResponse(BaseModel):
    """POST /compile response body."""
    request_id: str
    payload: OntologyPayload
    fallback_used: bool = False
    processing_time_ms: float = 0.0


# ─────────────────────────────────────────────────────────────
# Plugin contract — domain plugins implement this
# ─────────────────────────────────────────────────────────────

class ISemanticPlugin(IContractPlugin):
    """
    Domain plugin interface for Pattern Weavers semantic compilation.

    Each domain (finance, energy, healthcare, ...) implements this to
    provide domain-specific prompts, entity types, and validation.

    Plugins are registered at service startup and selected based on
    the ``domain`` field in CompileRequest.
    """

    PLUGIN_CONTRACT_NAME: ClassVar[str]    = "semantic_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "3.0.0"
    PLUGIN_CONTRACT_OWNER: ClassVar[str]   = "pattern_weavers"

    @abstractmethod
    def get_domain_name(self) -> str:
        """Return domain identifier (e.g. 'finance', 'energy')."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for LLM compilation.

        Must instruct the LLM to return JSON matching OntologyPayload schema.
        The prompt is domain-specific: it lists valid entity types, intent
        vocabulary, topic vocabulary, and gate rules.
        """
        ...

    @abstractmethod
    def get_entity_types(self) -> List[str]:
        """Return valid entity_type values for this domain."""
        ...

    @abstractmethod
    def get_gate_keywords(self) -> List[str]:
        """
        Return high-confidence gate keywords for embedding fast-path.

        If the query contains these AND embedding confidence > threshold,
        the LLM gate check can be skipped (optimization).
        """
        ...

    def get_intent_vocabulary(self) -> List[str]:
        """Return valid intent_hint values for this domain."""
        return ["unknown"]

    def get_topic_vocabulary(self) -> List[str]:
        """Return common topic labels for this domain."""
        return []

    def validate_payload(self, payload: OntologyPayload) -> OntologyPayload:
        """
        Optional domain-specific validation/enrichment.

        Default: return payload unchanged.
        Override to add domain-specific post-processing
        (e.g. normalize ticker symbols, verify sector names).
        """
        return payload


# ─────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────

__all__ = [
    "GateVerdict",
    "DomainGate",
    "OntologyEntity",
    "OntologyPayload",
    "CompileRequest",
    "CompileResponse",
    "ISemanticPlugin",
]
