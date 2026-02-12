"""
VWRE Types — Domain-Agnostic Attribution Analysis Data Structures
==================================================================

Frozen dataclasses for the Vitruvyan Weighted Reverse Engineering engine.
No I/O, no domain logic, no external dependencies.

Version: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AttributionConfig:
    """Configuration for a VWRE attribution session."""
    profile: str = "balanced"          # AggregationProfile name
    residual_tolerance: float = 0.1    # Max acceptable residual for "verified"
    residual_warning: float = 0.5      # Max before "error" status
    min_contribution: float = 0.05     # Min abs contribution for "secondary" rank


@dataclass(frozen=True)
class FactorAttribution:
    """Attribution detail for a single factor."""
    name: str                # Factor key (e.g., "momentum", "severity")
    z_score: float           # Raw input value
    weight: float            # Weight from profile
    contribution: float      # z_score * weight
    percentage: float        # Contribution as % of total
    rank: str                # "primary driver" | "secondary support" | "minor" | "negligible"
    narrative: str           # Human-readable explanation


@dataclass(frozen=True)
class AttributionResult:
    """
    Complete output of a VWRE attribution analysis.

    Domain-agnostic: explains why any entity scored the way it did.
    """
    entity_id: str
    composite_score: float
    profile: str
    timestamp: datetime

    # Factor breakdown
    factors: Dict[str, FactorAttribution]

    # Primary driver
    primary_driver: Optional[str]
    primary_contribution: float

    # Secondary drivers
    secondary_drivers: List[str]

    # Verification
    sum_contributions: float       # Should ≈ composite_score
    residual: float                # composite_score - sum_contributions
    verification_status: str       # "verified" | "warning" | "error"

    # Explainability
    rank_explanation: str          # One-line summary
    technical_summary: str         # Full mathematical breakdown

    # Metadata
    domain_tag: Optional[str] = None

    def to_state_dict(self) -> Dict:
        """Serialize to LangGraph-compatible state dict."""
        return {
            "vwre_entity_id": self.entity_id,
            "vwre_composite_score": self.composite_score,
            "vwre_primary_driver": self.primary_driver,
            "vwre_primary_contribution": self.primary_contribution,
            "vwre_verification": self.verification_status,
            "vwre_rank_explanation": self.rank_explanation,
            "vwre_factor_contributions": {
                n: {"contribution": f.contribution, "percentage": f.percentage}
                for n, f in self.factors.items()
            },
        }


@dataclass(frozen=True)
class ComparisonResult:
    """
    Contrastive analysis between two entities.

    Answers: "Why did entity A score higher than entity B?"
    """
    entity_a: str
    entity_b: str
    delta_composite: float
    primary_difference: str        # Factor with largest delta
    primary_delta: float
    all_deltas: Dict[str, float]
    explanation: str               # Human-readable contrastive narrative
