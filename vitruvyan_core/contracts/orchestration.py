"""
Vitruvyan Core — Orchestration Contracts
=========================================

Canonical contract surface for orchestration extension points.
"""

try:
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
    from core.orchestration.graph_engine import (
        GraphPlugin,
        NodeContract,
        GraphEngine,
    )
    from core.orchestration.parser import (
        Parser,
        BaseParser,
        ParsedSlots,
    )
except ModuleNotFoundError:
    from vitruvyan_core.core.orchestration.base_state import (
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
    from vitruvyan_core.core.orchestration.graph_engine import (
        GraphPlugin,
        NodeContract,
        GraphEngine,
    )
    from vitruvyan_core.core.orchestration.parser import (
        Parser,
        BaseParser,
        ParsedSlots,
    )

__all__ = [
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
    "GraphPlugin",
    "NodeContract",
    "GraphEngine",
    "Parser",
    "BaseParser",
    "ParsedSlots",
]
