"""
VARE Types — Domain-Agnostic Risk Assessment Data Structures
=============================================================

Frozen dataclasses for the Vitruvyan Adaptive Risk Engine.
No I/O, no domain logic, no external dependencies.

Version: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass(frozen=True)
class RiskDimensionScore:
    """Score for a single risk dimension."""
    name: str                  # e.g., "market_risk", "delay_risk"
    score: float               # 0-100 (higher = riskier)
    raw_value: float           # Underlying metric before normalization
    explanation: str           # Human-readable dimension explanation


@dataclass(frozen=True)
class RiskConfig:
    """Configuration for a VARE analysis session."""
    profile: str = "balanced"       # Risk weighting profile name
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "LOW": 25.0,
        "MODERATE": 50.0,
        "HIGH": 75.0,
        # Above HIGH = EXTREME
    })
    dimension_weights: Dict[str, float] = field(default_factory=dict)
    # If empty, engine uses provider's default profile weights


@dataclass(frozen=True)
class RiskResult:
    """
    Complete output of a VARE risk assessment.

    Domain-agnostic: works for any entity (ticker, patient, route, sensor).
    """
    entity_id: str
    timestamp: datetime

    # Per-dimension scores
    dimension_scores: Dict[str, RiskDimensionScore]

    # Composite
    overall_risk: float        # 0-100 weighted composite
    risk_category: str         # "LOW" | "MODERATE" | "HIGH" | "EXTREME"

    # Explainability
    primary_risk_factor: str   # Dimension with highest score
    explanation: Dict[str, str]  # {"summary", "technical", "detailed"}

    # Confidence
    confidence: float          # 0.0-1.0

    # Config used
    profile: str = "balanced"

    # Metadata
    domain_tag: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_state_dict(self) -> Dict[str, Any]:
        """Serialize to LangGraph-compatible state dict."""
        return {
            "vare_entity_id": self.entity_id,
            "vare_overall_risk": self.overall_risk,
            "vare_risk_category": self.risk_category,
            "vare_primary_factor": self.primary_risk_factor,
            "vare_confidence": self.confidence,
            "vare_dimension_scores": {
                name: {"score": ds.score, "raw_value": ds.raw_value}
                for name, ds in self.dimension_scores.items()
            },
            "vare_explanation": self.explanation,
            "vare_profile": self.profile,
        }
