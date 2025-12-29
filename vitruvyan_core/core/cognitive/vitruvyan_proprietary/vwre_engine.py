# core/logic/vitruvyan_proprietary/vwre_engine.py
"""
⚙️ VWRE - Vitruvyan Weighted Reverse Engineering (Attribution Analysis)

Decompone composite_z scores in contributi espliciti dei singoli fattori.
Risponde alla domanda: "Perché AAPL rank 1 invece di TSLA rank 5?"

Principi:
- Explainability: ogni rank è matematicamente verificabile
- Transparency: attribution breakdown per ogni factor (momentum, trend, vola, sentiment, fundamentals)
- Auditability: somma contributi ≈ composite_score (verifica coerenza)
- Composability: funziona standalone o integrato in Neural Engine

Sacred Order: REASON (Quantitative Reasoning Layer)
Integration: Neural Engine → VWRE → VEE (signal synthesis → attribution → narrative)

Author: Vitruvyan Development Team
Created: December 23, 2025
Status: ✅ PRODUCTION READY
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class VWREResult:
    """Risultato dell'attribution analysis per un ticker"""
    ticker: str
    composite_score: float
    profile: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Attribution breakdown
    factor_contributions: Dict[str, float] = field(default_factory=dict)  # {"momentum": 0.735, "trend": 0.225, ...}
    factor_percentages: Dict[str, float] = field(default_factory=dict)    # {"momentum": 39.7, "trend": 12.2, ...}
    factor_ranks: Dict[str, str] = field(default_factory=dict)            # {"momentum": "primary", "trend": "secondary", ...}
    
    # Primary driver identification
    primary_driver: Optional[str] = None              # "momentum"
    primary_contribution: float = 0.0                 # 0.735
    secondary_drivers: List[str] = field(default_factory=list)  # ["fundamentals", "trend"]
    
    # Composite verification (mathematical audit)
    sum_contributions: float = 0.0                    # Should ≈ composite_score
    residual: float = 0.0                             # composite_score - sum_contributions (risk adjustment or rounding)
    verification_status: str = "unknown"              # "verified", "warning", "error"
    
    # Explainability strings (for VEE integration)
    rank_explanation: str = ""                        # "Rank 1 driven by momentum (40%)"
    factor_narratives: Dict[str, str] = field(default_factory=dict)  # {"momentum": "exceptional signal (z=2.1)"}
    technical_summary: str = ""                       # Full mathematical breakdown


