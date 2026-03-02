# core/langgraph/graph_flow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any, List

from core.orchestration.base_state import BaseGraphState

# Import modular nodes
from core.orchestration.langgraph.node.parse_node import parse_node
from core.orchestration.langgraph.node.route_node import route_node
from core.orchestration.langgraph.node import route_node as _route_mod
from core.orchestration.langgraph.node.exec_node import exec_node
from core.orchestration.langgraph.node.qdrant_node import qdrant_node
from core.orchestration.langgraph.node.compose_node import compose_node
# Babel Gardens Emotion Detection (v2 — HTTP adapter)
from core.orchestration.langgraph.node.emotion_detector import emotion_detector_node as babel_emotion_node
# Enhanced LLM node with caching
from core.orchestration.langgraph.node.cached_llm_node import cached_llm_node
from core.orchestration.langgraph.memory_utils import merge_slots

# 🧠 Intent Detection (domain-agnostic node + finance plugin)
from core.orchestration.langgraph.node.intent_detection_node import intent_detection_node
from core.orchestration.langgraph.node import intent_detection_node as _intent_mod

# Configure intent detection with domain plugin pattern (dynamic import)
import os as _os
import importlib as _importlib
import logging as _logging

_INTENT_DOMAIN = _os.getenv("INTENT_DOMAIN", "generic")
_log = _logging.getLogger(__name__)

def _load_domain_intent_registry(domain: str):
    """Dynamically load intent registry from domain plugin."""
    if domain == "generic":
        from core.orchestration.intent_registry import create_generic_registry
        return create_generic_registry(), {}, {}
    try:
        mod = _importlib.import_module(f"domains.{domain}.intent_config")
        factory = getattr(mod, f"create_{domain}_registry")
        registry = factory()
        ctx_kw = getattr(mod, "CONTEXT_KEYWORDS", {})
        amb_pat = getattr(mod, "AMBIGUOUS_PATTERNS", {})
        return registry, ctx_kw, amb_pat
    except (ImportError, AttributeError) as e:
        _log.warning(f"[graph_flow] Domain '{domain}' intent_config not found: {e}. Using generic.")
        from core.orchestration.intent_registry import create_generic_registry
        return create_generic_registry(), {}, {}

_intent_reg, _ctx_kw, _amb_pat = _load_domain_intent_registry(_INTENT_DOMAIN)
if _ctx_kw or _amb_pat:
    _intent_mod.configure(_intent_reg, context_keywords=_ctx_kw, ambiguous_patterns=_amb_pat)
else:
    _intent_mod.configure(_intent_reg)

# Configure route_node with registry-driven intent routing (domain-agnostic)
# NOTE: route_node.configure() is called AFTER _graph_routes_ext is loaded
# so that direct_routes from domain extension are available.
# See below, after _load_domain_graph_extension().

# 🔍 Configure EntityResolverRegistry (domain plugin pattern — dynamic import)
_ENTITY_DOMAIN = _os.getenv("ENTITY_DOMAIN", _INTENT_DOMAIN)
if _ENTITY_DOMAIN and _ENTITY_DOMAIN != "generic":
    try:
        _entity_mod = _importlib.import_module(f"domains.{_ENTITY_DOMAIN}.entity_resolver_config")
        _register_fn = getattr(_entity_mod, f"register_{_ENTITY_DOMAIN}_entity_resolver")
        _register_fn()
    except (ImportError, AttributeError) as e:
        _log.debug(f"[graph_flow] No entity resolver for domain '{_ENTITY_DOMAIN}': {e}")

# 🎨 Register domain prompts with PromptRegistry (domain plugin pattern)
if _INTENT_DOMAIN and _INTENT_DOMAIN != "generic":
    try:
        _prompts_mod = _importlib.import_module(f"domains.{_INTENT_DOMAIN}.prompts")
        _register_prompts_fn = getattr(_prompts_mod, f"register_{_INTENT_DOMAIN}_prompts", None)
        if _register_prompts_fn:
            _register_prompts_fn()
            _log.info(f"[graph_flow] ✅ Registered prompt domain: {_INTENT_DOMAIN}")
    except (ImportError, AttributeError) as e:
        _log.debug(f"[graph_flow] No prompts registration for domain '{_INTENT_DOMAIN}': {e}")

