"""
Comprehension Engine — Unified Semantic Contracts
==================================================

Single-LLM-call contract for ontology + semantics + linguistic signals.

Produced by Babel Gardens /comprehend endpoint.
Consumes OntologyPayload (PW v3 reuse) and adds SemanticPayload.
Consumed by comprehension_node and all downstream graph nodes.

Layer architecture:
    Layer 1 — LLM Comprehension: ontology + semantics in one call
    Layer 2 — Specialized Models: domain contributors (FinBERT, SecBERT, …)
    Layer 3 — Signal Fusion: merge L1 + L2 into FusionResult

Schema: strict (extra="forbid") — hallucinated fields are rejected.

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .pattern_weavers import OntologyPayload


# ─────────────────────────────────────────────────────────────
# Semantic Payloads — Linguistic understanding output
# ─────────────────────────────────────────────────────────────

class SentimentPayload(BaseModel):
    """Structured sentiment analysis output."""
    model_config = ConfigDict(extra="forbid")

    label: str = "neutral"                          # positive|negative|neutral|mixed
    score: float = Field(default=0.0, ge=-1.0, le=1.0)  # -1 = very neg, +1 = very pos
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    magnitude: float = Field(default=0.0, ge=0.0, le=1.0)  # expression intensity
    aspects: List[Dict[str, Any]] = Field(default_factory=list)  # per-aspect sentiment
    reasoning: str = ""


class EmotionPayload(BaseModel):
    """Structured emotion detection output."""
    model_config = ConfigDict(extra="forbid")

    primary: str = "neutral"
    secondary: List[str] = Field(default_factory=list)
    intensity: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    cultural_context: str = "neutral"
    reasoning: str = ""


class LinguisticPayload(BaseModel):
    """Structural / pragmatic linguistic signals."""
    model_config = ConfigDict(extra="forbid")

    text_register: str = "neutral"    # formal|informal|technical|colloquial|neutral
    irony_detected: bool = False
    ambiguity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    code_switching: bool = False  # multiple languages in query


class SemanticPayload(BaseModel):
    """
    Grouped semantic analysis — everything about HOW the query is expressed.

    Produced alongside OntologyPayload (WHAT the query is about) in a
    single LLM call.
    """
    model_config = ConfigDict(extra="forbid")

    sentiment: SentimentPayload = Field(default_factory=SentimentPayload)
    emotion: EmotionPayload = Field(default_factory=EmotionPayload)
    linguistic: LinguisticPayload = Field(default_factory=LinguisticPayload)


# ─────────────────────────────────────────────────────────────
# ComprehensionResult — The unified output
# ─────────────────────────────────────────────────────────────

class ComprehensionResult(BaseModel):
    """
    Unified comprehension contract.

    Merges:
    - Ontology (PW v3 OntologyPayload) — WHAT the query is about
    - Semantics (SemanticPayload)       — HOW the query is expressed

    One LLM call produces both. Domain plugins shape the prompt.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0.0"

    # Ontology — reuse PW v3 contract verbatim
    ontology: OntologyPayload = Field(default_factory=OntologyPayload)

    # Semantics — new unified linguistic layer
    semantics: SemanticPayload = Field(default_factory=SemanticPayload)

    # Source
    raw_query: str = ""
    language: str = "en"

    # Processing metadata
    comprehension_metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Service-level request / response (HTTP contract)
# ─────────────────────────────────────────────────────────────

class ComprehendRequest(BaseModel):
    """POST /comprehend request body."""
    query: str = Field(..., min_length=1, description="User query text")
    user_id: str = "anonymous"
    language: str = "auto"
    domain: str = "auto"
    context: Dict[str, Any] = Field(default_factory=dict)


class ComprehendResponse(BaseModel):
    """POST /comprehend response body."""
    request_id: str
    result: ComprehensionResult
    fallback_used: bool = False
    processing_time_ms: float = 0.0


# ─────────────────────────────────────────────────────────────
# Signal Evidence — Layer 2 domain model outputs
# ─────────────────────────────────────────────────────────────

class SignalEvidence(BaseModel):
    """
    A single piece of evidence from a domain-specific model.

    Examples:
        FinBERT → SignalEvidence(signal_name="finbert_sentiment", value=-0.73, ...)
        SecBERT → SignalEvidence(signal_name="threat_severity", value=0.91, ...)
    """
    model_config = ConfigDict(extra="forbid")

    signal_name: str                    # Unique signal identifier
    value: float                        # Extracted value
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = ""                    # Model/method that produced this
    method: str = ""                    # extraction technique
    extraction_trace: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Fusion — Merging Layer 1 + Layer 2 signals
# ─────────────────────────────────────────────────────────────

class FusionStrategy(str, Enum):
    """How signals are fused."""
    WEIGHTED = "weighted"
    BAYESIAN = "bayesian"
    LLM_ARBITRATED = "llm_arbitrated"


