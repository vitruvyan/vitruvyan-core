"""
Orthodoxy Wardens — LogDecision Domain Object

A LogDecision is the Chronicler's output: given an event, verdict, or finding,
it decides WHETHER to log, at WHAT severity, for HOW LONG, and for WHOM.

This is a meta-decision — "I decide to remember" — and is unique among the
domain objects because it has no external-world counterpart.

Sacred Order: Truth & Governance
Layer: Foundational (domain)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LogDecision:
    """
    Immutable decision about whether and how to persist an event.

    The Chronicler consumer produces LogDecisions. The service layer
    executes them (writes to PostgreSQL, Qdrant, etc.).

    Attributes:
        should_log: Whether this event should be persisted at all
        severity: Logging severity level
            - "critical": Immediate attention required
            - "high": Important for audit trail
            - "medium": Standard operational logging
            - "low": Debug/trace level
            - "debug": Development only, not persisted in production
        retention: How long to keep the record
            - "permanent": Never delete (blockchain-anchored events)
            - "long": 1 year (compliance-relevant findings)
            - "medium": 90 days (standard audit trail)
            - "short": 30 days (operational events)
            - "ephemeral": 24 hours (debug/trace)
        audience: Who should see this log (frozen tuple)
            - "audit": Compliance/legal review
            - "governance": Sacred Order oversight
            - "operations": DevOps/SRE
            - "analytics": Data science / trend analysis
            - "security": Security team
        category: Classification of the event being logged
        reason: Why this logging decision was made (traceable to a rule or heuristic)
    """

    should_log: bool
    severity: str
    retention: str
    audience: tuple  # Frozen tuple of audience strings
    category: str
    reason: str

    _VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low", "debug"})
    _VALID_RETENTIONS = frozenset({"permanent", "long", "medium", "short", "ephemeral"})
    _VALID_AUDIENCES = frozenset({
        "audit", "governance", "operations", "analytics", "security",
    })

    def __post_init__(self):
        if self.severity not in self._VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of: {self._VALID_SEVERITIES}"
            )
        if self.retention not in self._VALID_RETENTIONS:
            raise ValueError(
                f"Invalid retention '{self.retention}'. "
                f"Must be one of: {self._VALID_RETENTIONS}"
            )
        for a in self.audience:
            if a not in self._VALID_AUDIENCES:
                raise ValueError(
                    f"Invalid audience '{a}'. "
                    f"Must be one of: {self._VALID_AUDIENCES}"
                )

    @classmethod
    def skip(cls, reason: str) -> "LogDecision":
        """Factory: event should NOT be logged."""
        return cls(
            should_log=False,
            severity="debug",
            retention="ephemeral",
            audience=(),
            category="skipped",
            reason=reason,
        )

    @classmethod
    def critical_audit(cls, category: str, reason: str) -> "LogDecision":
        """Factory: critical event for audit trail (permanent retention)."""
        return cls(
            should_log=True,
            severity="critical",
            retention="permanent",
            audience=("audit", "governance", "security"),
            category=category,
            reason=reason,
        )

    @classmethod
    def standard(cls, category: str, reason: str) -> "LogDecision":
        """Factory: standard operational event (90-day retention)."""
        return cls(
            should_log=True,
            severity="medium",
            retention="medium",
            audience=("audit", "operations"),
            category=category,
            reason=reason,
        )