# 🔌 Optional graph_nodes domain extension (experimental hook)
# Contract:
# - module: domains.<domain>.graph_nodes.registry
# - function: get_<domain>_graph_nodes() -> Dict[str, Callable]
# - optional: get_<domain>_graph_edges() -> List[Tuple[str, str]]
# - optional: get_<domain>_route_targets() -> Dict[str, str]
_GRAPH_DOMAIN = _os.getenv("GRAPH_DOMAIN", _INTENT_DOMAIN)


def _load_domain_graph_extension(domain: str):
    """Load optional domain graph extension from graph_nodes/registry."""
    if not domain or domain == "generic":
        return {}, [], {}

    module_path = f"domains.{domain}.graph_nodes.registry"
    try:
        mod = _importlib.import_module(module_path)

        nodes_fn = getattr(mod, f"get_{domain}_graph_nodes")
        edges_fn = getattr(mod, f"get_{domain}_graph_edges", None)
        routes_fn = getattr(mod, f"get_{domain}_route_targets", None)

        nodes = nodes_fn() if callable(nodes_fn) else {}
        edges = edges_fn() if callable(edges_fn) else []
        routes = routes_fn() if callable(routes_fn) else {}

        if not isinstance(nodes, dict):
            _log.warning(
                f"[graph_flow] {module_path}.{nodes_fn.__name__} must return dict. Ignoring graph nodes."
            )
            nodes = {}
        if not isinstance(edges, list):
            _log.warning(
                f"[graph_flow] {module_path}.get_{domain}_graph_edges must return list. Ignoring graph edges."
            )
            edges = []
        if not isinstance(routes, dict):
            _log.warning(
                f"[graph_flow] {module_path}.get_{domain}_route_targets must return dict. Ignoring route targets."
            )
            routes = {}

        if nodes or edges or routes:
            _log.info(
                f"[graph_flow] Loaded graph_nodes extension for domain '{domain}' "
                f"(nodes={len(nodes)}, edges={len(edges)}, routes={len(routes)})"
            )

        return nodes, edges, routes
    except ImportError as e:
        _log.debug(f"[graph_flow] No graph_nodes extension for domain '{domain}': {e}")
    except AttributeError as e:
        _log.debug(f"[graph_flow] graph_nodes extension missing required factory for '{domain}': {e}")
    except Exception as e:
        _log.warning(f"[graph_flow] Failed loading graph_nodes extension for '{domain}': {e}")

    return {}, [], {}


_graph_nodes_ext, _graph_edges_ext, _graph_routes_ext = _load_domain_graph_extension(_GRAPH_DOMAIN)

# Configure route_node AFTER domain graph extension is loaded
# so that direct_routes (intent → route_value) are available.
# Exclude route overrides (e.g. "dispatcher_exec") — those are resolved by
# _decide_route_targets, not by intent matching in route_node.
_ROUTE_OVERRIDES = {"dispatcher_exec", "llm_soft", "semantic_fallback"}
_direct_routes = {
    route_key: route_key
    for route_key in _graph_routes_ext.keys()
    if route_key not in _ROUTE_OVERRIDES
}
_route_mod.configure(
    exec_intents=_intent_reg.get_exec_intent_names(),
    soft_intents=_intent_reg.get_soft_intent_names(),
    direct_routes=_direct_routes if _direct_routes else None,
)

# 🔍 PHASE 2.2 - Quality Check (REMOVED)

# ⚙️ PHASE 2.3 - Consolidated Parameter Extraction (horizon_parser + topk_parser)
from core.orchestration.langgraph.node.params_extraction_node import params_extraction_node

# 🔥 New planned nodes (stubs + new)
from core.orchestration.langgraph.node.entity_resolver_node import entity_resolver_node
from core.orchestration.langgraph.node.output_normalizer_node import output_normalizer_node
from core.orchestration.langgraph.node.audit_node_simple import audit_node

