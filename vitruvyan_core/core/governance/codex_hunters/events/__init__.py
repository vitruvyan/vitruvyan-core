"""
Codex Hunters - Event Channels
==============================

Event channel constants and event envelope definitions.
Domain-agnostic - channel prefixes are configurable.

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Default channel prefix (can be overridden via config)
DEFAULT_PREFIX = "codex"


class Channels:
    """
    Event channel name constants.
    
    Usage:
        from ..events import Channels
        channel = Channels.discovery(prefix="codex.finance")
    """
    
    # Discovery events
    DISCOVERY_REQUESTED = "discovery.requested"
    DISCOVERY_STARTED = "discovery.started"
    DISCOVERY_COMPLETED = "discovery.completed"
    DISCOVERY_FAILED = "discovery.failed"
    
    # Entity events
    ENTITY_DISCOVERED = "entity.discovered"
    ENTITY_RESTORED = "entity.restored"
    ENTITY_BOUND = "entity.bound"
    ENTITY_VERIFIED = "entity.verified"
    ENTITY_INVALID = "entity.invalid"
    
    # Expedition events
    EXPEDITION_REQUESTED = "expedition.requested"
    EXPEDITION_STARTED = "expedition.started"
    EXPEDITION_PROGRESS = "expedition.progress"
    EXPEDITION_COMPLETED = "expedition.completed"
    EXPEDITION_FAILED = "expedition.failed"
    
    # Health events
    HEALTH_CHECK = "health.check"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"
    
    @classmethod
    def with_prefix(cls, channel: str, prefix: str = DEFAULT_PREFIX) -> str:
        """Build full channel name with prefix."""
        return f"{prefix}.{channel}"
    
    @classmethod
    def discovery(cls, prefix: str = DEFAULT_PREFIX) -> str:
        return cls.with_prefix(cls.DISCOVERY_COMPLETED, prefix)
    
    @classmethod
    def entity_discovered(cls, prefix: str = DEFAULT_PREFIX) -> str:
        return cls.with_prefix(cls.ENTITY_DISCOVERED, prefix)
    
    @classmethod
    def entity_bound(cls, prefix: str = DEFAULT_PREFIX) -> str:
        return cls.with_prefix(cls.ENTITY_BOUND, prefix)
    
    @classmethod
    def expedition_completed(cls, prefix: str = DEFAULT_PREFIX) -> str:
        return cls.with_prefix(cls.EXPEDITION_COMPLETED, prefix)


@dataclass(frozen=True)
class EventEnvelope:
    """
    Standard event envelope for Codex Hunters events.
    
    Used for serialization/deserialization at LIVELLO 2.
    LIVELLO 1 consumers work with domain objects, not envelopes.
    """
    event_type: str
    source: str
    timestamp: str  # ISO format string
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    target: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "target": self.target,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventEnvelope':
        """Create from dictionary."""
        return cls(
            event_type=data["event_type"],
            source=data["source"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            target=data.get("target"),
            version=data.get("version", "1.0"),
        )


def create_event_envelope(
    event_type: str,
    source: str,
    payload: Dict[str, Any],
    correlation_id: str = None,
    target: str = None,
) -> EventEnvelope:
    """Factory function to create event envelopes."""
    return EventEnvelope(
        event_type=event_type,
        source=source,
        timestamp=datetime.utcnow().isoformat(),
        payload=payload,
        correlation_id=correlation_id,
        target=target,
    )
