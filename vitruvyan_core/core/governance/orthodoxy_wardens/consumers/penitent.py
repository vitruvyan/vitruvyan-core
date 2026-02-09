"""
Orthodoxy Wardens — Penitent (Sacred Role)

The Penitent is the CORRECTION ADVISOR of the tribunal.
It receives a heretical or purified Verdict and DECIDES what corrections
should be requested. It does NOT execute corrections.

"Il giudice non è mai il boia" — the judge is never the executioner.

Input:  Verdict (heretical or purified)
Output: CorrectionPlan (frozen, declarative correction requests)

Extracted from: penitent_agent.py (strategy selection, correction logic)

Sacred Order: Truth & Governance
Layer: Foundational (consumers)
"""

from typing import Any, Optional, Tuple

from .base import SacredRole
from ..domain.verdict import Verdict
from ..domain.finding import Finding


# =============================================================================
# Correction Domain Objects — frozen, pure data
# =============================================================================


class CorrectionRequest:
    """
    A single, immutable correction request.

    Describes WHAT should be corrected, not HOW.
    Execution is the service layer's responsibility.
    """

    __slots__ = (
        "_finding",
        "_strategy",
        "_priority",
        "_description",
        "_automated",
    )

    VALID_STRATEGIES = frozenset({
        "remove_pattern",       # Remove the offending pattern from text/code
        "replace_pattern",      # Replace with compliant alternative
        "add_guard",            # Add validation/guard clause
        "refactor_structure",   # Structural refactoring needed
        "escalate_human",       # Requires human review
        "suppress_output",      # Block output from reaching user
        "add_disclaimer",       # Append epistemic disclaimer
        "rerun_with_context",   # Re-execute with corrective context
    })

    VALID_PRIORITIES = frozenset({"critical", "high", "medium", "low"})

    def __init__(
        self,
        finding: Finding,
        strategy: str,
        priority: str,
        description: str,
        automated: bool = True,
    ):
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Valid: {sorted(self.VALID_STRATEGIES)}"
            )
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{priority}'. "
                f"Valid: {sorted(self.VALID_PRIORITIES)}"
            )

        object.__setattr__(self, "_finding", finding)
        object.__setattr__(self, "_strategy", strategy)
        object.__setattr__(self, "_priority", priority)
        object.__setattr__(self, "_description", description)
        object.__setattr__(self, "_automated", automated)

    def __setattr__(self, name, value):
        raise AttributeError("CorrectionRequest is frozen")

    @property
    def finding(self) -> Finding:
        return self._finding

    @property
    def strategy(self) -> str:
        return self._strategy

    @property
    def priority(self) -> str:
        return self._priority

    @property
    def description(self) -> str:
        return self._description

    @property
    def automated(self) -> bool:
        return self._automated

    def __repr__(self) -> str:
        return (
            f"CorrectionRequest(strategy='{self._strategy}', "
            f"priority='{self._priority}', automated={self._automated})"
        )


class CorrectionPlan:
    """
    Frozen collection of CorrectionRequests for a given Verdict.

    This is a PLAN, not an execution receipt. The service layer
    decides whether and how to execute each request.
    """

    __slots__ = ("_verdict_status", "_confession_id", "_requests", "_requires_human")

    def __init__(
        self,
        verdict_status: str,
        confession_id: str,
        requests: Tuple[CorrectionRequest, ...],
        requires_human: bool,
    ):
        object.__setattr__(self, "_verdict_status", verdict_status)
        object.__setattr__(self, "_confession_id", confession_id)
        object.__setattr__(self, "_requests", requests)
        object.__setattr__(self, "_requires_human", requires_human)

    def __setattr__(self, name, value):
        raise AttributeError("CorrectionPlan is frozen")

    @property
    def verdict_status(self) -> str:
        return self._verdict_status

    @property
    def confession_id(self) -> str:
        return self._confession_id

    @property
    def requests(self) -> Tuple[CorrectionRequest, ...]:
        return self._requests

    @property
    def requires_human(self) -> bool:
        return self._requires_human

    @property
    def total_requests(self) -> int:
        return len(self._requests)

    @property
    def automated_requests(self) -> Tuple[CorrectionRequest, ...]:
        return tuple(r for r in self._requests if r.automated)

    @property
    def human_requests(self) -> Tuple[CorrectionRequest, ...]:
        return tuple(r for r in self._requests if not r.automated)

    @property
    def critical_requests(self) -> Tuple[CorrectionRequest, ...]:
        return tuple(r for r in self._requests if r.priority == "critical")

    @property
    def is_empty(self) -> bool:
        return len(self._requests) == 0

    def __repr__(self) -> str:
        return (
            f"CorrectionPlan(verdict='{self._verdict_status}', "
            f"requests={self.total_requests}, "
            f"human_required={self._requires_human})"
        )


# =============================================================================
# Strategy Selection — maps findings to correction strategies
# =============================================================================

