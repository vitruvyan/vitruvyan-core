"""
VWRE Engine — Vitruvyan Weighted Reverse Engineering v2.0
==========================================================

Domain-agnostic attribution analysis.
Decomposes composite scores into weighted factor contributions.

Answers the question: "Why did entity X score higher than entity Y?"

Pipeline:
    1. Provider supplies factor mappings and profile weights
    2. Engine calculates contribution = z_score × weight for each factor
    3. Engine verifies sum(contributions) ≈ composite_score
    4. Engine identifies primary/secondary drivers
    5. Provider generates domain-specific explanation strings

Pure computation — no Neural Engine imports, no raw DB access.

Version: 2.0.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .types import (
    AttributionConfig,
    AttributionResult,
    ComparisonResult,
    FactorAttribution,
)

logger = logging.getLogger(__name__)


class VWREEngine:
    """
    Vitruvyan Weighted Reverse Engineering — provider-driven attribution.

    Usage:
        provider = MyDomainAggregationProvider()
        engine = VWREEngine(provider)
        result = engine.analyze("entity_1", 1.85, factors, config)
    """

    def __init__(self, provider, *, domain_tag: Optional[str] = None):
        """
        Args:
            provider: Object implementing AggregationProvider contract
                      (from vitruvyan_core/domains/aggregation_contract.py)
            domain_tag: Optional safety marker
        """
        self.provider = provider
        self.domain_tag = domain_tag

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def analyze(
        self,
        entity_id: str,
        composite_score: float,
        factors: Dict[str, float],
        config: Optional[AttributionConfig] = None,
    ) -> AttributionResult:
        """
        Reverse-engineer a composite score into factor contributions.

        Args:
            entity_id: Entity identifier
            composite_score: Final composite score to decompose
            factors: Dict of raw factor values (z-scores, normalized, etc.)
            config: Optional attribution configuration

        Returns:
            AttributionResult with full breakdown and verification.
        """
        config = config or AttributionConfig()

        # 1. Validate factors via provider
        validation = self.provider.validate_factors(factors)
        clean_factors = validation.get("cleaned_factors", factors)

        # 2. Get profile weights + factor mappings from provider
        profiles = self.provider.get_aggregation_profiles()
        profile = profiles.get(config.profile)
        if not profile:
            # Fallback to first available profile
            profile = next(iter(profiles.values())) if profiles else None

        if not profile:
            logger.warning(f"VWRE: no profile found for '{config.profile}'")
            return self._error_result(entity_id, composite_score, config,
                                      "No aggregation profile available")

        factor_map = self.provider.get_factor_mappings()

        # 3. Calculate contributions
        contributions: Dict[str, Dict] = {}
        for raw_key, weight_key in factor_map.items():
            if raw_key not in clean_factors:
                continue
            value = clean_factors[raw_key]
            if value is None:
                continue
            weight = profile.factor_weights.get(weight_key, 0.0)
            if weight <= 0:
                continue
            contribution = self.provider.calculate_contribution(value, weight, profile)
            contributions[weight_key] = {
                "z_score": value,
                "weight": weight,
                "contribution": contribution,
            }

        if not contributions:
            return self._error_result(entity_id, composite_score, config,
                                      "No valid factors for attribution")

        # 4. Percentages
        total = sum(c["contribution"] for c in contributions.values())
        for key, data in contributions.items():
            data["percentage"] = (
                (data["contribution"] / total * 100.0) if total != 0 else 0.0
            )

        # 5. Ranks
        sorted_factors = sorted(
            contributions.items(), key=lambda x: abs(x[1]["contribution"]), reverse=True
        )
        for i, (key, data) in enumerate(sorted_factors):
            if i == 0:
                data["rank"] = "primary driver"
            elif i < 3 and abs(data["contribution"]) > config.min_contribution:
                data["rank"] = "secondary support"
            elif abs(data["contribution"]) > 0.01:
                data["rank"] = "minor contribution"
            else:
                data["rank"] = "negligible"

        # 6. Primary / secondary drivers
        primary_key = sorted_factors[0][0] if sorted_factors else None
        primary_contrib = contributions[primary_key]["contribution"] if primary_key else 0.0
        secondary = [
            k for k, d in sorted_factors[1:3]
            if abs(d["contribution"]) > config.min_contribution
        ]

        # 7. Verification
        residual = composite_score - total
        verification = self._verify(residual, config)

        # 8. Narratives (z-score → qualitative label)
        factor_attrs: Dict[str, FactorAttribution] = {}
        for key, data in contributions.items():
            narrative = self._z_narrative(key, data["z_score"], data["weight"], data["contribution"])
            factor_attrs[key] = FactorAttribution(
                name=key,
                z_score=data["z_score"],
                weight=data["weight"],
                contribution=data["contribution"],
                percentage=data["percentage"],
                rank=data["rank"],
                narrative=narrative,
            )

        # 9. Explanation strings via provider
        contrib_dict = {k: d["contribution"] for k, d in contributions.items()}
        expl = self.provider.format_attribution_explanation(
            contrib_dict, primary_key or "unknown", composite_score
        )
        rank_explanation = expl.get("summary", self._default_rank_explanation(
            primary_key, contributions, primary_contrib
        ))
        technical_summary = expl.get("technical", self._technical_summary(
            entity_id, composite_score, contrib_dict, residual, config.profile
        ))

        result = AttributionResult(
            entity_id=entity_id,
            composite_score=composite_score,
            profile=config.profile,
            timestamp=datetime.utcnow(),
            factors=factor_attrs,
            primary_driver=primary_key,
            primary_contribution=primary_contrib,
            secondary_drivers=secondary,
            sum_contributions=total,
            residual=residual,
            verification_status=verification,
            rank_explanation=rank_explanation,
            technical_summary=technical_summary,
            domain_tag=self.domain_tag,
        )

        logger.info(
            f"VWRE: {entity_id} → primary={primary_key} "
            f"({primary_contrib:+.3f}), residual={residual:.3f} [{verification}]"
        )
        return result

    def compare(
        self,
        result_a: AttributionResult,
        result_b: AttributionResult,
    ) -> ComparisonResult:
        """
        Contrastive analysis: why did entity A score higher than B?

        Args:
            result_a: Attribution result for entity A (typically higher score)
            result_b: Attribution result for entity B

        Returns:
            ComparisonResult with deltas and explanation.
        """
        delta_composite = result_a.composite_score - result_b.composite_score

        # Factor deltas (common factors only)
        deltas: Dict[str, float] = {}
        for key, fa in result_a.factors.items():
            if key in result_b.factors:
                deltas[key] = fa.contribution - result_b.factors[key].contribution

        # Primary differentiator
        if deltas:
            primary_key = max(deltas, key=lambda k: abs(deltas[k]))
            primary_delta = deltas[primary_key]
        else:
            primary_key = "unknown"
            primary_delta = 0.0

        # Explanation
        direction = "superior" if primary_delta > 0 else "weaker"
        explanation = (
            f"{result_a.entity_id} scores higher than {result_b.entity_id} "
            f"primarily due to {direction} {primary_key} ({primary_delta:+.3f})."
        )
        supporting = sorted(
            [(k, v) for k, v in deltas.items() if k != primary_key],
            key=lambda x: abs(x[1]), reverse=True
        )[:2]
        if supporting:
            parts = [f"{k} ({v:+.3f})" for k, v in supporting if abs(v) > 0.05]
            if parts:
                explanation += f" Supporting: {', '.join(parts)}."

        return ComparisonResult(
            entity_a=result_a.entity_id,
            entity_b=result_b.entity_id,
            delta_composite=delta_composite,
            primary_difference=primary_key,
            primary_delta=primary_delta,
            all_deltas=deltas,
            explanation=explanation,
        )

    def batch_analyze(
        self,
        entries: List[Dict[str, Any]],
        config: Optional[AttributionConfig] = None,
    ) -> List[AttributionResult]:
        """
        Batch attribution for multiple entities.

        Args:
            entries: List of {"entity_id", "composite_score", "factors"}
            config: Shared attribution configuration

        Returns:
            List[AttributionResult] in same order.
        """
        results = []
        for entry in entries:
            try:
                r = self.analyze(
                    entry["entity_id"],
                    entry["composite_score"],
                    entry.get("factors", {}),
                    config,
                )
                results.append(r)
            except Exception as e:
                logger.error(f"VWRE batch: {entry.get('entity_id')} failed: {e}")
                results.append(self._error_result(
                    entry.get("entity_id", "unknown"),
                    entry.get("composite_score", 0.0),
                    config, str(e),
                ))
        return results

    # ------------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------------

    @staticmethod
    def _verify(residual: float, config: AttributionConfig) -> str:
        """Verify mathematical consistency."""
        abs_r = abs(residual)
        if abs_r < config.residual_tolerance:
            return "verified"
        elif abs_r < config.residual_warning:
            logger.warning(f"VWRE verification warning: residual={residual:.3f}")
            return "warning"
        else:
            logger.error(f"VWRE verification error: residual={residual:.3f}")
            return "error"

    @staticmethod
    def _z_narrative(name: str, z: float, weight: float, contribution: float) -> str:
        """Human-readable narrative for a factor based on z-score."""
        if z > 1.5:
            strength = "exceptional signal"
        elif z > 1.0:
            strength = "strong signal"
        elif z > 0.5:
            strength = "above-average signal"
        elif z > 0.0:
            strength = "slightly positive"
        elif z > -0.5:
            strength = "neutral"
        elif z > -1.0:
            strength = "below-average signal"
        else:
            strength = "weak signal"
        return (
            f"{strength} (z={z:.2f}, weight={weight:.2%}, "
            f"contribution={contribution:+.3f})"
        )

    @staticmethod
    def _default_rank_explanation(
        primary: Optional[str],
        contributions: Dict[str, Dict],
        primary_contrib: float,
    ) -> str:
        if not primary:
            return "Ranking based on available factors"
        pct = contributions[primary]["percentage"]
        return (
            f"Score driven by {primary} "
            f"({pct:.1f}% weight, {primary_contrib:+.3f} contribution)"
        )

    @staticmethod
    def _technical_summary(
        entity_id: str,
        composite: float,
        contributions: Dict[str, float],
        residual: float,
        profile: str,
    ) -> str:
        parts = " + ".join(
            f"{k}({v:+.3f})"
            for k, v in sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        )
        total = sum(contributions.values())
        summary = f"{entity_id} composite={composite:.3f} (profile={profile})\n= {parts}\n= {total:.3f} base"
        if abs(residual) > 0.01:
            summary += f" + {residual:+.3f} adjustment = {composite:.3f} final"
        return summary

    def _error_result(
        self,
        entity_id: str,
        composite_score: float,
        config: Optional[AttributionConfig],
        error_msg: str,
    ) -> AttributionResult:
        return AttributionResult(
            entity_id=entity_id,
            composite_score=composite_score,
            profile=config.profile if config else "balanced",
            timestamp=datetime.utcnow(),
            factors={},
            primary_driver=None,
            primary_contribution=0.0,
            secondary_drivers=[],
            sum_contributions=0.0,
            residual=composite_score,
            verification_status="error",
            rank_explanation=f"Attribution failed: {error_msg}",
            technical_summary=error_msg,
            domain_tag=self.domain_tag,
        )
