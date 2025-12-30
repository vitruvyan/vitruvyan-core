"""
Mercator Vertical: Complete Financial Analysis Implementation

MercatorVertical orchestrates the complete cognitive pipeline for financial analysis:
Neural Engine → VWRE → VARE → VEE with domain-specific financial logic.

Key Features:
- Multi-factor quantitative evaluation (6 core factors)
- Strategy-based aggregation profiles (growth, value, balanced, defensive)
- Comprehensive risk assessment (5 risk dimensions)
- Investment narrative generation
- Portfolio-level analysis capabilities

Usage:
    mercator = MercatorVertical()
    analysis = mercator.analyze_entity("AAPL", entity_data)
    portfolio_analysis = mercator.analyze_portfolio(holdings)

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

# Core imports
from vitruvyan_core.core.cognitive.neural_engine import (
    AbstractFactor, EvaluationOrchestrator, ZScoreNormalizer, EvaluationContext
)
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vwre_engine import VWREEngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREEngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEEngine

# Integration utilities
from vitruvyan_core.integration import VerticalOrchestrator, BatchProcessor, ResultAggregator

# Mercator components
from .factors import (
    PriceMomentumFactor, EarningsQualityFactor, ValuationFactor,
    GrowthFactor, VolatilityFactor, LiquidityFactor
)
from .providers import (
    MercatorAggregationProvider, MercatorRiskProvider, MercatorExplainabilityProvider,
    MercatorAggregationProfile
)


@dataclass
class MercatorAnalysisResult:
    """Complete Mercator analysis result"""

    entity_id: str
    timestamp: str
    neural_evaluation: Dict[str, Any]
    attribution_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    explanation: Dict[str, Any]
    recommendation: str
    confidence_score: float


@dataclass
class PortfolioAnalysisResult:
    """Portfolio-level analysis result"""

    portfolio_id: str
    timestamp: str
    holdings_analysis: List[MercatorAnalysisResult]
    portfolio_metrics: Dict[str, float]
    risk_contribution: Dict[str, float]
    diversification_score: float
    recommendation: str


class MercatorVertical(VerticalOrchestrator):
    """
    Mercator Vertical: Complete financial analysis implementation.

    Orchestrates the full cognitive pipeline with financial domain expertise:
    - 6 quantitative factors (momentum, quality, valuation, growth, volatility, liquidity)
    - 4 investment strategies (balanced, growth, value, defensive)
    - 5 risk dimensions (market, volatility, liquidity, credit, concentration)
    - Investment narrative generation
    """

    def __init__(self):
        """Initialize Mercator with all components"""
        # Neural Engine components
        self.neural_factors = self._get_domain_factors()
        self.neural_orchestrator = EvaluationOrchestrator()
        self.neural_normalizer = ZScoreNormalizer()

        # Domain providers
        self.aggregation_provider = MercatorAggregationProvider()
        self.risk_provider = MercatorRiskProvider()
        self.explainability_provider = MercatorExplainabilityProvider()

        # Core engines with domain incarnation
        self.vwre_engine = VWREEngine()
        self.vare_engine = VAREEngine()
        self.vee_engine = VEEEngine()

        # Batch processing capabilities
        self.batch_processor = BatchProcessor()
        self.result_aggregator = ResultAggregator()

        print("🏛️ Mercator Vertical initialized - Financial Analysis Engine")

    def _get_domain_factors(self) -> List[AbstractFactor]:
        """Get all Mercator financial factors"""
        return [
            PriceMomentumFactor(),
            EarningsQualityFactor(),
            ValuationFactor(),
            GrowthFactor(),
            VolatilityFactor(),
            LiquidityFactor()
        ]

    def get_domain_factors(self) -> List[AbstractFactor]:
        """Public interface for domain factors"""
        return self.neural_factors

    def analyze_entity(self, entity_id: str, entity_data: Dict[str, Any],
                      strategy: str = "balanced", context: Optional[Dict[str, Any]] = None) -> MercatorAnalysisResult:
        """
        Complete financial analysis for single entity

        Args:
            entity_id: Entity identifier (ticker, ISIN, etc.)
            entity_data: Financial data dictionary
            strategy: Investment strategy (balanced, growth, value, defensive)
            context: Optional analysis context

        Returns:
            Complete MercatorAnalysisResult
        """
        print(f"\n📊 Analyzing {entity_id} with {strategy} strategy...")

        # Step 1: Neural Engine evaluation
        print("   1️⃣ Neural Engine quantitative evaluation...")
        ne_result = self._neural_evaluation(entity_id, entity_data, strategy)

        # Step 2: VWRE attribution analysis
        print("   2️⃣ VWRE factor attribution analysis...")
        vwre_result = self._vwre_attribution(ne_result, strategy)

        # Step 3: VARE risk assessment
        print("   3️⃣ VARE multi-dimensional risk assessment...")
        vare_result = self._vare_risk_assessment(entity_id, vwre_result, context)

        # Step 4: VEE explainability generation
        print("   4️⃣ VEE investment narrative generation...")
        vee_result = self._vee_explanation(entity_id, ne_result, vare_result, context)

        # Generate recommendation and confidence
        recommendation, confidence = self._generate_recommendation(ne_result, vare_result, strategy)

        # Compile complete result
        result = MercatorAnalysisResult(
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            neural_evaluation={
                'composite_score': ne_result.composite_score,
                'factor_contributions': ne_result.factor_contributions,
                'rank': ne_result.rank,
                'strategy': strategy
            },
            attribution_analysis={
                'primary_driver': vwre_result.primary_driver,
                'factor_contributions': vwre_result.factor_contributions,
                'factor_percentages': vwre_result.factor_percentages,
                'profile': vwre_result.profile
            },
            risk_assessment={
                'overall_risk': vare_result.overall_risk,
                'risk_category': vare_result.risk_category,
                'market_risk': vare_result.market_risk,
                'volatility_risk': vare_result.volatility_risk,
                'liquidity_risk': vare_result.liquidity_risk,
                'credit_risk': vare_result.credit_risk,
                'concentration_risk': vare_result.concentration_risk
            },
            explanation={
                'summary': vee_result.summary,
                'technical': vee_result.technical,
                'detailed': vee_result.detailed,
                'investment_thesis': vee_result.investment_thesis,
                'risk_narrative': vee_result.risk_narrative,
                'valuation_commentary': vee_result.valuation_commentary,
                'catalyst_assessment': vee_result.catalyst_assessment
            },
            recommendation=recommendation,
            confidence_score=confidence
        )

        print(f"   ✅ {entity_id} analysis complete - {recommendation} (confidence: {confidence:.1%})")
        return result

    def analyze_portfolio(self, holdings: List[Dict[str, Any]], portfolio_id: str = "portfolio",
                         strategy: str = "balanced", context: Optional[Dict[str, Any]] = None) -> PortfolioAnalysisResult:
        """
        Portfolio-level financial analysis

        Args:
            holdings: List of holding dictionaries with entity_id and data
            portfolio_id: Portfolio identifier
            strategy: Investment strategy
            context: Optional portfolio context

        Returns:
            PortfolioAnalysisResult with individual and aggregate analysis
        """
        print(f"\n📊 Analyzing portfolio {portfolio_id} with {len(holdings)} holdings...")

        # Analyze individual holdings
        holdings_analysis = []
        for holding in holdings:
            entity_id = holding.get('entity_id', 'unknown')
            entity_data = holding.get('data', {})
            analysis = self.analyze_entity(entity_id, entity_data, strategy, context)
            holdings_analysis.append(analysis)

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(holdings_analysis)

        # Calculate risk contribution
        risk_contribution = self._calculate_risk_contribution(holdings_analysis)

        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(holdings_analysis)

        # Generate portfolio recommendation
        portfolio_recommendation = self._generate_portfolio_recommendation(
            holdings_analysis, portfolio_metrics, diversification_score
        )

        result = PortfolioAnalysisResult(
            portfolio_id=portfolio_id,
            timestamp=datetime.now().isoformat(),
            holdings_analysis=holdings_analysis,
            portfolio_metrics=portfolio_metrics,
            risk_contribution=risk_contribution,
            diversification_score=diversification_score,
            recommendation=portfolio_recommendation
        )

        print(f"   ✅ Portfolio analysis complete - {portfolio_recommendation}")
        return result

    def _neural_evaluation(self, entity_id: str, entity_data: Dict[str, Any], strategy: str):
        """Neural Engine evaluation with Mercator factors"""
        # Create entity dataframe
        entities_df = pd.DataFrame([{
            'entity_id': entity_id,
            **entity_data
        }])

        # Create evaluation context
        context = EvaluationContext(
            entity_ids=[entity_id],
            profile_name=f"mercator_{strategy}",
            normalizer_name="zscore",
            mode="evaluate"
        )

        # Get aggregation profile for strategy
        profile = self.aggregation_provider.get_profile(entity_id, {"strategy": strategy})

        # Run evaluation
        return self.neural_orchestrator.evaluate_entities(
            entities_df, self.neural_factors, self.neural_normalizer, profile, context
        )

    def _vwre_attribution(self, ne_result, strategy: str):
        """VWRE attribution analysis"""
        # Get profile for attribution
        profile = self.aggregation_provider.get_profile(ne_result.entity_id, {"strategy": strategy})

        return self.vwre_engine.analyze_attribution(ne_result, profile, self.aggregation_provider)

    def _vare_risk_assessment(self, entity_id: str, vwre_result, context: Optional[Dict]):
        """VARE risk assessment"""
        return self.risk_provider.assess_risk(entity_id, vwre_result, context)

    def _vee_explanation(self, entity_id: str, ne_result, vare_result, context: Optional[Dict]):
        """VEE explanation generation"""
        return self.explainability_provider.generate_explanation(entity_id, ne_result, vare_result, context)

    def _generate_recommendation(self, ne_result, vare_result, strategy: str) -> tuple[str, float]:
        """Generate investment recommendation and confidence score"""
        score = ne_result.composite_score
        risk = vare_result.overall_risk

        # Risk-adjusted score
        risk_adjusted_score = score * (1 - risk)

        # Strategy-specific thresholds
        if strategy == "defensive":
            buy_threshold = 0.6
            hold_threshold = 0.4
        elif strategy == "growth":
            buy_threshold = 0.7
            hold_threshold = 0.5
        else:  # balanced, value
            buy_threshold = 0.65
            hold_threshold = 0.45

        if risk_adjusted_score > buy_threshold:
            recommendation = "BUY"
            confidence = min(risk_adjusted_score, 0.95)
        elif risk_adjusted_score > hold_threshold:
            recommendation = "HOLD"
            confidence = 0.7
        else:
            recommendation = "SELL"
            confidence = min(1 - risk_adjusted_score, 0.9)

        return recommendation, confidence

    def _calculate_portfolio_metrics(self, holdings_analysis: List[MercatorAnalysisResult]) -> Dict[str, float]:
        """Calculate aggregate portfolio metrics"""
        if not holdings_analysis:
            return {}

        scores = [h.neural_evaluation['composite_score'] for h in holdings_analysis]
        risks = [h.risk_assessment['overall_risk'] for h in holdings_analysis]

        return {
            'avg_score': np.mean(scores),
            'avg_risk': np.mean(risks),
            'risk_adjusted_return': np.mean(scores) * (1 - np.mean(risks)),
            'score_volatility': np.std(scores),
            'risk_volatility': np.std(risks),
            'sharpe_ratio': np.mean(scores) / np.std(scores) if np.std(scores) > 0 else 0
        }

    def _calculate_risk_contribution(self, holdings_analysis: List[MercatorAnalysisResult]) -> Dict[str, float]:
        """Calculate risk contribution by category"""
        risk_categories = {}
        total_holdings = len(holdings_analysis)

        for analysis in holdings_analysis:
            category = analysis.risk_assessment['risk_category']
            risk_categories[category] = risk_categories.get(category, 0) + 1

        # Convert to percentages
        return {cat: count/total_holdings for cat, count in risk_categories.items()}

    def _calculate_diversification_score(self, holdings_analysis: List[MercatorAnalysisResult]) -> float:
        """Calculate portfolio diversification score (0-1, higher = better diversified)"""
        if len(holdings_analysis) < 2:
            return 0.0

        scores = [h.neural_evaluation['composite_score'] for h in holdings_analysis]
        score_std = np.std(scores)

        # Lower correlation between holdings = better diversification
        # Use score standard deviation as proxy for diversification
        diversification = 1.0 / (1.0 + score_std)

        return min(diversification, 1.0)

    def _generate_portfolio_recommendation(self, holdings_analysis: List[MercatorAnalysisResult],
                                         portfolio_metrics: Dict[str, float], diversification: float) -> str:
        """Generate portfolio-level recommendation"""
        avg_score = portfolio_metrics.get('avg_score', 0)
        avg_risk = portfolio_metrics.get('avg_risk', 1)
        risk_adjusted = portfolio_metrics.get('risk_adjusted_return', 0)

        if risk_adjusted > 0.5 and diversification > 0.6:
            return "Strong portfolio - maintain allocation"
        elif risk_adjusted > 0.3 and diversification > 0.4:
            return "Balanced portfolio - monitor for rebalancing"
        elif avg_risk > 0.7:
            return "High-risk portfolio - consider risk reduction"
        elif diversification < 0.3:
            return "Concentrated portfolio - increase diversification"
        else:
            return "Portfolio needs review and potential rebalancing"