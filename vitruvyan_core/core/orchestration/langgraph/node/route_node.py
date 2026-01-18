from typing import Dict, Any
import json

def route_node(state: dict) -> dict:
    """
    Decides which node to route to based on LLM intent + proposed_exec.
    Priority:
      0. If Codex Hunters expedition needed → go to codex_expedition.
      1. If LLM suggested a proposed_exec → go to dispatcher_exec (technical analysis).
      2. Else, if intent is soft/horizon_advice → go to llm_soft (empathetic advisor).
      3. Else, if intent is unknown → go to semantic_fallback.
      4. Else, if intent is technical (trend, momentum, volatility, risk, backtest, allocate, collection, sentiment) → dispatcher_exec.
      5. Fallback: semantic_fallback.
    """
    print(f"\n{'='*80}")
    print(f"🔍 [ROUTE_NODE] ENTRY - Full state dump:")
    print(f"  - emotion_detected: {state.get('emotion_detected')}")
    print(f"  - _ux_metadata: {state.get('_ux_metadata')}")
    print(f"  - State keys: {list(state.keys())}")
    print(json.dumps({k: str(v)[:100] if isinstance(v, (dict, list)) else v for k, v in state.items()}, indent=2))
    print(f"{'='*80}\n")

    # 🗝️ Check for Codex Hunters expedition trigger first
    try:
        from core.langgraph.codex_trigger import should_trigger_codex_expedition
        
        if should_trigger_codex_expedition(state):
            state["route"] = "codex_expedition"
            print(f"🗝️ Routing: Codex Hunters expedition triggered → codex_expedition")
            print(f"[DEBUG route_node exit] route={state['route']}, codex_type={state.get('codex_expedition_type')}")
            return state
    except Exception as e:
        print(f"⚠️ Codex trigger check failed: {e}")

    intent = state.get("intent", "unknown")
    proposed_exec = state.get("proposed_exec")

    TECHNICAL_INTENTS = [
        "trend",
        "momentum",
        "volatility",
        "risk",
        "backtest",
        "allocate",
        "collection",
        "sentiment"
        # ❌ NOTE: "unknown" NOT included here - routed directly to compose for slot check
    ]

    if proposed_exec:
        # If LLM explicitly suggested a technical node, respect it
        state["route"] = "dispatcher_exec"
        print(f"➡️ Routing: proposed_exec '{proposed_exec}' → dispatcher_exec")

    elif intent in ["soft", "horizon_advice"]:
        state["route"] = "llm_soft"
        print(f"➡️ Routing: intent '{intent}' → llm_soft")

    elif intent == "unknown":
        # "unknown" goes to slot_filler for priority slot check in compose_node
        state["route"] = "slot_filler"
        print(f"➡️ Routing: intent 'unknown' → slot_filler (compose with slot check priority)")

    elif intent in TECHNICAL_INTENTS:
        state["route"] = "dispatcher_exec"
        print(f"➡️ Routing: intent '{intent}' → dispatcher_exec (technical)")

    else:
        # Fallback
        state["route"] = "semantic_fallback"
        print(f"➡️ Routing: intent '{intent}' not recognized → semantic_fallback")

    print(f"\n{'='*80}")
    print(f"🔍 [ROUTE_NODE] EXIT:")
    print(f"  - route: {state['route']}")
    print(f"  - intent: {intent}")
    print(f"  - proposed_exec: {proposed_exec}")
    print(f"  - entity_ids: {state.get('entity_ids')}")
    print(f"  - State keys: {list(state.keys())}")
    print(f"{'='*80}\n")
    
    return state
