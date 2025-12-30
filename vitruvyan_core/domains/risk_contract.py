"""
Vitruvyan Core — Risk Assessment Contract
==========================================

Abstract interface for domain-specific risk assessment providers.

This contract allows ANY domain to define:
1. Risk Dimensions — What constitutes risk in this domain?
2. Risk Profiles — How to combine risk dimensions?
3. Risk Calculations — Domain-specific risk computation logic

Domains implement RiskProvider to customize VARE Engine calculations
without changing core risk assessment logic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: ABSTRACT CONTRACT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Callable
import pandas as pd


@dataclass
class RiskDimension:
    """
    A single dimension of risk assessment.

    Defines how to calculate one aspect of risk for domain entities.
    """
    name: str                    # Risk dimension identifier (e.g., "market_risk")
    description: str             # Human-readable explanation
    calculation_fn: Callable[[pd.DataFrame], float]  # Function to compute risk score
    threshold_low: float         # Below this = low risk
    threshold_moderate: float    # Below this = moderate risk
    threshold_high: float        # Below this = high risk
    # Above high = extreme risk

    unit: str = "score"          # Unit of measurement
    higher_is_riskier: bool = True  # True if higher values = more risk


@dataclass
class RiskProfile:
    """
    How to combine multiple risk dimensions into overall risk assessment.

    Defines weighting scheme for aggregating risk dimensions.
    """
    name: str                    # Profile identifier
    description: str             # Human-readable explanation
    dimension_weights: Dict[str, float]  # {"dimension1": 0.3, "dimension2": 0.7}
    aggregation_method: str = "weighted_average"  # How to combine dimensions


class RiskProvider(ABC):
    """
    Interface that domains implement to provide risk assessment context.

    VARE Engine calls these methods to perform domain-appropriate risk analysis.
    """

    @abstractmethod
    def get_risk_dimensions(self) -> List[RiskDimension]:
        """
        Define what risk dimensions exist in this domain.

        Returns list of RiskDimension objects that define how to calculate
        different aspects of risk for domain entities.

        Examples:
        - Finance: market_risk, volatility_risk, liquidity_risk
        - Logistics: delay_risk, cost_risk, reliability_risk
        - Healthcare: readmission_risk, complication_risk, mortality_risk
        """
        pass

    @abstractmethod
    def get_risk_profiles(self) -> Dict[str, RiskProfile]:
        """
        Define predefined risk weighting schemes.

        Returns mapping of profile_name -> RiskProfile.
        Different profiles can emphasize different risk dimensions.

        Examples:
        - "conservative": High weight on volatility, low on market risk
        - "aggressive": Low weight on all risks
        - "balanced": Equal weights across dimensions
        """
        pass

    @abstractmethod
    def prepare_entity_data(self, entity_id: str, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare raw entity data for risk calculations.

        Convert domain-specific data format into standardized DataFrame
        that risk dimension calculation functions can consume.

        Args:
            entity_id: The entity being analyzed
            raw_data: Raw data from domain (could be dict, list, etc.)

        Returns:
            DataFrame with standardized columns for risk calculations
        """
        pass

    @abstractmethod
    def get_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get domain-specific risk thresholds.

        Returns nested dict: {"LOW": {"min": 0, "max": 25}, "MODERATE": {...}, ...}
        Used for categorizing overall risk levels.
        """
        pass

    @abstractmethod
    def format_risk_explanation(self, dimension_scores: Dict[str, float],
                               overall_risk: float, risk_category: str) -> Dict[str, str]:
        """
        Generate domain-specific risk explanations.

        Args:
            dimension_scores: Risk scores for each dimension
            overall_risk: Composite risk score
            risk_category: Risk category ("LOW", "MODERATE", etc.)

        Returns:
            Dict with explanation levels: {"summary", "technical", "detailed"}
        """
        pass