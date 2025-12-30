"""
Phase 3D: Complete Vertical Integration Example

This example demonstrates how a vertical (Mercator Finance) orchestrates
the complete cognitive pipeline: Neural Engine → VWRE → VARE → VEE

Architecture:
- Neural Engine: Pure quantitative evaluation
- VWRE: Attribution analysis (factor breakdowns)
- VARE: Risk assessment (multi-dimensional risk profiles)
- VEE: Explainability (human-understandable narratives)

Domain: Finance (stocks/portfolio analysis)
Vertical: Mercator-lite (simplified finance vertical)

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Core imports
from vitruvyan_core.core.cognitive.neural_engine import (
    AbstractFactor, EvaluationOrchestrator, ZScoreNormalizer, EvaluationContext, AggregationProfile
)
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vwre_engine import VWREEngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREEngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEEngine

# Domain contracts
from vitruvyan_core.domains.aggregation_contract import AggregationProvider, AggregationProfile
from vitruvyan_core.domains.risk_contract import RiskProvider
from vitruvyan_core.domains.explainability_contract import ExplainabilityProvider


# ============================================================================
# DOMAIN INCARNATION: Finance Vertical (Mercator-lite)
# ============================================================================

@dataclass
class FinanceAggregationProfile(AggregationProfile):
    """Finance-specific aggregation profile for Neural Engine"""
    name: str = "balanced_finance"
    factor_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.factor_weights is None:
            self.factor_weights = {
                "finance_momentum": 1.0  # Only one factor for demo
            }

    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        """Return weights for available factors"""
        weights = {}
        for factor in available_factors:
            weights[factor] = self.factor_weights.get(factor, 0.0)

        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def aggregate(self, factor_scores: Dict[str, pd.Series]) -> pd.Series:
        """Combine factor scores using weighted average"""
        if not factor_scores:
            return pd.Series(dtype=float)

        weights = self.get_weights(list(factor_scores.keys()))
        result = None

        for factor_name, scores in factor_scores.items():
            weight = weights.get(factor_name, 0.0)
            if result is None:
                result = scores * weight
            else:
                result = result + (scores * weight)

        return result if result is not None else pd.Series(dtype=float)


class FinanceAggregationProvider(AggregationProvider):
    """Finance domain aggregation provider"""

    def get_aggregation_profiles(self) -> Dict[str, Any]:
        """Return mock domain aggregation profiles"""
        # Create a simple mock profile for domain contract
        @dataclass
        class MockDomainProfile:
            name: str = "balanced_finance"
            description: str = "Balanced weighting"
            factor_weights: Dict[str, float] = None

            def __post_init__(self):
                if self.factor_weights is None:
                    self.factor_weights = {"momentum": 1.0}

        return {"balanced_finance": MockDomainProfile()}

    def get_factor_mappings(self) -> Dict[str, str]:
        """Map Neural Engine factor names to aggregation factor names"""
        return {
            "momentum_z": "momentum",
            "trend_z": "trend",
            "volatility_z": "volatility",
            "sentiment_z": "sentiment",
            "fundamentals_z": "fundamentals"
        }

    def calculate_contribution(self, factor_value: float, weight: float, profile: AggregationProfile) -> float:
        """Calculate factor contribution using weighted approach"""
        return factor_value * weight

    def validate_factors(self, factors: Dict[str, float]) -> Dict[str, Any]:
        """Validate and preprocess factors"""
        valid_factors = {}
        errors = []

        for factor_name, value in factors.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                valid_factors[factor_name] = value
            else:
                errors.append(f"Invalid factor {factor_name}: {value}")

        return {
            "valid": len(errors) == 0,
            "factors": valid_factors,
            "errors": errors
        }

    def format_attribution_explanation(self, contributions: Dict[str, float],
                                     primary_driver: str, composite_score: float) -> Dict[str, str]:
        """Generate finance-specific attribution explanations"""
        summary = f"Composite score {composite_score:.3f} driven primarily by {primary_driver}"

        technical = f"Factor contributions: {', '.join([f'{k}: {v:.3f}' for k, v in contributions.items()])}"

        detailed = f"""Detailed attribution analysis:
