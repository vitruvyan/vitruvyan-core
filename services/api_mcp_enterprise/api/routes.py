"""
Core MCP routes — proxied through MCP Enterprise Server.

These endpoints delegate to the core MCP server (port 8020) for actual
execution, while exposing enterprise tool schemas + normalization.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

from config import get_config
from adapters.enterprise_adapter import get_enterprise_adapter

logger = logging.getLogger(__name__)

router = APIRouter()


class ExecuteRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "mcp_enterprise_server",
        "version": "1.0.0",
        "domain": "enterprise",
        "description": "Enterprise MCP Bridge (ERP tool schemas + core MCP proxy)",
        "endpoints": {
            "tools": "/tools",
            "execute": "/execute",
            "health": "/health",
            "enterprise_config": "/v1/enterprise/config",
            "enterprise_tools": "/v1/enterprise/tools",
            "enterprise_normalize": "/v1/enterprise/normalize",
        },
    }


@router.get("/health")
async def health():
    """Health check — includes core MCP connectivity."""
    cfg = get_config()
    core_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{cfg.core_mcp_url}/health")
            core_status = "connected" if resp.status_code == 200 else "error"
    except Exception:
        core_status = "disconnected"

    return {
        "status": "healthy",
        "service": "mcp_enterprise_server",
        "domain": "enterprise",
        "core_mcp": core_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/tools")
async def get_tools():
    """Return merged tool schemas (generic + enterprise)."""
    adapter = get_enterprise_adapter()
    # Get generic schemas from core MCP
    cfg = get_config()
    generic_schemas = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{cfg.core_mcp_url}/tools")
            if resp.status_code == 200:
                data = resp.json()
                generic_schemas = data.get("tools", [])
    except Exception as exc:
        logger.warning("Could not fetch core MCP tools: %s", exc)

    # Add enterprise-specific schemas
    enterprise_schemas = adapter.get_tool_schemas()
    # Merge (avoid duplicates by name)
    names = {t["function"]["name"] for t in generic_schemas}
    for schema in enterprise_schemas:
        if schema["function"]["name"] not in names:
            generic_schemas.append(schema)

    return {
        "status": "success",
        "domain": "enterprise",
        "tools": generic_schemas,
        "total_tools": len(generic_schemas),
    }


@router.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """Execute tool — normalize enterprise args, then delegate to core MCP."""
    adapter = get_enterprise_adapter()
    cfg = get_config()

    resolved_tool = adapter.resolve_tool_name(request.tool)
    normalized_args = adapter.normalize_args(request.tool, request.args)

    logger.info(
        "MCP Enterprise Execute: requested=%s resolved=%s user=%s",
        request.tool, resolved_tool, request.user_id,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{cfg.core_mcp_url}/execute",
                json={
                    "tool": resolved_tool,
                    "args": normalized_args,
                    "user_id": request.user_id,
                },
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            return resp.json()
    except httpx.HTTPError as exc:
        logger.error("Core MCP call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Core MCP unreachable: {exc}")
