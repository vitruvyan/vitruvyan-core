"""
Memory Orders — HTTP Routes

Thin REST API endpoints. Validate → delegate → return.
ALL business logic in adapters/consumers.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — api)
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api_memory_orders.models.schemas import (
    CoherenceRequest,
    CoherenceResponse,
    SystemHealthResponse,
    SyncRequest,
    SyncResponse,
    HealthCheckResponse,
    ReconciliationRequest,
    ReconciliationResponse,
    ReconciliationExecutionResponse,
)
from api_memory_orders.adapters.bus_adapter import MemoryBusAdapter
from api_memory_orders.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()

# Global bus adapter (initialized in main.py startup)
bus_adapter: MemoryBusAdapter = None


def set_bus_adapter(adapter: MemoryBusAdapter):
    """Set global bus adapter instance."""
    global bus_adapter
    bus_adapter = adapter


# ========================================
#  Health Endpoints
# ========================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Simple health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/health/rag", response_model=SystemHealthResponse)
async def rag_health():
    """
    Comprehensive RAG system health check.
    
    Checks:
    - PostgreSQL (Archivarium)
    - Qdrant (Mnemosyne)
    - Redis (Cognitive Bus)
    - Embedding API
    - Babel Gardens
    
    Returns:
        SystemHealthResponse with overall status and component details
    """
    if bus_adapter is None:
        raise HTTPException(status_code=503, detail="Bus adapter not initialized")
    
    try:
        health = await bus_adapter.handle_health_check()
        response = SystemHealthResponse.from_domain(health)
        
        # Map overall status to HTTP status code
        status_code = 200
        if response.status in ["degraded", "critical"]:
            status_code = 503
        
        return JSONResponse(content=response.dict(), status_code=status_code)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ========================================
#  Coherence Endpoints
# ========================================

@router.post("/coherence", response_model=CoherenceResponse)
async def check_coherence(request: CoherenceRequest):
    """
    Check coherence between PostgreSQL and Qdrant.
    
    Args:
        request: CoherenceRequest with table/collection names
    
    Returns:
        CoherenceResponse with drift analysis
    """
    if bus_adapter is None:
        raise HTTPException(status_code=503, detail="Bus adapter not initialized")
    
    try:
        report = await bus_adapter.handle_coherence_check(
            table=request.table,
            collection=request.collection,
            embedded_column=request.embedded_column
        )
        return CoherenceResponse.from_domain(report)
    
    except Exception as e:
        logger.error(f"Coherence check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Coherence check failed: {str(e)}")


# ========================================
#  Sync Endpoints
# ========================================

@router.post("/sync", response_model=SyncResponse)
async def request_sync(request: SyncRequest):
    """
    Plan synchronization operations.
    
    Args:
        request: SyncRequest with mode, table, collection
    
    Returns:
        SyncResponse with operations to execute
    
    Note:
        This endpoint only PLANS sync operations.
        Execution is delegated to a separate worker/service.
    """
    if bus_adapter is None:
        raise HTTPException(status_code=503, detail="Bus adapter not initialized")
    
    try:
        plan = await bus_adapter.handle_sync_request(
            mode=request.mode,
            table=request.table,
            collection=request.collection,
            limit=request.limit
        )
        return SyncResponse.from_domain(plan)
    
    except Exception as e:
        logger.error(f"Sync planning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync planning failed: {str(e)}")


# ========================================
#  Root Endpoint
# ========================================

@router.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Memory Orders",
        "version": "2.0.0",
        "architecture": "LIVELLO 1 (Pure Domain) + LIVELLO 2 (Service)",
        "components": {
            "archivarium": "PostgreSQL (relational memory)",
            "mnemosyne": "Qdrant (semantic memory)"
        },
        "endpoints": {
            "health": "/health",
            "rag_health": "/health/rag",
            "coherence": "POST /coherence",
            "sync": "POST /sync",
            "reconcile": "POST /reconcile",
        }
    }


@router.post("/reconcile", response_model=ReconciliationResponse)
async def reconcile(request: ReconciliationRequest):
    """
    Build and optionally execute reconciliation plan with enforcement mode.
    """
    if bus_adapter is None:
        raise HTTPException(status_code=503, detail="Bus adapter not initialized")

    try:
        result = await bus_adapter.handle_reconciliation(
            table=request.table,
            collection=request.collection,
            limit=request.limit,
            execute=request.execute,
            idempotency_key=request.idempotency_key,
            allow_mass_delete=request.allow_mass_delete,
        )
        execution = result.get("execution")
        execution_model = None
        if isinstance(execution, dict):
            execution_model = ReconciliationExecutionResponse(**execution)

        return ReconciliationResponse(
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
    except RuntimeError as e:
        logger.warning(f"Reconciliation concurrency blocked: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Reconciliation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")
