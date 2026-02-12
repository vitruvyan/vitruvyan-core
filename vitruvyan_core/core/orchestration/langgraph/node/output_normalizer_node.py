# core/langgraph/node/output_normalizer_node.py

from typing import Dict, Any
from core.orchestration.langgraph.shared.state_preserv import preserve_ux_state  # 🎭 UX state preservation


@preserve_ux_state
def output_normalizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes outputs from diverse execution routes into a consistent `result` structure.
    Ensures compose_node always receives a uniform result dict regardless of upstream route.
    """
    route = state.get("route", "")
    result: Dict[str, Any] = {}

    # Route: Neural Engine execution
    if route == "ne" and "raw_output" in state:
        result = {
            "route": "ne",
            "summary": "Neural Engine results",
            "raw_output": state["raw_output"],
        }

    # Route: Secondary engine fallback
    elif route == "crew_fallback" and "raw_output" in state:
        result = {
            "route": "crew_fallback",
            "summary": "Fallback engine results",
            "raw_output": state["raw_output"],
        }

    # Route: Batch scoring / screening
    elif route == "screener" and "raw_output" in state:
        result = {
            "route": "screener",
            "summary": "Batch scoring results",
            "raw_output": state["raw_output"],
        }

    # Route: Qdrant semantic fallback
    elif route == "semantic_fallback" and "result" in state:
        result = {
            "route": "semantic_fallback",
            "summary": state["result"].get("summary", "Semantic fallback"),
            "hits": state["result"].get("hits", []),
        }

    # Route: Soft LLM response
    elif route == "llm_soft" and "result" in state:
        result = {
            "route": "llm_soft",
            "summary": state["result"].get("response_text", ""),
            "raw_output": state["result"],
        }

    # Route: Validation error
    elif route == "validation_error":
        result = {
            "route": "validation_error",
            "summary": "Validation failed",
            "raw_output": state.get("validation", {}),
        }

    # Route: Generic fallback
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