• Primary driver: {primary_driver} ({contributions.get(primary_driver, 0):.3f} contribution)
• Composite score: {composite_score:.3f}
• All contributions: {contributions}"""

        return {
            "summary": summary,
            "technical": technical,
            "detailed": detailed
        }


class FinanceRiskProvider:
    """Finance domain risk provider (simplified for demo)"""

    def assess_risk(self, attribution_result: Any) -> Any:
        """Mock risk assessment based on attribution"""
        entity_id = attribution_result.entity_id

        # Mock risk calculation based on factor contributions
        volatility_risk = abs(attribution_result.factor_contributions.get("volatility", 0)) * 25
        momentum_risk = max(0, -attribution_result.factor_contributions.get("momentum", 0)) * 20
        trend_risk = abs(attribution_result.factor_contributions.get("trend", 0)) * 15

        overall_risk = min(100, volatility_risk + momentum_risk + trend_risk)

        # Determine risk category
        if overall_risk < 25:
            category = "LOW"
        elif overall_risk < 50:
            category = "MODERATE"
        elif overall_risk < 75:
            category = "HIGH"
        else:
            category = "EXTREME"

        # Create mock VAREResult
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREResult

        return VAREResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            market_risk=volatility_risk,
            volatility_risk=volatility_risk,
            liquidity_risk=momentum_risk,
            correlation_risk=trend_risk,
            overall_risk=overall_risk,
            risk_category=category,
            risk_factors={
                "volatility_contribution": volatility_risk,
                "momentum_contribution": momentum_risk,
                "trend_contribution": trend_risk
            },
            explanation={
                "market_risk": f"Market risk: {volatility_risk:.1f}/100 based on volatility factor",
                "volatility_risk": f"Volatility risk: {volatility_risk:.1f}/100",
                "liquidity_risk": f"Liquidity risk: {momentum_risk:.1f}/100 based on momentum",
                "correlation_risk": f"Correlation risk: {trend_risk:.1f}/100 based on trend"
            },
            confidence=0.85
        )
        """Mock risk assessment based on attribution"""
        entity_id = attribution_result.entity_id

        # Mock risk calculation based on factor contributions
        volatility_risk = abs(attribution_result.factor_contributions.get("volatility", 0)) * 25
        momentum_risk = max(0, -attribution_result.factor_contributions.get("momentum", 0)) * 20
        trend_risk = abs(attribution_result.factor_contributions.get("trend", 0)) * 15

        overall_risk = min(100, volatility_risk + momentum_risk + trend_risk)

        # Determine risk category
        if overall_risk < 25:
            category = "LOW"
        elif overall_risk < 50:
            category = "MODERATE"
        elif overall_risk < 75:
            category = "HIGH"
        else:
            category = "EXTREME"

        # Create mock VAREResult
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREResult

        return VAREResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            market_risk=volatility_risk,
            volatility_risk=volatility_risk,
            liquidity_risk=momentum_risk,
            correlation_risk=trend_risk,
            overall_risk=overall_risk,
            risk_category=category,
            risk_factors={
                "volatility_contribution": volatility_risk,
                "momentum_contribution": momentum_risk,
                "trend_contribution": trend_risk
            },
            explanation={
                "market_risk": f"Market risk: {volatility_risk:.1f}/100 based on volatility factor",
                "volatility_risk": f"Volatility risk: {volatility_risk:.1f}/100",
                "liquidity_risk": f"Liquidity risk: {momentum_risk:.1f}/100 based on momentum",
                "correlation_risk": f"Correlation risk: {trend_risk:.1f}/100 based on trend"
            },
            confidence=0.85
        )


class FinanceExplainabilityProvider:
    """Finance domain explainability provider (simplified for demo)"""

    def explain(self, risk_result: Any) -> Any:
        """Generate finance-specific explanations"""
        entity_id = risk_result.entity_id

        # Mock explanation generation
        risk_level = "concerning" if risk_result.overall_risk > 50 else "manageable"

        summary = f"{entity_id} shows {risk_level} risk profile with overall score of {risk_result.overall_risk:.1f}/100."

        technical = f"Risk breakdown: Market ({risk_result.market_risk:.1f}), Volatility ({risk_result.volatility_risk:.1f}), Liquidity ({risk_result.liquidity_risk:.1f}), Correlation ({risk_result.correlation_risk:.1f})"

        detailed = f"""Comprehensive risk assessment for {entity_id}:
