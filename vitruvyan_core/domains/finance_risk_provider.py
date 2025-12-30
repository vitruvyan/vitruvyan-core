"""
Vitruvyan Core — Finance Risk Provider
=======================================

Concrete implementation of RiskProvider for financial markets.

Provides finance-specific:
1. Risk Dimensions (market, volatility, liquidity, correlation)
2. Risk Profiles (conservative, balanced, aggressive)
3. Risk Calculations (technical analysis based)

This allows VARE Engine to assess financial risk without hardcoded logic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: FINANCE DOMAIN IMPLEMENTATION
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from vitruvyan_core.domains.risk_contract import RiskProvider, RiskDimension, RiskProfile


class FinanceRiskProvider(RiskProvider):
    """
    Finance-specific risk assessment provider.

    Implements RiskProvider for financial markets with:
    - Market risk (beta, correlation to market)
    - Volatility risk (price swings, VIX correlation)
    - Liquidity risk (trading volume, bid-ask spread)
    - Correlation risk (sector, asset class correlations)
    """

    def __init__(self):
        super().__init__()
        self._initialize_risk_dimensions()
        self._initialize_risk_profiles()

    def _initialize_risk_dimensions(self):
        """Initialize finance-specific risk dimensions"""

        self.risk_dimensions = {

            "market_risk": RiskDimension(
                name="market_risk",
                description="Risk of adverse market movements affecting the asset",
                calculation_fn=self._calculate_market_risk,
                threshold_low=25.0,
                threshold_moderate=50.0,
                threshold_high=75.0,
                unit="score",
                higher_is_riskier=True
            ),

            "volatility_risk": RiskDimension(
                name="volatility_risk",
                description="Risk of significant price fluctuations",
                calculation_fn=self._calculate_volatility_risk,
                threshold_low=30.0,
                threshold_moderate=55.0,
                threshold_high=80.0,
                unit="score",
                higher_is_riskier=True
            ),

            "liquidity_risk": RiskDimension(
                name="liquidity_risk",
                description="Risk of inability to buy/sell without significant price impact",
                calculation_fn=self._calculate_liquidity_risk,
                threshold_low=20.0,
                threshold_moderate=45.0,
                threshold_high=70.0,
                unit="score",
                higher_is_riskier=True
            ),

            "correlation_risk": RiskDimension(
                name="correlation_risk",
                description="Risk from correlated movements with other assets",
                calculation_fn=self._calculate_correlation_risk,
                threshold_low=35.0,
                threshold_moderate=60.0,
                threshold_high=85.0,
                unit="score",
                higher_is_riskier=True
            )

        }

    def _initialize_risk_profiles(self):
        """Initialize finance-specific risk profiles"""

        self.risk_profiles = {

            "conservative": RiskProfile(
                name="conservative",
                description="Low-risk profile prioritizing stability over returns",
                dimension_weights={
                    "market_risk": 0.4,
                    "volatility_risk": 0.3,
                    "liquidity_risk": 0.2,
                    "correlation_risk": 0.1
                },
                aggregation_method="weighted_average"
            ),

            "balanced": RiskProfile(
                name="balanced",
                description="Moderate risk profile balancing stability and returns",
                dimension_weights={
                    "market_risk": 0.3,
                    "volatility_risk": 0.25,
                    "liquidity_risk": 0.25,
                    "correlation_risk": 0.2
                },
                aggregation_method="weighted_average"
            ),

            "aggressive": RiskProfile(
                name="aggressive",
                description="High-risk profile accepting volatility for potential returns",
                dimension_weights={
                    "market_risk": 0.2,
                    "volatility_risk": 0.2,
                    "liquidity_risk": 0.3,
                    "correlation_risk": 0.3
                },
                aggregation_method="weighted_average"
            )

        }

    def get_risk_dimensions(self) -> List[RiskDimension]:
        """Get all available risk dimensions for finance domain"""
        return list(self.risk_dimensions.values())

    def get_risk_profiles(self) -> Dict[str, RiskProfile]:
        """Get all available risk profiles for finance domain"""
        return self.risk_profiles

    def prepare_entity_data(self, entity_id: str, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare raw financial data for risk calculations.

        Args:
            entity_id: Financial instrument identifier
            raw_data: Raw data (expected to be dict with OHLCV data)

        Returns:
            DataFrame with standardized columns for risk calculations
        """
        try:
            # If raw_data is already a DataFrame, use it
            if isinstance(raw_data, pd.DataFrame):
                return raw_data

            # If raw_data is a dict, try to convert it
            if isinstance(raw_data, dict):
                # Assume it's OHLCV data
                df = pd.DataFrame(raw_data)
                return df

            # Fallback: create empty DataFrame
            return pd.DataFrame()

        except Exception as e:
            # Return empty DataFrame on error
            return pd.DataFrame()
        """
        Get finance-specific context for risk assessment

        Args:
            entity_id: Financial instrument identifier (ticker)

        Returns:
            Context data for risk calculations
        """
        # In a real implementation, this would fetch market data
        # For now, return placeholder context
        return {
            "entity_type": "equity",
            "market": "US",
            "sector": "unknown",  # Would be determined from data
            "market_cap_category": "unknown",
            "liquidity_category": "unknown"
        }

    def get_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get finance-specific risk thresholds.

        Returns:
            Nested dict with risk category thresholds
        """
        return {
            "LOW": {"min": 0.0, "max": 25.0},
            "MODERATE": {"min": 25.0, "max": 50.0},
            "HIGH": {"min": 50.0, "max": 75.0},
            "EXTREME": {"min": 75.0, "max": 100.0}
        }

    def format_risk_explanation(self, dimension_scores: Dict[str, float],
                               overall_risk: float, risk_category: str) -> Dict[str, str]:
        """
        Generate finance-specific risk explanations.

        Args:
            dimension_scores: Risk scores for each dimension
            overall_risk: Composite risk score
            risk_category: Risk category ("LOW", "MODERATE", etc.)

        Returns:
            Dict with explanation levels: {"summary", "technical", "detailed"}
        """
        # Summary explanation
        summary = f"Risk assessment: {risk_category} overall risk ({overall_risk:.1f}/100)"

        # Technical explanation with dimension breakdown
        technical_parts = []
        for dim_name, score in dimension_scores.items():
            explanation = self._format_single_dimension(dim_name, score)
            technical_parts.append(f"• {explanation}")

        technical = "Risk dimensions:\n" + "\n".join(technical_parts)

        # Detailed explanation
        detailed = f"""
