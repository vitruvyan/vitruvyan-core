"""
Enterprise-specific routes for MCP Enterprise Server.

/v1/enterprise/config — Enterprise MCP configuration
/v1/enterprise/tools — Enterprise-oriented tool schemas
/v1/enterprise/normalize — Normalize enterprise tool request to canonical MCP shape
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from adapters.enterprise_adapter import get_enterprise_adapter

router = APIRouter(prefix="/v1/enterprise", tags=["enterprise"])


class NormalizeRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: Dict[str, Any] = Field(default_factory=dict)


@router.get("/config")
async def enterprise_config():
    """Return active enterprise MCP configuration."""
    adapter = get_enterprise_adapter()
    cfg = adapter.config
    return {
        "status": "success",
        "vertical": "enterprise",
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
        "entity_field_aliases": cfg.entity_field_aliases,
        "signal_source_candidates": adapter.get_signal_source_candidates(),
    }


@router.get("/tools")
async def enterprise_tools():
    """Return enterprise-oriented tool schemas."""
    adapter = get_enterprise_adapter()
    schemas = adapter.get_tool_schemas()
    return {
        "status": "success",
        "vertical": "enterprise",
        "tools": schemas,
        "total_tools": len(schemas),
    }


@router.post("/normalize")
async def enterprise_normalize(payload: NormalizeRequest):
    """Normalize enterprise tool request into canonical MCP executor request."""
    adapter = get_enterprise_adapter()
    resolved_tool = adapter.resolve_tool_name(payload.tool)
    normalized_args = adapter.normalize_args(payload.tool, payload.args)
    return {
        "status": "success",
        "vertical": "enterprise",
        "requested_tool": payload.tool,
        "resolved_tool": resolved_tool,
        "normalized_args": normalized_args,
    }
