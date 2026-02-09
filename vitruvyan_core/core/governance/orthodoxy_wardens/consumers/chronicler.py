"""
Orthodoxy Wardens — Chronicler (Sacred Role)

The Chronicler is the LOG STRATEGIST of the tribunal.
It receives a Verdict and decides HOW to log and archive it.
It does NOT persist anything — that's the service layer's job.

Input:  Verdict
Output: ChronicleDecision (what to log, where, with what retention)

Extracted from: chronicler_agent.py (log evaluation, severity mapping)

Sacred Order: Truth & Governance
Layer: Foundational (consumers)
"""

from typing import Any, Tuple

from .base import SacredRole
from ..domain.verdict import Verdict
from ..domain.log_decision import LogDecision


# =============================================================================
# Chronicle Domain Objects — frozen, pure data
# =============================================================================


class ArchiveDirective:
    """
    Frozen directive for archival: where to send the verdict record.

    This is a DECLARATION, not an execution.
    The service layer reads these directives and routes accordingly.
    """

    __slots__ = ("_destination", "_retention_days", "_priority", "_reason")

    VALID_DESTINATIONS = frozenset({
        "postgresql",       # Structured storage (audit_findings)
        "qdrant",           # Vector embedding for semantic retrieval
        "blockchain",       # Immutable anchoring (Tron ledger)
        "cognitive_bus",    # Event broadcast via Redis Streams
    })

    def __init__(
        self,
        destination: str,
        retention_days: int,
        priority: str,
        reason: str,
    ):
        if destination not in self.VALID_DESTINATIONS:
            raise ValueError(
                f"Invalid destination '{destination}'. "
                f"Valid: {sorted(self.VALID_DESTINATIONS)}"
            )
        object.__setattr__(self, "_destination", destination)
        object.__setattr__(self, "_retention_days", retention_days)
        object.__setattr__(self, "_priority", priority)
        object.__setattr__(self, "_reason", reason)

    def __setattr__(self, name, value):
        raise AttributeError("ArchiveDirective is frozen")

    @property
    def destination(self) -> str:
        return self._destination

    @property
    def retention_days(self) -> int:
        return self._retention_days

    @property
    def priority(self) -> str:
        return self._priority

    @property
    def reason(self) -> str:
        return self._reason

    def __repr__(self) -> str:
        return (
            f"ArchiveDirective(dest='{self._destination}', "
            f"retention={self._retention_days}d, priority='{self._priority}')"
        )


class ChronicleDecision:
    """
    Frozen meta-decision: what to log, where, and for how long.

    Wraps a LogDecision (should we log?) with ArchiveDirectives (where?).
    """

    __slots__ = ("_log_decision", "_directives", "_verdict_status", "_confession_id")

    def __init__(
        self,
        log_decision: LogDecision,
        directives: Tuple[ArchiveDirective, ...],
        verdict_status: str,
        confession_id: str,
    ):
        object.__setattr__(self, "_log_decision", log_decision)
        object.__setattr__(self, "_directives", directives)
        object.__setattr__(self, "_verdict_status", verdict_status)
        object.__setattr__(self, "_confession_id", confession_id)

    def __setattr__(self, name, value):
        raise AttributeError("ChronicleDecision is frozen")

    @property
    def log_decision(self) -> LogDecision:
        return self._log_decision

    @property
    def directives(self) -> Tuple[ArchiveDirective, ...]:
        return self._directives

    @property
    def verdict_status(self) -> str:
        return self._verdict_status

    @property
    def confession_id(self) -> str:
        return self._confession_id

    @property
    def should_log(self) -> bool:
        return self._log_decision.should_log

    @property
    def should_archive(self) -> bool:
        return len(self._directives) > 0

    @property
    def destinations(self) -> Tuple[str, ...]:
        return tuple(d.destination for d in self._directives)

    @property
    def requires_blockchain(self) -> bool:
        return "blockchain" in self.destinations

    def __repr__(self) -> str:
        return (
            f"ChronicleDecision(log={self.should_log}, "
            f"archives={len(self._directives)}, "
            f"verdict='{self._verdict_status}')"
        )


# =============================================================================
# Archival Strategy — maps verdict status to archive destinations
# =============================================================================

