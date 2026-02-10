"""
Pattern Weavers - Event Constants
=================================

Event channel definitions and envelope structures.
Pure Python - no I/O.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


class Channels:
    """
    Event channel constants for Pattern Weavers.
    
    All channels use dot notation: <domain>.<entity>.<action>
    Channel names are configurable via PatternConfig.
    """
    
    # Core channels
    WEAVE_REQUEST = "pattern.weave.request"
    WEAVE_RESPONSE = "pattern.weave.response"
    WEAVE_ERROR = "pattern.weave.error"
    
    # Taxonomy channels
    TAXONOMY_UPDATED = "pattern.taxonomy.updated"
    TAXONOMY_REFRESH = "pattern.taxonomy.refresh"
    
    # Health channels
    HEALTH_CHECK = "pattern.health.check"
    HEALTH_STATUS = "pattern.health.status"


@dataclass
class EventEnvelope:
    """
    Standard event envelope for Pattern Weavers events.
    
    Wraps payload with standard metadata for StreamBus.
    """
    
    event_type: str
    channel: str
    payload: Dict[str, Any]
    emitter: str = "pattern_weavers"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    version: str = "2.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for StreamBus."""
        return {
            "event_type": self.event_type,
            "channel": self.channel,
            "payload": self.payload,
            "emitter": self.emitter,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "version": self.version,
        }


def create_event_envelope(
    event_type: str,
    channel: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> EventEnvelope:
    """Factory function to create event envelopes."""
    return EventEnvelope(
        event_type=event_type,
        channel=channel,
        payload=payload,
        correlation_id=correlation_id,
    )
