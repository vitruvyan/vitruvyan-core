# core/langgraph/graph_flow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any, List

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

# Configure intent detection with finance domain (domain plugin pattern)
import os as _os
_INTENT_DOMAIN = _os.getenv("INTENT_DOMAIN", "finance")
if _INTENT_DOMAIN == "finance":
    from domains.finance.intent_config import (
        create_finance_registry,
        CONTEXT_KEYWORDS as _CTX_KW,
        AMBIGUOUS_PATTERNS as _AMB_PAT,
    )
    _intent_reg = create_finance_registry()
    _intent_mod.configure(_intent_reg, context_keywords=_CTX_KW, ambiguous_patterns=_AMB_PAT)
else:
    from core.orchestration.intent_registry import create_generic_registry
    _intent_reg = create_generic_registry()
    _intent_mod.configure(_intent_reg)

# Configure route_node with registry-driven intent routing (domain-agnostic)
_route_mod.configure(
    exec_intents=_intent_reg.get_exec_intent_names(),
    soft_intents=_intent_reg.get_soft_intent_names(),
)

# 🔍 PHASE 2.2 - Quality Check (ARCHIVED → _legacy/quality_check_node.py)

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

# 💡 Proactive Suggestions (ARCHIVED → _legacy/proactive_suggestions_node.py)

# 🔌 MCP Integration - Phase 4 (Model Context Protocol + OpenAI Function Calling)
from core.orchestration.langgraph.node.llm_mcp_node import llm_mcp_node

# 🧠 VSGS (Vitruvyan Semantic Grounding System) - PR-A Bootstrap
from core.orchestration.langgraph.node.semantic_grounding_node import semantic_grounding_node

# Pattern Weavers - Semantic enrichment (v2 — HTTP adapter)
from core.orchestration.langgraph.node.pattern_weavers_node import pattern_weavers_node as weaver_node

# 🎯 Advisor Node - Decision-making layer (Dec 27, 2025)
from core.orchestration.langgraph.node.advisor_node import advisor_node

# 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
from core.orchestration.langgraph.node.can_node import can_node