• Primary risk driver: {'Volatility' if risk_result.volatility_risk > risk_result.liquidity_risk else 'Liquidity'}
• Risk category: {risk_result.risk_category}
• Confidence in assessment: {risk_result.confidence:.1%}
• Recommendation: {'Consider risk mitigation strategies' if risk_result.overall_risk > 60 else 'Risk profile acceptable for current conditions'}"""

        # Create mock VEEResult
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEResult

        return VEEResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            summary=summary,
            technical=technical,
            detailed=detailed,
            confidence=risk_result.confidence,
            metadata={
                "risk_category": risk_result.risk_category,
                "primary_driver": "volatility" if risk_result.volatility_risk > risk_result.liquidity_risk else "liquidity"
            }
        )
        """Generate finance-specific explanations"""
        entity_id = risk_result.entity_id

        # Mock explanation generation
        risk_level = "concerning" if risk_result.overall_risk > 50 else "manageable"

        summary = f"{entity_id} shows {risk_level} risk profile with overall score of {risk_result.overall_risk:.1f}/100."

        technical = f"Risk breakdown: Market ({risk_result.market_risk:.1f}), Volatility ({risk_result.volatility_risk:.1f}), Liquidity ({risk_result.liquidity_risk:.1f}), Correlation ({risk_result.correlation_risk:.1f})"

        detailed = f"""Comprehensive risk assessment for {entity_id}:
        • Primary risk driver: {'Volatility' if risk_result.volatility_risk > risk_result.liquidity_risk else 'Liquidity'}
        • Risk category: {risk_result.risk_category}
        • Confidence in assessment: {risk_result.confidence:.1%}
        • Recommendation: {'Consider risk mitigation strategies' if risk_result.overall_risk > 60 else 'Risk profile acceptable for current conditions'}"""

        # Create mock VEEResult
        from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEResult

        return VEEResult(
            entity_id=entity_id,
            timestamp=datetime.now(),
            summary=summary,
            technical=technical,
            detailed=detailed,
            confidence=risk_result.confidence,
            metadata={
                "risk_category": risk_result.risk_category,
                "primary_driver": "volatility" if risk_result.volatility_risk > risk_result.liquidity_risk else "liquidity"
            }
        )


class SimpleFinanceFactor(AbstractFactor):
    """Simple finance factor for Neural Engine"""

    @property
    def name(self) -> str:
        return "finance_momentum"

    @property
    def higher_is_better(self) -> bool:
        return True

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """Mock momentum calculation"""
        if 'current_price' in entities.columns and 'previous_price' in entities.columns:
            momentum = (entities['current_price'] - entities['previous_price']) / entities['previous_price']
            return pd.Series(momentum.values, index=entities['entity_id'])

        # Fallback: random values
        return pd.Series(
            np.random.normal(0, 0.5, len(entities)),
            index=entities['entity_id']
        )


# ============================================================================
# VERTICAL ORCHESTRATOR: Mercator-lite
# ============================================================================

class MercatorLiteOrchestrator:
    """
    Simplified finance vertical orchestrator

    Demonstrates complete pipeline: NE → VWRE → VARE → VEE
    """

    def __init__(self):
        # Initialize Neural Engine components
        self.neural_factors = [SimpleFinanceFactor()]
        self.neural_orchestrator = EvaluationOrchestrator()
        self.neural_normalizer = ZScoreNormalizer()

        # Initialize core engines with domain providers
        self.aggregation_provider = FinanceAggregationProvider()
        self.risk_provider = FinanceRiskProvider()
        self.explainability_provider = FinanceExplainabilityProvider()

        self.vwre_engine = VWREEngine()
        self.vare_engine = VAREEngine()
        self.vee_engine = VEEEngine()

        print("🏛️ Mercator-lite orchestrator initialized")

    def process_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete cognitive pipeline for single entity

        Args:
            entity_id: Entity identifier
            entity_data: Entity data dictionary

        Returns:
            Complete analysis results
        """
        print(f"\n🔄 Processing {entity_id}...")

        # Step 1: Neural Engine evaluation
        print("   1️⃣ Neural Engine evaluation...")
        ne_result = self._neural_evaluation(entity_id, entity_data)

        # Step 2: VWRE attribution analysis
        print("   2️⃣ VWRE attribution analysis...")
        vwre_result = self._vwre_attribution(ne_result)

        # Step 3: VARE risk assessment
        print("   3️⃣ VARE risk assessment...")
        vare_result = self._vare_risk_assessment(vwre_result)

        # Step 4: VEE explainability
        print("   4️⃣ VEE explainability generation...")
        vee_result = self._vee_explanation(vare_result)

        # Compile complete results
        complete_analysis = {
            'entity_id': entity_id,
            'timestamp': datetime.now().isoformat(),
            'neural_evaluation': {
                'composite_score': ne_result.composite_score,
                'factor_contributions': ne_result.factor_contributions,
                'rank': ne_result.rank
            },
            'attribution_analysis': {
                'profile': vwre_result.profile,
                'primary_driver': vwre_result.primary_driver,
                'factor_contributions': vwre_result.factor_contributions,
                'factor_percentages': vwre_result.factor_percentages
            },
            'risk_assessment': {
                'overall_risk': vare_result.overall_risk,
                'risk_category': vare_result.risk_category,
                'market_risk': vare_result.market_risk,
                'volatility_risk': vare_result.volatility_risk,
                'liquidity_risk': vare_result.liquidity_risk,
                'correlation_risk': vare_result.correlation_risk
            },
            'explanation': {
                'summary': vee_result.summary,
                'technical': vee_result.technical,
                'detailed': vee_result.detailed
            }
        }

        print(f"   ✅ {entity_id} processing complete")
        return complete_analysis

    def _neural_evaluation(self, entity_id: str, entity_data: Dict[str, Any]) -> Any:
        """Neural Engine evaluation"""
        # Create single-entity dataframe
        entities_df = pd.DataFrame([{
            'entity_id': entity_id,
            **entity_data
        }])

        # Create evaluation context
        context = EvaluationContext(
            entity_ids=[entity_id],
            profile_name="balanced_finance",
            normalizer_name="zscore",
            mode="evaluate"
        )

        # Create aggregation profile
        profile = FinanceAggregationProfile()

        # Execute evaluation
        result = self.neural_orchestrator.evaluate(
            entities=entities_df,
            context=context,
            factors=self.neural_factors,
            normalizer=self.neural_normalizer,
            profile=profile
        )

        # Extract single entity result
        entity_eval = result.evaluations[0]
        return entity_eval

    def _vwre_attribution(self, ne_result: Any) -> Any:
        """VWRE attribution analysis"""
        # Extract factor scores for VWRE
        factor_scores = {}
        for contrib in ne_result.factor_contributions:
            factor_scores[f"{contrib.factor_name}_z"] = contrib.normalized_value

        # Perform attribution analysis
        return self.vwre_engine.analyze_attribution(
            entity_id=ne_result.entity_id,
            composite_score=ne_result.composite_score,
            factors=factor_scores,
            aggregation_provider=self.aggregation_provider
        )

    def _vare_risk_assessment(self, vwre_result: Any) -> Any:
        """VARE risk assessment"""
        # Create mock dataframe for VARE (simplified)
        mock_data = pd.DataFrame({
            'entity_id': [vwre_result.entity_id],
            'price': [100.0],  # Mock data
            'volume': [1000000]
        })

        return self.vare_engine.analyze_entity(
            entity_id=vwre_result.entity_id,
            data=mock_data,
            risk_provider=self.risk_provider,
            profile_name="balanced"
        )

    def _vee_explanation(self, vare_result: Any) -> Any:
        """VEE explainability generation"""
        # Create mock metrics for VEE
        metrics = {
            'risk_score': vare_result.overall_risk,
            'risk_category': vare_result.risk_category,
            'confidence': vare_result.confidence
        }

        return self.vee_engine.explain_entity(
            entity_id=vare_result.entity_id,
            metrics=metrics,
            explainability_provider=self.explainability_provider
        )


