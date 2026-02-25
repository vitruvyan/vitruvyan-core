"""
Finance Routes - Conditional endpoints for MEMORY_DOMAIN=finance.

These routes are registered only when finance vertical is enabled.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api_memory_orders.adapters.finance_adapter import get_finance_adapter
from api_memory_orders.models.schemas import (
    CoherenceResponse,
    ReconciliationExecutionResponse,
    ReconciliationResponse,
    SyncResponse,
)

from . import routes as base_routes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class FinanceSourceRequest(BaseModel):
    table: Optional[str] = Field(default=None, description="Optional PostgreSQL source table override")
    collection: Optional[str] = Field(default=None, description="Optional Qdrant source collection override")
    auto_resolve_sources: bool = Field(
        default=True,
        description="If true, probe PostgreSQL/Qdrant and pick first existing source",
    )


class FinanceCoherenceRequest(FinanceSourceRequest):
    embedded_column: str = Field(default="embedded", description="Embedded status column")


class FinanceSyncRequest(FinanceSourceRequest):
    mode: str = Field(default="incremental", description="Sync mode: incremental | full")
    limit: int = Field(default=1000, ge=1, le=100000)


class FinanceReconciliationRequest(FinanceSourceRequest):
    limit: int = Field(default=1000, ge=1, le=100000)
    execute: bool = False
    idempotency_key: Optional[str] = None
    allow_mass_delete: bool = False


def _require_runtime() -> tuple[Any, Any]:
    """Validate that finance adapter and base bus adapter are initialized."""
    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        raise HTTPException(
            status_code=404,
            detail="Finance vertical not enabled. Set MEMORY_DOMAIN=finance",
        )

    bus_adapter = base_routes.bus_adapter
    if bus_adapter is None:
        raise HTTPException(status_code=503, detail="Bus adapter not initialized")

    return finance_adapter, bus_adapter


def _resolve_sources(finance_adapter: Any, persistence: Any, request: FinanceSourceRequest) -> dict[str, Any]:
    """Resolve source table/collection using finance adapter policy."""
    return finance_adapter.resolve_sources(
        persistence=persistence,
        table=request.table,
        collection=request.collection,
        probe_backends=request.auto_resolve_sources,
    )


@router.get("/config")
async def finance_config():
    """Get active finance memory configuration."""
    finance_adapter, _ = _require_runtime()
    cfg = finance_adapter.finance_config

    return {
        "status": "success",
        "vertical": "finance",
        "memory_domain": "finance",
        "primary_table": cfg.primary_table,
        "primary_collection": cfg.primary_collection,
        "legacy_table": cfg.legacy_table,
        "legacy_collection": cfg.legacy_collection,
        "thresholds": finance_adapter.get_thresholds(),
    }


@router.post("/sources/resolve")
async def finance_resolve_sources(request: FinanceSourceRequest):
    """Resolve effective finance source table/collection."""
    finance_adapter, bus_adapter = _require_runtime()
    resolved = _resolve_sources(finance_adapter, bus_adapter.persistence, request)
    return {
        "status": "success",
        "vertical": "finance",
        "source_resolution": resolved,
    }


@router.post("/coherence")
async def finance_coherence(request: FinanceCoherenceRequest):
    """Run finance coherence check with auto source resolution."""
    finance_adapter, bus_adapter = _require_runtime()
    resolved = _resolve_sources(finance_adapter, bus_adapter.persistence, request)

    report = await bus_adapter.handle_coherence_check(
        table=resolved["table"],
        collection=resolved["collection"],
        embedded_column=request.embedded_column,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "source_resolution": resolved,
        "coherence": CoherenceResponse.from_domain(report).model_dump(),
    }


@router.post("/sync")
async def finance_sync(request: FinanceSyncRequest):
    """Run finance sync planning with resolved sources."""
    finance_adapter, bus_adapter = _require_runtime()
    resolved = _resolve_sources(finance_adapter, bus_adapter.persistence, request)

    plan = await bus_adapter.handle_sync_request(
        mode=request.mode,
        table=resolved["table"],
        collection=resolved["collection"],
        limit=request.limit,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "source_resolution": resolved,
        "sync_plan": SyncResponse.from_domain(plan).model_dump(),
    }


@router.post("/reconcile")
async def finance_reconcile(request: FinanceReconciliationRequest):
    """Run finance reconciliation with resolved sources."""
    finance_adapter, bus_adapter = _require_runtime()
    resolved = _resolve_sources(finance_adapter, bus_adapter.persistence, request)

    result = await bus_adapter.handle_reconciliation(
        table=resolved["table"],
        collection=resolved["collection"],
        limit=request.limit,
        execute=request.execute,
        idempotency_key=request.idempotency_key,
        allow_mass_delete=request.allow_mass_delete,
    )

    execution = result.get("execution")
    execution_model = None
    if isinstance(execution, dict):
        execution_model = ReconciliationExecutionResponse(**execution)

    reconciliation = ReconciliationResponse(
        status=result["status"],
        severity=result["severity"],
        drift_types=result["drift_types"],
        operations_count=result["operations_count"],
        requires_execution=result["requires_execution"],
        execution=execution_model,
        recommendation=result["recommendation"],
        correlation_id=result["correlation_id"],
        idempotent_replay=bool(result.get("idempotent_replay", False)),
    )

    return {
        "status": "success",
        "vertical": "finance",
        "source_resolution": resolved,
        "reconciliation": reconciliation.model_dump(),
    }