# 🏛️ Sacred Orders Integration
from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node
from core.orchestration.langgraph.node.vault_node import vault_node

# 🗝️ Codex Hunters Integration
from core.orchestration.langgraph.node.codex_hunters_node import codex_hunters_node

# 💡 Proactive Suggestions (REMOVED)

# 🔌 MCP Integration - Phase 4 (Model Context Protocol + OpenAI Function Calling)
from core.orchestration.langgraph.node.llm_mcp_node import llm_mcp_node

# 🧠 VSGS (Vitruvyan Semantic Grounding System) - PR-A Bootstrap
from core.orchestration.langgraph.node.semantic_grounding_node import semantic_grounding_node

# Pattern Weavers - Semantic enrichment
# v3 (PATTERN_WEAVERS_V3=1): LLM-based semantic compilation → OntologyPayload
# v2 (default): Embedding-based taxonomy matching via /weave
import os as _os
if _os.getenv("PATTERN_WEAVERS_V3", "0") == "1":
    from core.orchestration.langgraph.node.pw_compile_node import pw_compile_node as weaver_node
else:
    from core.orchestration.langgraph.node.pattern_weavers_node import pattern_weavers_node as weaver_node

# 🎯 Advisor Node - Decision-making layer (Dec 27, 2025)
from core.orchestration.langgraph.node.advisor_node import advisor_node

# 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
from core.orchestration.langgraph.node.can_node import can_node

# ⚡ Early-exit for simple intents (greeting, farewell, thanks) — Feb 23, 2026
from core.orchestration.langgraph.node.early_exit_node import early_exit_node, is_early_exit

# ── Contract Enforcement (FASE 3) ──
from core.orchestration.contract_enforcement import enforced
from core.orchestration.node_contracts_registry import NODE_CONTRACTS, merge_domain_contracts

