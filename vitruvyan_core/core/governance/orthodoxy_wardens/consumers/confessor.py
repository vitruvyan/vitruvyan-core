"""
Orthodoxy Wardens — Confessor (Sacred Role)

The Confessor is the INTAKE OFFICER of the tribunal.
It receives raw events or requests, validates them, and produces
a structured Confession that enters the judgment pipeline.

The Confessor does NOT judge — it prepares the case for judgment.

Input:  OrthodoxyEvent or dict (raw audit request)
Output: Confession (validated, structured, frozen)

Extracted from: confessor_agent.py trigger_analysis node

Sacred Order: Truth & Governance
Layer: Foundational (consumers)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .base import SacredRole
from ..domain.confession import Confession
from ..events.orthodoxy_events import (
    OrthodoxyEvent,
    CONFESSION_RECEIVED,
    CONFESSION_ACCEPTED,
    CONFESSION_REJECTED,
)


# =============================================================================
# Trigger Type Mapping — maps event sources to confession trigger types
# =============================================================================

_EVENT_TO_TRIGGER = {
    "codex.discovery.mapped": "event",
    "neural_engine.screen.completed": "event",
    "langgraph.output.ready": "output_validation",
    "synaptic.conclave.broadcast": "event",
    "conclave.mcp.actions": "output_validation",
}

_EVENT_TO_SCOPE = {
    "codex.discovery.mapped": "single_event",
    "neural_engine.screen.completed": "single_service",
    "langgraph.output.ready": "single_output",
    "synaptic.conclave.broadcast": "complete_realm",
    "conclave.mcp.actions": "single_output",
}

_EVENT_TO_URGENCY = {
    "codex.discovery.mapped": "routine",
    "neural_engine.screen.completed": "routine",
    "langgraph.output.ready": "high",
    "synaptic.conclave.broadcast": "low",
    "conclave.mcp.actions": "high",
}


class Confessor(SacredRole):
    """
    Intake officer — transforms raw events into structured Confessions.

    The Confessor validates incoming audit requests, determines trigger type,
    scope, and urgency, then produces a frozen Confession ready for the
    Inquisitor to examine.

    Usage:
        confessor = Confessor()
        event = OrthodoxyEvent(event_type="langgraph.output.ready", ...)
        if confessor.can_handle(event):
            confession = confessor.process(event)
    """

    @property
    def role_name(self) -> str:
        return "confessor"

    @property
    def description(self) -> str:
        return "Intake officer: transforms raw events into structured Confessions"

    def can_handle(self, event: Any) -> bool:
        """
        Accept OrthodoxyEvent, dict with event_type, or dict with trigger_type.
        """
        if isinstance(event, OrthodoxyEvent):
            return True
        if isinstance(event, dict):
            return "event_type" in event or "trigger_type" in event
        return False

    def process(self, event: Any) -> Confession:
        """
        Transform an event into a validated Confession.

        Args:
            event: OrthodoxyEvent, or dict with audit request fields

        Returns:
            Frozen Confession ready for the judgment pipeline

        Raises:
            ValueError: If event is malformed or unprocessable
        """
        now = datetime.now(timezone.utc)
        confession_id = f"confession_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        if isinstance(event, OrthodoxyEvent):
            return self._from_orthodoxy_event(event, confession_id, now)
        elif isinstance(event, dict):
            return self._from_dict(event, confession_id, now)
        else:
            raise ValueError(
                f"Confessor cannot process event of type {type(event).__name__}"
            )

    def _from_orthodoxy_event(
        self, event: OrthodoxyEvent, confession_id: str, now: datetime
    ) -> Confession:
        """Build Confession from an OrthodoxyEvent."""
        trigger_type = _EVENT_TO_TRIGGER.get(event.event_type, "event")
        scope = _EVENT_TO_SCOPE.get(event.event_type, "single_event")
        urgency = _EVENT_TO_URGENCY.get(event.event_type, "routine")

        return Confession(
            confession_id=confession_id,
            trigger_type=trigger_type,
            scope=scope,
            urgency=urgency,
            source=event.source,
            timestamp=now.isoformat(),
            correlation_id=event.correlation_id,
            metadata=event.payload,
        )

    def _from_dict(
        self, data: dict, confession_id: str, now: datetime
    ) -> Confession:
        """Build Confession from a raw dict (manual/API trigger)."""
        trigger_type = data.get("trigger_type", "manual")
        scope = data.get("scope", "single_output")
        urgency = data.get("urgency", "routine")
        source = data.get("source", "api.manual")

        # Convert dict metadata to frozen tuple
        raw_meta = data.get("metadata", {})
        if isinstance(raw_meta, dict):
            metadata = tuple(raw_meta.items())
        elif isinstance(raw_meta, (list, tuple)):
            metadata = tuple(raw_meta)
        else:
            metadata = ()

        return Confession(
            confession_id=confession_id,
            trigger_type=trigger_type,
            scope=scope,
            urgency=urgency,
            source=source,
            timestamp=now.isoformat(),
            correlation_id=data.get("correlation_id"),
            metadata=metadata,
        )
