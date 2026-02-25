"""
Finance Routes - Conditional endpoints for ORTHODOXY_DOMAIN=finance.

These routes are registered only when finance vertical is enabled.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api_orthodoxy_wardens.adapters.bus_adapter import OrthodoxyBusAdapter
from api_orthodoxy_wardens.adapters.finance_adapter import get_finance_adapter

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class FinanceValidationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8192)
    code: str = Field(default="", max_length=16384)
    trigger_type: Optional[str] = None
    scope: Optional[str] = None
    source: Optional[str] = None


def _get_runtime() -> tuple[Any, OrthodoxyBusAdapter, Dict[str, Any]]:
    """Create finance-aware runtime components for a request."""
    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        raise HTTPException(
            status_code=404,
            detail="Finance vertical not enabled. Set ORTHODOXY_DOMAIN=finance",
        )

    ruleset = finance_adapter.build_ruleset()
    bus_adapter = OrthodoxyBusAdapter(ruleset=ruleset)
    stats = finance_adapter.get_rules_stats()
    return finance_adapter, bus_adapter, stats


@router.get("/config")
async def finance_config():
    """Get active finance configuration and ruleset stats."""
    finance_adapter, _, stats = _get_runtime()
    cfg = finance_adapter.config
    defaults = finance_adapter.build_event(text="")

    return {
        "status": "success",
        "vertical": "finance",
        "domain": cfg.domain_name,
        "ruleset_version": stats["ruleset_version"],
        "ruleset_checksum": stats["ruleset_checksum"],
        "active_rules": stats["active_rules"],
        "total_rules": stats["total_rules"],
        "strict_mode": cfg.strict_mode,
        "confidence_floor": cfg.confidence_floor,
        "event_defaults": {
            "trigger_type": defaults["trigger_type"],
            "scope": defaults["scope"],
            "source": defaults["source"],
        },
    }


@router.get("/rules/stats")
async def finance_rules_stats():
    """Get rule distribution by category/severity."""
    _, _, stats = _get_runtime()
    return {
        "status": "success",
        "vertical": "finance",
        **stats,
    }


@router.post("/validate")
async def finance_validate(request: FinanceValidationRequest):
    """Quick finance validation (confession + inquisitor + verdict)."""
    finance_adapter, bus_adapter, stats = _get_runtime()
    event = finance_adapter.build_event(
        text=request.text,
        code=request.code,
        trigger_type=request.trigger_type,
        scope=request.scope,
        source=request.source,
    )
    result = bus_adapter.handle_quick_validation(event)

    return {
        "status": "success",
        "mode": "quick_validation",
        "vertical": "finance",
        "result": result,
        "ruleset_version": stats["ruleset_version"],
        "ruleset_checksum": stats["ruleset_checksum"],
    }


@router.post("/audit")
async def finance_audit(request: FinanceValidationRequest):
    """Full finance audit (includes correction plan + chronicle decision)."""
    finance_adapter, bus_adapter, stats = _get_runtime()
    event = finance_adapter.build_event(
        text=request.text,
        code=request.code,
        trigger_type=request.trigger_type,
        scope=request.scope,
        source=request.source,
    )
    result = bus_adapter.handle_event(event)

    return {
        "status": "success",
        "mode": "full_audit",
        "vertical": "finance",
        "result": result,
        "ruleset_version": stats["ruleset_version"],
        "ruleset_checksum": stats["ruleset_checksum"],
    }
