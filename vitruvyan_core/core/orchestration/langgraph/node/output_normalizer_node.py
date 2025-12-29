# core/langgraph/node/output_normalizer_node.py

from typing import Dict, Any
from core.orchestration.langgraph.shared.state_preserv import preserve_ux_state  # 🎭 UX state preservation


@preserve_ux_state
def output_normalizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizza gli output provenienti da diversi percorsi (exec/NE, crew fallback, screener, qdrant, llm_soft).
    Obiettivo: avere sempre una chiave `result` coerente per il compose node.
    """
    route = state.get("route", "")
    result: Dict[str, Any] = {}

    # Caso 1: Exec (Neural Engine)
    if route == "ne" and "raw_output" in state:
        result = {
            "route": "ne",
            "summary": "Neural Engine results",
            "raw_output": state["raw_output"],
        }

    # Caso 2: Crew fallback
    elif route == "crew_fallback" and "raw_output" in state:
        result = {
            "route": "crew_fallback",
            "summary": "CrewAI fallback results",
            "raw_output": state["raw_output"],
        }

    # Caso 3: Screener
    elif route == "screener" and "raw_output" in state:
        result = {
            "route": "screener",
            "summary": "Screener results",
            "raw_output": state["raw_output"],
        }

    # Caso 4: Qdrant semantic fallback
    elif route == "semantic_fallback" and "result" in state:
        result = {
            "route": "semantic_fallback",
            "summary": state["result"].get("summary", "Semantic fallback"),
            "hits": state["result"].get("hits", []),
        }

    # Caso 5: Soft LLM response
    elif route == "llm_soft" and "result" in state:
        result = {
            "route": "llm_soft",
            "summary": state["result"].get("response_text", ""),
            "raw_output": state["result"],
        }

    # Caso 6: Validation error
    elif route == "validation_error":
        result = {
            "route": "validation_error",
            "summary": "Validation failed",
            "raw_output": state.get("validation", {}),
        }

    # Caso fallback generico
    else:
        result = {
            "route": route or "unknown",
            "summary": "No normalized output",
            "raw_output": state.get("raw_output", {}),
        }

    # 🔎 Merge validation se presente
    if "validation" in state:
        result["validation"] = state["validation"]

    state["result"] = result
    print(f"[output_normalizer_node] route={route} → summary={result.get('summary')}")
    return state
