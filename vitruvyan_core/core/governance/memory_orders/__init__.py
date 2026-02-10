"""
Memory Orders — Dual-Memory Coherence System

Sacred Order responsible for epistemic integrity between
Archivarium (PostgreSQL) and Mnemosyne (Qdrant).

Refactoring Status: FASE 1 complete (LIVELLO 1 structure)

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1)
"""

# Domain objects
from .domain import (
    CoherenceInput,
    CoherenceReport,
    ComponentHealth,
    SystemHealth,
    SyncInput,
    SyncOperation,
    SyncPlan,
)

# Consumers
from .consumers import (
    MemoryRole,
    CoherenceAnalyzer,
    HealthAggregator,
    SyncPlanner,
)

# Governance
from .governance import (
    CoherenceThresholds,
    DEFAULT_THRESHOLDS,
    STRICT_THRESHOLDS,
    RELAXED_THRESHOLDS,
    aggregate_component_statuses,
    calculate_health_score,
)

# Events
from .events import (
    MEMORY_COHERENCE_REQUESTED,
    MEMORY_COHERENCE_CHECKED,
    MEMORY_HEALTH_REQUESTED,
    MEMORY_HEALTH_CHECKED,
    MEMORY_SYNC_REQUESTED,
    MEMORY_SYNC_COMPLETED,
    MEMORY_SYNC_FAILED,
    MEMORY_AUDIT_RECORDED,
    MemoryEvent,
)

# Monitoring
from .monitoring import (
    COHERENCE_DRIFT_PCT,
    COHERENCE_STATUS,
    HEALTH_STATUS,
    HEALTH_SCORE,
    ARCHIVARIUM_CONNECTED,
    MNEMOSYNE_CONNECTED,
    REDIS_CONNECTED,
    SYNC_OPERATIONS_TOTAL,
    AUDIT_RECORDS_TOTAL,
)

__version__ = "2.0.0"  # LIVELLO 1 refactoring complete

__all__ = [
    # Domain
    "CoherenceInput",
    "CoherenceReport",
    "ComponentHealth",
    "SystemHealth",
    "SyncInput",
    "SyncOperation",
    "SyncPlan",
    # Consumers
    "MemoryRole",
    "CoherenceAnalyzer",
    "HealthAggregator",
    "SyncPlanner",
    # Governance
    "CoherenceThresholds",
    "DEFAULT_THRESHOLDS",
    "STRICT_THRESHOLDS",
    "RELAXED_THRESHOLDS",
    "aggregate_component_statuses",
    "calculate_health_score",
    # Events
    "MEMORY_COHERENCE_REQUESTED",
    "MEMORY_COHERENCE_CHECKED",
    "MEMORY_HEALTH_REQUESTED",
    "MEMORY_HEALTH_CHECKED",
    "MEMORY_SYNC_REQUESTED",
    "MEMORY_SYNC_COMPLETED",
    "MEMORY_SYNC_FAILED",
    "MEMORY_AUDIT_RECORDED",
    "MemoryEvent",
    # Monitoring
    "COHERENCE_DRIFT_PCT",
    "COHERENCE_STATUS",
    "HEALTH_STATUS",
    "HEALTH_SCORE",
    "ARCHIVARIUM_CONNECTED",
    "MNEMOSYNE_CONNECTED",
    "REDIS_CONNECTED",
    "SYNC_OPERATIONS_TOTAL",
    "AUDIT_RECORDS_TOTAL",
]