class VWREEngine:
    """
    Vitruvyan Weighted Reverse Engineering — Attribution Analysis Engine
    
    Reverse engineer composite_z scores into weighted factor contributions.
    Provides mathematical transparency for Neural Engine rankings.
    
    Architecture:
    1. Input: composite_score + factors dict + profile weights
    2. Process: Calculate contribution = z_score × weight for each factor
    3. Output: Attribution breakdown with primary drivers and verification
    
    Integration Points:
    - Neural Engine: pack_rows() calls analyze_attribution()
    - VEE Generator: Uses attribution data to enhance narratives
    - Orthodoxy Wardens: Uses verification_status for audit
    """
    
    def __init__(self):
        """Initialize VWRE Engine with Neural Engine profile weights"""
        try:
            # Import profile weights and factor mapping from Neural Engine
            from core.cognitive.neural_engine.engine_core import PROFILE_WEIGHTS, FACTOR_MAP
            self.profile_weights = PROFILE_WEIGHTS
            self.factor_map = FACTOR_MAP
            logger.info("✅ VWRE Engine initialized with Neural Engine weights")
        except ImportError as e:
            logger.error(f"❌ Failed to import Neural Engine weights: {e}")
            # Fallback to basic weights (should never happen in production)
            self.profile_weights = {"short_spec": {"momentum": 0.35, "trend": 0.15, "vola": 0.08, "sent": 0.10}}
            self.factor_map = {"momentum_z": "momentum", "trend_z": "trend", "vola_z": "vola", "sentiment_z": "sent"}
    
    def analyze_attribution(
        self,
        ticker: str,
        composite_score: float,
        factors: Dict[str, float],
        profile: str = "short_spec"
    ) -> VWREResult:
        """
        Reverse engineer composite_score into factor contributions.
        
        Args:
            ticker: Symbol (e.g., "AAPL")
            composite_score: Final composite z-score from Neural Engine
            factors: Dict with z-scores (momentum_z, trend_z, vola_z, sentiment_z, etc.)
            profile: Screening profile determining weights (short_spec, balanced_mid, etc.)
        
        Returns:
            VWREResult with complete attribution breakdown
        
        Example:
            >>> vwre = VWREEngine()
            >>> attribution = vwre.analyze_attribution(
            ...     ticker="AAPL",
            ...     composite_score=1.85,
            ...     factors={"momentum_z": 2.1, "trend_z": 1.5, "vola_z": -0.3, "sentiment_z": 0.8, "fundamentals_z": 1.2},
            ...     profile="short_spec"
            ... )
            >>> print(attribution.rank_explanation)
            "Rank driven by momentum (39.7% weight, +0.735 contribution)"
        """
        logger.info(f"[VWRE] Analyzing attribution for {ticker} (composite={composite_score:.3f}, profile={profile})")
        
        # Get profile weights
        weights = self.profile_weights.get(profile, self.profile_weights.get("short_spec", {}))
        
        if not weights:
            logger.warning(f"⚠️ No weights found for profile '{profile}', using short_spec")
            weights = self.profile_weights["short_spec"]
        
        # Calculate raw contributions (factor_z × weight)
        contributions = {}
        raw_factors_used = {}  # Track which z-scores were actually used
        
        for factor_col, weight_key in self.factor_map.items():
            if factor_col in factors:
                z_score = factors[factor_col]
                
                # Skip null/nan values
                if z_score is None or (isinstance(z_score, float) and np.isnan(z_score)):
                    continue
                
                weight = weights.get(weight_key, 0.0)
                
                if weight > 0:  # Only include factors with non-zero weight
                    contribution = z_score * weight
                    contributions[weight_key] = contribution
                    raw_factors_used[weight_key] = {"z_score": z_score, "weight": weight}
        
        # Handle case with no valid factors
        if not contributions:
            logger.warning(f"⚠️ No valid factors found for {ticker}")
            return VWREResult(
                ticker=ticker,
                composite_score=composite_score,
                profile=profile,
                verification_status="error",
                rank_explanation="No valid factors available for attribution analysis"
            )
        
        # Calculate total contribution (should ≈ composite_score before risk adjustment)
        total_contribution = sum(contributions.values())
        
        # Calculate percentages (normalized to 100%)
        percentages = {}
        if total_contribution != 0:
            percentages = {
                k: (v / total_contribution * 100) for k, v in contributions.items()
            }
        else:
            # Edge case: all contributions cancel out to zero
            percentages = {k: 0.0 for k in contributions}
        
        # Rank factors by absolute contribution (primary, secondary, tertiary)
        factor_ranks = self._assign_ranks(contributions)
        
        # Identify primary and secondary drivers
        sorted_factors = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        primary_driver = sorted_factors[0][0] if sorted_factors else None
        primary_contribution = contributions.get(primary_driver, 0.0) if primary_driver else 0.0
        secondary_drivers = [f[0] for f in sorted_factors[1:3] if abs(f[1]) > 0.05]  # Top 2-3 supporting factors
        
        # Composite verification (residual = risk adjustment + rounding)
        residual = composite_score - total_contribution
        verification_status = self._verify_composite(composite_score, total_contribution, residual)
        
        # Generate explainability strings (for VEE integration)
        rank_explanation = self._generate_rank_explanation(primary_driver, percentages, primary_contribution)
        factor_narratives = self._generate_factor_narratives(raw_factors_used, contributions)
        technical_summary = self._generate_technical_summary(ticker, composite_score, contributions, residual, profile)
        
        result = VWREResult(
            ticker=ticker,
            composite_score=composite_score,
            profile=profile,
            factor_contributions=contributions,
            factor_percentages=percentages,
            factor_ranks=factor_ranks,
            primary_driver=primary_driver,
            primary_contribution=primary_contribution,
            secondary_drivers=secondary_drivers,
            sum_contributions=total_contribution,
            residual=residual,
            verification_status=verification_status,
            rank_explanation=rank_explanation,
            factor_narratives=factor_narratives,
            technical_summary=technical_summary
        )
        
        logger.info(f"✅ [VWRE] {ticker}: primary_driver={primary_driver}, contribution={primary_contribution:.3f}, residual={residual:.3f}")
        
        return result
    
    def compare_tickers(
        self,
        ticker_a: str,
        ticker_b: str,
        attribution_a: VWREResult,
        attribution_b: VWREResult
    ) -> Dict[str, Any]:
        """
        Contrastive analysis: "Why AAPL rank 1 vs TSLA rank 5?"
        
        Identifies which factor most differentiates the two tickers.
        
        Args:
            ticker_a: First ticker (typically higher rank)
            ticker_b: Second ticker (typically lower rank)
            attribution_a: VWRE result for ticker_a
            attribution_b: VWRE result for ticker_b
        
        Returns:
            Dict with comparative analysis including:
            - delta_composite: Composite score difference
            - primary_difference: Factor with largest delta
            - all_deltas: Full factor-by-factor comparison
            - explanation: Human-readable contrastive narrative
        
        Example:
            >>> comparison = vwre.compare_tickers("AAPL", "TSLA", attr_aapl, attr_tsla)
            >>> print(comparison["explanation"])
            "AAPL ranks higher primarily due to superior momentum (+0.8), despite weaker sentiment (-0.3)"
        """
        delta_composite = attribution_a.composite_score - attribution_b.composite_score
        
        # Calculate factor deltas (only for common factors)
        factor_deltas = {}
        for factor in attribution_a.factor_contributions:
            if factor in attribution_b.factor_contributions:
                delta = attribution_a.factor_contributions[factor] - attribution_b.factor_contributions[factor]
                factor_deltas[factor] = delta
        
        # Find largest absolute delta (primary differentiator)
        if factor_deltas:
            primary_diff = max(factor_deltas.items(), key=lambda x: abs(x[1]))
            primary_factor = primary_diff[0]
            primary_delta = primary_diff[1]
        else:
            primary_factor = "unknown"
            primary_delta = 0.0
        
        # Generate contrastive explanation
        if primary_delta > 0:
            explanation = (
                f"{ticker_a} ranks higher than {ticker_b} primarily due to superior "
                f"{primary_factor} (+{primary_delta:.3f}). "
            )
        else:
            explanation = (
                f"{ticker_a} ranks higher than {ticker_b} despite weaker "
                f"{primary_factor} ({primary_delta:.3f}). "
            )
        
        # Add supporting factors (top 2 other deltas)
        sorted_deltas = sorted(factor_deltas.items(), key=lambda x: abs(x[1]), reverse=True)
        supporting = [f for f in sorted_deltas[1:3] if abs(f[1]) > 0.05]
        
        if supporting:
            support_text = ", ".join([f"{f[0]} ({f[1]:+.3f})" for f in supporting])
            explanation += f"Supporting factors: {support_text}."
        
        comparison = {
            "ticker_a": ticker_a,
            "ticker_b": ticker_b,
            "delta_composite": delta_composite,
            "primary_difference": primary_factor,
            f"{primary_factor}_delta": primary_delta,
            "all_deltas": factor_deltas,
            "explanation": explanation,
            "attribution_a_primary": attribution_a.primary_driver,
            "attribution_b_primary": attribution_b.primary_driver
        }
        
        logger.info(f"[VWRE] Comparison {ticker_a} vs {ticker_b}: primary_diff={primary_factor} ({primary_delta:+.3f})")
        
        return comparison
    
    def _assign_ranks(self, contributions: Dict[str, float]) -> Dict[str, str]:
        """
        Assign qualitative ranks to factors based on contribution magnitude.
        
        Ranks:
        - "primary driver": Largest absolute contribution
        - "secondary support": Top 2-3 contributors
        - "minor contribution": Small but non-negligible
        - "negligible": Very small contribution
        """
        sorted_factors = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        ranks = {}
        
        for i, (factor, contrib) in enumerate(sorted_factors):
            abs_contrib = abs(contrib)
            
            if i == 0:
                ranks[factor] = "primary driver"
            elif i < 3 and abs_contrib > 0.05:
                ranks[factor] = "secondary support"
            elif abs_contrib > 0.01:
                ranks[factor] = "minor contribution"
            else:
                ranks[factor] = "negligible"
        
        return ranks
    
    def _generate_factor_narratives(
        self, 
        raw_factors: Dict[str, Dict[str, float]], 
        contributions: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Generate human-readable narratives for each factor.
        
        Uses z-score thresholds to assign qualitative labels:
        - z > 1.5: "exceptional"
        - z > 1.0: "strong"
        - z > 0.5: "above average"
        - z > 0.0: "slightly positive"
        - z < -1.0: "weak"
        - z < -0.5: "below average"
        - else: "neutral"
        """
        narratives = {}
        
        for factor_name, factor_data in raw_factors.items():
            z_score = factor_data["z_score"]
            weight = factor_data["weight"]
            contribution = contributions.get(factor_name, 0.0)
            
            # Qualitative z-score labels
            if z_score > 1.5:
                strength = "exceptional signal"
            elif z_score > 1.0:
                strength = "strong signal"
            elif z_score > 0.5:
                strength = "above-average signal"
            elif z_score > 0.0:
                strength = "slightly positive signal"
            elif z_score < -1.0:
                strength = "weak signal"
            elif z_score < -0.5:
                strength = "below-average signal"
            else:
                strength = "neutral signal"
            
            narratives[factor_name] = (
                f"{strength} (z={z_score:.2f}, weight={weight:.2%}, "
                f"contribution={contribution:+.3f})"
            )
        
        return narratives
    
    def _generate_rank_explanation(
        self, 
        primary_driver: Optional[str], 
        percentages: Dict[str, float],
        primary_contribution: float
    ) -> str:
        """Generate concise rank explanation string for VEE integration"""
        if not primary_driver:
            return "Ranking based on available factors with recalibrated weights"
        
        pct = percentages.get(primary_driver, 0)
        return (
            f"Rank driven by {primary_driver} "
            f"({pct:.1f}% weight, {primary_contribution:+.3f} contribution)"
        )
    
    def _generate_technical_summary(
        self,
        ticker: str,
        composite_score: float,
        contributions: Dict[str, float],
        residual: float,
        profile: str
    ) -> str:
        """
        Generate technical mathematical breakdown for audit/documentation.
        
        Format:
        AAPL composite_score=1.85 (profile=short_spec)
        = momentum(0.735) + fundamentals(0.288) + trend(0.225) + sentiment(0.080) + vola(-0.024)
        = 1.304 base + 0.546 risk_adjustment = 1.85 final
        """
        contrib_parts = " + ".join([
            f"{k}({v:+.3f})" for k, v in sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        ])
        
        sum_contrib = sum(contributions.values())
        
        summary = (
            f"{ticker} composite_score={composite_score:.3f} (profile={profile})\n"
            f"= {contrib_parts}\n"
            f"= {sum_contrib:.3f} base"
        )
        
        if abs(residual) > 0.01:
            summary += f" + {residual:+.3f} adjustment = {composite_score:.3f} final"
        
        return summary
    
    def _verify_composite(
        self, 
        composite_score: float, 
        sum_contributions: float, 
        residual: float
    ) -> str:
        """
        Verify mathematical consistency between composite and sum of contributions.
        
        Returns:
        - "verified": residual < 0.1 (acceptable due to risk adjustment)
        - "warning": residual 0.1-0.5 (investigate potential issue)
        - "error": residual > 0.5 (mathematical inconsistency)
        """
        abs_residual = abs(residual)
        
        if abs_residual < 0.1:
            return "verified"
        elif abs_residual < 0.5:
            logger.warning(f"⚠️ [VWRE] Verification warning: residual={residual:.3f} (expected <0.1)")
            return "warning"
        else:
            logger.error(f"❌ [VWRE] Verification error: residual={residual:.3f} (expected <0.5)")
            return "error"
    
    def batch_analyze(
        self,
        tickers_data: List[Dict[str, Any]],
        profile: str = "short_spec"
    ) -> List[VWREResult]:
        """
        Batch attribution analysis for multiple tickers.
        
        Optimized for Neural Engine integration where multiple tickers
        are ranked simultaneously.
        
        Args:
            tickers_data: List of dicts with ticker, composite_score, factors
            profile: Screening profile
        
        Returns:
            List of VWREResult objects (same order as input)
        """
        results = []
        
        for ticker_data in tickers_data:
            try:
                result = self.analyze_attribution(
                    ticker=ticker_data["ticker"],
                    composite_score=ticker_data["composite_score"],
                    factors=ticker_data.get("factors", {}),
                    profile=profile
                )
                results.append(result)
            except Exception as e:
                logger.error(f"❌ [VWRE] Failed to analyze {ticker_data.get('ticker', 'UNKNOWN')}: {e}")
                # Append error result to maintain list consistency
                results.append(VWREResult(
                    ticker=ticker_data.get("ticker", "UNKNOWN"),
                    composite_score=ticker_data.get("composite_score", 0.0),
                    profile=profile,
                    verification_status="error",
                    rank_explanation=f"Attribution analysis failed: {str(e)}"
                ))
        
        logger.info(f"✅ [VWRE] Batch analysis complete: {len(results)} tickers processed")
        
        return results


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def explain_rank(ticker: str, composite_score: float, factors: Dict[str, float], profile: str = "short_spec") -> str:
    """
    Quick utility: Generate rank explanation string.
    
    Example:
        >>> explanation = explain_rank("AAPL", 1.85, {"momentum_z": 2.1, "trend_z": 1.5})
        >>> print(explanation)
        "Rank driven by momentum (39.7% weight, +0.735 contribution)"
    """
    vwre = VWREEngine()
    result = vwre.analyze_attribution(ticker, composite_score, factors, profile)
    return result.rank_explanation


def compare_two(
    ticker_a: str, 
    composite_a: float, 
    factors_a: Dict[str, float],
    ticker_b: str,
    composite_b: float,
    factors_b: Dict[str, float],
    profile: str = "short_spec"
) -> str:
    """
    Quick utility: Generate comparison explanation.
    
    Example:
        >>> comparison = compare_two("AAPL", 1.85, {...}, "TSLA", 0.95, {...})
        >>> print(comparison)
        "AAPL ranks higher primarily due to superior momentum (+0.8)"
    """
    vwre = VWREEngine()
    attr_a = vwre.analyze_attribution(ticker_a, composite_a, factors_a, profile)
    attr_b = vwre.analyze_attribution(ticker_b, composite_b, factors_b, profile)
    comparison = vwre.compare_tickers(ticker_a, ticker_b, attr_a, attr_b)
    return comparison["explanation"]


# ============================================================
# POSTGRESQL INTEGRATION (Optional)
# ============================================================

def store_attribution(result: VWREResult, connection) -> bool:
    """
    Store VWRE attribution result in PostgreSQL for audit trail.
    
    Table schema (create if needed):
    CREATE TABLE vwre_attributions (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(10),
        composite_score FLOAT,
        profile VARCHAR(50),
        primary_driver VARCHAR(50),
        primary_contribution FLOAT,
        sum_contributions FLOAT,
        residual FLOAT,
        verification_status VARCHAR(20),
        rank_explanation TEXT,
        technical_summary TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO vwre_attributions (
                    ticker, composite_score, profile, primary_driver, 
                    primary_contribution, sum_contributions, residual,
                    verification_status, rank_explanation, technical_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                result.ticker,
                result.composite_score,
                result.profile,
                result.primary_driver,
                result.primary_contribution,
                result.sum_contributions,
                result.residual,
                result.verification_status,
                result.rank_explanation,
                result.technical_summary
            ))
            connection.commit()
            logger.info(f"✅ [VWRE] Attribution stored for {result.ticker}")
            return True
    except Exception as e:
        logger.error(f"❌ [VWRE] Failed to store attribution: {e}")
        return False


if __name__ == "__main__":
    # Self-test example
    print("🧪 VWRE Engine Self-Test\n")
    
    vwre = VWREEngine()
    
    # Example: AAPL attribution
    result = vwre.analyze_attribution(
        ticker="AAPL",
        composite_score=1.85,
        factors={
            "momentum_z": 2.1,
            "trend_z": 1.5,
            "vola_z": -0.3,
            "sentiment_z": 0.8,
            "fundamentals_z": 1.2
        },
        profile="short_spec"
    )
    
    print(f"✅ {result.ticker}: {result.rank_explanation}")
    print(f"   Primary: {result.primary_driver} ({result.primary_contribution:.3f})")
    print(f"   Verification: {result.verification_status} (residual={result.residual:.3f})")
    print(f"\n📊 Technical Summary:\n{result.technical_summary}")
    print(f"\n💬 Factor Narratives:")
    for factor, narrative in result.factor_narratives.items():
        print(f"   • {factor}: {narrative}")