# Shared state — Domain-Agnostic OS Kernel
class GraphState(TypedDict, total=False):
    # Core OS fields
    input_text: str
    route: str
    result: Dict[str, Any]
    error: Optional[str]
    response: Dict[str, Any]
    user_id: Optional[str]
    intent: Optional[str]
    raw_output: Optional[Dict[str, Any]]
    final_response: Optional[str]            # 🎯 Formatted narrative for user display
    # proactive_suggestions: ARCHIVED (was domain-specific finance feature)
    
    # Domain-agnostic entity/signal fields (replaces budget/horizon/entity_ids)
    entities: Optional[List[Dict[str, Any]]]  # Generic entities (id, type, attributes)
    entity_ids: Optional[List[str]]           # Legacy entity IDs (tickers, codes) - used by parse/compose
    validated_entities: Optional[List[str]]   # Client-validated entities (authoritative per Golden Rules)
    context_entities: Optional[List[str]]     # Fallback entities from context/VSGS
    signals: Optional[Dict[str, Any]]         # Generic signals (sentiment, score, metadata)
    context: Optional[Dict[str, Any]]         # Vertical-specific extensible context
    top_k: Optional[int]                      # Generic parameter (top K results)
    
    # Legacy slot fields (used by parse/compose/route nodes)
    budget: Optional[Any]                    # Budget parameter
    horizon: Optional[str]                   # Time horizon
    amount: Optional[Any]                    # Amount (alias for budget in route_node)
    companies: Optional[List[str]]           # Extracted company names
    flow: Optional[str]                      # Flow type (direct, clarification)
    language: Optional[str]                  # Language hint from client
    
    # 🚨 Professional Boundaries Fields (Nov 2, 2025)
    needs_clarification: Optional[bool]      # True if query is ambiguous and requires clarification
    clarification_reason: Optional[str]      # Why the query was rejected (for UX messaging)
    
    # 🏛️ Sacred Orthodoxy Fields
    orthodoxy_status: Optional[str]           # blessed, purified, under_review, locally_blessed
    orthodoxy_verdict: Optional[str]          # absolution_granted, penance_required, local_blessing
    orthodoxy_findings: Optional[int]         # Number of heresies detected
    orthodoxy_confidence: Optional[float]     # Confidence in verdict (0.0-1.0)
    orthodoxy_blessing: Optional[str]         # Divine blessing message
    orthodoxy_message: Optional[str]          # Human-readable orthodoxy message
    orthodoxy_timestamp: Optional[str]        # When orthodoxy audit completed
    orthodoxy_duration_ms: Optional[float]    # Time taken for audit
    theological_metadata: Optional[Dict[str, Any]]  # Additional theological info
    
    # 🏰 Sacred Vault Fields 
    vault_status: Optional[str]               # blessed, protected, emergency_blessed, locally_blessed
    vault_protection: Optional[str]          # divine_blessing_applied, standard_blessing, emergency_fallback
    vault_guardian: Optional[str]            # protection_granted, local_protection, emergency_protection
    vault_blessing: Optional[Dict[str, Any]]  # Complete vault metadata
    vault_timestamp: Optional[str]           # When vault protection completed
    vault_duration_ms: Optional[float]       # Time taken for protection
    
    # 🛡️ Sentinel Order Fields
    sentinel_risk_score: Optional[float]     # Current risk assessment (0.0-1.0)
    sentinel_collection_value: Optional[float] # Value of collection under protection
    sentinel_protection_mode: Optional[str]  # conservative, balanced, aggressive, emergency
    sentinel_alerts: Optional[List[str]]     # Active alerts
    sentinel_status: Optional[str]           # monitoring, alert_issued, emergency, recovery
    sentinel_escalation: Optional[bool]      # Whether escalation was triggered
    sentinel_message: Optional[str]          # Human-readable sentinel message
    sentinel_timestamp: Optional[str]        # When sentinel processing completed
    sentinel_correlation_id: Optional[str]   # Event correlation ID
    conclave_event: Optional[Dict[str, Any]] # Raw Synaptic Conclave event data
    
    # 🧠 CrewAI Strategic Order Fields
    crew_correlation_id: Optional[str]       # Correlation ID for async tracking
    crew_analysis_type: Optional[str]        # Type of analysis (comprehensive, trend, risk, etc.)
    crew_status: Optional[str]               # requested, processing, completed, failed
    crew_strategy_result: Optional[Dict[str, Any]]  # Complete strategy result
    crew_agents_used: Optional[List[str]]    # List of agents in execution
    crew_execution_time: Optional[float]     # Time taken for strategy generation
    crew_confidence: Optional[float]         # Confidence score (0.0-1.0)
    crew_timestamp: Optional[str]            # When crew processing completed
    
    # 🌿 Babel Gardens Linguistic Unity Fields
    babel_status: Optional[str]              # success, degraded, failed, idle
    sentiment_label: Optional[str]           # positive, negative, neutral, error
    sentiment_score: Optional[float]         # Fused sentiment score (None on failure)
    language_detected: Optional[str]         # Language code (en, de, it, ja, etc.)
    language_confidence: Optional[float]     # Language detection confidence (0.0-1.0)
    cultural_context: Optional[str]          # Cultural interpretation
    babel_analysis_summary: Optional[Dict[str, Any]]  # Complete Babel analysis
    babel_metrics: Optional[Dict[str, Any]]  # Performance telemetry
    babel_timestamp: Optional[str]           # When Babel processing completed
    
    # 🎭 Babel Gardens Emotion Detection Fields (Phase 2.1)
    emotion_detected: Optional[str]          # Primary emotion (frustrated, excited, anxious, etc.)
    emotion_confidence: Optional[float]      # Detection confidence (0.0-1.0)
    emotion_intensity: Optional[str]         # low, medium, high
    emotion_secondary: Optional[str]         # Secondary emotion if present
    emotion_reasoning: Optional[str]         # Why this emotion was detected
    emotion_sentiment_label: Optional[str]   # Sentiment from emotion module
    emotion_sentiment_score: Optional[float] # Sentiment score from emotion module
    emotion_metadata: Optional[Dict[str, Any]]  # Additional emotion context
    _ux_metadata: Optional[Dict[str, Any]]   # Protected UX fields for Sacred Orders bypass
    
    # 🧠 VSGS (Vitruvyan Semantic Grounding System) Fields (PR-A Bootstrap)
    trace_id: Optional[str]                  # Request trace ID for audit trail (generated in graph_runner)
    semantic_matches: Optional[List[Dict[str, Any]]]  # Top-k similar contexts from Qdrant
    vsgs_status: Optional[str]               # enabled, disabled, error, skipped
    vsgs_elapsed_ms: Optional[float]         # VSGS processing time
    vsgs_error: Optional[str]                # Error message if vsgs_status=error
    
    # 🕸️ Pattern Weavers Context
    weaver_context: Optional[Dict[str, Any]] # Semantic context from Pattern Weavers
    
    # 🎯 Advisor Node Fields (Dec 27, 2025)
    advisor_recommendation: Optional[Dict[str, Any]]  # Actionable recommendation (action, confidence, rationale)
    user_requests_action: Optional[bool]  # Trigger for advisor activation ("cosa fare?", "comprare?")
    
    # 🧠 CAN v2 Fields (Dec 27, 2025)
    can_response: Optional[Dict[str, Any]]  # CAN structured response (CANResponse schema)
    can_mode: Optional[str]  # urgent | analytical | exploratory | conversational
    can_route: Optional[str]  # Routing mode (domain plugin defines valid values)
    follow_ups: Optional[List[str]]  # Suggested next questions
    conversation_type: Optional[str]  # Conversation mode (domain plugin defines valid values)


