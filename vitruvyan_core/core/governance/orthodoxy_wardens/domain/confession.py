"""
Orthodoxy Wardens — Confession Domain Object

A Confession represents an audit request entering the tribunal.
It captures WHO initiated the audit, WHAT scope it covers, and HOW urgent it is.
A Confession is immutable after creation — it is evidence, not a mutable state.

Sacred Order: Truth & Governance
Layer: Foundational (domain)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Confession:
    """
    Immutable record of an audit request.

    A Confession enters the tribunal and triggers the judgment pipeline:
    Confession → Findings → Verdict.

    Attributes:
        confession_id: Unique identifier (format: "confession_YYYYMMDD_HHMMSS")
        trigger_type: What initiated this audit
            - "code_commit": Git push detected
            - "scheduled": Periodic surveillance (every N minutes)
            - "manual": Human-initiated via API
            - "output_validation": Pre-delivery check on LLM output
            - "event": Triggered by Cognitive Bus event
        scope: What is being audited
            - "complete_realm": Full system audit
            - "single_service": One microservice
            - "single_output": One LLM response
            - "single_event": One bus event
        urgency: How fast the verdict is needed
            - "critical": Blocking — caller waits for verdict
            - "high": Near-realtime — verdict within seconds
            - "routine": Background — verdict within minutes
            - "low": Informational — no SLA
        source: Who/what initiated (e.g., "langgraph.orthodoxy_node", "api.manual")
        timestamp: ISO 8601 creation time
        correlation_id: Links this confession to a Cognitive Bus event chain
        metadata: Additional context (non-structural, varies by trigger_type)
    """

    confession_id: str
    trigger_type: str
    scope: str
    urgency: str
    source: str
    timestamp: str
    correlation_id: Optional[str] = None
    metadata: tuple = ()  # Frozen: tuple of (key, value) pairs, not dict

    def __post_init__(self):
        _valid_triggers = {"code_commit", "scheduled", "manual", "output_validation", "event"}
        _valid_scopes = {"complete_realm", "single_service", "single_output", "single_event"}
        _valid_urgencies = {"critical", "high", "routine", "low"}

        if self.trigger_type not in _valid_triggers:
            raise ValueError(
                f"Invalid trigger_type '{self.trigger_type}'. "
                f"Must be one of: {_valid_triggers}"
            )
        if self.scope not in _valid_scopes:
            raise ValueError(
                f"Invalid scope '{self.scope}'. "
                f"Must be one of: {_valid_scopes}"
            )
        if self.urgency not in _valid_urgencies:
            raise ValueError(
                f"Invalid urgency '{self.urgency}'. "
                f"Must be one of: {_valid_urgencies}"
            )
