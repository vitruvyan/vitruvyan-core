"""
Codex Hunters API Routes
========================

Thin HTTP endpoints that validate inputs, delegate to adapters, and return responses.
All business logic is in LIVELLO 1 consumers or adapters.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response

from ..adapters import get_bus_adapter, get_persistence
from ..models import (
    ExpeditionRunRequest,
    ExpeditionStatusResponse,
    SystemHealthResponse,
    StatsResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    RestoreRequest,
    RestoreResponse,
    BindRequest,
    BindResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Expedition Tracking (in-memory for now, could be moved to persistence)
# ============================================================================

class ExpeditionTracker:
    """Simple in-memory expedition tracker."""
    
    def __init__(self):
        self.expeditions: Dict[str, Dict[str, Any]] = {}
        self.counter = 0
    
    def create(self, expedition_type: str, params: Dict[str, Any]) -> str:
        """Create new expedition entry."""
        self.counter += 1
        exp_id = f"exp_{expedition_type}_{self.counter}_{int(datetime.utcnow().timestamp())}"
        self.expeditions[exp_id] = {
            "expedition_id": exp_id,
            "expedition_type": expedition_type,
            "status": "queued",
            "progress": 0.0,
            "started_at": None,
            "completed_at": None,
            "agents_deployed": [],
            "results": None,
            "error_message": None,
            "parameters": params,
        }
        return exp_id
    
    def update(self, exp_id: str, updates: Dict[str, Any]) -> None:
        """Update expedition status."""
        if exp_id in self.expeditions:
            self.expeditions[exp_id].update(updates)
    
    def get(self, exp_id: str) -> Dict[str, Any] | None:
        """Get expedition by ID."""
        return self.expeditions.get(exp_id)
    
    def get_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get expeditions from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = []
        for exp in self.expeditions.values():
            started = exp.get("started_at")
            if started:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace("Z", "+00:00"))
                if started >= cutoff:
                    recent.append(exp)
        return sorted(recent, key=lambda x: x.get("started_at", ""), reverse=True)


# Singleton tracker
_tracker = ExpeditionTracker()


# ============================================================================
# Health & Metrics
# ============================================================================

@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """System health check endpoint."""
    persistence = get_persistence()
    bus_adapter = get_bus_adapter()
    
    db_ok = persistence.check_database_health()
    qdrant_ok = persistence.check_qdrant_health()
    bus_ok = bus_adapter.check_bus_health()
    consumers_status = bus_adapter.get_consumers_status()
    
    # Calculate overall status
    all_ok = db_ok and bus_ok
    degraded = db_ok or bus_ok
    status = "healthy" if all_ok else ("degraded" if degraded else "unhealthy")
    
    active_count = sum(1 for e in _tracker.expeditions.values() if e["status"] == "running")
    completed_count = len(_tracker.get_recent(hours=24))
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "agents_status": consumers_status,
        "redis_connected": bus_ok,
        "database_connected": db_ok,
        "qdrant_connected": qdrant_ok,
        "active_expeditions": active_count,
        "completed_expeditions_24h": completed_count,
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get system statistics."""
    completed = sum(1 for e in _tracker.expeditions.values() if e["status"] == "completed")
    failed = sum(1 for e in _tracker.expeditions.values() if e["status"] == "failed")
    
    return StatsResponse(
        total_discoveries=0,  # Would come from persistence
        total_restored=0,
        total_bound=0,
        expeditions_completed=completed,
        expeditions_failed=failed,
        uptime_seconds=0.0,  # Would track from startup
    )


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Prometheus metrics endpoint."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        raise HTTPException(status_code=501, detail="Prometheus client not available")


# ============================================================================
# Expedition Endpoints
# ============================================================================

@router.post("/expedition/run", response_model=Dict[str, Any])
async def run_expedition(request: ExpeditionRunRequest) -> Dict[str, Any]:
    """Trigger a new expedition."""
    exp_id = _tracker.create(request.expedition_type, request.parameters or {})
    
    # Update to running state
    _tracker.update(exp_id, {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "progress": 0.1,
    })
    
    logger.info(f"🚀 Starting expedition: {exp_id}")
    
    # For now, return immediately (expeditions would run in background)
    return {
        "expedition_id": exp_id,
        "status": "running",
        "message": f"Expedition {request.expedition_type} started",
    }


@router.get("/expedition/status/{expedition_id}", response_model=ExpeditionStatusResponse)
async def get_expedition_status(expedition_id: str) -> ExpeditionStatusResponse:
    """Get expedition status by ID."""
    exp = _tracker.get(expedition_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    return ExpeditionStatusResponse(
        expedition_id=exp["expedition_id"],
        status=exp["status"],
        progress=exp["progress"],
        started_at=exp.get("started_at"),
        completed_at=exp.get("completed_at"),
        agents_deployed=exp.get("agents_deployed", []),
        results=exp.get("results"),
        error_message=exp.get("error_message"),
    )


@router.get("/expedition/history", response_model=List[Dict[str, Any]])
async def get_expedition_history(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent expedition history."""
    return _tracker.get_recent(hours=hours)


# ============================================================================
# Discovery Pipeline Endpoints
# ============================================================================

@router.post("/discover", response_model=DiscoveryResponse)
async def discover_entity(request: DiscoveryRequest) -> DiscoveryResponse:
    """Discover and track an entity."""
    bus_adapter = get_bus_adapter()
    
    result = bus_adapter.process_discovery(
        entity_id=request.entity_id,
        source_type=request.source_type,
        raw_data=request.raw_data or {},
        metadata=request.metadata,
    )
    
    return DiscoveryResponse(
        success=result["success"],
        entity_id=result["entity_id"],
        status="discovered" if result["success"] else "invalid",
        message=result.get("message", ""),
        discovered_at=datetime.utcnow(),
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_entity(request: RestoreRequest) -> RestoreResponse:
    """Restore and normalize entity data."""
    bus_adapter = get_bus_adapter()
    
    result = bus_adapter.process_restore(
        entity_id=request.entity_id,
        raw_data=request.raw_data,
        source_type=request.source_type,
    )
    
    return RestoreResponse(
        success=result["success"],
        entity_id=result["entity_id"],
        quality_score=result.get("quality_score", 0.0),
        normalized_fields=list(result.get("normalized_data", {}).keys()),
        warnings=result.get("warnings", []),
    )


@router.post("/bind", response_model=BindResponse)
async def bind_entity(request: BindRequest) -> BindResponse:
    """Bind entity to persistent storage."""
    bus_adapter = get_bus_adapter()
    
    result = bus_adapter.process_bind(
        entity_id=request.entity_id,
        normalized_data=request.normalized_data,
        embedding=request.embedding,
    )
    
    return BindResponse(
        success=result["success"],
        entity_id=result["entity_id"],
        postgres_stored=result.get("postgres_stored", False),
        qdrant_stored=result.get("qdrant_stored", False),
        bound_at=datetime.utcnow(),
    )