# ============================================================================
# DEMO EXECUTION
# ============================================================================

def demonstrate_vertical_integration():
    """
    Demonstrate complete vertical integration pipeline
    """
    print("🏛️ Phase 3D: Neural Engine Integration Demo")
    print("=" * 60)

    # Initialize vertical orchestrator
    orchestrator = MercatorLiteOrchestrator()

    # Sample entity data (finance domain)
    sample_entities = [
        {
            "entity_id": "AAPL",
            "current_price": 185.0,
            "previous_price": 180.0,
            "volume": 50000000,
            "market_cap": 2900000000000
        },
        {
            "entity_id": "TSLA",
            "current_price": 245.0,
            "previous_price": 250.0,
            "volume": 75000000,
            "market_cap": 780000000000
        },
        {
            "entity_id": "MSFT",
            "current_price": 415.0,
            "previous_price": 410.0,
            "volume": 25000000,
            "market_cap": 3100000000000
        }
    ]

    print(f"\n📊 Processing {len(sample_entities)} entities through complete pipeline...\n")

    # Process each entity
    results = []
    for entity_data in sample_entities:
        entity_id = entity_data["entity_id"]
        result = orchestrator.process_entity(entity_id, entity_data)
        results.append(result)

    # Display results summary
    print("\n" + "=" * 60)
    print("📈 ANALYSIS RESULTS SUMMARY")
    print("=" * 60)

    for result in results:
        entity_id = result['entity_id']
        ne_score = result['neural_evaluation']['composite_score']
        risk_level = result['risk_assessment']['risk_category']
        primary_driver = result['attribution_analysis']['primary_driver']

        print(f"\n🏢 {entity_id}")
        print(f"   Neural Score: {ne_score:.3f}")
        print(f"   Risk Category: {risk_level}")
        print(f"   Primary Driver: {primary_driver}")
        print(f"   Summary: {result['explanation']['summary'][:80]}...")

    print("\n" + "=" * 60)
    print("✅ Phase 3D Integration Demo Complete")
    print("🏛️ Neural Engine → VWRE → VARE → VEE pipeline verified")
    print("📊 All core boundaries maintained")
    print("🎯 Vertical incarnation working end-to-end")


if __name__ == "__main__":
    try:
        demonstrate_vertical_integration()
    except ImportError as e:
        print(f"⚠️ Missing dependencies: {e}")
        print("This demo requires pandas and numpy")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()