"""
Vitruvyan Core — Finance Aggregation Provider
==============================================

Concrete implementation of AggregationProvider for financial markets.

Provides finance-specific:
1. Aggregation Profiles (short_spec, balanced_mid, etc.)
2. Factor Mappings (momentum_z → momentum, etc.)
3. Contribution Calculations (z_score × weight)
4. Attribution Explanations (finance-specific narratives)

This allows VWRE Engine to perform attribution analysis without hardcoded logic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: FINANCE DOMAIN IMPLEMENTATION
"""

import numpy as np
from typing import Dict, Any, List
from vitruvyan_core.domains.aggregation_contract import AggregationProvider, AggregationProfile


class FinanceAggregationProvider(AggregationProvider):
    """
    Finance-specific aggregation provider.

    Implements AggregationProvider for financial markets with:
    - Neural Engine style weighting profiles
    - Z-score factor mappings
    - Weighted sum aggregation
    - Finance attribution narratives
    """

    def __init__(self):
        super().__init__()
        self._initialize_profiles()
        self._initialize_mappings()

    def get_aggregation_profiles(self) -> Dict[str, AggregationProfile]:
        """Return all available aggregation profiles for finance domain"""
        return self.profiles

    def get_factor_mappings(self) -> Dict[str, str]:
        """Return factor name mappings for finance domain"""
        return self.factor_mappings

    def _initialize_profiles(self):
        """Initialize finance-specific aggregation profiles (from Neural Engine)"""

        # These are the actual profiles from Neural Engine
        self.profiles = {

            "short_spec": AggregationProfile(
                name="short_spec",
                description="Short-term speculation profile emphasizing momentum and trend",
                factor_weights={
                    "momentum": 0.35,
                    "trend": 0.15,
                    "vola": 0.08,
                    "sent": 0.10,
                    "fundamentals": 0.12,
                    "technical": 0.10,
                    "quality": 0.05,
                    "size": 0.05
                },
                aggregation_method="weighted_sum"
            ),

            "balanced_mid": AggregationProfile(
                name="balanced_mid",
                description="Balanced mid-term profile with equal factor weighting",
                factor_weights={
                    "momentum": 0.20,
                    "trend": 0.15,
                    "vola": 0.10,
                    "sent": 0.15,
                    "fundamentals": 0.20,
                    "technical": 0.10,
                    "quality": 0.05,
                    "size": 0.05
                },
                aggregation_method="weighted_sum"
            ),

            "long_term": AggregationProfile(
                name="long_term",
                description="Long-term investment profile emphasizing fundamentals and quality",
                factor_weights={
                    "momentum": 0.10,
                    "trend": 0.05,
                    "vola": 0.05,
                    "sent": 0.10,
                    "fundamentals": 0.35,
                    "technical": 0.15,
                    "quality": 0.15,
                    "size": 0.05
                },
                aggregation_method="weighted_sum"
            ),

            "defensive": AggregationProfile(
                name="defensive",
                description="Defensive profile prioritizing low volatility and quality",
                factor_weights={
                    "momentum": 0.05,
                    "trend": 0.05,
                    "vola": 0.25,  # Inverted - low vola preferred
                    "sent": 0.10,
                    "fundamentals": 0.20,
                    "technical": 0.10,
                    "quality": 0.20,
                    "size": 0.05
                },
                aggregation_method="weighted_sum"
            )

        }

    def _initialize_mappings(self):
        """Initialize factor name mappings"""

        # Map Neural Engine factor columns to weighting keys
        self.factor_mappings = {
            "momentum_z": "momentum",
            "trend_z": "trend",
            "vola_z": "vola",
            "sentiment_z": "sent",
            "fundamentals_z": "fundamentals",
            "technical_z": "technical",
            "quality_z": "quality",
            "size_z": "size",

            # Alternative naming conventions
            "momentum_score": "momentum",
            "trend_score": "trend",
            "volatility_score": "vola",
            "sentiment_score": "sent",
            "fundamental_score": "fundamentals",
            "technical_score": "technical",
            "quality_score": "quality",
            "size_score": "size"
        }

    def get_aggregation_profiles(self) -> Dict[str, AggregationProfile]:
        """Get all available aggregation profiles for finance domain"""
        return self.profiles

    def get_factor_mappings(self) -> Dict[str, str]:
        """Get factor name mappings for finance domain"""
        return self.factor_mappings

    def calculate_contribution(self, factor_value: float, weight: float,
                             profile: AggregationProfile) -> float:
        """
        Calculate contribution using z-score × weight formula

        Args:
            factor_value: Z-score or normalized factor value
            weight: Weight for this factor
            profile: Aggregation profile (unused in basic calculation)

        Returns:
            Contribution to composite score
        """
        return factor_value * weight

    def validate_factors(self, factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate and preprocess financial factors

        Args:
            factors: Raw factor dictionary

        Returns:
            Dict with validation results and cleaned factors
        """
        cleaned_factors = {}
        validation_issues = []

        for factor_name, value in factors.items():
            # Skip null/nan values
            if value is None or (isinstance(value, float) and np.isnan(value)):
                validation_issues.append(f"Skipped null/nan value for {factor_name}")
                continue

            # Validate reasonable z-score range (-5 to +5 is typical)
            if abs(value) > 10:
                validation_issues.append(f"Unusual value {value} for {factor_name} (expected z-score range)")
                # Still include but log warning

            cleaned_factors[factor_name] = value

        return {
            "cleaned_factors": cleaned_factors,
            "validation_issues": validation_issues,
            "factors_count": len(cleaned_factors),
            "total_input_factors": len(factors)
        }

    def format_attribution_explanation(self, contributions: Dict[str, float],
                                     primary_driver: str, composite_score: float) -> Dict[str, str]:
        """
        Generate finance-specific attribution explanations

        Args:
            contributions: Factor contributions to composite score
            primary_driver: Name of the most important factor
            composite_score: Final composite score

        Returns:
            Dict with explanation levels
        """
        # Calculate percentages
        total_contribution = sum(abs(c) for c in contributions.values())
        if total_contribution == 0:
            percentages = {k: 0.0 for k in contributions.keys()}
        else:
            percentages = {k: abs(v) / total_contribution * 100 for k, v in contributions.items()}

        # Sort by contribution magnitude
        sorted_factors = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        top_factors = sorted_factors[:3]  # Top 3 drivers

        # Summary explanation
        if primary_driver and primary_driver in contributions:
            primary_pct = percentages.get(primary_driver, 0)
            summary = f"Composite score {composite_score:.2f} driven by {primary_driver} ({primary_pct:.1f}%)"
        else:
            summary = f"Composite score {composite_score:.2f} with mixed factor contributions"

        # Technical explanation with breakdown
        technical_parts = []
        for factor, contribution in top_factors:
            pct = percentages.get(factor, 0)
            technical_parts.append(f"{factor}: {contribution:+.3f} ({pct:.1f}%)")

        technical = f"Top factor contributions: {', '.join(technical_parts)}"

        # Detailed explanation
        detailed_parts = [f"Composite Score: {composite_score:.3f}"]
        detailed_parts.append("Factor Contributions:")
        for factor, contribution in sorted_factors:
            pct = percentages.get(factor, 0)
            detailed_parts.append(f"  • {factor}: {contribution:+.3f} contribution ({pct:.1f}% of total)")

        detailed = "\n".join(detailed_parts)

        return {
            'summary': summary,
            'technical': technical,
            'detailed': detailed
        }