"""
Vault Keepers — API Routes

HTTP endpoints for vault operations.
Routes are THIN: validate → delegate to adapter → return response.

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api_vault_keepers.models.schemas import (
    IntegrityCheckRequest,
    BackupRequest,
    RestoreRequest,
    IntegrityStatus,
    BackupResult,
    VaultStatus,
    HealthCheck,
)
from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter

logger = logging.getLogger("VaultKeepers.Routes")

# Router instance
router = APIRouter(prefix="/vault", tags=["vault"])

# Global adapter instance (set by main.py on startup)
_bus_adapter: Optional[VaultBusAdapter] = None


def set_bus_adapter(adapter: VaultBusAdapter) -> None:
    """Set the bus adapter instance (called by main.py)"""
    global _bus_adapter
    _bus_adapter = adapter


def get_adapter() -> VaultBusAdapter:
    """Get the bus adapter instance (raises if not initialized)"""
    if _bus_adapter is None:
        raise HTTPException(status_code=503, detail="Vault Keepers not initialized")
    return _bus_adapter


# ═══════════════════════════════════════════════════════════════════════════
# Health & Status Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint.
    
    Returns overall service health including database connectivity.
    """
    try:
        adapter = get_adapter()
        health = adapter.persistence.health_check()
        
        overall_healthy = health["pg_healthy"] and health["qdrant_healthy"]
        
        return HealthCheck(
            status="healthy" if overall_healthy else "degraded",
            vault_status="blessed" if overall_healthy else "requires_attention",
            synaptic_conclave="connected" if adapter.bus else "disconnected",
            postgresql="sacred" if health["pg_healthy"] else "corrupted",
            qdrant="blessed" if health["qdrant_healthy"] else "cursed",
            sacred_timestamp=__import__('datetime').datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/status", response_model=VaultStatus)
async def vault_status():
    """
    Get comprehensive vault status.
    
    Returns detailed status including integrity validation and audit summary.
    """
    try:
        adapter = get_adapter()
        status = adapter.get_vault_status()
        return VaultStatus(**status)
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Vault Operations
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/integrity_check", response_model=IntegrityStatus)
async def integrity_check(request: IntegrityCheckRequest):
    """
    Manual integrity check.
    
    Validates PostgreSQL, Qdrant, and cross-system coherence.
    """
    try:
        adapter = get_adapter()
        result = adapter.handle_integrity_check(request.dict())
        return IntegrityStatus(**result)
    except Exception as e:
        logger.error(f"Integrity check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup", response_model=BackupResult)
async def backup(request: BackupRequest):
    """
    Manual backup creation.
    
    Creates snapshot of PostgreSQL and optionally Qdrant.
    """
    try:
        adapter = get_adapter()
        result = adapter.handle_backup(
            mode=request.mode,
            include_vectors=request.include_vectors,
            correlation_id=request.correlation_id
        )
        return BackupResult(**result)
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore(request: RestoreRequest):
    """
    Data restoration.
    
    Restores data from a snapshot. Use dry_run=true for testing.
    """
    try:
        adapter = get_adapter()
        result = adapter.handle_restore(
            snapshot_id=request.snapshot_id,
            dry_run=request.dry_run
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive")
async def archive(payload: dict):
    """
    Archive content from other orders.
    
    Receives audit results, screening results, or other content for archival.
    """
    try:
        adapter = get_adapter()
        result = adapter.handle_archive(payload)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Archive failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
