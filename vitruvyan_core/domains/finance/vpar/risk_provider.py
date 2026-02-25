"""
Finance Domain — Risk Provider (VARE Contract)
================================================

Implements RiskProvider for the finance/trading vertical.
Injects stock-market risk semantics into the domain-agnostic VARE Engine:

- Dimensions: market_risk, volatility_risk, momentum_risk, liquidity_risk
- Profiles: conservative, balanced, aggressive
- Thresholds: Finance-specific risk categorization bands

Metrics consumed: z-scores from Neural Engine (momentum_z, trend_z,
volatility_z, volume_z, etc.) and composite_score.

Author: Vitruvyan Core Team
Created: February 25, 2026
Status: PRODUCTION
"""

import logging
from typing import Dict, Any, List

import numpy as np
import pandas as pd

from domains.risk_contract import (
    RiskProvider,
    RiskDimension,
    RiskProfile,
)

logger = logging.getLogger(__name__)


class FinanceRiskProvider(RiskProvider):
    """
    Finance-domain risk assessment provider for VARE Engine.

    Maps stock-market z-score metrics to multi-dimensional risk profiling.
    """

    # ── Risk Dimensions ──────────────────────────────────────────────────

    def get_risk_dimensions(self) -> List[RiskDimension]:
        return [
            RiskDimension(
                name="market_risk",
                description="Overall market directional risk based on trend and momentum signals",
                calculation_fn=self._calc_market_risk,
                threshold_low=20.0,
                threshold_moderate=45.0,
                threshold_high=70.0,
                unit="score",
                higher_is_riskier=True,
            ),
            RiskDimension(
                name="volatility_risk",
                description="Price volatility risk — higher realized volatility increases uncertainty",
                calculation_fn=self._calc_volatility_risk,
                threshold_low=15.0,
                threshold_moderate=40.0,
                threshold_high=65.0,
                unit="score",
                higher_is_riskier=True,
            ),
            RiskDimension(
                name="momentum_risk",
                description="Risk from momentum extremes — overbought or oversold conditions",
                calculation_fn=self._calc_momentum_risk,
                threshold_low=20.0,
                threshold_moderate=45.0,
                threshold_high=70.0,
                unit="score",
                higher_is_riskier=True,
            ),
            RiskDimension(
                name="liquidity_risk",
                description="Risk from abnormal trading volume — both surges and dry-ups",
                calculation_fn=self._calc_liquidity_risk,
                threshold_low=15.0,
                threshold_moderate=35.0,
                threshold_high=60.0,
                unit="score",
                higher_is_riskier=True,
            ),
        ]

    # ── Risk Profiles ────────────────────────────────────────────────────

    def get_risk_profiles(self) -> Dict[str, RiskProfile]:
        return {
            "conservative": RiskProfile(
                name="conservative",
                description="Capital preservation — high sensitivity to volatility and drawdown risk",
                dimension_weights={
                    "market_risk": 0.20,
                    "volatility_risk": 0.40,
                    "momentum_risk": 0.15,
                    "liquidity_risk": 0.25,
                },
            ),
            "balanced": RiskProfile(
                name="balanced",
                description="Balanced risk weighting — equal consideration of all dimensions",
                dimension_weights={
                    "market_risk": 0.30,
                    "volatility_risk": 0.25,
                    "momentum_risk": 0.25,
                    "liquidity_risk": 0.20,
                },
            ),
            "aggressive": RiskProfile(
                name="aggressive",
                description="Growth-oriented — tolerant of volatility, focused on market direction",
                dimension_weights={
                    "market_risk": 0.40,
                    "volatility_risk": 0.15,
                    "momentum_risk": 0.30,
                    "liquidity_risk": 0.15,
                },
            ),
        }

    # ── Data Preparation ─────────────────────────────────────────────────

    def prepare_entity_data(self, entity_id: str, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert z-score dict to DataFrame for dimension calculations.

        Expects raw_data keys like: momentum_z, trend_z, volatility_z, volume_z,
        rsi_z, macd_z, composite_score, etc.
        """
        # Flatten to single-row DataFrame (VARE dimensions operate row-wise)
        metrics = {}
        for key, value in raw_data.items():
            try:
                metrics[key] = float(value)
            except (TypeError, ValueError):
                continue

        if not metrics:
            logger.warning(f"[FinanceRiskProvider] No numeric metrics for {entity_id}")
            return pd.DataFrame({"_empty": [0.0]})

        return pd.DataFrame([metrics])

    # ── Thresholds ───────────────────────────────────────────────────────

    def get_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
        return {
            "LOW": {"min": 0.0, "max": 25.0},
            "MODERATE": {"min": 25.0, "max": 50.0},
            "HIGH": {"min": 50.0, "max": 75.0},
            "EXTREME": {"min": 75.0, "max": 100.0},
        }

    # ── Risk Explanations ────────────────────────────────────────────────

    def format_risk_explanation(
        self,
        dimension_scores: Dict[str, float],
        overall_risk: float,
        risk_category: str,
    ) -> Dict[str, str]:
        # Sort dimensions by score descending for narrative
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_dims[0] if sorted_dims else ("unknown", 0.0)
        secondary = sorted_dims[1:3]

        # Labels
        dim_labels = {
            "market_risk": "Market direction risk",
            "volatility_risk": "Volatility risk",
            "momentum_risk": "Momentum extreme risk",
            "liquidity_risk": "Liquidity risk",
        }

        primary_label = dim_labels.get(primary[0], primary[0])
        secondary_text = ", ".join(
            f"{dim_labels.get(d, d)} ({s:.0f}/100)" for d, s in secondary
        )

        summary = (
            f"Overall risk: {risk_category} ({overall_risk:.0f}/100). "
            f"Primary concern: {primary_label} ({primary[1]:.0f}/100)."
        )

        technical = (
            f"Risk profile: {risk_category} (composite={overall_risk:.1f}). "
            f"Breakdown: " +
            ", ".join(f"{dim_labels.get(d, d)}={s:.1f}" for d, s in sorted_dims) +
            "."
        )

        detailed = (
            f"Multi-dimensional risk assessment: {risk_category} ({overall_risk:.1f}/100).\n"
            f"Primary risk driver: {primary_label} at {primary[1]:.0f}/100.\n"
        )
        if secondary_text:
            detailed += f"Secondary factors: {secondary_text}.\n"
        detailed += (
            f"{'This indicates elevated risk requiring attention.' if overall_risk > 50 else 'Risk levels are within acceptable parameters.'}"
        )

        return {
            "summary": summary,
            "technical": technical,
            "detailed": detailed,
        }

    # ── Dimension Calculation Functions ───────────────────────────────────
    # Each receives a single-row DataFrame of z-scores and returns a
    # raw risk value (higher = riskier, before normalization).

    @staticmethod
    def _calc_market_risk(df: pd.DataFrame) -> float:
        """Market risk from trend weakness / negative momentum.

        Strong positive trend = low market risk; weak/negative = high risk.
        """
        trend_z = df.iloc[0].get("trend_z", 0.0) if "trend_z" in df.columns else 0.0
        momentum_z = df.iloc[0].get("momentum_z", 0.0) if "momentum_z" in df.columns else 0.0
        # Invert: positive trend/momentum → low risk
        # Scale from z-score (-3,+3) to risk (0, ~100)
        market_signal = (trend_z * 0.6 + momentum_z * 0.4)
        # Transform: positive = safe, negative = risky
        risk = 50.0 - (market_signal * 20.0)
        return float(np.clip(risk, 0.0, 100.0))

    @staticmethod
    def _calc_volatility_risk(df: pd.DataFrame) -> float:
        """Volatility risk from realized volatility z-score.

        Higher volatility_z = higher risk.
        """
        vol_z = df.iloc[0].get("volatility_z", 0.0) if "volatility_z" in df.columns else 0.0
        # Direct mapping: vol_z of +2 → ~90 risk, vol_z of -1 → ~30 risk
        risk = 50.0 + (vol_z * 20.0)
        return float(np.clip(risk, 0.0, 100.0))

    @staticmethod
    def _calc_momentum_risk(df: pd.DataFrame) -> float:
        """Risk from momentum extremes (overbought/oversold).

        Very high or very low momentum_z increases risk (reversal probability).
        """
        momentum_z = df.iloc[0].get("momentum_z", 0.0) if "momentum_z" in df.columns else 0.0
        rsi_z = df.iloc[0].get("rsi_z", 0.0) if "rsi_z" in df.columns else 0.0
        # Extreme in either direction = risk
        extreme = (abs(momentum_z) * 0.6 + abs(rsi_z) * 0.4)
        risk = extreme * 30.0  # z=2 → 60 risk
        return float(np.clip(risk, 0.0, 100.0))

    @staticmethod
    def _calc_liquidity_risk(df: pd.DataFrame) -> float:
        """Liquidity risk from volume anomalies.

        Both very low volume (illiquidity) and very high volume (panic) are risky.
        """
        volume_z = df.iloc[0].get("volume_z", 0.0) if "volume_z" in df.columns else 0.0
        # Deviation from normal volume = risk
        risk = abs(volume_z) * 25.0  # z=2 → 50 risk
        return float(np.clip(risk, 0.0, 100.0))
