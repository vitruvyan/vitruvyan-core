"""
DSE Node — LangGraph Integration
=================================

Sacred Order: Orchestration (LangGraph pipeline)
Role: Thin HTTP adapter for Design Space Exploration (api_edge_dse)

Pipeline position:
    pattern_weavers → ... → dse_node → compose_node → END

State Contract:
    Input:
        state["weaver_context"]   — dict from pattern_weavers_node
        state["user_id"]          — str
        state["trace_id"]         — str (optional, generated if absent)

    Output:
        state["dse_artifact"]     — full artifact dict (pareto_frontier + ranking)
        state["dse_summary"]      — lightweight preview for compose_node
        state["route"]            — "dse_complete" | "error"

ZERO business logic — pure HTTP adapter.
Domain-agnostic: weaver_context structure defined by the active domain plugin.

Author: Vitruvyan Core Team
Date: Feb 26, 2026
Version: 1.0.0
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import httpx

from config.api_config import get_dse_url

logger = logging.getLogger(__name__)

# Service endpoint
DSE_RUN_FROM_CONTEXT = get_dse_url("/dse/run_from_context")
API_TIMEOUT = 15.0  # seconds — DSE compute may take a few seconds


def dse_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Design Space Exploration via api_edge_dse.

    Calls POST /dse/run_from_context (synchronous full pipeline):
      prepare (strategy + sampling) → run_dse (Pareto + ranking) → persist → events

    Args:
        state: LangGraph state dict

    Returns:
        Updated state with dse_artifact, dse_summary, route
    """
    logger.info("[DSE Node] Starting DSE workflow")

    # Extract context
    user_id = state.get("user_id", "anonymous")
    trace_id = state.get("trace_id") or str(uuid.uuid4())
    weaver_context = state.get("weaver_context") or {}

    if not weaver_context:
        logger.warning("[DSE Node] Empty weaver_context — skipping DSE")
        return _fallback(state, "empty_weaver_context")

    logger.debug(
        "[DSE Node] user_id=%s trace_id=%s weaver_context_keys=%s",
        user_id, trace_id, list(weaver_context.keys()),
    )

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            response = client.post(
                DSE_RUN_FROM_CONTEXT,
                json={
                    "weaver_context": weaver_context,
                    "user_id": user_id,
                    "trace_id": trace_id,
                    "seed": state.get("dse_seed", 42),
                    "use_case": state.get("use_case", "graph_pipeline"),
                },
            )

        if response.status_code == 422:
            logger.warning("[DSE Node] Validation error (schema mismatch)")
            return _fallback(state, "validation_error")

        if response.status_code != 200:
            logger.error("[DSE Node] API error %d", response.status_code)
            return _fallback(state, f"api_error_{response.status_code}")

        data = response.json()

        artifact = data.get("artifact", {})
        top_designs = data.get("top_designs", [])

        logger.info(
            "[DSE Node] Complete: pareto=%d/%d strategy=%s trace_id=%s",
            data.get("pareto_count", 0),
            data.get("total_design_points", 0),
            data.get("strategy", "?"),
            trace_id,
        )

        return {
            "dse_artifact": artifact,
            "dse_summary": {
                "total_design_points": data.get("total_design_points", 0),
                "pareto_count":        data.get("pareto_count", 0),
                "strategy":            data.get("strategy", "unknown"),
                "confidence":          data.get("confidence", 0.0),
                "input_hash":          data.get("input_hash", ""),
                "asof":                data.get("asof", ""),
                "top_3_designs":       top_designs,
            },
            "trace_id": trace_id,
            "route": "dse_complete",
        }

    except httpx.TimeoutException:
        logger.error("[DSE Node] Timeout calling api_edge_dse")
        return _fallback(state, "timeout")

    except httpx.ConnectError:
        logger.error("[DSE Node] Cannot connect to api_edge_dse at %s", DSE_RUN_FROM_CONTEXT)
        return _fallback(state, "service_unavailable")

    except Exception as exc:
        logger.error("[DSE Node] Unexpected error: %s", exc, exc_info=True)
        return _fallback(state, "unexpected_error")


def _fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Return error state for graceful degradation."""
    logger.warning("[DSE Node] Fallback: reason=%s", reason)
    return {
        "dse_artifact": None,
        "dse_summary": {
            "total_design_points": 0,
            "pareto_count": 0,
            "strategy": "none",
            "confidence": 0.0,
            "input_hash": "",
            "asof": datetime.utcnow().isoformat(),
            "top_3_designs": [],
            "fallback_reason": reason,
        },
        "route": "error",
        "error_message": f"DSE failed: {reason}",
        "error_type": "dse_node",
    }