Comprehensive risk analysis:

Overall Risk Score: {overall_risk:.1f}/100
Risk Category: {risk_category}

Dimension Breakdown:
{chr(10).join(f"- {dim}: {score:.1f}/100" for dim, score in dimension_scores.items())}

This assessment provides quantitative risk metrics for investment decision support.
All scores are normalized to 0-100 scale where higher values indicate higher risk.
"""

        return {
            'summary': summary.strip(),
            'technical': technical.strip(),
            'detailed': detailed.strip()
        }

    def _format_single_dimension(self, dimension_name: str, score: float) -> str:
        """Format explanation for a single risk dimension"""
        dimension = self.risk_dimensions.get(dimension_name)
        if not dimension:
            return f"{dimension_name}: {score:.1f}/100"

        # Determine risk level
        if score <= dimension.threshold_low:
            level = "LOW"
        elif score <= dimension.threshold_moderate:
            level = "MODERATE"
        elif score <= dimension.threshold_high:
            level = "HIGH"
        else:
            level = "EXTREME"

        return f"{dimension.description}: {level} risk ({score:.1f}/100)"

    # Risk calculation methods

    def _calculate_market_risk(self, data: pd.DataFrame) -> float:
        """
        Calculate market risk based on beta and market correlation

        Args:
            data: DataFrame with price data and market data

        Returns:
            Market risk score (0-100)
        """
        try:
            # Simplified market risk calculation
            # In real implementation, would calculate beta vs market index

            if 'close' not in data.columns:
                return 50.0  # Neutral risk if no data

            # Use price volatility as proxy for market risk
            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized

            # Convert to 0-100 scale
            risk_score = min(100.0, volatility * 1000)  # Rough scaling

            return risk_score

        except Exception:
            return 50.0  # Neutral risk on error

    def _calculate_volatility_risk(self, data: pd.DataFrame) -> float:
        """
        Calculate volatility risk based on price fluctuations

        Args:
            data: DataFrame with price data

        Returns:
            Volatility risk score (0-100)
        """
        try:
            if 'close' not in data.columns:
                return 50.0

            returns = data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)

            # Convert to 0-100 scale
            risk_score = min(100.0, volatility * 2000)  # Higher multiplier for volatility

            return risk_score

        except Exception:
            return 50.0

    def _calculate_liquidity_risk(self, data: pd.DataFrame) -> float:
        """
        Calculate liquidity risk based on volume and spread

        Args:
            data: DataFrame with volume and price data

        Returns:
            Liquidity risk score (0-100)
        """
        try:
            if 'volume' not in data.columns or 'close' not in data.columns:
                return 50.0

            # Use average volume as liquidity proxy
            avg_volume = data['volume'].mean()

            # Lower volume = higher liquidity risk
            # This is simplified - real implementation would use bid-ask spread
            if avg_volume > 1000000:  # High volume
                risk_score = 20.0
            elif avg_volume > 100000:  # Medium volume
                risk_score = 50.0
            else:  # Low volume
                risk_score = 80.0

            return risk_score

        except Exception:
            return 50.0

    def _calculate_correlation_risk(self, data: pd.DataFrame) -> float:
        """
        Calculate correlation risk with market/other assets

        Args:
            data: DataFrame with price data

        Returns:
            Correlation risk score (0-100)
        """
        try:
            # Simplified correlation calculation
            # In real implementation, would correlate with market index

            if 'close' not in data.columns:
                return 50.0

            # Use autocorrelation as proxy for correlation risk
            returns = data['close'].pct_change().dropna()
            autocorr = abs(returns.autocorr(lag=1)) if len(returns) > 1 else 0.5

            # Higher autocorrelation = higher correlation risk
            risk_score = autocorr * 100

            return risk_score

        except Exception:
            return 50.0