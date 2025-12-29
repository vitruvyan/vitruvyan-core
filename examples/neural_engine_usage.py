"""
Example: How a vertical (Mercator) would use Neural Engine Core.

This demonstrates the proper separation between core and domain logic.
"""

from typing import List, Dict
import pandas as pd

from vitruvyan_core.core.cognitive.neural_engine import (
    AbstractFactor,
    AggregationProfile,
    EvaluationContext,
    EvaluationOrchestrator,
    ZScoreNormalizer,
)


# ============================================================================
# DOMAIN-SPECIFIC IMPLEMENTATION (Lives in Mercator, NOT in core)
# ============================================================================

class SimpleMomentumFactor(AbstractFactor):
    """
    Example factor from Mercator vertical.
    
    This demonstrates how verticals implement domain-specific logic
    while using the core's abstract interface.
    """
    
    @property
    def name(self) -> str:
        return "simple_momentum"
    
    @property
    def higher_is_better(self) -> bool:
        return True
    
    def compute(self, entities: pd.DataFrame, context: EvaluationContext) -> pd.Series:
        """
        Compute momentum score for each entity.
        
        In a real implementation, this would:
        1. Query historical data from Mercator's data layer
        2. Calculate price changes over time
        3. Return momentum scores
        
        For this example, we'll use dummy data from the entities DataFrame.
        """
        # Example: simple price change calculation
        if 'current_price' in entities.columns and 'previous_price' in entities.columns:
            momentum = (entities['current_price'] - entities['previous_price']) / entities['previous_price']
            return pd.Series(momentum.values, index=entities['entity_id'])
        
        # Fallback: use dummy values
        return pd.Series({
            entity_id: float(idx) 
            for idx, entity_id in enumerate(entities['entity_id'])
        })


class BalancedProfile(AggregationProfile):
    """
    Example aggregation profile from Mercator vertical.
    
    Defines how to weight and combine multiple factors.
    """
    
    @property
    def name(self) -> str:
        return "balanced"
    
    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        """
        Define weights for each factor.
        
        In a real implementation, this might:
        - Load weights from configuration
        - Adjust weights based on market conditions
        - Recalibrate if factors are missing
        """
        # Example weights (Mercator's domain knowledge)
        all_weights = {
            "simple_momentum": 0.4,
            "trend_strength": 0.3,
            "volatility": 0.3,
        }
        
        # Recalibrate for available factors
        weights = {f: all_weights.get(f, 0.0) for f in available_factors}
        total = sum(weights.values())
        
        if total > 0:
            weights = {f: w / total for f, w in weights.items()}
        
        return weights
    
    def aggregate(self, factor_scores: Dict[str, pd.Series]) -> pd.Series:
        """
        Combine factor scores using weighted average.
        """
        weights = self.get_weights(list(factor_scores.keys()))
        
        composite = None
        for factor_name, scores in factor_scores.items():
            weight = weights.get(factor_name, 0.0)
            
            if composite is None:
                composite = scores * weight
            else:
                composite = composite + (scores * weight)
        
        return composite if composite is not None else pd.Series(dtype=float)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def evaluate_entities():
    """
    Example of how Mercator would use the Neural Engine Core.
    """
    
    print("🏛️ Mercator Evaluation Example\n")
    print("=" * 60)
    
    # 1. Prepare entity data (from Mercator's data layer)
    entities = pd.DataFrame({
        'entity_id': ['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
        'current_price': [150.0, 2800.0, 380.0, 3400.0],
        'previous_price': [145.0, 2750.0, 375.0, 3500.0],
    })
    
    print(f"\n📊 Evaluating {len(entities)} entities:")
    for _, row in entities.iterrows():
        print(f"   - {row['entity_id']}: ${row['current_price']:.2f}")
    
    # 2. Instantiate domain-specific components (Mercator)
    factors = [SimpleMomentumFactor()]
    profile = BalancedProfile()
    normalizer = ZScoreNormalizer()
    
    # 3. Create evaluation context
    context = EvaluationContext(
        entity_ids=entities['entity_id'].tolist(),
        profile_name="balanced",
        normalizer_name="zscore",
        mode="evaluate"
    )
    
    # 4. Execute evaluation using core
    orchestrator = EvaluationOrchestrator()
    result = orchestrator.evaluate(
        entities=entities,
        context=context,
        factors=factors,
        normalizer=normalizer,
        profile=profile
    )
    
    # 5. Display results
    print(f"\n✅ Evaluation complete in {result.duration_ms:.2f}ms")
    print(f"\n📈 Results (ranked by composite score):\n")
    
    sorted_evals = sorted(result.evaluations, key=lambda e: e.composite_score, reverse=True)
    
    for eval in sorted_evals:
        print(f"   #{eval.rank} {eval.entity_id:6s} | Score: {eval.composite_score:6.3f}")
        
        for contrib in eval.factor_contributions:
            print(f"      └─ {contrib.factor_name}: "
                  f"raw={contrib.raw_value:6.3f}, "
                  f"norm={contrib.normalized_value:6.3f}, "
                  f"contrib={contrib.contribution:6.3f}")
    
    print("\n" + "=" * 60)
    print("✅ Core remains domain-agnostic!")
    print("   - No knowledge of stocks, prices, or momentum")
    print("   - Only computed: factor → normalize → aggregate")
    print("   - All domain logic lives in Mercator")


if __name__ == "__main__":
    # Run the example (will work once pandas is available)
    try:
        evaluate_entities()
    except ImportError as e:
        print(f"⚠️  Cannot run example: {e}")
        print("\nThis example demonstrates the proper architecture:")
        print("1. Core provides abstract interfaces and orchestration")
        print("2. Verticals (like Mercator) implement domain-specific factors")
        print("3. Core has ZERO knowledge of the domain")
