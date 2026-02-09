"""
Orthodoxy Wardens — Event Definitions

Event type constants and the OrthodoxyEvent envelope for all events
flowing through the Cognitive Bus that concern the tribunal.

These are TYPE DEFINITIONS only — no I/O, no bus, no Redis.
The service layer uses these constants for channel names and event routing.

Sacred Order: Truth & Governance
Layer: Foundational (events)
"""

from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Event Type Constants — dot notation per Cognitive Bus convention
# Format: <sacred_order>.<domain>.<action>
# =============================================================================

# Confession lifecycle
CONFESSION_RECEIVED = "orthodoxy.confession.received"
CONFESSION_ACCEPTED = "orthodoxy.confession.accepted"
CONFESSION_REJECTED = "orthodoxy.confession.rejected"

# Examination (audit process)
EXAMINATION_STARTED = "orthodoxy.examination.started"
EXAMINATION_COMPLETED = "orthodoxy.examination.completed"

# Findings
FINDING_RECORDED = "orthodoxy.finding.recorded"
HERESY_DETECTED = "orthodoxy.heresy.detected"
ANOMALY_DETECTED = "orthodoxy.anomaly.detected"

# Verdicts
VERDICT_RENDERED = "orthodoxy.verdict.rendered"
VERDICT_BLESSED = "orthodoxy.verdict.blessed"
VERDICT_HERETICAL = "orthodoxy.verdict.heretical"
VERDICT_NON_LIQUET = "orthodoxy.verdict.non_liquet"

# Purification (correction requests — sent OUT, not executed by Orthodoxy)
PURIFICATION_REQUESTED = "orthodoxy.purification.requested"
PURIFICATION_REPORTED = "orthodoxy.purification.reported"

# Surveillance (periodic checks)
SURVEILLANCE_CYCLE_STARTED = "orthodoxy.surveillance.started"
SURVEILLANCE_CYCLE_COMPLETED = "orthodoxy.surveillance.completed"

# Archival (sent to Vault Keepers)
ARCHIVE_REQUESTED = "orthodoxy.archive.requested"


# =============================================================================
# Channel Groups — for consumer group subscriptions
# =============================================================================

# Channels this order PUBLISHES to
PUBLISH_CHANNELS = (
    VERDICT_RENDERED,
    HERESY_DETECTED,
    PURIFICATION_REQUESTED,
    ARCHIVE_REQUESTED,
)

# Channels this order CONSUMES from (external events)
CONSUME_CHANNELS = (
    "codex.discovery.mapped",           # New data discovered
    "neural_engine.screen.completed",   # Screening results ready
    "langgraph.output.ready",           # LLM output awaiting validation
    "synaptic.conclave.broadcast",      # System-wide announcements
    "conclave.mcp.actions",             # MCP tool executions
)


# =============================================================================
# OrthodoxyEvent — the event envelope
# =============================================================================

@dataclass(frozen=True)
class OrthodoxyEvent:
    """
    Immutable event envelope for all Orthodoxy Wardens events.

    This is the foundational event type. The Cognitive Bus transports it
    as an opaque payload (TransportEvent wraps it).

    Attributes:
        event_type: One of the constants defined above
        payload: Event-specific data (frozen tuple of (key, value) pairs)
        timestamp: ISO 8601 event creation time
        source: Who produced the event (e.g., "inquisitor", "confessor")
        correlation_id: Links events in a causal chain
        causation_id: Direct parent event that caused this one
    """

    event_type: str
    payload: tuple  # Frozen: tuple of (key, value) pairs
    timestamp: str
    source: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize for transport over the Cognitive Bus."""
        return {
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OrthodoxyEvent":
        """Deserialize from Cognitive Bus transport."""
        payload = data.get("payload", {})
        if isinstance(payload, dict):
            payload = tuple(payload.items())
        return cls(
            event_type=data["event_type"],
            payload=payload,
            timestamp=data["timestamp"],
            source=data.get("source", "unknown"),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
        )
