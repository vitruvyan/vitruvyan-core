"""
Finance Domain — Explainability Provider (VEE Contract)
========================================================

Implements ExplainabilityProvider for the finance/trading vertical.
Injects stock-market semantics into the domain-agnostic VEE Engine:

- Normalization: z-scores (momentum_z, trend_z, volatility_z, etc.)
- Dimensions: momentum, trend, volatility, sentiment, fundamentals
- Patterns: bullish/bearish momentum, divergence, overbought/oversold
- Templates: Finance-specific narrative templates with ticker references

All metrics use the z-score convention from the Neural Engine:
  momentum_z, trend_z, volatility_z, rsi_z, macd_z, volume_z, etc.

Author: Vitruvyan Core Team
Created: February 25, 2026
Status: PRODUCTION
"""

from typing import Dict, List, Optional, Tuple

from domains.explainability_contract import (
    ExplainabilityProvider,
    ExplanationTemplate,
    NormalizationRule,
    AnalysisDimension,
    PatternRule,
    ConfidenceCriteria,
    MetricDefinition,
)


# ── Ticker → Company Name lookup (subset) ────────────────────────────────────

_TICKER_NAMES: Dict[str, str] = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corp.",
    "NFLX": "Netflix Inc.",
    "AMD": "Advanced Micro Devices",
    "INTC": "Intel Corp.",
    "CRM": "Salesforce Inc.",
    "ADBE": "Adobe Inc.",
    "PYPL": "PayPal Holdings",
    "QCOM": "Qualcomm Inc.",
    "CSCO": "Cisco Systems",
    "IBM": "IBM Corp.",
    "ORCL": "Oracle Corp.",
    "SQ": "Block Inc.",
    "BA": "Boeing Co.",
    "DIS": "Walt Disney Co.",
    "JPM": "JPMorgan Chase",
    "GS": "Goldman Sachs",
    "V": "Visa Inc.",
    "MA": "Mastercard Inc.",
    "WMT": "Walmart Inc.",
    "KO": "Coca-Cola Co.",
    "PEP": "PepsiCo Inc.",
    "JNJ": "Johnson & Johnson",
    "PFE": "Pfizer Inc.",
    "UNH": "UnitedHealth Group",
}