class FusionContributor(BaseModel):
    """A signal evidence with its applied weight in the fusion."""
    model_config = ConfigDict(extra="forbid")

    evidence: SignalEvidence
    applied_weight: float = Field(default=1.0, ge=0.0, le=1.0)


class FusionResult(BaseModel):
    """
    Output of signal fusion (Layer 3).

    Combines Layer 1 (LLM comprehension) signals with
    Layer 2 (domain model) signals into a single fused verdict.
    """
    model_config = ConfigDict(extra="forbid")

    signal_name: str                    # What was fused (e.g. "sentiment")
    fused_value: float                  # Final fused numeric value
    fused_label: str = ""               # Categorical label
    fused_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    strategy_used: FusionStrategy = FusionStrategy.WEIGHTED
    contributors: List[FusionContributor] = Field(default_factory=list)
    reasoning: str = ""


class FuseRequest(BaseModel):
    """POST /fuse request body."""
    comprehension: ComprehensionResult
    evidences: List[SignalEvidence] = Field(default_factory=list)
    strategy: FusionStrategy = FusionStrategy.WEIGHTED
    weights: Dict[str, float] = Field(default_factory=dict)


class FuseResponse(BaseModel):
    """POST /fuse response body."""
    request_id: str
    results: List[FusionResult] = Field(default_factory=list)
    processing_time_ms: float = 0.0


# ─────────────────────────────────────────────────────────────
# Plugin contracts — domain plugins implement these
# ─────────────────────────────────────────────────────────────

class IComprehensionPlugin(ABC):
    """
    Domain plugin for the unified comprehension engine.

    Extends ISemanticPlugin (ontology) with semantic prompt sections.
    Each domain provides ONE plugin that shapes both ontology and
    semantic analysis in a single LLM prompt.
    """

    @abstractmethod
    def get_domain_name(self) -> str:
        """Return domain identifier (e.g. 'finance', 'security')."""
        ...

    @abstractmethod
    def get_ontology_prompt_section(self) -> str:
        """
        Return the ontology section of the LLM system prompt.

        Must instruct LLM to produce JSON matching OntologyPayload fields:
        gate, entities, intent_hint, topics, sentiment_hint, etc.
        """
        ...

    @abstractmethod
    def get_semantics_prompt_section(self) -> str:
        """
        Return the semantics section of the LLM system prompt.

        Must instruct LLM to produce JSON matching SemanticPayload fields:
        sentiment, emotion, linguistic quality signals.
        """
        ...

    @abstractmethod
    def get_entity_types(self) -> List[str]:
        """Return valid entity_type values for this domain."""
        ...

    def get_gate_keywords(self) -> List[str]:
        """Return high-confidence gate keywords for fast-path."""
        return []

    def get_intent_vocabulary(self) -> List[str]:
        """Return valid intent_hint values."""
        return ["unknown"]

    def get_topic_vocabulary(self) -> List[str]:
        """Return common topic labels."""
        return []

    def get_signal_schemas(self) -> List[Dict[str, Any]]:
        """Return signal schemas that domain contributors produce."""
        return []

    def validate_result(self, result: ComprehensionResult) -> ComprehensionResult:
        """
        Domain-specific post-validation/enrichment.

        Default: return result unchanged.
        """
        return result


class ISignalContributor(ABC):
    """
    Domain signal contributor interface (Layer 2).

    Each specialized model (FinBERT, SecBERT, BioBERT, …)
    implements this to contribute domain-specific signals.

    Contributors live in DOMAIN code, never in core.
    """

    @abstractmethod
    def get_contributor_name(self) -> str:
        """Unique contributor identifier (e.g. 'finbert', 'secbert')."""
        ...

    @abstractmethod
    def get_signal_names(self) -> List[str]:
        """Signal names this contributor can produce."""
        ...

    @abstractmethod
    def contribute(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SignalEvidence]:
        """
        Extract domain-specific signals from text.

        Returns list of SignalEvidence (one per signal this model extracts).
        Must be self-contained: load model, run inference, return evidence.
        """
        ...

    def is_available(self) -> bool:
        """Check if underlying model is loaded and ready."""
        return True


# ─────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────

__all__ = [
    # Semantic payloads
    "SentimentPayload",
    "EmotionPayload",
    "LinguisticPayload",
    "SemanticPayload",
    # Unified result
    "ComprehensionResult",
    # HTTP contracts
    "ComprehendRequest",
    "ComprehendResponse",
    # Signal evidence
    "SignalEvidence",
    # Fusion
    "FusionStrategy",
    "FusionContributor",
    "FusionResult",
    "FuseRequest",
    "FuseResponse",
    # Plugin ABCs
    "IComprehensionPlugin",
    "ISignalContributor",
]
