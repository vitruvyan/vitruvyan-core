"""Memory Orders — Events Package

Event definitions and channel constants for dual-memory coherence system.
"""

from .memory_events import (
    # Channel constants
    MEMORY_COHERENCE_REQUESTED,
    MEMORY_COHERENCE_CHECKED,
    MEMORY_HEALTH_REQUESTED,
    MEMORY_HEALTH_CHECKED,
    MEMORY_SYNC_REQUESTED,
    MEMORY_SYNC_COMPLETED,
    MEMORY_SYNC_FAILED,
    MEMORY_AUDIT_RECORDED,
    # Event envelope
    MemoryEvent,
)

__all__ = [
    # Coherence
    "MEMORY_COHERENCE_REQUESTED",
    "MEMORY_COHERENCE_CHECKED",
    # Health
    "MEMORY_HEALTH_REQUESTED",
    "MEMORY_HEALTH_CHECKED",
    # Sync
    "MEMORY_SYNC_REQUESTED",
    "MEMORY_SYNC_COMPLETED",
    "MEMORY_SYNC_FAILED",
    # Audit
    "MEMORY_AUDIT_RECORDED",
    # Envelope
    "MemoryEvent",
]
