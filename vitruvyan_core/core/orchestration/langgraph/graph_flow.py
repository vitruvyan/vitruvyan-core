# core/langgraph/graph_flow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict, Any, List

# Import modular nodes
from core.orchestration.langgraph.node.parse_node import parse_node
from core.orchestration.langgraph.node.route_node import route_node
from core.orchestration.langgraph.node.exec_node import exec_node
from core.orchestration.langgraph.node.qdrant_node import qdrant_node
from core.orchestration.langgraph.node.compose_node import compose_node
from core.orchestration.langgraph.node.sentiment_node import run_sentiment_node
# 🎭 PHASE 2.1 - Babel Gardens Emotion Detection
from core.orchestration.langgraph.node.babel_emotion_node import babel_emotion_node
# Enhanced LLM node with caching
from core.orchestration.langgraph.node.cached_llm_node import cached_llm_node
from core.orchestration.langgraph.memory_utils import merge_slots

# 🧠 PHASE 2.1 - Consolidated Intent Detection (babel + intent_llm + intent_mapper)
from core.orchestration.langgraph.node.intent_detection_node import intent_detection_node

# 🔍 PHASE 2.2 - Consolidated Quality Check (fallback + validation)
from core.orchestration.langgraph.node.quality_check_node import quality_check_node

# ⚙️ PHASE 2.3 - Consolidated Parameter Extraction (horizon_parser + topk_parser)
from core.orchestration.langgraph.node.params_extraction_node import params_extraction_node

# 🔥 New planned nodes (stubs + new)
from core.orchestration.langgraph.node.entity_resolver_node import entity_resolver_node
from core.orchestration.langgraph.node.screener_node import screener_node
from core.orchestration.langgraph.node.output_normalizer_node import output_normalizer_node
from core.orchestration.langgraph.node.audit_node_simple import audit_node

# 🏛️ Sacred Orders Integration
from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node
from core.orchestration.langgraph.node.vault_node import vault_node

# 🛡️ Sentinel Order Integration  
from core.orchestration.langgraph.node.sentinel_node import sentinel_node

# 🗝️ Codex Hunters Integration
from core.orchestration.langgraph.node.codex_hunters_node import codex_hunters_node

# 🧠 CrewAI Strategic Order Integration
from core.orchestration.langgraph.node.crew_node import crew_node

# 💡 Proactive Intelligence - Phase 2.1
from core.orchestration.langgraph.node.proactive_suggestions_node import proactive_suggestions_node

# 🔌 MCP Integration - Phase 4 (Model Context Protocol + OpenAI Function Calling)
from core.orchestration.langgraph.node.llm_mcp_node import llm_mcp_node

# 🏛️ Collection Analysis - Day 3
from core.orchestration.langgraph.node.portfolio_node import portfolio_node

# 🧠 VSGS (Vitruvyan Semantic Grounding System) - PR-A Bootstrap
from core.orchestration.langgraph.node.semantic_grounding_node import semantic_grounding_node

# 🕸️ Pattern Weavers - Semantic enrichment (Nov 2025)
from core.cognitive.pattern_weavers.weaver_node import weaver_node

# 🎯 Advisor Node - Decision-making layer (Dec 27, 2025)
from core.orchestration.langgraph.node.advisor_node import advisor_node

# 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
from core.orchestration.langgraph.node.can_node import can_node

# Shared state
class GraphState(TypedDict, total=False):
    input_text: str
    route: str
    result: Dict[str, Any]
    error: Optional[str]
    response: Dict[str, Any]
    budget: Optional[str]
    entity_ids: Optional[list[str]]
    horizon: Optional[str]
    user_id: Optional[str]
    sentiment: Optional[Dict[str, Any]]
    intent: Optional[str]
    raw_output: Optional[Dict[str, Any]]
    top_k: Optional[int]
    final_response: Optional[str]            # 🎯 Formatted narrative for user display
    proactive_suggestions: Optional[List[Dict[str, Any]]]  # 💡 Phase 2.1 - Proactive suggestions
    
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
    sentinel_portfolio_value: Optional[float] # Collection value under protection
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
    can_route: Optional[str]  # single | comparison | screening | collection | allocation | sector | chat
    follow_ups: Optional[List[str]]  # Suggested next questions
    conversation_type: Optional[str]  # single | comparison | collection | screening | allocation | sector


