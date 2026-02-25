"""
Financial Scoring Strategy
==========================

Finance-specific profile weights and risk adjustment logic for Neural Engine.
Ported from legacy Vitruvyan Neural Engine monolith into contract-based strategy.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from vitruvyan_core.contracts import IScoringStrategy

logger = logging.getLogger(__name__)


class FinancialScoringStrategy(IScoringStrategy):
    """
    Finance implementation of IScoringStrategy.

    Canonical profiles mirror legacy finance profiles from the monolith:
    - short_spec
    - balanced_mid
    - trend_follow
    - momentum_focus
    - sentiment_boost
    - low_risk
    """

    PROFILE_ALIASES: Dict[str, str] = {
        # Keep compatibility with agnostic profile names used in some tools/tests.
        "balanced": "balanced_mid",
        "aggressive": "momentum_focus",
        "conservative": "low_risk",
    }

    # NOTE:
    # Keys are RAW feature names (not z-score columns). CompositeScorer maps
    # feature_name -> feature_name_z internally.
    PROFILE_WEIGHTS: Dict[str, Dict[str, float]] = {
        "short_spec": {
            "momentum": 0.12,
            "trend": 0.35,
            "volatility": 0.10,
            "sentiment": 0.08,
            "growth": 0.04,
            "quality": 0.04,
            "revenue_growth_yoy": 0.05,
            "eps_growth_yoy": 0.05,
            "net_margin": 0.04,
            "debt_to_equity_inv": 0.03,
            "free_cash_flow": 0.05,
            "dividend_yield": 0.01,
            "interest_rate": 0.04,
        },
        "balanced_mid": {
            "momentum": 0.15,
            "trend": 0.20,
            "volatility": 0.12,
            "sentiment": 0.10,
            "value": 0.05,
            "growth": 0.05,
            "quality": 0.05,
            "revenue_growth_yoy": 0.05,
            "eps_growth_yoy": 0.05,
            "net_margin": 0.05,
            "debt_to_equity_inv": 0.04,
            "free_cash_flow": 0.05,
            "dividend_yield": 0.04,
            "inflation_rate": 0.05,
        },
        "trend_follow": {
            "momentum": 0.10,
            "trend": 0.35,
            "volatility": 0.12,
            "sentiment": 0.08,
            "growth": 0.05,
            "quality": 0.05,
            "revenue_growth_yoy": 0.04,
            "eps_growth_yoy": 0.04,
            "net_margin": 0.04,
            "debt_to_equity_inv": 0.04,
            "free_cash_flow": 0.04,
            "dividend_yield": 0.02,
            "interest_rate": 0.08,
        },
        "momentum_focus": {
            "momentum": 0.35,
            "trend": 0.15,
            "volatility": 0.08,
            "sentiment": 0.10,
            "academic_momentum": 0.08,
            "revenue_growth_yoy": 0.04,
            "eps_growth_yoy": 0.04,
            "net_margin": 0.03,
            "debt_to_equity_inv": 0.03,
            "free_cash_flow": 0.04,
            "dividend_yield": 0.01,
            "market_volatility": 0.05,
        },
        "sentiment_boost": {
            "momentum": 0.10,
            "trend": 0.10,
            "volatility": 0.10,
            "sentiment": 0.25,
            "growth": 0.08,
            "revenue_growth_yoy": 0.05,
            "eps_growth_yoy": 0.05,
            "net_margin": 0.05,
            "debt_to_equity_inv": 0.04,
            "free_cash_flow": 0.05,
            "dividend_yield": 0.03,
            "inflation_rate": 0.05,
            "interest_rate": 0.05,
        },
        "low_risk": {
            "momentum": 0.05,
            "trend": 0.15,
            "volatility": 0.30,
            "sentiment": 0.05,
            "value": 0.10,
            "growth": 0.05,
            "quality": 0.15,
            "revenue_growth_yoy": 0.03,
            "eps_growth_yoy": 0.03,
            "net_margin": 0.05,
            "debt_to_equity_inv": 0.05,
            "free_cash_flow": 0.02,
            "dividend_yield": 0.02,
            "interest_rate": 0.00,
        },
    }

    PROFILE_METADATA: Dict[str, Dict[str, str]] = {
        "short_spec": {
            "description": "Short-term speculative profile focused on trend acceleration.",
            "use_case": "High-tempo tactical selection.",
        },
        "balanced_mid": {
            "description": "Balanced medium-term profile blending technicals and fundamentals.",
            "use_case": "Default diversified screening.",
        },
        "trend_follow": {
            "description": "Trend-following profile prioritizing persistent trend strength.",
            "use_case": "Momentum continuation with moderate risk control.",
        },
        "momentum_focus": {
            "description": "Aggressive momentum profile with stronger technical weighting.",
            "use_case": "Fast-moving markets and breakouts.",
        },
        "sentiment_boost": {
            "description": "Sentiment-centric profile with macro overlays.",
            "use_case": "Narrative-driven market phases.",
        },
        "low_risk": {
            "description": "Conservative profile emphasizing stability and quality.",
            "use_case": "Risk-sensitive allocation.",
        },
    }

    RISK_PENALTY_MAP: Dict[str, float] = {
        "low": 0.40,
        "medium": 0.20,
        "high": 0.08,
    }

    def get_profile_weights(self, profile: str) -> Dict[str, float]:
        resolved = self._resolve_profile(profile)
        weights = self.PROFILE_WEIGHTS.get(resolved)
        if not weights:
            raise ValueError(f"Profile '{profile}' not found")
        raw = dict(weights)
        total = sum(raw.values())
        if total <= 0:
            raise ValueError(f"Profile '{profile}' has invalid weight sum: {total}")
        if abs(total - 1.0) < 1e-9:
            return raw
        # Normalize legacy profile sets that were historically close to 1.0.
        return {k: (v / total) for k, v in raw.items()}

    def get_available_profiles(self) -> List[str]:
        canonical = set(self.PROFILE_WEIGHTS.keys())
        aliases = set(self.PROFILE_ALIASES.keys())
        return sorted(canonical | aliases)

    def apply_risk_adjustment(
        self,
        df: pd.DataFrame,
        risk_tolerance: Optional[str] = None,
        risk_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Apply VARE-based risk adjustment with volatility fallback.

        Priority 1 (preferred):
            composite_score *= (1 - vare_risk_score/100 * penalty)

        Priority 2 (fallback when VARE score is missing):
            composite_score /= (1 + abs(volatility_z) * penalty)
        """
        _ = risk_columns  # reserved for future use

        if risk_tolerance is None or df.empty:
            return df

        tolerance = str(risk_tolerance).lower()
        penalty = self.RISK_PENALTY_MAP.get(tolerance)
        if penalty is None:
            logger.warning(
                "Unknown risk_tolerance '%s' - skipping risk adjustment",
                risk_tolerance,
            )
            return df

        out = df.copy()
        if "composite_score" not in out.columns:
            return out

        if "composite_score_original" not in out.columns:
            out["composite_score_original"] = out["composite_score"]

        vare_col = "vare_risk_score"
        vare_mask = (
            out["composite_score"].notna()
            & out.get(vare_col, pd.Series([None] * len(out))).notna()
        )

        if vare_mask.any():
            out.loc[vare_mask, "composite_score"] = out.loc[vare_mask, "composite_score"] * (
                1 - (out.loc[vare_mask, vare_col] / 100.0) * penalty
            )

        # Fallback: use volatility z-score when VARE is missing.
        vol_z_col = "volatility_z"
        vol_mask = (
            out["composite_score"].notna()
            & ~vare_mask
            & out.get(vol_z_col, pd.Series([None] * len(out))).notna()
        )

        if vol_mask.any():
            out.loc[vol_mask, "composite_score"] = out.loc[vol_mask, "composite_score"] / (
                1 + out.loc[vol_mask, vol_z_col].abs() * penalty
            )

        return out

    def get_profile_metadata(self, profile: str) -> Dict[str, Any]:
        resolved = self._resolve_profile(profile)
        base = self.PROFILE_METADATA.get(
            resolved,
            {
                "description": f"Profile: {resolved}",
                "use_case": "General-purpose ranking.",
            },
        )
        return {
            "description": base["description"],
            "use_case": base["use_case"],
            "weights": self.get_profile_weights(resolved),
            "risk_adjustment": True,
        }

    def _resolve_profile(self, profile: str) -> str:
        p = str(profile).strip()
        if p in self.PROFILE_WEIGHTS:
            return p
        return self.PROFILE_ALIASES.get(p, p)