# Shared state — Domain-Agnostic OS Kernel
# Inherits ~35 domain-agnostic fields from BaseGraphState (base_state.py).
# Only graph-specific / domain-extension fields are declared below.
class GraphState(BaseGraphState, total=False):
    # ── Additional core fields (not in BaseGraphState) ──
    raw_output: Optional[Dict[str, Any]]

    # ── Pattern Weavers v3 — Semantic Compilation (Feb 24, 2026) ──
    ontology_payload: Optional[Dict[str, Any]]  # OntologyPayload from /compile (v3)

    # ── Domain-agnostic entity/signal fields ──
    entities: Optional[List[Dict[str, Any]]]  # Generic entities (id, type, attributes)
    entity_ids: Optional[List[str]]           # Legacy entity IDs (codes, symbols) - used by parse/compose
    validated_entities: Optional[List[str]]   # Client-validated entities (authoritative per Golden Rules)
    context_entities: Optional[List[str]]     # Fallback entities from context/VSGS
    signals: Optional[Dict[str, Any]]         # Generic signals (sentiment, score, metadata)
    context: Optional[Dict[str, Any]]         # Vertical-specific extensible context
    top_k: Optional[int]                      # Generic parameter (top K results)

    # ── Domain parameters — generic extensible dict for domain-specific slots ──
    domain_params: Optional[Dict[str, Any]]   # Generic domain-specific parameters

    # ── Legacy slot fields — DEPRECATED: Use domain_params dict instead ──
    budget: Optional[Any]                    # DEPRECATED -> domain_params["budget"]
    horizon: Optional[str]                   # DEPRECATED -> domain_params["horizon"]
    amount: Optional[Any]                    # DEPRECATED -> domain_params["amount"]
    companies: Optional[List[str]]           # DEPRECATED -> domain_params["companies"]
    flow: Optional[str]                      # Flow type (direct, clarification)
    language: Optional[str]                  # Language hint from client

    # ── Sentinel Order Fields — REMOVED from core state (Feb 15, 2026) ──
    # Domain plugins inject these via GraphPlugin.get_state_extensions() or context dict.

    # ── CrewAI Strategic Order Fields — DEPRECATED (see CREWAI_DEPRECATION_NOTICE.md) ──

    # ── Babel Gardens extra fields (beyond BaseGraphState) ──
    sentiment_label: Optional[str]           # positive, negative, neutral, error
    sentiment_score: Optional[float]         # Fused sentiment score (None on failure)
    babel_analysis_summary: Optional[Dict[str, Any]]  # Complete Babel analysis
    babel_metrics: Optional[Dict[str, Any]]  # Performance telemetry
    babel_timestamp: Optional[str]           # When Babel processing completed

    # ── Babel Gardens Emotion extra fields (beyond BaseGraphState) ──
    emotion_sentiment_label: Optional[str]   # Sentiment from emotion module
    emotion_sentiment_score: Optional[float] # Sentiment score from emotion module
    emotion_metadata: Optional[Dict[str, Any]]  # Additional emotion context

    # ── VSGS extra fields (beyond BaseGraphState) ──
    vsgs_elapsed_ms: Optional[float]         # VSGS processing time
    vsgs_error: Optional[str]                # Error message if vsgs_status=error

    # ── Advisor Node Fields ──
    advisor_recommendation: Optional[Dict[str, Any]]  # Actionable recommendation
    user_requests_action: Optional[bool]     # Trigger for advisor activation

    # ── Domain Extensions (populated by domain graph_nodes via hook pattern) ──
    # Domain-specific fields (numerical_panel, vee_explanations, vare_risk, etc.)
    # are injected at runtime by domain graph_nodes. They are NOT declared here
    # because GraphState is the OS-agnostic kernel. TypedDict(total=False) allows
    # arbitrary keys at runtime. graph_runner propagates them via domain_extensions.
    domain_extensions: Optional[Dict[str, Any]]        # Opaque domain payload (pass-through)

    # ── MCP Tool Integration Fields ──
    mcp_tool_used: Optional[str]                       # Name of MCP tool selected by LLM
    mcp_result: Optional[Dict[str, Any]]               # MCP tool execution result (status, data, error)
    mcp_orthodoxy: Optional[str]                       # Orthodoxy status from MCP tool result

    # ── Compose Node Output Fields ──
    narrative: Optional[str]                           # Natural language synthesis from compose_node
    action: Optional[str]                              # Action type: synthesis, conversation, clarify
    service_result: Optional[Dict[str, Any]]           # Service result payload for compose
    questions: Optional[List[str]]                     # Clarification questions (LLM/MCP follow-up)
    needed_slots: Optional[List[str]]                  # Legacy compatibility field

    # ── Quality Check / Validation Fields ──
    ok: Optional[bool]                                 # Quality check pass/fail
    validation: Optional[Dict[str, Any]]               # Validation errors/warnings


# run_graph_once() REMOVED — consolidated into graph_runner.py
# Use: from core.orchestration.langgraph.graph_runner import run_graph_once


# ── Contract enforcement wrapper ──
# Map graph_flow node names to registry keys where they differ
_NODE_ALIAS = {"llm_soft": "cached_llm", "intent": "intent_detection"}


def _wrap(name, fn):
    """Wrap a node function with @enforced using its registered contract."""
    registry_key = _NODE_ALIAS.get(name, name)
    spec = NODE_CONTRACTS.get(registry_key)
    if spec and (spec.requires or spec.produces):
        return enforced(
            requires=spec.requires,
            produces=spec.produces,
            node_name=name,
        )(fn)
    return fn