def _build_directives(verdict: Verdict) -> Tuple[ArchiveDirective, ...]:
    """
    Determine archive destinations based on verdict status.

    Heretical → all 4 destinations (full audit trail + blockchain)
    Purified  → PostgreSQL + Qdrant + Cognitive Bus (no blockchain)
    Blessed   → PostgreSQL only (minimal footprint)
    Non-liquet → PostgreSQL + Qdrant (needs future retrieval)
    """
    status = verdict.status
    directives = []

    if status == "heretical":
        directives = [
            ArchiveDirective(
                destination="postgresql",
                retention_days=365,
                priority="critical",
                reason="Heretical verdict requires permanent audit record",
            ),
            ArchiveDirective(
                destination="qdrant",
                retention_days=365,
                priority="critical",
                reason="Heretical verdict embedded for semantic retrieval",
            ),
            ArchiveDirective(
                destination="blockchain",
                retention_days=-1,  # Permanent
                priority="critical",
                reason="Heretical verdict anchored for immutable proof",
            ),
            ArchiveDirective(
                destination="cognitive_bus",
                retention_days=0,  # Immediate broadcast
                priority="critical",
                reason="Heretical verdict broadcast to all Sacred Orders",
            ),
        ]

    elif status == "purified":
        directives = [
            ArchiveDirective(
                destination="postgresql",
                retention_days=180,
                priority="high",
                reason="Purified verdict stored for compliance tracking",
            ),
            ArchiveDirective(
                destination="qdrant",
                retention_days=90,
                priority="medium",
                reason="Purified verdict embedded for pattern analysis",
            ),
            ArchiveDirective(
                destination="cognitive_bus",
                retention_days=0,
                priority="medium",
                reason="Purified verdict broadcast for awareness",
            ),
        ]

    elif status == "blessed":
        directives = [
            ArchiveDirective(
                destination="postgresql",
                retention_days=30,
                priority="low",
                reason="Blessed verdict stored for audit completeness",
            ),
        ]

    elif status == "non_liquet":
        directives = [
            ArchiveDirective(
                destination="postgresql",
                retention_days=180,
                priority="high",
                reason="Non-liquet verdict requires follow-up investigation",
            ),
            ArchiveDirective(
                destination="qdrant",
                retention_days=180,
                priority="high",
                reason="Non-liquet embedded for future resolution matching",
            ),
        ]

    elif status == "clarification_needed":
        directives = [
            ArchiveDirective(
                destination="postgresql",
                retention_days=90,
                priority="medium",
                reason="Clarification request stored for follow-up",
            ),
        ]

    return tuple(directives)


# =============================================================================
# Chronicler Consumer
# =============================================================================


class Chronicler(SacredRole):
    """
    Log strategist — decides WHAT to log, WHERE, and for HOW LONG.

    Given a Verdict, the Chronicler produces a ChronicleDecision that
    specifies logging strategy and archive destinations. It never
    touches a database, file system, or network.

    Archive Strategy:
    - heretical: ALL destinations (PostgreSQL + Qdrant + Blockchain + Bus)
    - purified:  PostgreSQL + Qdrant + Bus
    - blessed:   PostgreSQL only (minimal)
    - non_liquet: PostgreSQL + Qdrant (needs future retrieval)

    Usage:
        chronicler = Chronicler()
        if chronicler.can_handle(verdict):
            decision = chronicler.process(verdict)
            # decision.should_log → bool
            # decision.directives → archival destinations
            # decision.requires_blockchain → bool
    """

    @property
    def role_name(self) -> str:
        return "chronicler"

    @property
    def description(self) -> str:
        return "Log strategist: decides what to log, where, and retention policy"

    def can_handle(self, event: Any) -> bool:
        """Accept Verdict objects or dicts containing 'verdict'."""
        if isinstance(event, Verdict):
            return True
        if isinstance(event, dict) and "verdict" in event:
            return isinstance(event["verdict"], Verdict)
        return False

    def process(self, event: Any) -> ChronicleDecision:
        """
        Produce a ChronicleDecision from a Verdict.

        Args:
            event: Verdict or dict with 'verdict' key

        Returns:
            ChronicleDecision with logging and archival strategy
        """
        if isinstance(event, Verdict):
            verdict = event
        elif isinstance(event, dict):
            verdict = event["verdict"]
        else:
            raise ValueError(
                f"Chronicler expects Verdict or dict, got {type(event).__name__}"
            )

        return self._decide(verdict)

    def _decide(self, verdict: Verdict) -> ChronicleDecision:
        """Core decision logic — pure, deterministic."""
        from ..governance import VerdictEngine

        # Use VerdictEngine's logging decision
        engine = VerdictEngine()
        log_decision = engine.decide_logging(verdict)

        # Build archive directives based on verdict status
        directives = _build_directives(verdict)

        confession_id = getattr(verdict, "confession_id", "unknown")

        return ChronicleDecision(
            log_decision=log_decision,
            directives=directives,
            verdict_status=verdict.status,
            confession_id=confession_id,
        )
