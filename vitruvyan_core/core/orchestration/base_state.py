"""
Vitruvyan Core — Base Graph State
==================================

Domain-agnostic TypedDict that defines the MINIMAL state required
by ANY LangGraph orchestration in Vitruvyan.

This is LEVEL 1 (Pure Python, no I/O, no infrastructure).

Domain verticals (finance, logistics, healthcare) EXTEND this state
by inheriting from BaseGraphState in their own FinanceGraphState, etc.

Design Principles:
1. Only ~30 fields (vs 100+ in legacy finance monolith)
2. Zero domain-specific fields (no tickers, portfolios, allocations)
3. Sacred Orders fields are agnostic (orthodoxy, vault work for any domain)
4. Emotion/language fields are agnostic (Babel Gardens works for any domain)

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: LEVEL 1 — FOUNDATIONAL
"""

from typing import TypedDict, Optional, Dict, Any, List


class BaseGraphState(TypedDict, total=False):
    """
    Domain-agnostic graph state.
    
    All fields here are universal — they work for finance, logistics,
    healthcare, or any other vertical.
    
    Domain-specific fields (tickers, portfolios, routes, patients)
    are added via inheritance in the vertical's GraphPlugin.
    """
    
    # =========================================================================
    # ESSENTIALS — Every graph needs these
    # =========================================================================
    input_text: str                           # User's raw input
    route: str                                # Current routing decision
    result: Dict[str, Any]                    # Generic result container
    error: Optional[str]                      # Error message if any
    response: Dict[str, Any]                  # Final response to user
    user_id: Optional[str]                    # User identifier
    
    # =========================================================================
    # INTENT & CLARIFICATION — Understanding what user wants
    # =========================================================================
    intent: Optional[str]                     # Detected intent (domain defines valid intents)
    needs_clarification: Optional[bool]       # True if query is ambiguous
    clarification_reason: Optional[str]       # Why clarification is needed
    
    # =========================================================================
    # LANGUAGE & CULTURE — Babel Gardens (domain-agnostic)
    # =========================================================================
    language_detected: Optional[str]          # ISO language code (en, it, de, ja, etc.)
    language_confidence: Optional[float]      # Detection confidence (0.0-1.0)
    cultural_context: Optional[str]           # Cultural interpretation
    babel_status: Optional[str]               # success, degraded, failed, idle
    
    # =========================================================================
    # EMOTION — Babel Gardens Emotion Detection (domain-agnostic)
    # =========================================================================
    emotion_detected: Optional[str]           # Primary emotion (frustrated, excited, anxious)
    emotion_confidence: Optional[float]       # Detection confidence (0.0-1.0)
    emotion_intensity: Optional[str]          # low, medium, high
    emotion_secondary: Optional[str]          # Secondary emotion if present
    emotion_reasoning: Optional[str]          # Why this emotion was detected
    _ux_metadata: Optional[Dict[str, Any]]    # Protected UX fields for Sacred Orders bypass
    
    # =========================================================================
    # SACRED ORDERS: ORTHODOXY — Truth & Validation (domain-agnostic)
    # =========================================================================
    orthodoxy_status: Optional[str]           # blessed, purified, under_review, locally_blessed
    orthodoxy_verdict: Optional[str]          # absolution_granted, penance_required, local_blessing
    orthodoxy_findings: Optional[int]         # Number of heresies detected
    orthodoxy_confidence: Optional[float]     # Confidence in verdict (0.0-1.0)
    orthodoxy_blessing: Optional[str]         # Divine blessing message
    orthodoxy_message: Optional[str]          # Human-readable orthodoxy message
    orthodoxy_timestamp: Optional[str]        # When orthodoxy audit completed
    orthodoxy_duration_ms: Optional[float]    # Time taken for audit
    theological_metadata: Optional[Dict[str, Any]]  # Additional theological info
    
    # =========================================================================
    # SACRED ORDERS: VAULT — Memory & Persistence (domain-agnostic)
    # =========================================================================
    vault_status: Optional[str]               # blessed, protected, emergency_blessed
    vault_protection: Optional[str]           # divine_blessing_applied, standard_blessing
    vault_guardian: Optional[str]             # protection_granted, local_protection
    vault_blessing: Optional[Dict[str, Any]]  # Complete vault metadata
    vault_timestamp: Optional[str]            # When vault protection completed
    vault_duration_ms: Optional[float]        # Time taken for protection
    
    # =========================================================================
    # TRACING & SEMANTIC GROUNDING — VSGS (domain-agnostic)
    # =========================================================================
    trace_id: Optional[str]                   # Request trace ID for audit trail
    semantic_matches: Optional[List[Dict[str, Any]]]  # Top-k similar contexts
    vsgs_status: Optional[str]                # enabled, disabled, error, skipped
    
    # =========================================================================
    # PATTERN WEAVERS — Semantic Context (domain-agnostic structure)
    # =========================================================================
    weaver_context: Optional[Dict[str, Any]]  # Semantic context (concepts, patterns)
    
    # =========================================================================
    # CAN (Conversational Advisor Node) — Conversation Flow (domain-agnostic)
    # =========================================================================
    can_response: Optional[Dict[str, Any]]    # CAN structured response
    can_mode: Optional[str]                   # urgent, analytical, exploratory, conversational
    can_route: Optional[str]                  # Routing decision from CAN
    follow_ups: Optional[List[str]]           # Suggested next questions
    conversation_type: Optional[str]          # Type of conversation
    final_response: Optional[str]             # Formatted narrative for user display
    proactive_suggestions: Optional[List[Dict[str, Any]]]  # Proactive suggestions