# run_graph_once() REMOVED — consolidated into graph_runner.py
# Use: from core.orchestration.langgraph.graph_runner import run_graph_once


def build_graph():
    g = StateGraph(GraphState)

    # Nodi
    g.add_node("parse", parse_node)
    
    # 🧠 PHASE 2.1 - Consolidated Intent Detection (babel + intent_llm + intent_mapper)
    g.add_node("intent_detection", intent_detection_node)
    
    # 🕸️ Pattern Weavers - Semantic enrichment after intent detection (Nov 2025)
    g.add_node("weaver", weaver_node)
    
    g.add_node("entity_resolver", entity_resolver_node)
    
    # ⚙️ PHASE 2.3 - Consolidated Parameter Extraction (horizon_parser + topk_parser)
    g.add_node("params_extraction", params_extraction_node)
    
    g.add_node("decide", route_node)
    # 🎭 PHASE 2.1 - Babel Gardens Emotion Detection
    g.add_node("babel_emotion", babel_emotion_node)
    # 🧠 PR-A: VSGS Semantic Grounding (feature flag OFF by default)
    g.add_node("semantic_grounding", semantic_grounding_node)
    g.add_node("exec", exec_node)
    
    # 🔍 quality_check: ARCHIVED (domain-specific validation)
    g.add_node("qdrant", qdrant_node)
    # 💡 UX Quick Win 2: Enhanced LLM with Emotional Intelligence (Oct 29, 2025)
    g.add_node("llm_soft", cached_llm_node)
    g.add_node("output_normalizer", output_normalizer_node)
    g.add_node("compose", compose_node)
    
    # 💡 proactive_suggestions: ARCHIVED (domain-specific)
    
    # 🎯 Advisor Node - Decision-making layer (Dec 27, 2025)
    g.add_node("advisor", advisor_node)
    
    # 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
    g.add_node("can", can_node)
    
    # 🏛️ Sacred Orders Integration  
    g.add_node("orthodoxy", orthodoxy_node)
    g.add_node("vault", vault_node)
    
    # 🗝️ Codex Hunters Integration
    g.add_node("codex_hunters", codex_hunters_node)
    
    # 🔌 MCP Integration - Phase 4 (OpenAI Function Calling gateway)
    g.add_node("llm_mcp", llm_mcp_node)

    g.set_entry_point("parse")

    # 🧠 PHASE 2: Consolidated pipeline
    # parse → intent_detection → weaver → entity_resolver → babel_emotion → semantic_grounding → params_extraction → decide
    g.add_edge("parse", "intent_detection")
    g.add_edge("intent_detection", "weaver") # New edge
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
        
        # 🔌 MCP Integration: Check if MCP should handle this route
        use_mcp = os.getenv("USE_MCP", "0") == "1"
        if use_mcp and route_value == "dispatcher_exec":
            print(f"\n{'🔌'*40}")
            print(f"🔌 [MCP ROUTING] USE_MCP=1 detected, routing to llm_mcp node")
            print(f"  - Original route: '{route_value}'")
            print(f"  - MCP will use OpenAI Function Calling for tool selection")
            print(f"  - Sacred Orders validation will be applied via MCP server")
            print(f"{'🔌'*40}\n")
            return "llm_mcp"
        
        print(f"\n{'🔀'*40}")
        print(f"🔀 [CONDITIONAL_EDGE] Evaluating route from 'decide' node:")
        print(f"  - state['route'] = '{route_value}'")
        print(f"  - state['intent'] = '{intent_value}'")
        print(f"  - state['entities'] = {entities_value}")
        print(f"  - All state keys: {list(state.keys())}")
        print(f"🔀 Target node: '{route_value}'")
        print(f"{'🔀'*40}\n")
        
        return route_value

    g.add_conditional_edges(
        "decide",
        route_from_decide,
        {
            "semantic_fallback": "qdrant",
            "dispatcher_exec": "exec",            # Direct execution (no sentiment prereq)
            "llm_mcp": "llm_mcp",                 # 🔌 Phase 4: MCP routing (when USE_MCP=1)
            "slot_filler": "compose",
            "llm_soft": "llm_soft",
            "codex_expedition": "codex_hunters",  # 🗝️ Codex Hunters (maintenance system)
        },
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
    
    # 🧠 CAN v2 → Advisor (conditional: only if user_requests_action=True or can_mode='urgent')
    g.add_conditional_edges(
        "can",
        lambda state: "advisor" if (state.get("user_requests_action", False) or state.get("can_mode") == "urgent") else END,
        {
            "advisor": "advisor",
            END: END,
        }
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

    g.add_node("parse", parse_node)
    g.add_node("intent", intent_detection_node)
    g.add_node("decide", route_node)
    g.add_node("compose", compose_node)

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
