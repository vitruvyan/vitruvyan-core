"""
Finance Domain — Aggregation Provider (VWRE Contract)
======================================================

Implements AggregationProvider for the finance/trading vertical.
Injects stock-market attribution semantics into the domain-agnostic VWRE Engine:

- Factor Mappings: momentum_z → momentum, trend_z → trend, etc.
- Profiles: short_spec, balanced_mid, long_quality, momentum_pure
- Contribution: weighted z-score attribution

Decomposes a composite_score into factor contributions so the system can
answer: "Why does AAPL rank higher than MSFT?"

Author: Vitruvyan Core Team
Created: February 25, 2026
Status: PRODUCTION
"""

import logging
from typing import Dict, Any, List

from domains.aggregation_contract import (
    AggregationProvider,
    AggregationProfile,
)

logger = logging.getLogger(__name__)


class FinanceAggregationProvider(AggregationProvider):
    """
    Finance-domain aggregation provider for VWRE Engine.

    Maps z-score factors to weighted composite score attribution.
    Supports multiple investment-style profiles.
    """

    # ── Aggregation Profiles ─────────────────────────────────────────────

    def get_aggregation_profiles(self) -> Dict[str, AggregationProfile]:
        return {
            "short_spec": AggregationProfile(
                name="short_spec",
                description="Short-term speculative — momentum and volatility dominant",
                factor_weights={
                    "momentum": 0.25,
                    "trend": 0.15,
                    "volatility": 0.20,
                    "volume": 0.10,
                    "sentiment": 0.08,
                    "revenue_growth_yoy": 0.05,
                    "eps_growth_yoy": 0.05,
                    "net_margin": 0.04,
                    "debt_to_equity_inv": 0.03,
                    "free_cash_flow": 0.05,
                },
            ),
            "balanced_mid": AggregationProfile(
                name="balanced_mid",
                description="Balanced medium-term — equal weight to momentum, trend, volatility + fundamentals",
                factor_weights={
                    "momentum": 0.15,
                    "trend": 0.20,
                    "volatility": 0.12,
                    "volume": 0.10,
                    "sentiment": 0.10,
                    "revenue_growth_yoy": 0.05,
                    "eps_growth_yoy": 0.05,
                    "net_margin": 0.05,
                    "debt_to_equity_inv": 0.04,
                    "free_cash_flow": 0.05,
                    "dividend_yield": 0.04,
                },
            ),
            "long_quality": AggregationProfile(
                name="long_quality",
                description="Long-term quality — trend strength, low volatility, strong fundamentals",
                factor_weights={
                    "momentum": 0.10,
                    "trend": 0.15,
                    "volatility": 0.10,
                    "volume": 0.05,
                    "sentiment": 0.08,
                    "revenue_growth_yoy": 0.08,
                    "eps_growth_yoy": 0.08,
                    "net_margin": 0.10,
                    "debt_to_equity_inv": 0.10,
                    "free_cash_flow": 0.10,
                    "dividend_yield": 0.06,
                },
            ),
            "momentum_pure": AggregationProfile(
                name="momentum_pure",
                description="Pure momentum strategy — almost all weight on price momentum",
                factor_weights={
                    "momentum": 0.40,
                    "trend": 0.15,
                    "volatility": 0.10,
                    "volume": 0.10,
                    "sentiment": 0.05,
                    "revenue_growth_yoy": 0.04,
                    "eps_growth_yoy": 0.04,
                    "net_margin": 0.03,
                    "debt_to_equity_inv": 0.03,
                    "free_cash_flow": 0.04,
                    "dividend_yield": 0.02,
                },
            ),
            # Default fallback
            "balanced": AggregationProfile(
                name="balanced",
                description="Default balanced profile",
                factor_weights={
                    "momentum": 0.15,
                    "trend": 0.20,
                    "volatility": 0.12,
                    "volume": 0.10,
                    "sentiment": 0.10,
                    "revenue_growth_yoy": 0.05,
                    "eps_growth_yoy": 0.05,
                    "net_margin": 0.05,
                    "debt_to_equity_inv": 0.04,
                    "free_cash_flow": 0.05,
                    "dividend_yield": 0.04,
                },
            ),
        }

    # ── Factor Mappings ──────────────────────────────────────────────────

    def get_factor_mappings(self) -> Dict[str, str]:
        """Map raw Neural Engine z-score keys to weight profile keys."""
        return {
            # Technical z-scores
            "momentum_z": "momentum",
            "trend_z": "trend",
            "volatility_z": "volatility",
            "volume_z": "volume",
            "sentiment_z": "sentiment",
            # Technical aliases (some pipelines use different naming)
            "rsi_z": "momentum",         # RSI feeds into momentum bucket
            "macd_z": "momentum",        # MACD feeds into momentum bucket
            "sma_z": "trend",            # SMA alignment → trend
            "ema_z": "trend",            # EMA alignment → trend
            "atr_z": "volatility",       # ATR → volatility bucket
            "bb_width_z": "volatility",  # Bollinger Band width → volatility
            "obv_z": "volume",           # OBV → volume bucket
            # Fundamentals z-scores (direct mapping — names match NE ScoringStrategy)
            "revenue_growth_yoy_z": "revenue_growth_yoy",
            "eps_growth_yoy_z": "eps_growth_yoy",
            "net_margin_z": "net_margin",
            "debt_to_equity_inv_z": "debt_to_equity_inv",
            "free_cash_flow_z": "free_cash_flow",
            "dividend_yield_z": "dividend_yield",
        }

    # ── Contribution Calculation ─────────────────────────────────────────

    def calculate_contribution(
        self,
        factor_value: float,
        weight: float,
        profile: AggregationProfile,
    ) -> float:
        """Standard weighted contribution: z-score × weight.

        For finance z-scores this gives attribution in the same unit
        as composite_score (which is itself a weighted sum of z-scores).
        """
        return factor_value * weight

    # ── Factor Validation ────────────────────────────────────────────────

    def validate_factors(self, factors: Dict[str, float]) -> Dict[str, Any]:
        """Validate and clean z-score factors.

        - Clips extreme z-scores to [-5, +5] (numerical stability)
        - Warns on missing key factors
        - Returns cleaned factors + validation metadata
        """
        cleaned = {}
        warnings: List[str] = []
        clipped_count = 0

        for key, value in factors.items():
            if value is None:
                warnings.append(f"Factor '{key}' is None, skipped")
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                warnings.append(f"Factor '{key}' not numeric: {value}")
                continue

            # Clip extreme z-scores
            if abs(v) > 5.0:
                v = max(-5.0, min(5.0, v))
                clipped_count += 1

            cleaned[key] = v

        # Check for essential factors (technical OR fundamentals must be present)
        technical = {"momentum_z", "trend_z", "volatility_z"}
        fundamentals = {"revenue_growth_yoy_z", "eps_growth_yoy_z", "net_margin_z"}
        has_technical = bool(technical & set(cleaned.keys()))
        has_fundamentals = bool(fundamentals & set(cleaned.keys()))
        missing = []
        if not has_technical and not has_fundamentals:
            missing = list(technical | fundamentals)
            warnings.append(f"Missing essential factors: no technical or fundamentals z-scores found")

        return {
            "cleaned_factors": cleaned,
            "valid": len(cleaned) > 0,
            "factor_count": len(cleaned),
            "missing_essential": list(missing) if missing else [],
            "clipped_count": clipped_count,
            "warnings": warnings,
        }

    # ── Attribution Explanations ─────────────────────────────────────────

    def format_attribution_explanation(
        self,
        contributions: Dict[str, float],
        primary_driver: str,
        composite_score: float,
    ) -> Dict[str, str]:
        """Finance-specific attribution narratives."""
        # Sort by absolute contribution
        sorted_factors = sorted(
            contributions.items(), key=lambda x: abs(x[1]), reverse=True
        )

        factor_labels = {
            "momentum": "Price momentum",
            "trend": "Trend strength",
            "volatility": "Volatility profile",
            "volume": "Trading volume",
            "sentiment": "Market sentiment",
            "revenue_growth_yoy": "Revenue growth",
            "eps_growth_yoy": "EPS growth",
            "net_margin": "Net margin",
            "debt_to_equity_inv": "Financial health (low debt)",
            "free_cash_flow": "Free cash flow",
            "dividend_yield": "Dividend yield",
        }

        primary_label = factor_labels.get(primary_driver, primary_driver)
        primary_contrib = contributions.get(primary_driver, 0.0)
        direction = "positive" if primary_contrib > 0 else "negative"

        summary = (
            f"Composite score {composite_score:.3f} driven primarily by "
            f"{primary_label} ({direction}, {primary_contrib:+.3f} contribution)."
        )

        # Technical: full factor breakdown
        parts = []
        for factor, contrib in sorted_factors:
            label = factor_labels.get(factor, factor)
            pct = (contrib / composite_score * 100.0) if composite_score != 0 else 0.0
            parts.append(f"{label}: {contrib:+.3f} ({pct:+.1f}%)")
        technical = f"Attribution breakdown: {'; '.join(parts)}."

        # Detailed
        detailed = f"Score decomposition for composite={composite_score:.3f}:\n"
        for factor, contrib in sorted_factors:
            label = factor_labels.get(factor, factor)
            bar_len = int(min(abs(contrib) * 20, 30))
            bar = "█" * bar_len
            detailed += f"  {label:20s}: {contrib:+.3f} {bar}\n"
        residual = composite_score - sum(contributions.values())
        if abs(residual) > 0.01:
            detailed += f"  {'Residual':20s}: {residual:+.3f}\n"

        return {
            "summary": summary,
            "technical": technical,
            "detailed": detailed,
        }
