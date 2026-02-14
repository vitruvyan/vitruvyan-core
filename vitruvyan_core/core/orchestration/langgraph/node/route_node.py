from typing import Dict, Any

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
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[ROUTE_NODE] intent={state.get('intent')}, proposed_exec={state.get('proposed_exec')}")

    # 🗝️ Check for Codex Hunters expedition trigger first
    try:
        from core.orchestration.langgraph.codex_trigger import should_trigger_codex_expedition
        
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
        # "unknown" goes to semantic_fallback (LLM-first architecture via RAG)
        # Rationale: Deprecated slot-filling pattern (see SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md)
        # RAG search provides context → compose → CAN node extracts semantic meaning
        state["route"] = "semantic_fallback"
        print(f"➡️ Routing: intent 'unknown' → semantic_fallback (RAG + LLM-first)")

    elif intent in TECHNICAL_INTENTS:
        state["route"] = "dispatcher_exec"
        print(f"➡️ Routing: intent '{intent}' → dispatcher_exec (technical)")

    else:
        # Fallback
        state["route"] = "semantic_fallback"
        print(f"➡️ Routing: intent '{intent}' not recognized → semantic_fallback")

    logger.info(f"[ROUTE_NODE] intent={intent} → route={state['route']}")
    return state
