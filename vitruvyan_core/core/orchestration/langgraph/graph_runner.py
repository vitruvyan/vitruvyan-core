# core/langgraph/graph_runner.py

import os
import json
from typing import Dict, Any
from core.orchestration.langgraph.graph_flow import build_graph, build_minimal_graph
from core.orchestration.langgraph.memory_utils import merge_slots
# proactive_suggestions: ARCHIVED (was domain-specific finance feature)
# from core.logging.audit import  # TODO: audit module not available generate_trace_id  # 🆕 VSGS trace_id generation

# Stub for generate_trace_id
import uuid
def generate_trace_id():
    return str(uuid.uuid4())[:8]

from langdetect import detect
from langdetect import DetectorFactory

# Deterministic language detection
DetectorFactory.seed = 0

# --- Language detection (normalized to {en, it, es}) ---
def _detect_language(text: str) -> str:
    """
    Detect ISO-639-1 code and normalize to supported set.
    Defaults to 'en' if unknown.
    """
    try:
        code = (detect(text or "") or "en").lower()
    except Exception:
        code = "en"
    return "it" if code.startswith("it") else ("es" if code.startswith("es") else "en")


# In-memory session cache (fast, but not persistent)
_SESSION_STATE: Dict[str, Dict[str, Any]] = {}

# Compile the LangGraph once at module load
_ENABLE_MINIMAL = os.getenv("ENABLE_MINIMAL_GRAPH", "false").lower() == "true"
_GRAPH = build_minimal_graph() if _ENABLE_MINIMAL else build_graph()