# =============================================================================
# TYPE ALIASES — For cleaner code
# =============================================================================
GraphStateType = BaseGraphState
"""Alias for BaseGraphState, used in type hints."""


# =============================================================================
# FIELD CATEGORIES — For introspection and validation
# =============================================================================
ESSENTIAL_FIELDS = frozenset([
    "input_text", "route", "result", "error", "response", "user_id"
])

INTENT_FIELDS = frozenset([
    "intent", "needs_clarification", "clarification_reason"
])

LANGUAGE_FIELDS = frozenset([
    "language_detected", "language_confidence", "cultural_context", "babel_status"
])

EMOTION_FIELDS = frozenset([
    "emotion_detected", "emotion_confidence", "emotion_intensity",
    "emotion_secondary", "emotion_reasoning", "_ux_metadata"
])

ORTHODOXY_FIELDS = frozenset([
    "orthodoxy_status", "orthodoxy_verdict", "orthodoxy_findings",
    "orthodoxy_confidence", "orthodoxy_blessing", "orthodoxy_message",
    "orthodoxy_timestamp", "orthodoxy_duration_ms", "theological_metadata"
])

VAULT_FIELDS = frozenset([
    "vault_status", "vault_protection", "vault_guardian",
    "vault_blessing", "vault_timestamp", "vault_duration_ms"
])

TRACING_FIELDS = frozenset([
    "trace_id", "semantic_matches", "vsgs_status"
])

WEAVER_FIELDS = frozenset([
    "weaver_context"
])

CAN_FIELDS = frozenset([
    "can_response", "can_mode", "can_route", "follow_ups",
    "conversation_type", "final_response", "proactive_suggestions"
])

ALL_BASE_FIELDS = (
    ESSENTIAL_FIELDS | INTENT_FIELDS | LANGUAGE_FIELDS | EMOTION_FIELDS |
    ORTHODOXY_FIELDS | VAULT_FIELDS | TRACING_FIELDS | WEAVER_FIELDS | CAN_FIELDS
)
"""All 35 fields in BaseGraphState."""


def get_base_field_count() -> int:
    """Returns the count of fields in BaseGraphState."""
    return len(ALL_BASE_FIELDS)


def is_base_field(field_name: str) -> bool:
    """Check if a field belongs to BaseGraphState."""
    return field_name in ALL_BASE_FIELDS


def get_domain_fields(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract domain-specific fields from a state dict.
    
    Returns only fields that are NOT part of BaseGraphState.
    Useful for debugging domain extensions.
    """
    return {k: v for k, v in state.items() if k not in ALL_BASE_FIELDS}
