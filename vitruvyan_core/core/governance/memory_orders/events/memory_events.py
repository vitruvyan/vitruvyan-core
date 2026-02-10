"""
Memory Orders — Event Definitions

Channel constants and event envelopes for dual-memory coherence system.

Sacred Order: Memory & Coherence
Layer: Foundational (LIVELLO 1 — events)
"""

from dataclasses import dataclass
from typing import Any


# ========================================
#  Channel Constants
# ========================================

# Coherence Events
MEMORY_COHERENCE_REQUESTED = "memory.coherence.requested"
MEMORY_COHERENCE_CHECKED = "memory.coherence.checked"

# Health Events
MEMORY_HEALTH_REQUESTED = "memory.health.requested"
MEMORY_HEALTH_CHECKED = "memory.health.checked"

# Sync Events
MEMORY_SYNC_REQUESTED = "memory.sync.requested"
MEMORY_SYNC_COMPLETED = "memory.sync.completed"
MEMORY_SYNC_FAILED = "memory.sync.failed"

# Audit Events
MEMORY_AUDIT_RECORDED = "memory.audit.recorded"


# ========================================
#  Event Envelope
# ========================================

@dataclass(frozen=True)
class MemoryEvent:
    """
    Event envelope for all Memory Orders events.
    
    Attributes:
        stream: Channel name (e.g., 'memory.coherence.checked')
        payload: Event data as immutable tuple
        timestamp: ISO8601 timestamp
        correlation_id: Optional correlation ID for tracing
        source: Source service/component that emitted the event
    """
    stream: str
    payload: tuple[tuple[str, Any], ...]
    timestamp: str
    correlation_id: str | None = None
    source: str = "memory_orders"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for bus serialization."""
        return {
            "stream": self.stream,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEvent":
        """Deserialize from bus dict."""
        payload_dict = data.get("payload", {})
        payload_tuple = tuple(payload_dict.items()) if isinstance(payload_dict, dict) else ()
        
        return cls(
            stream=data["stream"],
            payload=payload_tuple,
            timestamp=data["timestamp"],
            correlation_id=data.get("correlation_id"),
            source=data.get("source", "memory_orders"),
        )
