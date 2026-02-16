"""
Memory Orders — Pydantic Schemas

Request/response models for HTTP API.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — models)
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# ========================================
#  Coherence Schemas
# ========================================

class CoherenceRequest(BaseModel):
    """Request for coherence check."""
    table: str = Field(default="entities", description="PostgreSQL table name")
    collection: Optional[str] = Field(default=None, description="Qdrant collection name")
    embedded_column: str = Field(default="embedded", description="Embedded status column")


class CoherenceResponse(BaseModel):
    """Response from coherence check."""
    status: str = Field(..., description="Coherence status: healthy | warning | critical")
    drift_percentage: float = Field(..., description="Drift percentage")
    recommendation: str = Field(..., description="Action recommendation")
    pg_count: int = Field(..., description="PostgreSQL record count")
    qdrant_count: int = Field(..., description="Qdrant point count")
    drift_absolute: int = Field(..., description="Absolute drift")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    table: str = Field(..., description="Source table")
    collection: str = Field(..., description="Source collection")
    
    @classmethod
    def from_domain(cls, report: Any) -> "CoherenceResponse":
        """Convert domain CoherenceReport to Pydantic response."""
        return cls(
            status=report.status,
            drift_percentage=report.drift_percentage,
            recommendation=report.recommendation,
            pg_count=report.pg_count,
            qdrant_count=report.qdrant_count,
            drift_absolute=report.drift_absolute,
            timestamp=report.timestamp,
            table=report.table,
            collection=report.collection,
        )


# ========================================
#  Health Schemas
# ========================================

class ComponentHealthResponse(BaseModel):
    """Single component health status."""
    component: str
    status: str
    metrics: Dict[str, Any]
    error: Optional[str] = None
    response_time_ms: Optional[float] = None


class SystemHealthResponse(BaseModel):
    """Overall system health."""
    status: str = Field(..., description="Overall status: healthy | degraded | critical")
    components: Dict[str, ComponentHealthResponse]
    summary: Dict[str, Any]
    timestamp: str
    
    @classmethod
    def from_domain(cls, health: Any) -> "SystemHealthResponse":
        """Convert domain SystemHealth to Pydantic response."""
        components_dict = {}
        for comp in health.components:
            components_dict[comp.component] = ComponentHealthResponse(
                component=comp.component,
                status=comp.status,
                metrics=dict(comp.metrics),
                error=comp.error,
                response_time_ms=comp.response_time_ms,
            )
        
        return cls(
            status=health.overall_status,
            components=components_dict,
            summary=dict(health.summary),
            timestamp=health.timestamp,
        )


# ========================================
#  Sync Schemas
# ========================================

class SyncRequest(BaseModel):
    """Request for synchronization."""
    mode: str = Field(default="incremental", description="Sync mode: incremental | full")
    table: str = Field(default="entities", description="PostgreSQL table")
    collection: Optional[str] = Field(default=None, description="Qdrant collection")
    limit: int = Field(default=1000, description="Max records to process")


class SyncOperationResponse(BaseModel):
    """Single sync operation."""
    operation_type: str
    target: str
    payload: Dict[str, Any]
    entity_id: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from sync planning."""
    operations: List[SyncOperationResponse]
    estimated_duration_s: float
    mode: str
    total_operations: int
    
    @classmethod
    def from_domain(cls, plan: Any) -> "SyncResponse":
        """Convert domain SyncPlan to Pydantic response."""
        operations_list = []
        for op in plan.operations:
            operations_list.append(SyncOperationResponse(
                operation_type=op.operation_type,
                target=op.target,
                payload=dict(op.payload),
                entity_id=op.entity_id,
            ))
        
        return cls(
            operations=operations_list,
            estimated_duration_s=plan.estimated_duration_s,
            mode=plan.mode,
            total_operations=plan.total_operations,
        )


# ========================================
#  Reconciliation Schemas
# ========================================

class ReconciliationRequest(BaseModel):
    """Request for dual-memory reconciliation planning/execution."""
    table: str = Field(default="entities", description="Canonical PostgreSQL table")
    collection: Optional[str] = Field(default=None, description="Derived Qdrant collection")
    limit: int = Field(default=1000, description="Max records per snapshot")
    execute: bool = Field(default=False, description="Execute operations if mode allows")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for safe retries")
    allow_mass_delete: bool = Field(default=False, description="Allow delete-heavy execution")


class ReconciliationExecutionResponse(BaseModel):
    """Execution summary for reconciliation operations."""
    attempted: int
    applied: int
    skipped: int
    failed: int
    mode: str
    dead_lettered: int = 0


class ReconciliationResponse(BaseModel):
    """Response for reconciliation planning/execution."""
    status: str
    severity: str
    drift_types: List[str]
    operations_count: int
    requires_execution: bool
    execution: Optional[ReconciliationExecutionResponse] = None
    recommendation: str
    correlation_id: str
    idempotent_replay: bool = False


# ========================================
#  Generic Responses
# ========================================

class HealthCheckResponse(BaseModel):
    """Simple health check response."""
    status: str
    service: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    timestamp: str
