"""
Orthodoxy Wardens — Finding Domain Object

A Finding is a single observation produced during audit examination.
It records WHAT was found, HOW severe it is, and WHICH rule triggered it.
Findings are collected into a Verdict. They are evidence, not judgments.

Sacred Order: Truth & Governance
Layer: Foundational (domain)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Finding:
    """
    Immutable record of a single audit observation.

    Multiple Findings are collected during a Confession examination
    and bundled into a Verdict by the Abbot.

    Attributes:
        finding_id: Unique identifier (format: "finding_YYYYMMDD_HHMMSS_NNN")
        finding_type: Nature of the observation
            - "violation": Rule was broken
            - "warning": Potential issue, not definitive
            - "anomaly": Statistical outlier detected
            - "blessing": Positive confirmation (everything OK)
        severity: Impact classification
            - "critical": Must block output delivery
            - "high": Should flag for review
            - "medium": Log for audit trail
            - "low": Informational only
        category: Domain of the finding
            - "compliance": Regulatory rule (e.g., MiFID, FINRA)
            - "data_quality": Missing/impossible values
            - "architectural": Service boundary violation
            - "performance": Latency/resource threshold exceeded
            - "hallucination": Fabricated content detected
            - "epistemic": Confidence/uncertainty issue
        message: Human-readable description of what was found
        source_rule: Identifier of the rule that triggered this finding (from RuleSet)
        context: Additional evidence (frozen tuple of (key, value) pairs)
    """

    finding_id: str
    finding_type: str
    severity: str
    category: str
    message: str
    source_rule: Optional[str] = None
    context: tuple = ()  # Frozen: tuple of (key, value) pairs

    def __post_init__(self):
        _valid_types = {"violation", "warning", "anomaly", "blessing"}
        _valid_severities = {"critical", "high", "medium", "low"}
        _valid_categories = {
            "compliance", "security", "data_quality", "architectural",
            "performance", "quality", "hallucination", "epistemic",
        }

        if self.finding_type not in _valid_types:
            raise ValueError(
                f"Invalid finding_type '{self.finding_type}'. "
                f"Must be one of: {_valid_types}"
            )
        if self.severity not in _valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. "
                f"Must be one of: {_valid_severities}"
            )
        if self.category not in _valid_categories:
            raise ValueError(
                f"Invalid category '{self.category}'. "
                f"Must be one of: {_valid_categories}"
            )

    @property
    def is_blocking(self) -> bool:
        """Whether this finding should block output delivery."""
        return self.severity == "critical" and self.finding_type == "violation"
