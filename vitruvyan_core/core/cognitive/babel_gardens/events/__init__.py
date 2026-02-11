"""
Babel Gardens - Event Definitions
=================================

Channel names and event envelope for StreamBus communication.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


class Channels:
    """Redis Streams channel names for Babel Gardens."""
    
    # Embedding channels
    EMBEDDING_REQUEST = "babel.embedding.request"
    EMBEDDING_RESPONSE = "babel.embedding.response"
    
    # Sentiment channels
    SENTIMENT_REQUEST = "babel.sentiment.request"
    SENTIMENT_RESPONSE = "babel.sentiment.response"
    
    # Emotion channels
    EMOTION_REQUEST = "babel.emotion.request"
    EMOTION_RESPONSE = "babel.emotion.response"
    
    # Synthesis channels
    SYNTHESIS_REQUEST = "babel.synthesis.request"
    SYNTHESIS_RESPONSE = "babel.synthesis.response"
    
    # Topic channels
    TOPIC_REQUEST = "babel.topic.request"
    TOPIC_RESPONSE = "babel.topic.response"
    
    # Error channel
    ERROR = "babel.error"


@dataclass
class EventEnvelope:
    """Wrapper for events on the bus."""
    
    event_type: str
    payload: Dict[str, Any]
    source: str = "babel_gardens"
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for bus emission."""
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        """Create from dictionary."""
        return cls(
            event_type=data.get("event_type", "unknown"),
            payload=data.get("payload", {}),
            source=data.get("source", "unknown"),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
        )


__all__ = ["Channels", "EventEnvelope"]
