"""
Vitruvyan Core — Public Contracts
==================================

Single import point for all domain-extensible contracts and ABCs.

Domain implementors import from here instead of reaching into internal modules:

    from core.contracts import GraphPlugin, NodeContract, BaseGraphState
    from core.contracts import Parser, BaseParser, ParsedSlots

This package re-exports from canonical locations:
- base_state.py    → BaseGraphState, field categories
- graph_engine.py  → GraphPlugin, NodeContract, GraphEngine
- parser.py        → Parser, BaseParser, ParsedSlots

Author: Vitruvyan Core Team
Created: February 16, 2026
Status: LEVEL 1 — FOUNDATIONAL
"""

# ── Base State ──
from core.orchestration.base_state import (
    BaseGraphState,
    GraphStateType,
    ESSENTIAL_FIELDS,
    INTENT_FIELDS,
    LANGUAGE_FIELDS,
    EMOTION_FIELDS,
    ORTHODOXY_FIELDS,
    VAULT_FIELDS,
    TRACING_FIELDS,
    WEAVER_FIELDS,
    CAN_FIELDS,
    ALL_BASE_FIELDS,
    get_base_field_count,
    is_base_field,
    get_domain_fields,
)

# ── Graph Engine & Plugin ──
from core.orchestration.graph_engine import (
    GraphPlugin,
    NodeContract,
    GraphEngine,
)

# ── Parser ──
from core.orchestration.parser import (
    Parser,
    BaseParser,
    ParsedSlots,
)

__all__ = [
    # State
    "BaseGraphState",
    "GraphStateType",
    "ESSENTIAL_FIELDS",
    "INTENT_FIELDS",
    "LANGUAGE_FIELDS",
    "EMOTION_FIELDS",
    "ORTHODOXY_FIELDS",
    "VAULT_FIELDS",
    "TRACING_FIELDS",
    "WEAVER_FIELDS",
    "CAN_FIELDS",
    "ALL_BASE_FIELDS",
    "get_base_field_count",
    "is_base_field",
    "get_domain_fields",
    # Engine
    "GraphPlugin",
    "NodeContract",
    "GraphEngine",
    # Parser
    "Parser",
    "BaseParser",
    "ParsedSlots",
]
