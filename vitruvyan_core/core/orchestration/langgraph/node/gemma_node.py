# core/langgraph/node/gemma_node.py

from typing import Dict, Any
import logging
from core.cognitive.gemma_client import gemma_predict

logger = logging.getLogger(__name__)

def gemma_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo LangGraph per chiamare Gemma e aggiornare lo stato con intent + slot.
    """
    user_input = state.get("input_text", "")
    user_id = state.get("user_id", "demo")

    if not user_input:
        return {**state, "error": "input_vuoto"}

    logger.info(f"🔎 [gemma_node] Analisi Gemma per user={user_id}, input={user_input}")

    result = gemma_predict(user_input)

    # Aggiorna lo stato con i campi di Gemma
    new_state = dict(state)
    new_state["intent"] = result.get("intent", "unknown")
    new_state["tickers"] = result.get("tickers") or []
    new_state["horizon"] = result.get("horizon")
    new_state["budget"] = result.get("budget")
    new_state["gemma_raw"] = result.get("raw_output")
    new_state["gemma_error"] = result.get("error")

    logger.info(f"✅ [gemma_node] Output: {new_state}")

    return new_state
