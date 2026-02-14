"""
Vitruvyan Core — Orchestration Package
=======================================

This package provides domain-agnostic orchestration primitives.

Core Components:
- base_state: BaseGraphState TypedDict (~35 fields)
- graph_engine: GraphPlugin ABC + GraphEngine builder
- parser: Parser ABC for domain-specific input parsing
- intent_registry: IntentRegistry for configurable intent detection
- route_registry: RouteRegistry for configurable routing
- entity_resolver_registry: EntityResolverRegistry for domain-specific entity resolution (hook pattern)
- execution_registry: ExecutionRegistry for domain-specific execution handlers (hook pattern)

LangGraph Implementation:
- langgraph/: LangGraph-specific implementation

Author: Vitruvyan Core Team
Created: February 10, 2026
Updated: February 14, 2026 (Hook pattern for entity_resolver + exec nodes)
"""

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
    NodeContract,
    GraphPlugin,
    GraphEngine,
    create_node_contract,
    get_engine,
    reset_engine,
)

from core.orchestration.sacred_flow import (
    SacredFlowConfig,
    SACRED_FLOW_NODES,
    SACRED_FLOW_EDGES,
    UX_PRESERVATION_FIELDS,
    should_activate_advisor,
    create_can_to_advisor_router,
    snapshot_ux_fields,
    restore_ux_fields,
    create_invoke_with_preservation,
    get_sacred_flow_spec,
    validate_sacred_flow_state,
)

from core.orchestration.parser import (
    Parser,
    BaseParser,
    GenericParser,
    ParsedSlots,
)

from core.orchestration.intent_registry import (
    IntentRegistry,
    IntentDefinition,
    ScreeningFilter,
    create_generic_registry as create_generic_intent_registry,
)

from core.orchestration.route_registry import (
    RouteRegistry,
    RouteDefinition,
    IntentRouteMapping,
    create_generic_registry as create_generic_route_registry,
)

from core.orchestration.entity_resolver_registry import (
    EntityResolverRegistry,
    EntityResolverDefinition,
    get_entity_resolver_registry,
    reset_entity_resolver_registry,
)

from core.orchestration.execution_registry import (
    ExecutionRegistry,
    ExecutionHandlerDefinition,
    get_execution_registry,
    reset_execution_registry,
)

__all__ = [
    # Base State
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
    # Graph Engine
    "NodeContract",
    "GraphPlugin",
    "GraphEngine",
    "create_node_contract",
    "get_engine",
    "reset_engine",
    # Sacred Flow
    "SacredFlowConfig",
    "SACRED_FLOW_NODES",
    "SACRED_FLOW_EDGES",
    "UX_PRESERVATION_FIELDS",
    "should_activate_advisor",
    "create_can_to_advisor_router",
    "snapshot_ux_fields",
    "restore_ux_fields",
    "create_invoke_with_preservation",
    "get_sacred_flow_spec",
    "validate_sacred_flow_state",
    # Parser
    "Parser",
    "BaseParser",
    "GenericParser",
    "ParsedSlots",
    # Intent Registry
    "IntentRegistry",
    "IntentDefinition",
    "ScreeningFilter",
    "create_generic_intent_registry",
    # Route Registry
    "RouteRegistry",
    "RouteDefinition",
    "IntentRouteMapping",
    "create_generic_route_registry",
    # Entity Resolver Registry
    "EntityResolverRegistry",
    "EntityResolverDefinition",
    "get_entity_resolver_registry",
    "reset_entity_resolver_registry",
    # Execution Registry
    "ExecutionRegistry",
    "ExecutionHandlerDefinition",
    "get_execution_registry",
    "reset_execution_registry",
]
