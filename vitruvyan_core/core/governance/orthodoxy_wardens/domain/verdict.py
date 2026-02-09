"""
Orthodoxy Wardens — Verdict Domain Object

A Verdict is the final judgment rendered by the tribunal on a Confession.
It aggregates Findings into a single disposition with five possible statuses.
The Verdict determines whether an output reaches the user or is blocked.

This is the most important domain object in Orthodoxy Wardens.

Sacred Order: Truth & Governance
Layer: Foundational (domain)
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Verdict:
    """
    Immutable final judgment on a Confession.

    The five statuses implement the Socratic Pattern — including the ability
    to explicitly say "I don't know" (non_liquet), which prevents the
    "confident hallucination" problem.

    Attributes:
        status: The disposition
            - "blessed": Output valid, high confidence → send to user
            - "purified": Output corrected, errors removed → send corrected version
            - "heretical": Output rejected, hallucination or violation → block
            - "non_liquet": Insufficient confidence → send with uncertainty admission
            - "clarification_needed": Input too ambiguous → ask user for clarification
        confidence: Tribunal confidence in this verdict (0.0 - 1.0)
        findings: All Findings collected during examination (frozen tuple)
        explanation: Human-readable summary of the verdict reasoning
        should_send: Whether the output should reach the user
        ruleset_version: Hash/version of the RuleSet used for this judgment
        what_we_know: (non_liquet only) Certain facts established
        what_is_uncertain: (non_liquet only) Admitted knowledge gaps
        uncertainty_sources: (non_liquet only) Why confidence is low
        best_guess: (non_liquet only) Partial result, if available
    """

    status: str
    confidence: float
    findings: tuple  # Tuple[Finding, ...] — must be frozen
    explanation: str
    should_send: bool
    ruleset_version: Optional[str] = None
    # non_liquet specific fields
    what_we_know: tuple = ()
    what_is_uncertain: tuple = ()
    uncertainty_sources: tuple = ()
    best_guess: Optional[str] = None

    _VALID_STATUSES = frozenset({
        "blessed", "purified", "heretical",
        "non_liquet", "clarification_needed",
    })

    def __post_init__(self):
        if self.status not in self._VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. "
                f"Must be one of: {self._VALID_STATUSES}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    # =========================================================================
    # Factory methods — canonical way to create Verdicts
    # =========================================================================

    @classmethod
    def blessed(
        cls,
        confidence: float,
        findings: tuple = (),
        explanation: str = "Output validated successfully.",
        ruleset_version: Optional[str] = None,
    ) -> "Verdict":
        """Create a blessed (approved) verdict."""
        return cls(
            status="blessed",
            confidence=confidence,
            findings=findings,
            explanation=explanation,
            should_send=True,
            ruleset_version=ruleset_version,
        )

    @classmethod
    def purified(
        cls,
        confidence: float,
        findings: tuple,
        explanation: str,
        ruleset_version: Optional[str] = None,
    ) -> "Verdict":
        """Create a purified (corrected) verdict."""
        return cls(
            status="purified",
            confidence=confidence,
            findings=findings,
            explanation=explanation,
            should_send=True,
            ruleset_version=ruleset_version,
        )

    @classmethod
    def heretical(
        cls,
        findings: tuple,
        explanation: str,
        confidence: float = 0.95,
        ruleset_version: Optional[str] = None,
    ) -> "Verdict":
        """Create a heretical (rejected) verdict. Blocks output delivery."""
        return cls(
            status="heretical",
            confidence=confidence,
            findings=findings,
            explanation=explanation,
            should_send=False,
            ruleset_version=ruleset_version,
        )

    @classmethod
    def non_liquet(
        cls,
        confidence: float,
        what_we_know: tuple,
        what_is_uncertain: tuple,
        uncertainty_sources: tuple,
        best_guess: Optional[str] = None,
        findings: tuple = (),
        ruleset_version: Optional[str] = None,
    ) -> "Verdict":
        """
        Create a non_liquet (insufficient evidence) verdict.
        Latin: "it is not clear" — used by Roman judges when evidence
        was insufficient to render a definitive verdict.
        Output is sent WITH explicit uncertainty admission.
        """
        return cls(
            status="non_liquet",
            confidence=confidence,
            findings=findings,
            explanation="Insufficient confidence for a definitive judgment.",
            should_send=True,
            ruleset_version=ruleset_version,
            what_we_know=what_we_know,
            what_is_uncertain=what_is_uncertain,
            uncertainty_sources=uncertainty_sources,
            best_guess=best_guess,
        )

    @classmethod
    def clarification_needed(
        cls,
        explanation: str,
        findings: tuple = (),
        ruleset_version: Optional[str] = None,
    ) -> "Verdict":
        """Create a clarification_needed verdict — input was too ambiguous."""
        return cls(
            status="clarification_needed",
            confidence=0.0,
            findings=findings,
            explanation=explanation,
            should_send=True,
            ruleset_version=ruleset_version,
        )

    # =========================================================================
    # Query methods
    # =========================================================================

    @property
    def is_blocking(self) -> bool:
        """Whether this verdict blocks output delivery."""
        return not self.should_send

    @property
    def has_violations(self) -> bool:
        """Whether any findings are violations."""
        return any(
            getattr(f, "finding_type", None) == "violation"
            for f in self.findings
        )

    @property
    def critical_count(self) -> int:
        """Number of critical-severity findings."""
        return sum(
            1 for f in self.findings
            if getattr(f, "severity", None) == "critical"
        )
