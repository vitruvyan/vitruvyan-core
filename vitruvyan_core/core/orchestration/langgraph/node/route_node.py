"""
Route Node — Domain-Agnostic Routing
======================================

Decides which node to route to based on LLM intent + proposed_exec.
Routing is fully configurable via IntentRegistry route_types.

Priority:
  0. If Codex Hunters expedition needed → codex_expedition.
  1. If LLM suggested a proposed_exec → dispatcher_exec.
  2. Else, if intent route_type is "soft" → llm_soft.
  3. Else, if intent route_type is "semantic" → semantic_fallback.
  4. Else, if intent route_type is "exec" → dispatcher_exec.
  5. Fallback: semantic_fallback.

Configuration:
  Call configure(exec_intents, soft_intents) at boot time.
  graph_flow.py does this automatically from IntentRegistry.

Version: 3.0 (Feb 14, 2026)
  - Finance-specific TECHNICAL_INTENTS removed
  - Routing driven by IntentRegistry route_types
"""

from typing import Dict, Any, List

import logging

logger = logging.getLogger(__name__)

# Module-level configuration (set by graph_flow.py at boot)
_exec_intents: List[str] = []
_soft_intents: List[str] = ["soft"]


def configure(exec_intents: List[str] = None, soft_intents: List[str] = None) -> None:
    """
    Configure routing intent lists from IntentRegistry.
    Called by graph_flow.py during graph construction.
    
    Args:
        exec_intents: Intent names that route to dispatcher_exec
        soft_intents: Intent names that route to llm_soft
    """
    global _exec_intents, _soft_intents
    if exec_intents is not None:
        _exec_intents = exec_intents
    if soft_intents is not None:
        _soft_intents = soft_intents
    logger.info(f"[ROUTE_NODE] Configured: exec_intents={_exec_intents}, soft_intents={_soft_intents}")


def route_node(state: dict) -> dict:
    """
    Domain-agnostic routing based on intent + proposed_exec.
    Uses configure() lists set at boot time from IntentRegistry.
    """
    logger.debug(f"[ROUTE_NODE] intent={state.get('intent')}, proposed_exec={state.get('proposed_exec')}")

    # Check for Codex Hunters expedition trigger first
    try:
        from core.orchestration.langgraph.codex_trigger import should_trigger_codex_expedition
        
        if should_trigger_codex_expedition(state):
            state["route"] = "codex_expedition"
            logger.info(f"[ROUTE_NODE] Codex Hunters expedition triggered → codex_expedition")
            return state
    except Exception as e:
        logger.warning(f"[ROUTE_NODE] Codex trigger check failed: {e}")

    intent = state.get("intent", "unknown")
    proposed_exec = state.get("proposed_exec")

    if proposed_exec:
        state["route"] = "dispatcher_exec"
        logger.info(f"[ROUTE_NODE] proposed_exec '{proposed_exec}' → dispatcher_exec")

    elif intent in _soft_intents:
        state["route"] = "llm_soft"
        logger.info(f"[ROUTE_NODE] intent '{intent}' → llm_soft")

    elif intent == "unknown":
        state["route"] = "semantic_fallback"
        logger.info(f"[ROUTE_NODE] intent 'unknown' → semantic_fallback (RAG + LLM-first)")

    elif intent in _exec_intents:
        state["route"] = "dispatcher_exec"
        logger.info(f"[ROUTE_NODE] intent '{intent}' → dispatcher_exec")

    else:
        state["route"] = "semantic_fallback"
        logger.info(f"[ROUTE_NODE] intent '{intent}' not recognized → semantic_fallback")

    logger.info(f"[ROUTE_NODE] intent={intent} → route={state['route']}")
    return state