def run_graph_once(user_input: str, user_id: str = "demo"):
    state = {"input_text": user_input, "user_id": user_id}

    # 0) Load previous slots - REMOVED (Phase 1 Migration Nov 2025)
    # Reason: VSGS (semantic_grounding_node) handles conversation context automatically
    # state["semantic_matches"] will be populated by semantic_grounding_node if enabled
    # Old code: last_slots = get_last_conversation(user_id)
    last_slots = None  # Placeholder for merge_slots compatibility

    # 1) Parse input
    state = parse_node(state)

    # 2) Merge slots
    if last_slots:
        state = merge_slots(last_slots, state)

    # 3) 🧠 PHASE 2.1 - Unified Intent Detection (language + intent + synonyms)
    state = intent_detection_node(state)
    
    # 🕸️ Pattern Weavers - Semantic enrichment after intent detection (Nov 2025)
    state = weaver_node(state)

    # 4) Resolve entity_id
    state = entity_resolver_node(state)

    # 5) Parse horizon
    state = horizon_parser_node(state)

    # 6) Parse top-k
    state = topk_parser_node(state)

    # 7) Routing
    state = route_node(state)

    # 9) Save updated state - REMOVED (Phase 1 Migration Nov 2025)
    # Reason: semantic_grounding_node auto-saves conversations to PostgreSQL + Qdrant
    # Old code (kept as reference for Phase 2 removal):
    # try:
    #     slots_to_save = {
    #         "entity_ids": state.get("entity_ids"),
    #         "budget": state.get("budget"),
    #         "horizon": state.get("horizon"),
    #         "language": state.get("language"),
    #     }
    #     save_conversation(
    #         user_id=state.get("user_id"),
    #         input_text=state.get("input_text") or "<NO_INPUT>",
    #         slots=slots_to_save,
    #         intent=state.get("intent", "unknown")
    #     )
    # except Exception as e:
    #     print(f"⚠️ Error saving conversation: {e}")

    return state


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
    g.add_node("sentiment_node", run_sentiment_node)
    # 🎭 PHASE 2.1 - Babel Gardens Emotion Detection
    g.add_node("babel_emotion", babel_emotion_node)
    # 🧠 PR-A: VSGS Semantic Grounding (feature flag OFF by default)
    g.add_node("semantic_grounding", semantic_grounding_node)
    g.add_node("exec", exec_node)
    
    # 🔍 PHASE 2.2 - Consolidated Quality Check (fallback + validation)
    g.add_node("quality_check", quality_check_node)
    
    g.add_node("screener", screener_node)
    g.add_node("qdrant", qdrant_node)
    # 💡 UX Quick Win 2: Enhanced LLM with Emotional Intelligence (Oct 29, 2025)
    g.add_node("llm_soft", cached_llm_node)
    g.add_node("output_normalizer", output_normalizer_node)
    g.add_node("compose", compose_node)
    
    # 💡 Phase 2.1: Proactive Intelligence
    g.add_node("proactive_suggestions", proactive_suggestions_node)
    
    # � Advisor Node - Decision-making layer (Dec 27, 2025)
    g.add_node("advisor", advisor_node)
    
    # 🧠 CAN v2 - Conversational Advisor Node (Dec 27, 2025)
    g.add_node("can", can_node)
    
    # �🏛️ Collection Analysis - Day 3
    g.add_node("collection", portfolio_node)
    
    # 🏛️ Sacred Orders Integration  
    g.add_node("orthodoxy", orthodoxy_node)
    g.add_node("vault", vault_node)
    
    # 🛡️ Sentinel Order Integration
    g.add_node("sentinel", sentinel_node)
    
    # 🗝️ Codex Hunters Integration
    g.add_node("codex_hunters", codex_hunters_node)
    
    # 🧠 CrewAI Strategic Order Integration
    g.add_node("crew", crew_node)
    
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
        
        🔌 Phase 4: If USE_MCP=1 and route is dispatcher_exec, route to llm_mcp instead of sentiment_node.
        This enables OpenAI Function Calling → MCP → Sacred Orders flow.
        """
        import os
        
        route_value = state.get("route")
        intent_value = state.get("intent")
        tickers_value = state.get("entity_ids")
        
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
        print(f"  - state['entity_ids'] = {tickers_value}")
        print(f"  - All state keys: {list(state.keys())}")
        print(f"🔀 Target node: '{route_value}'")
        print(f"{'🔀'*40}\n")
        
        return route_value

    g.add_conditional_edges(
        "decide",
        route_from_decide,
        {
            "semantic_fallback": "qdrant",
            "dispatcher_exec": "sentiment_node",
            "llm_mcp": "llm_mcp",                 # 🔌 Phase 4: MCP routing (when USE_MCP=1)
            "slot_filler": "compose",
            "llm_soft": "llm_soft",
            "screener": "screener",
            "codex_expedition": "codex_hunters",  # 🗝️ New route for Codex Hunters
            "sentinel_monitoring": "sentinel",    # 🛡️ Collection Guardian / Sentinel Order
            "portfolio_guardian": "sentinel",     # 🛡️ Alternative route name
            "risk_assessment": "sentinel",        # 🛡️ Risk analysis route
            "emergency": "sentinel",              # 🛡️ Emergency response route
            "portfolio_review": "collection",      # 🏛️ Collection analysis with LLM reasoning (Day 3)
            "crew_strategy": "crew",              # 🧠 CrewAI strategic analysis
            "trend": "crew",                      # 🧠 Trend analysis via CrewAI
            "momentum": "crew",                   # 🧠 Momentum analysis via CrewAI
            "volatility": "crew",                 # 🧠 Volatility analysis via CrewAI
            "backtest": "crew",                   # 🧠 Backtest via CrewAI
            "collection": "crew",                  # 🧠 Collection analysis via CrewAI (legacy)
        },
    )

    # 🔍 PHASE 2.2: Consolidated quality check pipeline
    # exec → quality_check → output_normalizer
    g.add_edge("sentiment_node", "exec")
    g.add_edge("exec", "quality_check")
    g.add_edge("quality_check", "output_normalizer")
    
    # 🔌 Phase 4: MCP → quality_check (Sacred Orders results validation)
    g.add_edge("llm_mcp", "quality_check")
    
    # Altri rami verso normalizer
    g.add_edge("screener", "output_normalizer")
    g.add_edge("qdrant", "output_normalizer")
    g.add_edge("llm_soft", "output_normalizer")
    
    # 🗝️ Codex Hunters routing (Fixed Dec 27, 2025)
    # Codex is a MAINTENANCE system, NOT financial analysis.
    # It bypasses Sacred Flow (normalizer→orthodoxy→vault→compose→CAN) 
    # and returns directly to END with formatted response.
    #
    # Routes set by codex_hunters_node.py:
    #   - full_audit → codex_complete (direct END)
    #   - healing → codex_complete (direct END)
    #   - discovery → codex_complete (direct END)
    #   - error → quality_check (for error handling)
    g.add_conditional_edges(
        "codex_hunters",
        lambda state: "quality_check" if state.get("route") == "error_handling" else END,
        {
            "quality_check": "quality_check",  # Expedition failed → quality check
            END: END,                          # Success → direct END (response already formatted)
        }
    )
    
    # 🛡️ Sentinel Order routing based on risk level and situation
    g.add_conditional_edges(
        "sentinel",
        lambda state: state.get("route"),
        {
            "emergency": "vault",                   # Emergency → Direct vault protection
            "monitor": "orthodoxy",                 # Enhanced monitoring → Standard flow
            "compose": "output_normalizer",         # Normal operations → Continue normally
            "escalation": "vault",                  # Escalated situations → Vault protection
        }
    )
    
    # 🧠 CrewAI Strategic Order routing (async acknowledgment flow)
    g.add_conditional_edges(
        "crew",
        lambda state: state.get("route"),
        {
            "compose": "output_normalizer",         # Strategy request acknowledged → Continue
            "error": "quality_check",               # Error in request → Quality check handling (PHASE 2.2)
        }
    )
    
    # 🏛️ Collection Analysis routing (Day 3)
    g.add_conditional_edges(
        "collection",
        lambda state: state.get("route"),
        {
            "portfolio_complete": "compose",        # Collection analysis complete → Direct to compose (skip normalizer)
            "error": "quality_check",               # Error in collection fetch → Quality check
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
        lambda state: "advisor" if (state.get("user_requests_action", False) or state.get("can_mode") == "urgent") else "proactive_suggestions",
        {
            "advisor": "advisor",
            "proactive_suggestions": "proactive_suggestions",
        }
    )
    
    g.add_edge("advisor", "proactive_suggestions")
    g.add_edge("proactive_suggestions", END)
    
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
        
        # Restore sentiment/entity_ids if lost (legacy)
        if "sentiment" in state and "sentiment" not in final_state:
            final_state["sentiment"] = state["sentiment"]
        if "entity_ids" in state and "entity_ids" not in final_state:
            final_state["entity_ids"] = state["entity_ids"]
        
        # 🎭 PHASE 2.1: Restore UX fields if lost during Sacred Orders pipeline
        for field, snapshot_value in ux_snapshot.items():
            if snapshot_value is not None and (field not in final_state or final_state.get(field) is None):
                final_state[field] = snapshot_value
        
        return final_state

    compiled.invoke = invoke_with_propagation
    return compiled
