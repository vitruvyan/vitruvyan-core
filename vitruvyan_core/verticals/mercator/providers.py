"""
Mercator Providers

Domain-specific implementations of core contracts for financial analysis:
- MercatorAggregationProvider: Financial weighting schemes
- MercatorRiskProvider: Multi-dimensional risk assessment
- MercatorExplainabilityProvider: Investment narrative generation

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from vitruvyan_core.domains.aggregation_contract import AggregationProvider, AggregationProfile
from vitruvyan_core.domains.risk_contract import RiskProvider
from vitruvyan_core.domains.explainability_contract import ExplainabilityProvider


@dataclass
class ExplanationResult:
    """Mercator-specific explanation result"""
    summary: str = ""
    technical: str = ""
    detailed: str = ""


@dataclass
class MercatorExplanationResult(ExplanationResult):
    """Mercator-specific explanation with investment narrative"""

    investment_thesis: str = ""
    risk_narrative: str = ""
    valuation_commentary: str = ""
    catalyst_assessment: str = ""
    """Mercator-specific risk assessment with financial risk dimensions"""

    overall_risk: float = 0.0
    risk_category: str = "Low"
    market_risk: float = 0.0
    volatility_risk: float = 0.0
    liquidity_risk: float = 0.0
    credit_risk: float = 0.0
    concentration_risk: float = 0.0

    @property
    def risk_dimensions(self) -> Dict[str, float]:
        """All risk dimensions for comprehensive assessment"""
        return {
            "market_risk": self.market_risk,
            "volatility_risk": self.volatility_risk,
            "liquidity_risk": self.liquidity_risk,
            "credit_risk": self.credit_risk,
            "concentration_risk": self.concentration_risk
        }


@dataclass
class MercatorAggregationProfile(AggregationProfile):
    """Mercator-specific aggregation profile with financial strategy weights"""

    strategy: str = "balanced"  # growth, value, balanced, defensive

    def __post_init__(self):
        if self.factor_weights is None:
            # Default balanced financial weights
            self.factor_weights = {
                "price_momentum": 0.25,
                "earnings_quality": 0.20,
                "valuation": 0.20,
                "growth": 0.15,
                "volatility": 0.10,
                "liquidity": 0.10
            }

        # Strategy-specific overrides
        if self.strategy == "growth":
            self.factor_weights.update({
                "growth": 0.30,
                "price_momentum": 0.25,
                "valuation": 0.10,
                "earnings_quality": 0.15,
                "volatility": 0.10,
                "liquidity": 0.10
            })
        elif self.strategy == "value":
            self.factor_weights.update({
                "valuation": 0.35,
                "earnings_quality": 0.25,
                "price_momentum": 0.10,
                "growth": 0.10,
                "volatility": 0.10,
                "liquidity": 0.10
            })
        elif self.strategy == "defensive":
            self.factor_weights.update({
                "volatility": 0.20,
                "liquidity": 0.20,
                "earnings_quality": 0.25,
                "valuation": 0.15,
                "price_momentum": 0.10,
                "growth": 0.10
            })


class MercatorAggregationProvider(AggregationProvider):
    """
    Financial aggregation provider implementing various investment strategies.

    Supports multiple weighting schemes:
    - Balanced: Equal emphasis on quality and growth
    - Growth: Emphasis on growth and momentum
    - Value: Emphasis on attractive valuations
    - Defensive: Emphasis on low risk and liquidity
    """

    def get_profile(self, entity_id: str, context: Optional[Dict[str, Any]] = None) -> AggregationProfile:
        """
        Get aggregation profile for entity based on strategy context

        Args:
            entity_id: Entity identifier
            context: Optional context with strategy preference

        Returns:
            MercatorAggregationProfile with appropriate weights
        """
        strategy = "balanced"  # default

        if context and "strategy" in context:
            strategy = context["strategy"]

        return MercatorAggregationProfile(strategy=strategy)

    def get_available_profiles(self) -> List[str]:
        """Return available strategy profiles"""
        return ["balanced", "growth", "value", "defensive"]


@dataclass
class MercatorRiskAssessment:
    """Mercator-specific risk assessment with financial risk dimensions"""

    market_risk: float = 0.0
    volatility_risk: float = 0.0
    liquidity_risk: float = 0.0
    credit_risk: float = 0.0
    concentration_risk: float = 0.0

    @property
    def risk_dimensions(self) -> Dict[str, float]:
        """All risk dimensions for comprehensive assessment"""
        return {
            "market_risk": self.market_risk,
            "volatility_risk": self.volatility_risk,
            "liquidity_risk": self.liquidity_risk,
            "credit_risk": self.credit_risk,
            "concentration_risk": self.concentration_risk
        }


class MercatorRiskProvider(RiskProvider):
    """
    Financial risk assessment provider.

    Evaluates multiple risk dimensions:
    - Market risk: Beta and systematic risk
    - Volatility risk: Price fluctuation risk
    - Liquidity risk: Trading and market depth risk
    - Credit risk: Default and credit quality risk
    - Concentration risk: Portfolio concentration effects
    """

    def assess_risk(self, entity_id: str, evaluation_result: Any, context: Optional[Dict[str, Any]] = None) -> MercatorRiskAssessment:
        """
        Comprehensive risk assessment for financial entity

        Args:
            entity_id: Entity identifier
            evaluation_result: Neural Engine evaluation result
            context: Optional risk assessment context

        Returns:
            MercatorRiskAssessment with detailed risk breakdown
        """
        # Extract factor scores from evaluation result
        factor_scores = evaluation_result.factor_contributions if hasattr(evaluation_result, 'factor_contributions') else {}

        # Market risk (beta, correlation to market)
        market_risk = self._calculate_market_risk(factor_scores, context)

        # Volatility risk (price stability, drawdown risk)
        volatility_risk = self._calculate_volatility_risk(factor_scores, context)

        # Liquidity risk (trading volume, bid-ask spread)
        liquidity_risk = self._calculate_liquidity_risk(factor_scores, context)

        # Credit risk (earnings quality, debt levels)
        credit_risk = self._calculate_credit_risk(factor_scores, context)

        # Concentration risk (portfolio impact if applicable)
        concentration_risk = self._calculate_concentration_risk(factor_scores, context)

        # Overall risk (weighted average)
        overall_risk = (
            0.3 * market_risk +
            0.25 * volatility_risk +
            0.2 * liquidity_risk +
            0.15 * credit_risk +
            0.1 * concentration_risk
        )

        # Risk category
        risk_category = self._categorize_risk(overall_risk)

        return MercatorRiskAssessment(
            overall_risk=overall_risk,
            risk_category=risk_category,
            market_risk=market_risk,
            volatility_risk=volatility_risk,
            liquidity_risk=liquidity_risk,
            credit_risk=credit_risk,
            concentration_risk=concentration_risk
        )

    def _calculate_market_risk(self, factor_scores: Dict[str, float], context: Optional[Dict]) -> float:
        """Calculate systematic market risk"""
        volatility_score = factor_scores.get('volatility', 0.5)
        momentum_score = factor_scores.get('price_momentum', 0.0)

        # Higher volatility and extreme momentum indicate higher market risk
        market_risk = 0.6 * volatility_score + 0.4 * abs(momentum_score)
        return min(market_risk, 1.0)

    def _calculate_volatility_risk(self, factor_scores: Dict[str, float], context: Optional[Dict]) -> float:
        """Calculate price volatility risk"""
        return factor_scores.get('volatility', 0.5)

    def _calculate_liquidity_risk(self, factor_scores: Dict[str, float], context: Optional[Dict]) -> float:
        """Calculate liquidity risk"""
        liquidity_score = factor_scores.get('liquidity', 0.5)
        # Invert liquidity score (lower liquidity = higher risk)
        return 1.0 - liquidity_score

    def _calculate_credit_risk(self, factor_scores: Dict[str, float], context: Optional[Dict]) -> float:
        """Calculate credit/default risk"""
        quality_score = factor_scores.get('earnings_quality', 0.5)
        valuation_score = factor_scores.get('valuation', 0.5)

        # Lower quality and higher valuation pressure indicate higher credit risk
        credit_risk = (1.0 - quality_score) * 0.6 + valuation_score * 0.4
        return min(credit_risk, 1.0)

    def _calculate_concentration_risk(self, factor_scores: Dict[str, float], context: Optional[Dict]) -> float:
        """Calculate concentration/portfolio risk"""
        # This would typically consider portfolio context, but for single entity we use volatility as proxy
        return factor_scores.get('volatility', 0.5) * 0.8

    def _categorize_risk(self, overall_risk: float) -> str:
        """Categorize overall risk level"""
        if overall_risk < 0.2:
            return "Very Low"
        elif overall_risk < 0.4:
            return "Low"
        elif overall_risk < 0.6:
            return "Moderate"
        elif overall_risk < 0.8:
            return "High"
        else:
            return "Very High"


@dataclass
class MercatorExplanationResult(ExplanationResult):
    """Mercator-specific explanation with investment narrative"""

    investment_thesis: str = ""
    risk_narrative: str = ""
    valuation_commentary: str = ""
    catalyst_assessment: str = ""


class MercatorExplainabilityProvider(ExplainabilityProvider):
    """
    Financial explainability provider generating investment narratives.

    Creates comprehensive explanations including:
    - Investment thesis and recommendation
    - Risk assessment narrative
    - Valuation commentary
    - Catalyst and timing assessment
    """

    def generate_explanation(self, entity_id: str, evaluation_result: Any,
                           risk_assessment: MercatorRiskAssessment, context: Optional[Dict[str, Any]] = None) -> MercatorExplanationResult:
        """
        Generate comprehensive financial explanation

        Args:
            entity_id: Entity identifier
            evaluation_result: Neural Engine evaluation result
            risk_assessment: Risk assessment result
            context: Optional explanation context

        Returns:
            MercatorExplanationResult with detailed financial narrative
        """
        # Extract key metrics
        composite_score = evaluation_result.composite_score if hasattr(evaluation_result, 'composite_score') else 0.0
        factor_contributions = evaluation_result.factor_contributions if hasattr(evaluation_result, 'factor_contributions') else {}

        # Generate investment thesis
        investment_thesis = self._generate_investment_thesis(composite_score, factor_contributions, risk_assessment)

        # Generate risk narrative
        risk_narrative = self._generate_risk_narrative(risk_assessment)

        # Generate valuation commentary
        valuation_commentary = self._generate_valuation_commentary(factor_contributions)

        # Generate catalyst assessment
        catalyst_assessment = self._generate_catalyst_assessment(factor_contributions, context)

        # Create summary explanation
        summary = self._create_summary_explanation(composite_score, risk_assessment, factor_contributions)

        # Create technical explanation
        technical = self._create_technical_explanation(factor_contributions)

        # Create detailed explanation
        detailed = f"""
        Investment Thesis: {investment_thesis}

        Risk Assessment: {risk_narrative}

        Valuation Analysis: {valuation_commentary}

        Catalyst Assessment: {catalyst_assessment}

        Quantitative Factors:
        {self._format_factor_contributions(factor_contributions)}
        """

        return MercatorExplanationResult(
            summary=summary,
            technical=technical,
            detailed=detailed.strip(),
            investment_thesis=investment_thesis,
            risk_narrative=risk_narrative,
            valuation_commentary=valuation_commentary,
            catalyst_assessment=catalyst_assessment
        )

    def _generate_investment_thesis(self, score: float, factors: Dict[str, float], risk: MercatorRiskAssessment) -> str:
        """Generate investment thesis based on quantitative factors"""
        if score > 0.7 and risk.overall_risk < 0.4:
            return "Strong investment opportunity with attractive risk-adjusted returns"
        elif score > 0.5 and risk.overall_risk < 0.6:
            return "Moderate investment opportunity with balanced risk-reward profile"
        elif score > 0.3:
            return "Speculative opportunity requiring careful risk management"
        else:
            return "High-risk investment with limited upside potential"

    def _generate_risk_narrative(self, risk: MercatorRiskAssessment) -> str:
        """Generate risk assessment narrative"""
        category = risk.risk_category
        overall = risk.overall_risk

        if hasattr(risk, 'risk_dimensions'):
            dimensions = risk.risk_dimensions
            high_risks = [k for k, v in dimensions.items() if v > 0.6]

            if high_risks:
                return f"{category} risk profile with elevated {', '.join(high_risks)}"
            else:
                return f"{category} risk profile with well-managed risk factors"

        return f"{category} overall risk level ({overall:.1%})"

    def _generate_valuation_commentary(self, factors: Dict[str, float]) -> str:
        """Generate valuation analysis commentary"""
        valuation = factors.get('valuation', 0.5)
        growth = factors.get('growth', 0.5)

        if valuation > 0.7 and growth > 0.6:
            return "Attractively valued with strong growth prospects"
        elif valuation > 0.7:
            return "Undervalued relative to fundamentals"
        elif valuation < 0.3:
            return "Richly valued, premium pricing justified by quality/growth"
        else:
            return "Fairly valued with balanced growth and quality metrics"

    def _generate_catalyst_assessment(self, factors: Dict[str, float], context: Optional[Dict]) -> str:
        """Assess potential catalysts for price movement"""
        momentum = factors.get('momentum', 0.0)

        if momentum > 0.6:
            return "Strong momentum suggests continued upward trajectory"
        elif momentum > 0.3:
            return "Moderate momentum with potential for further gains"
        elif momentum < -0.3:
            return "Negative momentum may persist without catalysts"
        else:
            return "Neutral momentum, catalysts needed to drive change"

    def _create_summary_explanation(self, score: float, risk: MercatorRiskAssessment, factors: Dict[str, float]) -> str:
        """Create concise summary explanation"""
        score_desc = "attractive" if score > 0.6 else "moderate" if score > 0.4 else "speculative"
        risk_desc = risk.risk_category.lower()

        return f"{score_desc.capitalize()} investment opportunity with {risk_desc} risk profile"

    def _create_technical_explanation(self, factors: Dict[str, float]) -> str:
        """Create technical factor explanation"""
        top_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

        factor_desc = []
        for factor_name, contribution in top_factors:
            direction = "positive" if contribution > 0 else "negative"
            factor_desc.append(f"{factor_name.replace('_', ' ')} ({direction}: {contribution:.2f})")

        return f"Key drivers: {', '.join(factor_desc)}"

    def _format_factor_contributions(self, factors: Dict[str, float]) -> str:
        """Format factor contributions for detailed explanation"""
        lines = []
        for factor_name, contribution in sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True):
            factor_display = factor_name.replace('_', ' ').title()
            lines.append(f"  • {factor_display}: {contribution:+.3f}")

        return '\n'.join(lines)