_CATEGORY_STRATEGY_MAP = {
    "security": "remove_pattern",
    "hallucination": "suppress_output",
    "compliance": "add_guard",
    "data_quality": "rerun_with_context",
    "performance": "refactor_structure",
    "quality": "refactor_structure",
    "architectural": "refactor_structure",
    "epistemic": "add_disclaimer",
}

_SEVERITY_PRIORITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
}

_HUMAN_REQUIRED_CATEGORIES = frozenset({"security", "architectural"})
_HUMAN_REQUIRED_SEVERITIES = frozenset({"critical"})


def _select_strategy(finding: Finding) -> str:
    """Select correction strategy based on finding category."""
    return _CATEGORY_STRATEGY_MAP.get(finding.category, "escalate_human")


def _select_priority(finding: Finding) -> str:
    """Map finding severity to correction priority."""
    return _SEVERITY_PRIORITY_MAP.get(finding.severity, "medium")


def _needs_human(finding: Finding) -> bool:
    """Determine if a finding requires human review."""
    if finding.severity in _HUMAN_REQUIRED_SEVERITIES:
        return True
    if finding.category in _HUMAN_REQUIRED_CATEGORIES:
        return True
    return False


def _build_description(finding: Finding, strategy: str) -> str:
    """Generate correction description from finding + strategy."""
    descriptions = {
        "remove_pattern": f"Remove {finding.category} issue: {finding.message}",
        "replace_pattern": f"Replace non-compliant pattern: {finding.message}",
        "add_guard": f"Add validation guard for: {finding.message}",
        "refactor_structure": f"Refactor to address: {finding.message}",
        "escalate_human": f"Human review required: {finding.message}",
        "suppress_output": f"Block output containing: {finding.message}",
        "add_disclaimer": f"Add epistemic disclaimer for: {finding.message}",
        "rerun_with_context": f"Re-execute with corrected context: {finding.message}",
    }
    return descriptions.get(strategy, f"Correction needed: {finding.message}")


# =============================================================================
# Penitent Consumer
# =============================================================================


class Penitent(SacredRole):
    """
    Correction advisor — decides WHAT corrections should be applied.

    Given a Verdict with findings, the Penitent produces a CorrectionPlan
    describing which corrections to request. It never executes them.

    Rules:
    - blessed verdicts → empty CorrectionPlan (no corrections needed)
    - purified verdicts → corrections for warnings only
    - heretical verdicts → corrections for all violations + warnings
    - critical findings → always require human review
    - security/architectural → always require human review

    Usage:
        penitent = Penitent()
        if penitent.can_handle(verdict):
            plan = penitent.process(verdict)
            # plan.requests → tuple of CorrectionRequests
            # plan.requires_human → bool
    """

    @property
    def role_name(self) -> str:
        return "penitent"

    @property
    def description(self) -> str:
        return "Correction advisor: decides WHAT corrections to apply, never HOW"

    def can_handle(self, event: Any) -> bool:
        """Accept Verdict objects or dicts containing 'verdict'."""
        if isinstance(event, Verdict):
            return True
        if isinstance(event, dict) and "verdict" in event:
            return isinstance(event["verdict"], Verdict)
        return False

    def process(self, event: Any) -> CorrectionPlan:
        """
        Produce a CorrectionPlan from a Verdict.

        Args:
            event: Verdict or dict with 'verdict' key

        Returns:
            CorrectionPlan with correction requests
        """
        if isinstance(event, Verdict):
            verdict = event
        elif isinstance(event, dict):
            verdict = event["verdict"]
        else:
            raise ValueError(
                f"Penitent expects Verdict or dict, got {type(event).__name__}"
            )

        return self._plan_corrections(verdict)

    def _plan_corrections(self, verdict: Verdict) -> CorrectionPlan:
        """Core correction planning — pure, deterministic."""
        confession_id = getattr(verdict, "confession_id", "unknown")

        # Blessed → no corrections
        if verdict.status == "blessed":
            return CorrectionPlan(
                verdict_status=verdict.status,
                confession_id=confession_id,
                requests=(),
                requires_human=False,
            )

        # Heretical or purified → create correction requests
        requests = []
        any_human = False

        for finding in verdict.findings:
            # Skip blessings and anomalies for correction purposes
            if finding.finding_type == "blessing":
                continue

            strategy = _select_strategy(finding)
            priority = _select_priority(finding)
            human_needed = _needs_human(finding)
            automated = not human_needed

            if human_needed:
                any_human = True
                strategy = "escalate_human"

            description = _build_description(finding, strategy)

            requests.append(
                CorrectionRequest(
                    finding=finding,
                    strategy=strategy,
                    priority=priority,
                    description=description,
                    automated=automated,
                )
            )

        # Sort by priority: critical first, then high, medium, low
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        requests.sort(key=lambda r: priority_order.get(r.priority, 99))

        return CorrectionPlan(
            verdict_status=verdict.status,
            confession_id=confession_id,
            requests=tuple(requests),
            requires_human=any_human,
        )