class FinanceExplainabilityProvider(ExplainabilityProvider):
    """
    Finance-domain explainability provider for VEE Engine.

    Maps stock-market z-score metrics to multi-level narrative explanations.
    Supports momentum, trend, volatility, sentiment, and fundamentals dimensions.
    """

    # ── Narrative Templates ──────────────────────────────────────────────

    def get_explanation_templates(self) -> ExplanationTemplate:
        return ExplanationTemplate(
            summary_template=(
                "{entity_reference} shows {direction} signals with "
                "overall intensity {intensity:.0%}. "
                "Primary driver: {dominant_factor}."
            ),
            technical_template=(
                "Technical analysis of {entity_reference}: {signals_text}. "
                "Dominant factor: {dominant_factor} "
                "(secondary: {secondary_factors}). "
                "Intensity={intensity:.2f}, {confidence_text}."
            ),
            detailed_template=(
                "Comprehensive analysis for {entity_reference}:\n"
                "Signals: {signals_text}.\n"
                "Dominant factor: {dominant_factor}.\n"
                "Detected patterns: {patterns_text}.\n"
                "Overall direction: {direction}.\n"
                "Data quality: {confidence_text}."
            ),
            contextual_template=(
                "{entity_reference} market overview: "
                "Key signals include {signals_text}. "
                "Market patterns: {patterns_text}. "
                "Direction: {direction}."
            ),
            summary_variants=[
                "{entity_reference}: {direction} outlook, intensity {intensity:.0%}.",
                "{entity_reference} trending {direction}. Key driver: {dominant_factor}.",
            ],
            technical_variants=[
                "{entity_reference} technical: {signals_text}. I={intensity:.2f}.",
            ],
        )

    def format_entity_reference(self, entity_id: str) -> str:
        """Format ticker as 'Company (TICKER)' when known, else just ticker."""
        name = _TICKER_NAMES.get(entity_id.upper())
        if name:
            return f"{name} ({entity_id})"
        return entity_id

    # ── Normalization ────────────────────────────────────────────────────

    def get_normalization_rules(self) -> List[NormalizationRule]:
        return [
            # Z-scores: use tanh squash to [0, 1]
            NormalizationRule(metric_pattern="_z", method="zscore_tanh"),
            # RSI already 0-100 → linear scale
            NormalizationRule(metric_pattern="rsi", method="linear_custom",
                              min_value=0.0, max_value=100.0),
            # Composite scores already 0-1
            NormalizationRule(metric_pattern="composite_score", method="linear_custom",
                              min_value=-3.0, max_value=3.0),
            # Volume ratio (0.5x - 3.0x range)
            NormalizationRule(metric_pattern="volume", method="linear_custom",
                              min_value=0.5, max_value=3.0),
            # Volatility metrics: higher = riskier (invert for "goodness" scale)
            NormalizationRule(metric_pattern="volatility_z", method="zscore_tanh",
                              invert=True),
        ]

    # ── Analysis Dimensions ──────────────────────────────────────────────

    def get_analysis_dimensions(self) -> List[AnalysisDimension]:
        return [
            AnalysisDimension(
                name="momentum",
                metric_keys=["momentum_z", "rsi_z", "macd_z"],
                display_name="Price Momentum",
                direction="higher_better",
                weight=1.2,
            ),
            AnalysisDimension(
                name="trend",
                metric_keys=["trend_z", "sma_z", "ema_z"],
                display_name="Trend Strength",
                direction="higher_better",
                weight=1.0,
            ),
            AnalysisDimension(
                name="volatility",
                metric_keys=["volatility_z", "atr_z", "bb_width_z"],
                display_name="Volatility Profile",
                direction="lower_better",
                weight=0.8,
            ),
            AnalysisDimension(
                name="volume",
                metric_keys=["volume_z", "obv_z", "volume_ratio"],
                display_name="Volume Activity",
                direction="higher_better",
                weight=0.6,
            ),
            AnalysisDimension(
                name="sentiment",
                metric_keys=["sentiment_z", "news_sentiment_z"],
                display_name="Market Sentiment",
                direction="higher_better",
                weight=0.5,
            ),
        ]

    # ── Pattern Detection ────────────────────────────────────────────────

    def get_pattern_rules(self) -> List[PatternRule]:
        return [
            PatternRule(
                name="bullish_momentum",
                display_text="Strong bullish momentum: price acceleration with trend confirmation",
                condition=lambda m: m.get("momentum_z", 0) > 0.7 and m.get("trend_z", 0) > 0.5,
            ),
            PatternRule(
                name="bearish_momentum",
                display_text="Bearish momentum: negative price acceleration with weakening trend",
                condition=lambda m: m.get("momentum_z", 0) < -0.5 and m.get("trend_z", 0) < -0.3,
            ),
            PatternRule(
                name="bullish_divergence",
                display_text="Possible bullish divergence: momentum recovering while trend lags",
                condition=lambda m: m.get("momentum_z", 0) > 0.3 and m.get("trend_z", 0) < -0.2,
            ),
            PatternRule(
                name="bearish_divergence",
                display_text="Possible bearish divergence: momentum fading despite positive trend",
                condition=lambda m: m.get("momentum_z", 0) < -0.2 and m.get("trend_z", 0) > 0.3,
            ),
            PatternRule(
                name="high_volatility_breakout",
                display_text="High volatility breakout: elevated volatility with strong momentum",
                condition=lambda m: abs(m.get("volatility_z", 0)) > 1.0 and abs(m.get("momentum_z", 0)) > 0.8,
            ),
            PatternRule(
                name="overbought",
                display_text="Overbought conditions: RSI and momentum at extreme highs",
                condition=lambda m: m.get("rsi_z", 0) > 1.2 and m.get("momentum_z", 0) > 1.0,
            ),
            PatternRule(
                name="oversold",
                display_text="Oversold conditions: RSI and momentum at extreme lows",
                condition=lambda m: m.get("rsi_z", 0) < -1.2 and m.get("momentum_z", 0) < -1.0,
            ),
            PatternRule(
                name="volume_surge",
                display_text="Unusual volume surge: trading activity significantly above average",
                condition=lambda m: m.get("volume_z", 0) > 1.5,
            ),
            PatternRule(
                name="low_conviction",
                display_text="Low conviction move: price change on below-average volume",
                condition=lambda m: abs(m.get("momentum_z", 0)) > 0.5 and m.get("volume_z", 0) < -0.5,
            ),
        ]

    # ── Intensity Weights ────────────────────────────────────────────────

    def get_intensity_weights(self) -> Dict[str, float]:
        return {
            "momentum": 0.30,
            "trend": 0.25,
            "volatility": 0.20,
            "volume": 0.15,
            "sentiment": 0.10,
        }

    # ── Confidence Criteria ──────────────────────────────────────────────

    def get_confidence_criteria(self) -> ConfidenceCriteria:
        return ConfidenceCriteria(
            min_metrics_high=5,      # Need 5+ z-scores for high confidence
            min_metrics_moderate=3,  # 3+ for moderate
            min_signals_high=3,      # 3+ active signals for high
            consistency_threshold=0.25,  # Std dev below this = "consistent"
        )

    # ── Optional: Metric Definitions ─────────────────────────────────────

    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        return {
            "momentum_z": MetricDefinition(
                name="momentum_z",
                description="Price momentum z-score over trailing window",
                unit="z-score",
                interpretation="Positive = upward momentum, negative = downward",
                normal_range=(-2.0, 2.0),
                display_name="Momentum",
            ),
            "trend_z": MetricDefinition(
                name="trend_z",
                description="Trend strength z-score (SMA/EMA alignment)",
                unit="z-score",
                interpretation="Positive = uptrend, negative = downtrend",
                normal_range=(-2.0, 2.0),
                display_name="Trend",
            ),
            "volatility_z": MetricDefinition(
                name="volatility_z",
                description="Realized volatility z-score vs historical",
                unit="z-score",
                interpretation="Positive = high volatility, negative = calm market",
                normal_range=(-2.0, 2.0),
                display_name="Volatility",
            ),
            "rsi_z": MetricDefinition(
                name="rsi_z",
                description="RSI z-scored relative to historical distribution",
                unit="z-score",
                interpretation=">1.0 = overbought zone, <-1.0 = oversold zone",
                normal_range=(-2.0, 2.0),
                display_name="RSI",
            ),
            "volume_z": MetricDefinition(
                name="volume_z",
                description="Volume z-score vs 20-day average",
                unit="z-score",
                interpretation="Positive = above-average activity",
                normal_range=(-2.0, 2.0),
                display_name="Volume",
            ),
            "macd_z": MetricDefinition(
                name="macd_z",
                description="MACD histogram z-score",
                unit="z-score",
                interpretation="Positive = bullish MACD, negative = bearish",
                normal_range=(-2.0, 2.0),
                display_name="MACD",
            ),
        }
