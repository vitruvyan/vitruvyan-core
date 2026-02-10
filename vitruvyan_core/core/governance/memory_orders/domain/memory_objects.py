"""
Memory Orders — Domain Objects

Immutable data structures for dual-memory system coherence.
All objects are frozen dataclasses. No I/O. Pure Python.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — domain)
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CoherenceInput:
    """
    Input for coherence analysis between PostgreSQL (Archivarium) and Qdrant (Mnemosyne).
    
    Attributes:
        pg_count: Number of records in PostgreSQL with embedded=true
        qdrant_count: Number of points in Qdrant collection
        thresholds: Drift thresholds as immutable tuple (('healthy', 5.0), ('warning', 15.0))
        table: PostgreSQL table name (for audit trail)
        collection: Qdrant collection name (for audit trail)
    """
    pg_count: int
    qdrant_count: int
    thresholds: tuple[tuple[str, float], ...]
    table: str = "entities"
    collection: str = "entities_embeddings"
    
    def __post_init__(self):
        if self.pg_count < 0:
            raise ValueError(f"pg_count must be >= 0, got {self.pg_count}")
        if self.qdrant_count < 0:
            raise ValueError(f"qdrant_count must be >= 0, got {self.qdrant_count}")
        if not self.thresholds:
            raise ValueError("thresholds cannot be empty")


@dataclass(frozen=True)
class CoherenceReport:
    """
    Result of coherence analysis.
    
    Status levels:
    - 'healthy': drift < healthy_threshold (default: 5%)
    - 'warning': drift >= healthy_threshold AND < warning_threshold (default: 5-15%)
    - 'critical': drift >= warning_threshold (default: > 15%)
    
    Attributes:
        status: Overall coherence status ('healthy' | 'warning' | 'critical')
        drift_percentage: Absolute drift as percentage
        recommendation: Human-readable action recommendation
        pg_count: PostgreSQL record count (for audit)
        qdrant_count: Qdrant point count (for audit)
        drift_absolute: Absolute difference |pg_count - qdrant_count|
        timestamp: ISO8601 timestamp when analysis was performed
        table: Source table (for audit trail)
        collection: Source collection (for audit trail)
    """
    status: str
    drift_percentage: float
    recommendation: str
    pg_count: int
    qdrant_count: int
    drift_absolute: int
    timestamp: str
    table: str = "entities"
    collection: str = "entities_embeddings"
    
    VALID_STATUSES = frozenset(["healthy", "warning", "critical"])
    
    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")
        if self.drift_percentage < 0:
            raise ValueError(f"drift_percentage must be >= 0, got {self.drift_percentage}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API responses / event payloads."""
        return {
            "status": self.status,
            "drift_percentage": self.drift_percentage,
            "recommendation": self.recommendation,
            "pg_count": self.pg_count,
            "qdrant_count": self.qdrant_count,
            "drift_absolute": self.drift_absolute,
            "timestamp": self.timestamp,
            "table": self.table,
            "collection": self.collection
        }


@dataclass(frozen=True)
class ComponentHealth:
    """
    Health status of a single RAG component.
    
    Components: postgresql, qdrant, embedding_api, babel_gardens, redis
    
    Attributes:
        component: Component identifier
        status: Health status ('healthy' | 'degraded | 'unhealthy')
        metrics: Component-specific metrics as immutable tuple
        error: Error message if status is not healthy (None otherwise)
        response_time_ms: Response time in milliseconds (optional)
    """
    component: str
    status: str
    metrics: tuple[tuple[str, Any], ...]
    error: str | None = None
    response_time_ms: float | None = None
    
    VALID_STATUSES = frozenset(["healthy", "degraded", "unhealthy"])
    
    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")


@dataclass(frozen=True)
class SystemHealth:
    """
    Aggregated health status for entire RAG system.
    
    Overall status determination:
    - 'healthy': all components healthy
    - 'degraded': at least one component degraded, none unhealthy
    - 'critical': at least one component unhealthy
    
    Attributes:
        overall_status: System-wide health status
        components: Tuple of ComponentHealth objects
        summary: High-level metrics (drift_percentage, sync_lag, total_points, coherence_status)
        timestamp: ISO8601 timestamp when health check was performed
    """
    overall_status: str
    components: tuple[ComponentHealth, ...]
    summary: tuple[tuple[str, Any], ...]
    timestamp: str
    
    VALID_STATUSES = frozenset(["healthy", "degraded", "critical"])
    
    def __post_init__(self):
        if self.overall_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.overall_status}. Must be one of {self.VALID_STATUSES}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API responses / event payloads."""
        return {
            "status": self.overall_status,
            "components": {c.component: {
                "status": c.status,
                "metrics": dict(c.metrics),
                "error": c.error,
                "response_time_ms": c.response_time_ms
            } for c in self.components},
            "summary": dict(self.summary),
            "timestamp": self.timestamp
        }


@dataclass(frozen=True)
class SyncInput:
    """
    Input for synchronization planning between Archivarium and Mnemosyne.
    
    Attributes:
        pg_data: Data from PostgreSQL as immutable tuple
        qdrant_data: Data from Qdrant as immutable tuple
        mode: Sync mode ('incremental' | 'full')
        source_table: Source PostgreSQL table
        target_collection: Target Qdrant collection
    """
    pg_data: tuple[Any, ...]
    qdrant_data: tuple[Any, ...]
    mode: str
    source_table: str = "entities"
    target_collection: str = "entities_embeddings"
    
    VALID_MODES = frozenset(["incremental", "full"])
    
    def __post_init__(self):
        if self.mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {self.mode}. Must be one of {self.VALID_MODES}")


@dataclass(frozen=True)
class SyncOperation:
    """
    Single synchronization operation to be executed.
    
    Attributes:
        operation_type: Type of operation ('insert' | 'update' | 'delete')
        target: Target system ('archivarium' | 'mnemosyne')
        payload: Operation-specific data as immutable tuple
        entity_id: ID of affected entity (for audit trail)
    """
    operation_type: str
    target: str
    payload: tuple[tuple[str, Any], ...]
    entity_id: str | None = None
    
    VALID_OPERATIONS = frozenset(["insert", "update", "delete"])
    VALID_TARGETS = frozenset(["archivarium", "mnemosyne"])
    
    def __post_init__(self):
        if self.operation_type not in self.VALID_OPERATIONS:
            raise ValueError(f"Invalid operation_type: {self.operation_type}")
        if self.target not in self.VALID_TARGETS:
            raise ValueError(f"Invalid target: {self.target}")


@dataclass(frozen=True)
class SyncPlan:
    """
    Complete synchronization plan with multiple operations.
    
    Attributes:
        operations: Tuple of SyncOperation objects to execute
        estimated_duration_s: Estimated execution time in seconds
        mode: Sync mode that generated this plan
        total_operations: Total number of operations in plan
    """
    operations: tuple[SyncOperation, ...]
    estimated_duration_s: float
    mode: str
    
    @property
    def total_operations(self) -> int:
        """Total number of operations in plan."""
        return len(self.operations)
    
    def __post_init__(self):
        if self.estimated_duration_s < 0:
            raise ValueError(f"estimated_duration_s must be >= 0, got {self.estimated_duration_s}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API responses / event payloads."""
        return {
            "operations": [
                {
                    "operation_type": op.operation_type,
                    "target": op.target,
                    "payload": dict(op.payload),
                    "entity_id": op.entity_id
                }
                for op in self.operations
            ],
            "estimated_duration_s": self.estimated_duration_s,
            "mode": self.mode,
            "total_operations": self.total_operations
        }
