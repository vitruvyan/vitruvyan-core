# services/api_mcp/tools/__init__.py
"""MCP tool executors."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from adapters.finance_adapter import get_finance_adapter

from .compare import execute_compare_entities
from .screen import execute_screen_entities
from .semantic import execute_extract_semantic_context
from .sentiment import execute_query_sentiment
from .vee import execute_generate_vee_summary

_BASE_EXECUTORS = {
    "screen_entities": execute_screen_entities,
    "generate_vee_summary": execute_generate_vee_summary,
    "query_signals": execute_query_sentiment,
    "compare_entities": execute_compare_entities,
    "extract_semantic_context": execute_extract_semantic_context,
}


def get_tool_executors():
    """Return executor mapping, optionally enriched with finance aliases."""
    executors = dict(_BASE_EXECUTORS)
    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        return executors

    # Finance aliases from Vitruvyan MCP contracts.
    executors["screen_tickers"] = execute_screen_entities
    executors["compare_tickers"] = execute_compare_entities
    executors["query_sentiment"] = execute_query_sentiment
    return executors


def normalize_tool_request(tool_name: str, args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Normalize tool name/args using finance adapter when enabled."""
    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        return (tool_name or "").strip(), dict(args or {})

    resolved = finance_adapter.resolve_tool_name(tool_name or "")
    normalized_args = finance_adapter.normalize_args(tool_name or "", dict(args or {}))
    return resolved, normalized_args


# Backward-compatible export used by existing imports.
TOOL_EXECUTORS = get_tool_executors()

__all__ = [
    "TOOL_EXECUTORS",
    "get_tool_executors",
    "normalize_tool_request",
    "execute_screen_entities",
    "execute_generate_vee_summary",
    "execute_query_sentiment",
    "execute_compare_entities",
    "execute_extract_semantic_context",
]

