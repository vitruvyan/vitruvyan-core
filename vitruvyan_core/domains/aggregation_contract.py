"""
Vitruvyan Core — Aggregation Contract
======================================

Abstract interface for domain-specific aggregation/weighting providers.

This contract allows ANY domain to define:
1. Aggregation Profiles — How to weight different factors
2. Factor Mappings — How raw factors map to weighting keys
3. Contribution Calculations — Domain-specific attribution logic

Domains implement AggregationProvider to customize VWRE Engine calculations
without changing core attribution logic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: ABSTRACT CONTRACT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd


@dataclass
class AggregationProfile:
    """
    A weighting profile for aggregating factors into composite scores.

    Defines how different factors contribute to the overall score.
    """
    name: str                    # Profile identifier (e.g., "short_spec", "balanced")
    description: str             # Human-readable explanation
    factor_weights: Dict[str, float]  # {"momentum": 0.35, "trend": 0.15, ...}
    aggregation_method: str = "weighted_sum"  # How to combine factors


class AggregationProvider(ABC):
    """
    Interface that domains implement to provide aggregation/weighting context.

    VWRE Engine calls these methods to perform domain-appropriate attribution analysis.
    """

    @abstractmethod
    def get_aggregation_profiles(self) -> Dict[str, AggregationProfile]:
        """
        Define predefined aggregation profiles for the domain.

        Returns mapping of profile_name -> AggregationProfile.
        Different profiles can emphasize different factors.

        Examples:
        - Finance: "short_spec" (momentum heavy), "balanced_mid" (equal weights)
        - Healthcare: "acute_care" (symptoms heavy), "preventive" (risk factors heavy)
        """
        pass

    @abstractmethod
    def get_factor_mappings(self) -> Dict[str, str]:
        """
        Define how raw factor names map to weighting keys.

        Returns mapping of raw_factor_name -> weight_key.
        Allows domains to use different naming conventions.

        Examples:
        - Finance: {"momentum_z": "momentum", "trend_z": "trend"}
        - Healthcare: {"symptoms_score": "acute", "risk_factors": "preventive"}
        """
        pass

    @abstractmethod
    def calculate_contribution(self, factor_value: float, weight: float,
                             profile: AggregationProfile) -> float:
        """
        Calculate contribution of a single factor to composite score.

        Args:
            factor_value: Raw factor value (z-score, normalized score, etc.)
            weight: Weight for this factor in the profile
            profile: The aggregation profile being used

        Returns:
            Contribution value (typically factor_value × weight)
        """
        pass

    @abstractmethod
    def validate_factors(self, factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate and preprocess factors before attribution analysis.

        Args:
            factors: Raw factor dictionary

        Returns:
            Dict with validation results and cleaned factors
        """
        pass

    @abstractmethod
    def format_attribution_explanation(self, contributions: Dict[str, float],
                                     primary_driver: str, composite_score: float) -> Dict[str, str]:
        """
        Generate domain-specific attribution explanations.

        Args:
            contributions: Factor contributions to composite score
            primary_driver: Name of the most important factor
            composite_score: Final composite score

        Returns:
            Dict with explanation levels: {"summary", "technical", "detailed"}
        """
        pass
