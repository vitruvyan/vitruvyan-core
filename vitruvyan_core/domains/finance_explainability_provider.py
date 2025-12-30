"""
Finance Domain — Explainability Provider Implementation
=======================================================

Finance-specific implementation of ExplainabilityProvider for VEE Engine.

Provides financial market context for explainability generation:
- Templates for stock/portfolio explanations
- Metric definitions for financial KPIs
- Entity referencing for tickers
- Signal descriptions for market analysis

This allows VEE Engine to generate finance-appropriate narratives
while keeping the core engine domain-agnostic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: FINANCE DOMAIN ADAPTER
"""

from vitruvyan_core.domains.explainability_contract import (
    ExplainabilityProvider,
    ExplanationTemplate,
    MetricDefinition
)
from typing import Dict, List


class FinanceExplainabilityProvider(ExplainabilityProvider):
    """
    Finance domain implementation of explainability provider.

    Customizes VEE Engine for financial market analysis.
    """

    def get_explanation_templates(self) -> ExplanationTemplate:
        """Return finance-specific narrative templates."""
        return ExplanationTemplate(
            summary_template="{entity_id} shows {signals_text} with {dominant_factor} as the prevailing element.",
            technical_template="Technical analysis of {entity_id}: {dominant_factor} emerges as prevailing factor (intensity: {intensity:.1%}). Relevant parameters: {signals_summary}. Sentiment direction: {sentiment_direction}.",
            detailed_template="In-depth analysis of {entity_id}: Performance reflects a complex balance between various factors. {dominant_factor} emerges as dominant element with {intensity:.1%} intensity. {patterns_text} {confidence_text} This analysis provides no direct buy/sell indications but represents an objective assessment of current market state.",
            contextual_template="Compared to historical patterns, {entity_id} demonstrates {contextual_signals} consistent with {market_context}.",

            # Multiple variants for natural language variety
            summary_variants=[
                "{entity_id} displays {signals_text}, primarily characterized by {dominant_factor}.",
                "Analysis of {entity_id} highlights {signals_text}, dominated by {dominant_factor}.",
                "{entity_id} exhibits {signals_text} with {dominant_factor} as a critical factor."
            ],
            technical_variants=[
                "Technical breakdown {entity_id}: {dominant_factor} dominates analysis with {intensity:.1%} intensity. Signals identified: {signals_summary}. Overall sentiment: {sentiment_direction}.",
                "Technical assessment {entity_id}: {dominant_factor} represents main driver (strength: {intensity:.1%}). Significant metrics: {signals_summary}. Orientation: {sentiment_direction}."
            ],
            detailed_variants=[
                "Detailed study {entity_id}: Technical-fundamental framework highlights {dominant_factor} as main driver (intensity {intensity:.1%}). {patterns_text} Current configuration suggests {sentiment_direction} sentiment. {confidence_text} Interpretive caution is recommended.",
                "Comprehensive assessment {entity_id}: Multidimensional analysis identifies {dominant_factor} as prevailing factor (strength {intensity:.1%}). {patterns_text} The {sentiment_direction} sentiment is supported by secondary factors. {confidence_text} This evaluation is purely informational."
            ]
        )

    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Define what financial metrics mean."""
        return {
            "momentum_z": MetricDefinition(
                name="momentum_z",
                description="Price momentum relative to historical trends",
                unit="z-score",
                interpretation="Higher values indicate stronger upward momentum",
                normal_range=(-3.0, 3.0),
                display_name="Momentum"
            ),
            "trend_z": MetricDefinition(
                name="trend_z",
                description="Trend strength and direction",
                unit="z-score",
                interpretation="Higher values indicate stronger upward trends",
                normal_range=(-3.0, 3.0),
                display_name="Trend Strength"
            ),
            "vola_z": MetricDefinition(
                name="vola_z",
                description="Price volatility relative to market",
                unit="z-score",
                interpretation="Higher values indicate elevated volatility (risk)",
                normal_range=(-3.0, 3.0),
                display_name="Volatility"
            ),
            "sentiment_z": MetricDefinition(
                name="sentiment_z",
                description="Market sentiment from news and social media",
                unit="z-score",
                interpretation="Higher values indicate more positive sentiment",
                normal_range=(-3.0, 3.0),
                display_name="Sentiment"
            ),
            "technical_score": MetricDefinition(
                name="technical_score",
                description="Composite technical analysis score",
                unit="percentage",
                interpretation="Higher scores indicate favorable technical conditions",
                normal_range=(0.0, 100.0),
                display_name="Technical Score"
            ),
            "risk_score": MetricDefinition(
                name="risk_score",
                description="Overall risk assessment",
                unit="percentage",
                interpretation="Higher scores indicate higher risk",
                normal_range=(0.0, 100.0),
                display_name="Risk Score"
            ),
            "composite_score": MetricDefinition(
                name="composite_score",
                description="Overall investment attractiveness score",
                unit="percentage",
                interpretation="Higher scores indicate more attractive investment profile",
                normal_range=(0.0, 100.0),
                display_name="Composite Score"
            )
        }

    def format_entity_reference(self, entity_id: str) -> str:
        """Format ticker references for narratives."""
        # Could integrate with company name lookup, but for now just return ticker
        return f"{entity_id} stock"

    def get_signal_descriptions(self) -> Dict[str, str]:
        """Finance-specific signal descriptions."""
        return {
            "momentum": "price momentum indicators",
            "volatility": "volatility and risk metrics",
            "sentiment": "market sentiment signals",
            "risk": "risk profile indicators",
            "technical": "technical analysis signals",
            "fundamental": "fundamental valuation metrics",
            "strength": "overall strength indicators"
        }

    def get_factor_categories(self) -> Dict[str, str]:
        """Map factor names to semantic categories."""
        return {
            "momentum_z": "momentum",
            "trend_z": "trend analysis",
            "vola_z": "volatility",
            "sentiment_z": "sentiment",
            "technical_score": "technical analysis",
            "risk_score": "risk profile",
            "composite_score": "overall strength"
        }