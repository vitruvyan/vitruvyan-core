"""
VEE Core Types — Domain-agnostic data structures for explainability.

All types are plain Python dataclasses with no domain assumptions.
Optional fields allow partial data without raising errors.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class AnalysisResult:
    """Domain-agnostic analysis output from VEE Analyzer.

    Key design decisions:
    - dominant_factors is a List (co-dominance support, not single scalar)
    - direction is Optional[str] (domain defines semantics, not VEE)
    - confidence is Dict (multi-dimensional, not single float)
    """
    entity_id: str
    timestamp: datetime
    signals: List[str]
    signal_strengths: Dict[str, float]
    dominant_factors: List[Tuple[str, float]]  # [(factor_name, strength), ...]
    overall_intensity: float  # 0.0 - 1.0

    direction: Optional[str] = None
    confidence: Dict[str, float] = field(default_factory=lambda: {"overall": 0.0})
    patterns: List[str] = field(default_factory=list)
    anomalies: List[str] = field(default_factory=list)
    metrics_count: int = 0
    missing_dimensions: List[str] = field(default_factory=list)

    @property
    def primary_factor(self) -> str:
        """Convenience: first dominant factor name."""
        return self.dominant_factors[0][0] if self.dominant_factors else "unknown"

    @property
    def primary_strength(self) -> float:
        """Convenience: first dominant factor strength."""
        return self.dominant_factors[0][1] if self.dominant_factors else 0.0

    @property
    def overall_confidence(self) -> float:
        """Convenience: overall confidence value."""
        return self.confidence.get("overall", 0.0)


@dataclass
class ExplanationLevels:
    """Multi-level explanation output from VEE Generator."""
    entity_id: str
    timestamp: datetime
    summary: str
    technical: str
    detailed: str

    confidence_note: str = ""
    profile_adapted: bool = False

    # Context enrichment (Phase 3)
    contextualized: Optional[str] = None
    historical_reference: Optional[str] = None

    # VSGS Semantic Grounding (PR-C integration)
    semantic_grounded: Optional[str] = None
    epistemic_trace: Optional[List[str]] = None


@dataclass
class HistoricalExplanation:
    """Stored explanation retrieved from persistence."""
    id: int
    entity_id: str
    summary: str
    technical: str
    detailed: str
    created_at: datetime
    confidence: float = 0.0
    dominant_factor: str = ""
    direction: Optional[str] = None
    metrics_count: int = 0
    overall_intensity: float = 0.0
    domain_tag: str = ""
