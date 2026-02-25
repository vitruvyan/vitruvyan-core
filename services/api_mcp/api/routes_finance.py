"""
Finance routes for MCP Server (enabled when MCP_DOMAIN=finance).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from adapters.finance_adapter import get_finance_adapter
from schemas import get_tool_schemas
from tools import get_tool_executors, normalize_tool_request

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class NormalizeRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: Dict[str, Any] = Field(default_factory=dict)


def _require_finance_adapter():
    adapter = get_finance_adapter()
    if adapter is None:
        raise HTTPException(status_code=404, detail="Finance vertical not enabled. Set MCP_DOMAIN=finance")
    return adapter


@router.get("/config")
async def finance_config():
    """Return active finance MCP configuration."""
    adapter = _require_finance_adapter()
    cfg = adapter.config
    return {
        "status": "success",
        "vertical": "finance",
        "domain": cfg.domain_name,
        "default_language": cfg.default_language,
        "default_screen_profile": cfg.default_screen_profile,
        "signal_window_days": {
            "default": cfg.default_signal_window_days,
            "min": cfg.min_signal_window_days,
            "max": cfg.max_signal_window_days,
        },
        "tool_aliases": cfg.tool_aliases,
        "criteria_aliases": cfg.compare_criteria_aliases,
        "signal_source_candidates": adapter.get_signal_source_candidates(),
    }


@router.get("/tools")
async def finance_tools():
    """Return finance-oriented tools and current executor registry."""
    _require_finance_adapter()
    schemas = get_tool_schemas()
    executors = sorted(get_tool_executors().keys())
    return {
        "status": "success",
        "vertical": "finance",
        "tools": schemas,
        "executor_names": executors,
    }


@router.post("/normalize")
async def finance_normalize(payload: NormalizeRequest):
    """Normalize finance tool request into canonical MCP executor request."""
    _require_finance_adapter()
    resolved_tool, normalized_args = normalize_tool_request(payload.tool, payload.args)
    return {
        "status": "success",
        "vertical": "finance",
        "requested_tool": payload.tool,
        "resolved_tool": resolved_tool,
        "normalized_args": normalized_args,
    }

