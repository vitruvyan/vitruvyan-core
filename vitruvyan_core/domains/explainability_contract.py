"""
Vitruvyan Core — Explainability Contract v2.0
==============================================

Abstract interface for domain-specific explainability providers.

Domains implement ExplainabilityProvider to tell VEE:
1. How to normalize metrics         (NormalizationRule)
2. What analysis dimensions exist   (AnalysisDimension)
3. What patterns to detect          (PatternRule)
4. How to weight dimensions         (intensity_weights)
5. How to compute confidence        (ConfidenceCriteria)
6. How to generate narratives       (ExplanationTemplate)
7. How to reference entities        (format_entity_reference)

VEE Core contains ZERO domain knowledge. Everything is injected via this
contract. Any domain (finance, medical, IoT, legal) can implement a
provider without modifying VEE internals.

Version: 2.0.0 (Feb 12, 2026)
Breaking: Replaces get_signal_descriptions/get_factor_categories
          with get_analysis_dimensions (see _archived_v2/ for old contract).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Tuple


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class NormalizationRule:
    """How to normalize a metric to 0-1 range.

    Rules are matched by substring on metric key.
    Example: NormalizationRule("_z", "zscore_tanh") matches "momentum_z", "trend_z".
    """
    metric_pattern: str          # Substring match (e.g., "_z", "_score", "_risk")
    method: str                  # "zscore_tanh", "linear_100", "linear_custom", "sigmoid"
    invert: bool = False         # If True, high raw value → low normalized (e.g., risk)
    min_value: float = 0.0       # For linear_custom
    max_value: float = 100.0     # For linear_custom


@dataclass
class AnalysisDimension:
    """Defines an analysis dimension (replaces hardcoded kpi_categories).

    Each dimension groups related metrics and defines their semantic direction.
    Example (finance): AnalysisDimension("momentum", ["momentum_z", "rsi_z"], "price momentum")
    Example (medical): AnalysisDimension("cardiac", ["hr_z", "bp_z"], "cardiac function")
    """
    name: str                    # Internal key
    metric_keys: List[str]       # Which metrics belong to this dimension
    display_name: str            # Human-readable name
    direction: str = "higher_better"  # "higher_better", "lower_better", "neutral"
    weight: float = 1.0          # Relative weight for overall intensity


@dataclass
class PatternRule:
    """Domain-specific pattern detection rule.

    The condition callable receives normalized metrics dict and returns bool.
    Example:
        PatternRule(
            name="strong_momentum",
            display_text="Strong upward momentum detected",
            condition=lambda m: m.get("momentum_z", 0) > 0.8 and m.get("trend_z", 0) > 0.7
        )
    """
    name: str                    # Internal identifier
    display_text: str            # Human-readable pattern description
    condition: Callable[[Dict[str, float]], bool] = None  # Detection function


@dataclass
class ConfidenceCriteria:
    """How to compute analysis confidence.

    Defines thresholds for data completeness, signal clarity, and consistency.
    """
    min_metrics_high: int = 5        # Minimum metrics for high confidence
    min_metrics_moderate: int = 3    # Minimum for moderate confidence
    min_signals_high: int = 3        # Minimum signals for high confidence
    consistency_threshold: float = 0.2  # Std dev threshold for "consistent"


@dataclass
class ExplanationTemplate:
    """Domain-specific narrative templates for multi-level explanations.

    Templates use {placeholders} filled by VEE Generator:
      {entity_id}          — Raw entity identifier
      {entity_reference}   — Formatted reference (from format_entity_reference)
      {signals_text}       — Comma-separated identified signals
      {dominant_factor}    — Primary factor name
      {secondary_factors}  — Other significant factors
      {intensity}          — Overall intensity (0.0-1.0)
      {direction}          — Overall direction string
      {signals_summary}    — Brief signals summary
      {patterns_text}      — Detected patterns description
      {confidence_text}    — Confidence note
    """
    summary_template: str
    technical_template: str
    detailed_template: str
    contextual_template: str = ""
    summary_variants: List[str] = field(default_factory=list)
    technical_variants: List[str] = field(default_factory=list)
    detailed_variants: List[str] = field(default_factory=list)


@dataclass
class MetricDefinition:
    """Defines what a metric means in domain-specific terms."""
    name: str
    description: str
    unit: str
    interpretation: str
    normal_range: Tuple[float, float] = (0.0, 1.0)
    display_name: Optional[str] = None


# ── Provider interface ───────────────────────────────────────────────────────


class ExplainabilityProvider(ABC):
    """
    Interface that domains implement to provide explainability context.

    VEE Engine calls these methods — it contains ZERO domain knowledge itself.

    Implementation example:
        class FinanceExplainabilityProvider(ExplainabilityProvider):
            def get_normalization_rules(self):
                return [NormalizationRule("_z", "zscore_tanh"), ...]

            def get_analysis_dimensions(self):
                return [AnalysisDimension("momentum", ["momentum_z", "rsi_z"], "price momentum"), ...]
    """

    # ── Narrative generation ──

    @abstractmethod
    def get_explanation_templates(self) -> ExplanationTemplate:
        """Return domain-specific narrative templates.
        Templates use {placeholders} listed in ExplanationTemplate docstring."""
        ...

    @abstractmethod
    def format_entity_reference(self, entity_id: str) -> str:
        """How to refer to entities in natural language.
        Finance: "AAPL" → "Apple Inc.". Medical: "P123" → "Patient #123"."""
        ...

    # ── Analysis configuration ──

    @abstractmethod
    def get_normalization_rules(self) -> List[NormalizationRule]:
        """Define how to normalize each metric type to 0-1 range.
        Rules are matched by substring on metric key."""
        ...

    @abstractmethod
    def get_analysis_dimensions(self) -> List[AnalysisDimension]:
        """Define analysis dimensions (what categories of metrics exist).
        Replaces hardcoded kpi_categories. Each dimension groups related metrics."""
        ...

    @abstractmethod
    def get_pattern_rules(self) -> List[PatternRule]:
        """Define domain-specific pattern detection rules.
        Each rule has a condition function and display text."""
        ...

    @abstractmethod
    def get_intensity_weights(self) -> Dict[str, float]:
        """Relative weights for each dimension in overall intensity.
        Keys must match AnalysisDimension.name values."""
        ...

    @abstractmethod
    def get_confidence_criteria(self) -> ConfidenceCriteria:
        """Define thresholds for confidence calculation."""
        ...

    # ── Optional metadata ──

    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Optional: Define what each metric means in this domain.
        Default: empty (VEE works without it)."""
        return {}