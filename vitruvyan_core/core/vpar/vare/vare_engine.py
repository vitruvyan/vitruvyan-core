"""
VARE Engine — Vitruvyan Adaptive Risk Engine v2.0
==================================================

Domain-agnostic multi-dimensional risk profiling.
The engine delegates domain-specific logic to a RiskProvider contract.

Pipeline:
    1. Provider prepares entity data (DataFrame)
    2. Provider supplies risk dimensions with calculation functions
    3. Engine computes each dimension score
    4. Engine aggregates with profile weights → overall_risk
    5. Engine categorizes and generates explanations via provider

Pure computation — no data fetching, no yfinance, no raw DB access.

Version: 2.0.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import numpy as np

from .types import RiskConfig, RiskDimensionScore, RiskResult

logger = logging.getLogger(__name__)


class VAREEngine:
    """
    Vitruvyan Adaptive Risk Engine — provider-driven risk profiling.

    Usage:
        provider = MyDomainRiskProvider()
        engine = VAREEngine(provider)
        result = engine.assess_risk("entity_123", raw_data, config)
    """

    def __init__(self, provider, *, domain_tag: Optional[str] = None):
        """
        Args:
            provider: Object implementing RiskProvider contract
                      (from vitruvyan_core/domains/risk_contract.py)
            domain_tag: Optional safety marker (e.g., "finance", "medical")
        """
        self.provider = provider
        self.domain_tag = domain_tag

        # Adaptation tracking (EPOCH V)
        self._adaptation_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def assess_risk(
        self,
        entity_id: str,
        raw_data: Dict[str, Any],
        config: Optional[RiskConfig] = None,
    ) -> RiskResult:
        """
        Assess risk for a single entity.

        Args:
            entity_id: Entity identifier (ticker, patient_id, route_id, …)
            raw_data: Raw domain data — passed to provider.prepare_entity_data()
            config: Optional risk configuration (profile, thresholds, weights)

        Returns:
            RiskResult with dimension scores, composite, and explanations.
        """
        config = config or RiskConfig()

        # 1. Provider prepares data
        entity_df = self.provider.prepare_entity_data(entity_id, raw_data)

        # 2. Get risk dimensions from provider
        dimensions = self.provider.get_risk_dimensions()

        # 3. Calculate each dimension
        dimension_scores: Dict[str, RiskDimensionScore] = {}
        for dim in dimensions:
            try:
                raw_value = dim.calculation_fn(entity_df)
                score = self._normalize_score(raw_value, dim)
                explanation = self._dimension_explanation(dim, score, raw_value)
                dimension_scores[dim.name] = RiskDimensionScore(
                    name=dim.name,
                    score=score,
                    raw_value=float(raw_value),
                    explanation=explanation,
                )
            except Exception as e:
                logger.warning(f"VARE: dimension '{dim.name}' failed for {entity_id}: {e}")
                dimension_scores[dim.name] = RiskDimensionScore(
                    name=dim.name,
                    score=50.0,  # neutral fallback
                    raw_value=0.0,
                    explanation=f"Calculation failed: {e}",
                )

        # 4. Aggregate
        weights = self._resolve_weights(config, dimensions)
        overall_risk = self._aggregate(dimension_scores, weights)

        # 5. Categorize
        risk_category = self._categorize(overall_risk, config.thresholds)

        # 6. Primary factor
        primary = max(dimension_scores.values(), key=lambda ds: ds.score)

        # 7. Explanation (provider-driven)
        score_dict = {n: ds.score for n, ds in dimension_scores.items()}
        explanation = self.provider.format_risk_explanation(
            score_dict, overall_risk, risk_category
        )

        # 8. Confidence
        confidence = self._calculate_confidence(dimension_scores, entity_df)

        result = RiskResult(
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            dimension_scores=dimension_scores,
            overall_risk=overall_risk,
            risk_category=risk_category,
            primary_risk_factor=primary.name,
            explanation=explanation,
            confidence=confidence,
            profile=config.profile,
            domain_tag=self.domain_tag,
        )

        logger.info(
            f"VARE: {entity_id} → {risk_category} "
            f"({overall_risk:.1f}/100, primary={primary.name})"
        )
        return result

    def batch_assess(
        self,
        entities: List[Dict[str, Any]],
        config: Optional[RiskConfig] = None,
    ) -> List[RiskResult]:
        """
        Assess risk for multiple entities.

        Args:
            entities: List of {"entity_id": str, "raw_data": dict}
            config: Shared risk configuration

        Returns:
            List[RiskResult] in same order as input.
        """
        results = []
        for entry in entities:
            try:
                r = self.assess_risk(
                    entry["entity_id"], entry["raw_data"], config
                )
                results.append(r)
            except Exception as e:
                logger.error(f"VARE batch: {entry.get('entity_id')} failed: {e}")
                results.append(self._error_result(
                    entry.get("entity_id", "unknown"), str(e), config
                ))
        return results

    # ------------------------------------------------------------------
    # EPOCH V — ADAPTIVE METHODS
    # ------------------------------------------------------------------

    def adjust(self, parameter: str, delta: float) -> bool:
        """
        Dynamically adjust engine thresholds (called by Orthodoxy listeners).

        Args:
            parameter: Threshold key to adjust (e.g., "LOW", "MODERATE", "HIGH")
            delta: Signed adjustment value

        Returns:
            True if adjustment succeeded.
        """
        # This modifies no persistent state — callers must re-pass config
        self._adaptation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "parameter": parameter,
            "delta": delta,
        })
        logger.info(f"VARE: adaptation recorded — {parameter} {delta:+.2f}")
        return True

    @property
    def adaptation_history(self) -> List[Dict[str, Any]]:
        return list(self._adaptation_history)

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_score(raw_value: float, dim) -> float:
        """
        Normalize a raw metric to 0-100 risk score using dimension thresholds.

        Uses linear interpolation between threshold_low / moderate / high.
        """
        if dim.higher_is_riskier:
            if raw_value <= dim.threshold_low:
                return max(0.0, (raw_value / dim.threshold_low) * 25.0) if dim.threshold_low > 0 else 0.0
            elif raw_value <= dim.threshold_moderate:
                span = dim.threshold_moderate - dim.threshold_low
                return 25.0 + ((raw_value - dim.threshold_low) / span) * 25.0 if span > 0 else 50.0
            elif raw_value <= dim.threshold_high:
                span = dim.threshold_high - dim.threshold_moderate
                return 50.0 + ((raw_value - dim.threshold_moderate) / span) * 25.0 if span > 0 else 75.0
            else:
                return min(100.0, 75.0 + 25.0)
        else:
            # Invert: lower raw value = higher risk
            inverted = dim.threshold_high - raw_value + dim.threshold_low
            return VAREEngine._normalize_score(inverted, type(dim)(
                name=dim.name, description=dim.description,
                calculation_fn=dim.calculation_fn,
                threshold_low=dim.threshold_low,
                threshold_moderate=dim.threshold_moderate,
                threshold_high=dim.threshold_high,
                higher_is_riskier=True,
            ))

    @staticmethod
    def _dimension_explanation(dim, score: float, raw_value: float) -> str:
        """Generate a one-line explanation for a dimension score."""
        if score < 25:
            level = "low"
        elif score < 50:
            level = "moderate"
        elif score < 75:
            level = "high"
        else:
            level = "extreme"
        return f"{dim.description}: {level} risk ({score:.0f}/100, raw={raw_value:.4f})"

    def _resolve_weights(self, config: RiskConfig, dimensions) -> Dict[str, float]:
        """
        Resolve dimension weights: config overrides > provider profiles > equal.
        """
        if config.dimension_weights:
            return config.dimension_weights

        # Try provider profiles
        profiles = self.provider.get_risk_profiles()
        profile = profiles.get(config.profile)
        if profile:
            return profile.dimension_weights

        # Fallback: equal weights
        n = len(dimensions)
        return {d.name: 1.0 / n for d in dimensions} if n > 0 else {}

    @staticmethod
    def _aggregate(
        dimension_scores: Dict[str, RiskDimensionScore],
        weights: Dict[str, float],
    ) -> float:
        """Weighted average of dimension scores."""
        total_weight = 0.0
        weighted_sum = 0.0
        for name, ds in dimension_scores.items():
            w = weights.get(name, 0.0)
            weighted_sum += ds.score * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 50.0

    @staticmethod
    def _categorize(overall_risk: float, thresholds: Dict[str, float]) -> str:
        """Map overall score to risk category."""
        if overall_risk <= thresholds.get("LOW", 25.0):
            return "LOW"
        elif overall_risk <= thresholds.get("MODERATE", 50.0):
            return "MODERATE"
        elif overall_risk <= thresholds.get("HIGH", 75.0):
            return "HIGH"
        return "EXTREME"

    @staticmethod
    def _calculate_confidence(
        dimension_scores: Dict[str, RiskDimensionScore],
        entity_df,
    ) -> float:
        """
        Heuristic confidence based on dimension availability.

        Full confidence when all dimensions computed successfully;
        degraded when some fell back to neutral (score=50, raw=0).
        """
        if not dimension_scores:
            return 0.0
        valid = sum(
            1 for ds in dimension_scores.values()
            if not (ds.score == 50.0 and ds.raw_value == 0.0)
        )
        data_factor = min(1.0, len(entity_df) / 100) if hasattr(entity_df, '__len__') else 0.5
        return (valid / len(dimension_scores)) * 0.7 + data_factor * 0.3

    def _error_result(
        self, entity_id: str, error_msg: str, config: Optional[RiskConfig] = None
    ) -> RiskResult:
        """Create a neutral error result."""
        return RiskResult(
            entity_id=entity_id,
            timestamp=datetime.utcnow(),
            dimension_scores={},
            overall_risk=50.0,
            risk_category="MODERATE",
            primary_risk_factor="unknown",
            explanation={
                "summary": f"Risk analysis failed for {entity_id}: {error_msg}",
                "technical": "Unable to compute risk dimensions",
                "detailed": error_msg,
            },
            confidence=0.0,
            profile=config.profile if config else "balanced",
            domain_tag=self.domain_tag,
        )