def run_graph_once(
    input_text: str,
    user_id: str = "demo",
    return_full: bool = False,
    validated_entities: list = None,
    language: str = None,
) -> Dict[str, Any]:
    """
    Execute the graph once for a given user input.
    
    Pipeline:
    1. Load last known conversation state (RAM → Postgres).
    2. Merge with new input (slots, language, validated_entities).
    3. 🆕 Generate trace_id for VSGS audit trail.
    4. Run the LangGraph.
    5. Persist final state to RAM (cache) and Postgres/Qdrant.
    6. Return final response or full state.
    """
    # 1) Load previous state (RAM cache only - VSGS handles conversation context)
    # Phase 1 Migration (Nov 2025): Removed get_last_conversation() call
    # Reason: semantic_grounding_node populates state["semantic_matches"] automatically
    state = _SESSION_STATE.get(user_id) or {}
    state["input_text"] = input_text
    state["user_id"] = user_id
    
    # Golden Rule: validated_entities are authoritative (client validation contract)
    # None → server may attempt extraction; [] → user chose "no entities"; [...] → trust list
    if validated_entities is not None:
        state["entity_ids"] = validated_entities
        state["validated_entities"] = validated_entities
    if language:
        state["language"] = language
    
    # 🆕 2) Generate trace_id for VSGS audit trail (propagated through all nodes)
    state["trace_id"] = generate_trace_id()
    print(f"🔍 [graph_runner] Request trace_id: {state['trace_id']}")

    # 2) Detect and set language (fallback if babel_emotion_node hasn't run yet)
    lang = _detect_language(input_text) if input_text else state.get("language")
    if lang:
        state["language"] = lang

    # Merge slots (budget, entity_ids, horizon, language)
    state = merge_slots(state, state)
    print(f"➡️ [run_graph_once] Initial merged state: {state}")

    # 3) Run the LangGraph
    final_state = _GRAPH.invoke(state)

    # ✅ Override language with Babel Gardens detection (more accurate than langdetect)
    if final_state.get("emotion_metadata") and final_state["emotion_metadata"].get("language"):
        babel_lang = final_state["emotion_metadata"]["language"]
        # Normalize Babel Gardens language codes to our 3-lang system
        if babel_lang.lower() in ["it", "italian", "ita"]:
            final_state["language"] = "it"
        elif babel_lang.lower() in ["es", "spanish", "esp", "spa"]:
            final_state["language"] = "es"
        else:
            final_state["language"] = "en"
        print(f"🌍 [graph_runner] Language overridden from Babel Gardens: {babel_lang} → {final_state['language']}")

    # Debug log (safe truncation)
    print("🟢 [graph_runner] Final state after invoke:",
          json.dumps(final_state, indent=2, default=str)[:1000])
    
    # 🎭 DEBUG: Check emotion_detected presence
    print(f"🎭 [graph_runner] emotion_detected in final_state: {final_state.get('emotion_detected')}")
    print(f"🎭 [graph_runner] Keys in final_state: {list(final_state.keys()) if isinstance(final_state, dict) else 'NOT A DICT'}")

    # 4) Persist results
    _SESSION_STATE[user_id] = final_state
    
    # Phase 1 Migration (Nov 2025): save_conversation() removed
    # Reason: semantic_grounding_node auto-saves to conversations + semantic_states
    # Old code (kept as reference):
    # try:
    #     save_conversation(
    #         user_id=user_id,
    #         input_text=input_text,
    #         slots=final_state,
    #         intent=final_state.get("intent", "unknown")
    #     )
    # except Exception as e:
    #     print(f"⚠️ [graph_runner] Failed to persist conversation: {e}")

    # 5) Return final result
    if return_full:
        return final_state

    # Extract response - prioritize structured response from compose_node
    # Handle both nested and flattened response structures
    response = final_state.get("response") if isinstance(final_state, dict) else None
    
    # proactive_suggestions: ARCHIVED (domain-specific)
    
    # CASE 1: Valid nested response dict from compose_node
    if isinstance(response, dict) and "action" in response:
        # Already in correct format, just ensure Babel Gardens fields are present
        if not response.get("language_detected") and final_state.get("language_detected"):
            response["language_detected"] = final_state.get("language_detected")
            response["language_confidence"] = final_state.get("language_confidence")
            response["babel_status"] = final_state.get("babel_status")
            response["cultural_context"] = final_state.get("cultural_context")
        
        # 🎭 Phase 2.1: Propagate emotion detection from babel_emotion_node
        if final_state.get("emotion_detected"):
            response["emotion_detected"] = final_state.get("emotion_detected")
            response["emotion_confidence"] = final_state.get("emotion_confidence")
            response["emotion_intensity"] = final_state.get("emotion_intensity")
            response["emotion_secondary"] = final_state.get("emotion_secondary")
            response["emotion_reasoning"] = final_state.get("emotion_reasoning")
            response["emotion_sentiment_label"] = final_state.get("emotion_sentiment_label")
            response["emotion_sentiment_score"] = final_state.get("emotion_sentiment_score")
            response["emotion_metadata"] = final_state.get("emotion_metadata")
        
        # �️ FIX (Feb 10, 2026): Propagate Sacred Orders metadata (Orthodoxy + Vault)
        if final_state.get("orthodoxy_verdict"):
            response["orthodoxy_verdict"] = final_state.get("orthodoxy_verdict")
            response["orthodoxy_blessing"] = final_state.get("orthodoxy_blessing")
            response["orthodoxy_confidence"] = final_state.get("orthodoxy_confidence")
            response["orthodoxy_findings"] = final_state.get("orthodoxy_findings")
            response["orthodoxy_message"] = final_state.get("orthodoxy_message")
            response["orthodoxy_timestamp"] = final_state.get("orthodoxy_timestamp")
            response["theological_metadata"] = final_state.get("theological_metadata")
        
        if final_state.get("vault_blessing"):
            response["vault_blessing"] = final_state.get("vault_blessing")
            response["vault_status"] = final_state.get("vault_status")
        
        # ✅ FIX (Nov 2, 2025): Add intent, route, entity_ids, horizon to API response
        response["intent"] = final_state.get("intent")
        response["route"] = final_state.get("route")
        response["entity_ids"] = final_state.get("entity_ids")
        response["horizon"] = final_state.get("horizon")
        response["user_id"] = final_state.get("user_id")
        response["needed_slots"] = final_state.get("needed_slots", [])
        
        # ✅ FIX (Nov 4, 2025): Add VSGS fields to API response
        response["vsgs_status"] = final_state.get("vsgs_status")
        response["vsgs_elapsed_ms"] = final_state.get("vsgs_elapsed_ms")
        response["vsgs_error"] = final_state.get("vsgs_error")
        response["semantic_matches_count"] = len(final_state.get("semantic_matches", []))
        
        # 🕸️ FIX (Dec 25, 2025): Add Pattern Weaver context to API response
        response["weaver_context"] = final_state.get("weaver_context")
        
        # 🧠 FIX (Dec 28, 2025): Add CAN v2 fields to API response
        response["can_mode"] = final_state.get("can_mode")
        response["can_route"] = final_state.get("can_route")
        response["can_response"] = final_state.get("can_response")
        response["follow_ups"] = final_state.get("follow_ups")
        response["conversation_type"] = final_state.get("conversation_type")
        
        # 🎯 FIX (Dec 28, 2025): Add Advisor Node fields to API response
        response["advisor_recommendation"] = final_state.get("advisor_recommendation")
        response["user_requests_action"] = final_state.get("user_requests_action")
        
        return response
    
    # CASE 2: Flattened structure - response fields at root level
    if isinstance(final_state, dict) and "action" in final_state:
        result = {
            "action": final_state.get("action"),
            "questions": final_state.get("questions", []),
            "needed_slots": final_state.get("needed_slots", []),
            "language_detected": final_state.get("language_detected"),
            "language_confidence": final_state.get("language_confidence"),
            "babel_status": final_state.get("babel_status"),
            "cultural_context": final_state.get("cultural_context"),
            "sentiment_label": final_state.get("sentiment_label"),
            "raw_output": final_state.get("raw_output"),
            # 🎭 Phase 2.1: Include emotion detection from babel_emotion_node
            "emotion_detected": final_state.get("emotion_detected"),
            "emotion_confidence": final_state.get("emotion_confidence"),
            "emotion_intensity": final_state.get("emotion_intensity"),
            "emotion_secondary": final_state.get("emotion_secondary"),
            "emotion_reasoning": final_state.get("emotion_reasoning"),
            "emotion_sentiment_label": final_state.get("emotion_sentiment_label"),
            "emotion_sentiment_score": final_state.get("emotion_sentiment_score"),
            "emotion_metadata": final_state.get("emotion_metadata"),
            # 🛡️ FIX (Feb 10, 2026): Add Sacred Orders metadata (Orthodoxy + Vault)
            "orthodoxy_verdict": final_state.get("orthodoxy_verdict"),
            "orthodoxy_blessing": final_state.get("orthodoxy_blessing"),
            "orthodoxy_confidence": final_state.get("orthodoxy_confidence"),
            "orthodoxy_findings": final_state.get("orthodoxy_findings"),
            "orthodoxy_message": final_state.get("orthodoxy_message"),
            "orthodoxy_timestamp": final_state.get("orthodoxy_timestamp"),
            "theological_metadata": final_state.get("theological_metadata"),
            "vault_blessing": final_state.get("vault_blessing"),
            "vault_status": final_state.get("vault_status"),
            # ✅ FIX (Nov 2, 2025): Add intent, route, entity_ids, horizon to API response
            "intent": final_state.get("intent"),
            "route": final_state.get("route"),
            "entity_ids": final_state.get("entity_ids"),
            "horizon": final_state.get("horizon"),
            # ✅ FIX (Nov 4, 2025): Add VSGS fields to API response
            "vsgs_status": final_state.get("vsgs_status"),
            "vsgs_elapsed_ms": final_state.get("vsgs_elapsed_ms"),
            "vsgs_error": final_state.get("vsgs_error"),
            "semantic_matches_count": len(final_state.get("semantic_matches", [])),
            # 🕸️ FIX (Dec 25, 2025): Add Pattern Weaver context to API response
            "weaver_context": final_state.get("weaver_context"),
            # 🧠 FIX (Dec 28, 2025): Add CAN v2 fields to API response
            "can_mode": final_state.get("can_mode"),
            "can_route": final_state.get("can_route"),
            "can_response": final_state.get("can_response"),
            "follow_ups": final_state.get("follow_ups"),
            "conversation_type": final_state.get("conversation_type"),
            # 🎯 FIX (Dec 28, 2025): Add Advisor Node fields to API response
            "advisor_recommendation": final_state.get("advisor_recommendation"),
            "user_requests_action": final_state.get("user_requests_action"),
        }
        
        return result
    
    # CASE 3: No action field - likely semantic_fallback or error
    # Compose a minimal valid response with available metadata
    # Propagate ALL fields consistently (parity with CASE 1 and CASE 2)
    _s = final_state if isinstance(final_state, dict) else {}
    return {
        "action": "clarify",
        "questions": ["Unable to process request. Please provide more details."],
        "semantic_fallback": True,
        "needed_slots": _s.get("needed_slots", []),
        "language_detected": _s.get("language_detected"),
        "language_confidence": _s.get("language_confidence"),
        "babel_status": _s.get("babel_status"),
        "cultural_context": _s.get("cultural_context"),
        # Emotion detection
        "emotion_detected": _s.get("emotion_detected"),
        "emotion_confidence": _s.get("emotion_confidence"),
        "emotion_intensity": _s.get("emotion_intensity"),
        "emotion_secondary": _s.get("emotion_secondary"),
        "emotion_reasoning": _s.get("emotion_reasoning"),
        "emotion_sentiment_label": _s.get("emotion_sentiment_label"),
        "emotion_sentiment_score": _s.get("emotion_sentiment_score"),
        "emotion_metadata": _s.get("emotion_metadata"),
        # Core routing
        "intent": _s.get("intent"),
        "route": _s.get("route"),
        "entity_ids": _s.get("entity_ids"),
        "horizon": _s.get("horizon"),
        "user_id": _s.get("user_id"),
        # Sacred Orders: Orthodoxy
        "orthodoxy_verdict": _s.get("orthodoxy_verdict"),
        "orthodoxy_blessing": _s.get("orthodoxy_blessing"),
        "orthodoxy_confidence": _s.get("orthodoxy_confidence"),
        "orthodoxy_findings": _s.get("orthodoxy_findings"),
        "orthodoxy_message": _s.get("orthodoxy_message"),
        "orthodoxy_timestamp": _s.get("orthodoxy_timestamp"),
        "theological_metadata": _s.get("theological_metadata"),
        # Sacred Orders: Vault
        "vault_blessing": _s.get("vault_blessing"),
        "vault_status": _s.get("vault_status"),
        # VSGS
        "vsgs_status": _s.get("vsgs_status"),
        "vsgs_elapsed_ms": _s.get("vsgs_elapsed_ms"),
        "vsgs_error": _s.get("vsgs_error"),
        "semantic_matches_count": len(_s.get("semantic_matches", [])),
        # Pattern Weavers
        "weaver_context": _s.get("weaver_context"),
        # CAN
        "can_mode": _s.get("can_mode"),
        "can_route": _s.get("can_route"),
        "can_response": _s.get("can_response"),
        "follow_ups": _s.get("follow_ups"),
        "conversation_type": _s.get("conversation_type"),
        # Advisor
        "advisor_recommendation": _s.get("advisor_recommendation"),
        "user_requests_action": _s.get("user_requests_action"),
    }


def run_graph(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Variant that accepts an API-style payload:
    - { "input": "..." }
    - { "input_text": "..." }
    - { "user_id": "..." }
    """
    print(f"➡️ [run_graph] Incoming payload: {payload}")

    if not payload:
        return run_graph_once("", "demo")

    text = payload.get("input") or payload.get("input_text") or ""
    user_id = payload.get("user_id", "demo")
    print(f"➡️ [run_graph] user_id={user_id}, input_text={text.strip()}")

    return run_graph_once(text.strip(), user_id)
