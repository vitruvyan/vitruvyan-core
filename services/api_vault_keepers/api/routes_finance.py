"""
Finance Routes - Conditional endpoints for VAULT_DOMAIN=finance.

These routes are registered only when finance vertical is enabled.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api_vault_keepers.adapters.finance_adapter import get_finance_adapter

from .routes import get_adapter

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class FinanceIntegrityRequest(BaseModel):
    scope: Optional[str] = Field(
        default=None,
        description="Integrity scope: full | postgresql | qdrant (optional override)",
    )
    correlation_id: Optional[str] = None


class FinanceBackupRequest(BaseModel):
    mode: Optional[str] = Field(default=None, description="Backup mode: full | incremental")
    include_vectors: Optional[bool] = None
    correlation_id: Optional[str] = None


class FinanceArchiveRequest(BaseModel):
    content: Dict[str, Any] = Field(default_factory=dict)
    content_type: Optional[str] = None
    source_order: Optional[str] = None
    correlation_id: Optional[str] = None


class FinanceSignalArchiveRequest(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=256)
    signal_results: list[Dict[str, Any]] = Field(default_factory=list)
    schema_version: str = Field(default="2.1")
    retention_days: Optional[int] = Field(default=None, ge=1, le=36500)
    correlation_id: Optional[str] = None


def _runtime() -> tuple[Any, Any]:
    finance_adapter = get_finance_adapter()
    if finance_adapter is None:
        raise HTTPException(
            status_code=404,
            detail="Finance vertical not enabled. Set VAULT_DOMAIN=finance",
        )
    return finance_adapter, get_adapter()


@router.get("/config")
async def finance_config():
    """Get active finance vault configuration."""
    finance_adapter, _ = _runtime()
    return {
        "status": "success",
        "vertical": "finance",
        **finance_adapter.get_runtime_config(),
    }


@router.post("/integrity")
async def finance_integrity(request: FinanceIntegrityRequest):
    """Run integrity check with finance defaults."""
    finance_adapter, adapter = _runtime()
    cfg = finance_adapter.get_runtime_config()
    scope = request.scope or cfg["default_integrity_scope"]

    result = adapter.handle_integrity_check(
        scope=scope,
        correlation_id=request.correlation_id,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "integrity": result,
    }


@router.post("/backup")
async def finance_backup(request: FinanceBackupRequest):
    """Run finance backup using resolved defaults."""
    finance_adapter, adapter = _runtime()
    params = finance_adapter.resolve_backup_params(
        mode=request.mode,
        include_vectors=request.include_vectors,
    )
    result = adapter.handle_backup(
        mode=params["mode"],
        include_vectors=params["include_vectors"],
        correlation_id=request.correlation_id,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "resolved_params": params,
        "backup": result,
    }


@router.post("/archive")
async def finance_archive(request: FinanceArchiveRequest):
    """Archive payload with finance metadata normalization."""
    finance_adapter, adapter = _runtime()
    resolved = finance_adapter.resolve_archive_request(
        content_type=request.content_type,
        source_order=request.source_order,
        channel=request.content_type,
    )
    result = adapter.handle_archive(
        content=request.content,
        content_type=resolved["content_type"],
        source_order=resolved["source_order"],
        correlation_id=request.correlation_id,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "resolved_archive": resolved,
        "archive": result,
    }


@router.post("/signal-timeseries/archive")
async def finance_archive_signal_timeseries(request: FinanceSignalArchiveRequest):
    """Archive finance signal timeseries from Babel outputs."""
    finance_adapter, adapter = _runtime()
    retention_days = finance_adapter.resolve_signal_retention_days(request.retention_days)
    result = adapter.handle_signal_timeseries_archival(
        entity_id=request.entity_id,
        signal_results=request.signal_results,
        vertical="finance",
        schema_version=request.schema_version,
        retention_days=retention_days,
        correlation_id=request.correlation_id,
    )
    return {
        "status": "success",
        "vertical": "finance",
        "resolved_retention_days": retention_days,
        "timeseries_archive": result,
    }