def build_graph():
    g = StateGraph(GraphState)

    # Nodi (wrapped with @enforced contract enforcement)
    g.add_node("parse", _wrap("parse", parse_node))
    
    # 🧠 PHASE 2.1 - Consolidated Intent Detection (babel + intent_llm + intent_mapper)
    g.add_node("intent_detection", _wrap("intent_detection", intent_detection_node))
    
    # 🕸️ Pattern Weavers - Semantic enrichment after intent detection (Nov 2025)
    g.add_node("weaver", _wrap("weaver", weaver_node))
    
    g.add_node("entity_resolver", _wrap("entity_resolver", entity_resolver_node))
    
    # ⚙️ PHASE 2.3 - Consolidated Parameter Extraction (horizon_parser + topk_parser)
    g.add_node("params_extraction", _wrap("params_extraction", params_extraction_node))
    
    g.add_node("decide", _wrap("decide", route_node))
    # 🎭 PHASE 2.1 - Babel Gardens Emotion Detection
    g.add_node("babel_emotion", _wrap("babel_emotion", babel_emotion_node))
    # 🧠 PR-A: VSGS Semantic Grounding (feature flag OFF by default)
    g.add_node("semantic_grounding", _wrap("semantic_grounding", semantic_grounding_node))
    g.add_node("exec", _wrap("exec", exec_node))
    
    # 🔍 quality_check: ARCHIVED (domain-specific validation)
    g.add_node("qdrant", _wrap("qdrant", qdrant_node))
    # 💡 UX Quick Win 2: Enhanced LLM with Emotional Intelligence (Oct 29, 2025)
    g.add_node("llm_soft", _wrap("llm_soft", cached_llm_node))
    g.add_node("output_normalizer", _wrap("output_normalizer", output_normalizer_node))
    g.add_node("compose", _wrap("compose", compose_node))
    
    # 💡 proactive_suggestions: ARCHIVED (domain-specific)
    
    # 🎯 Advisor Node - Decision-making layer (Dec 27, 2025)
    g.add_node("advisor", _wrap("advisor", advisor_node))
    
    # 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
    g.add_node("can", _wrap("can", can_node))
    
    # 🏛️ Sacred Orders Integration  
    g.add_node("orthodoxy", _wrap("orthodoxy", orthodoxy_node))
    g.add_node("vault", _wrap("vault", vault_node))
    
    # 🗝️ Codex Hunters Integration
    g.add_node("codex_hunters", _wrap("codex_hunters", codex_hunters_node))
    
    # 🔌 MCP Integration - Phase 4 (OpenAI Function Calling gateway)
    g.add_node("llm_mcp", _wrap("llm_mcp", llm_mcp_node))

    # ⚡ Early-exit for simple intents (greeting, farewell, thanks)
    g.add_node("early_exit", _wrap("early_exit", early_exit_node))

    # 🔌 Optional domain graph_nodes extension (experimental)
    registered_nodes = {
        "parse",
        "intent_detection",
        "weaver",
        "entity_resolver",
        "params_extraction",
        "decide",
        "babel_emotion",
        "semantic_grounding",
        "exec",
        "qdrant",
        "llm_soft",
        "output_normalizer",
        "compose",
        "advisor",
        "can",
        "orthodoxy",
        "vault",
        "codex_hunters",
        "llm_mcp",
        "early_exit",
    }

    for node_name, node_handler in _graph_nodes_ext.items():
        if node_name in registered_nodes:
            _log.warning(
                f"[graph_flow] graph_nodes extension attempted to override core node '{node_name}'. Ignoring."
            )
            continue
        if not callable(node_handler):
            _log.warning(
                f"[graph_flow] graph_nodes extension node '{node_name}' is not callable. Ignoring."
            )
            continue
        g.add_node(node_name, _wrap(node_name, node_handler))
        registered_nodes.add(node_name)

    g.set_entry_point("parse")

    # 🧠 PHASE 2: Consolidated pipeline
    # parse → intent_detection → [early_exit_check] → weaver → ... → decide
    g.add_edge("parse", "intent_detection")

    # ⚡ Early-exit conditional: simple intents skip 14 nodes → direct END
    g.add_conditional_edges(
        "intent_detection",
        lambda state: "early_exit" if is_early_exit(state) else "weaver",
        {
            "early_exit": "early_exit",
            "weaver": "weaver",
        },
    )
    g.add_edge("early_exit", END)

    g.add_edge("weaver", "entity_resolver") # New edge
    # 🎭 PHASE 2.1: Emotion detection after entity_id resolution
    g.add_edge("entity_resolver", "babel_emotion")
    # 🧠 PR-A: VSGS Semantic Grounding (after emotion, before params extraction)
    g.add_edge("babel_emotion", "semantic_grounding")
    g.add_edge("semantic_grounding", "params_extraction")
    g.add_edge("params_extraction", "decide")

    def route_from_decide(state: dict) -> str:
        """
        Debug wrapper for conditional routing from decide node.
        Returns the target node based on state['route'].
        
        🔌 Phase 4: If USE_MCP=1 and route is dispatcher_exec, route to llm_mcp instead of exec.
        This enables OpenAI Function Calling → MCP → Sacred Orders flow.
        """
        import os
        
        route_value = state.get("route")
        intent_value = state.get("intent")
        entities_value = state.get("entities")  # Domain-agnostic entities field
        
        # MCP Integration: Check if MCP should handle this route
        use_mcp = os.getenv("USE_MCP", "0") == "1"
        if use_mcp and route_value == "dispatcher_exec":
            _log.debug("[MCP ROUTING] USE_MCP=1, routing to llm_mcp (original route: %s)", route_value)
            return "llm_mcp"

        _log.debug(
            "[route_from_decide] route=%s intent=%s entities=%s",
            route_value, intent_value, entities_value,
        )
        return route_value

    _decide_route_targets = {
        "semantic_fallback": "qdrant",
        "dispatcher_exec": "exec",            # Direct execution (no sentiment prereq)
        "llm_mcp": "llm_mcp",                 # 🔌 Phase 4: MCP routing (when USE_MCP=1)
        "llm_soft": "llm_soft",
        "codex_expedition": "codex_hunters",  # 🗝️ Codex Hunters (maintenance system)
    }
    for route_key, route_target in _graph_routes_ext.items():
        normalized_target = END if route_target == "END" else route_target
        if normalized_target is not END and normalized_target not in registered_nodes:
            _log.warning(
                f"[graph_flow] graph_nodes route target '{route_target}' for route '{route_key}' "
                "is not a registered node. Ignoring."
            )
            continue
        _decide_route_targets[route_key] = normalized_target

    g.add_conditional_edges(
        "decide",
        route_from_decide,
        _decide_route_targets,
    )

    # Additional domain edges (if declared by graph_nodes extension)
    for edge in _graph_edges_ext:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            _log.warning(f"[graph_flow] Invalid graph edge declaration '{edge}'. Expected (source, target).")
            continue
        source, target = edge
        normalized_target = END if target == "END" else target

        if source not in registered_nodes:
            _log.warning(
                f"[graph_flow] graph_nodes edge source '{source}' is not a registered node. Ignoring."
            )
            continue
        if normalized_target is not END and normalized_target not in registered_nodes:
            _log.warning(
                f"[graph_flow] graph_nodes edge target '{target}' is not a registered node. Ignoring."
            )
            continue

        try:
            g.add_edge(source, normalized_target)
        except Exception as e:
            _log.warning(
                f"[graph_flow] Failed to add graph_nodes edge ({source} -> {target}): {e}"
            )

    # exec → output_normalizer (quality_check archived)
    g.add_edge("exec", "output_normalizer")
    
    # 🔌 Phase 4: MCP → output_normalizer
    g.add_edge("llm_mcp", "output_normalizer")
    
    # Other routes to normalizer
    g.add_edge("qdrant", "output_normalizer")
    g.add_edge("llm_soft", "output_normalizer")
    
    # 🗝️ Codex Hunters routing
    # Codex is a MAINTENANCE system. Bypasses Sacred Flow.
    # Success → direct END, errors → output_normalizer for graceful handling
    g.add_conditional_edges(
        "codex_hunters",
        lambda state: "output_normalizer" if state.get("route") == "error_handling" else END,
        {
            "output_normalizer": "output_normalizer",  # Error → normalize
            END: END,                                    # Success → direct END
        }
    )

    # Normalizer → Orthodoxy → Vault → Compose → CAN v2 → Advisor (conditional) → Proactive → END
    g.add_edge("output_normalizer", "orthodoxy")
    g.add_edge("orthodoxy", "vault")
    g.add_edge("vault", "compose")
    g.add_edge("compose", "can")
    
    # 🧠 CAN v2 → Advisor / post-pipeline enrichment
    # If domain edges declare a node sourced from 'advisor' (e.g. proactive_suggestions),
    # that node replaces the default advisor → END terminal edge, and the can fallback
    # routes to it instead of END.
    _post_advisor_node = None
    for _edge in _graph_edges_ext:
        if isinstance(_edge, (list, tuple)) and len(_edge) == 2:
            _src, _tgt = _edge
            if _src == "advisor" and _tgt != "END" and _tgt in registered_nodes:
                _post_advisor_node = _tgt
                break

    if _post_advisor_node:
        # Domain provides post-pipeline enrichment (e.g. finance: proactive_suggestions)
        # advisor → _post_advisor_node edge is already added by domain edge loop above
        # _post_advisor_node → END edge is already added by domain edge loop above
        _pan = _post_advisor_node  # capture for lambda default arg
        g.add_conditional_edges(
            "can",
            lambda state, _fallback=_pan: "advisor" if (
                state.get("user_requests_action", False)
                or state.get("can_mode") == "urgent"
            ) else _fallback,
            {"advisor": "advisor", _pan: _pan},
        )
    else:
        # Default: no post-pipeline enrichment
        g.add_conditional_edges(
            "can",
            lambda state: "advisor" if (
                state.get("user_requests_action", False)
                or state.get("can_mode") == "urgent"
            ) else END,
            {"advisor": "advisor", END: END},
        )
        g.add_edge("advisor", END)
    
    # ❌ REMOVED (Dec 27, 2025): Direct edge codex_hunters → END
    # This was overriding the conditional edges above.
    # Codex Hunters now uses conditional routing based on expedition results.

    compiled = g.compile()
    original_invoke = compiled.invoke   # save original invoke

    def invoke_with_propagation(state: dict):
        """
        Wrapper that ensures critical UX fields survive through Sacred Orders pipeline.
        
        Preserves:
        - sentiment (legacy)
        - entity_ids (legacy)
        - emotion_detected, emotion_confidence, etc (PHASE 2.1)
        - language_detected, cultural_context (Babel Gardens)
        """
        # Snapshot critical UX fields BEFORE graph execution
        ux_snapshot = {
            "emotion_detected": state.get("emotion_detected"),
            "emotion_confidence": state.get("emotion_confidence"),
            "emotion_intensity": state.get("emotion_intensity"),
            "emotion_secondary": state.get("emotion_secondary"),
            "emotion_reasoning": state.get("emotion_reasoning"),
            "emotion_sentiment_label": state.get("emotion_sentiment_label"),
            "emotion_sentiment_score": state.get("emotion_sentiment_score"),
            "emotion_metadata": state.get("emotion_metadata"),
            "cultural_context": state.get("cultural_context"),
            "language_detected": state.get("language_detected"),
            "language_confidence": state.get("language_confidence"),
        }
        
        final_state = original_invoke(state)
        
        # Restore entities if lost during Sacred Orders pipeline
        if "entities" in state and "entities" not in final_state:
            final_state["entities"] = state["entities"]
        
        # 🎭 PHASE 2.1: Restore UX fields if lost during Sacred Orders pipeline
        for field, snapshot_value in ux_snapshot.items():
            if snapshot_value is not None and (field not in final_state or final_state.get(field) is None):
                final_state[field] = snapshot_value
        
        return final_state

    compiled.invoke = invoke_with_propagation
    return compiled


def build_minimal_graph():
    """Phase 1: Minimal LangGraph (4 nodes)."""
    g = StateGraph(GraphState)

    g.add_node("parse", _wrap("parse", parse_node))
    g.add_node("intent", _wrap("intent", intent_detection_node))
    g.add_node("decide", _wrap("decide", route_node))
    g.add_node("compose", _wrap("compose", compose_node))

    g.set_entry_point("parse")

    g.add_edge("parse", "intent")
    g.add_edge("intent", "decide")

    g.add_conditional_edges(
        "decide",
        lambda state: "compose",
        {"compose": "compose"},
    )

    g.add_edge("compose", END)

    return g.compile()
