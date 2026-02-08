"""
Mock Scoring Strategy (for testing)
===================================

Minimal implementation of IScoringStrategy for testing Neural Engine.

Author: vitruvyan-core
Date: February 8, 2026
"""

from typing import Dict, List
import pandas as pd

from vitruvyan_core.contracts import IScoringStrategy


class MockScoringStrategy(IScoringStrategy):
    """
    Mock scoring strategy for testing.
    
    Provides 2 profiles:
    - balanced: Equal weights (33% each)
    - aggressive: Momentum-heavy (60% momentum, 20% trend, 20% volatility)
    """
    
    PROFILES = {
        "balanced": {
            "momentum": 0.33,
            "trend": 0.33,
            "volatility": 0.34
        },
        "aggressive": {
            "momentum": 0.60,
            "trend": 0.20,
            "volatility": 0.20
        }
    }
    
    def get_profile_weights(self, profile: str) -> Dict[str, float]:
        """Returns weights for profile."""
        if profile not in self.PROFILES:
            raise ValueError(f"Profile '{profile}' not found")
        return self.PROFILES[profile]
    
    def get_available_profiles(self) -> List[str]:
        """Returns available profile names."""
        return list(self.PROFILES.keys())
    
    def compute_composite_score(
        self, 
        df: pd.DataFrame, 
        profile: str,
        z_score_columns: List[str]
    ) -> pd.DataFrame:
        """
        Computes composite score (delegated to CompositeScorer).
        This is a pass-through implementation.
        """
        # This method is typically handled by CompositeScorer
        # For mock, we return df as-is
        return df


# Add to test file
if __name__ == "__main__":
    from vitruvyan_core.core.neural_engine import NeuralEngine
    
    # Initialize with mock implementations
    provider = MockDataProvider()
    strategy = MockScoringStrategy()
    
    engine = NeuralEngine(
        data_provider=provider,
        scoring_strategy=strategy,
        stratification_mode="composite"
    )
    
    # Run ranking
    result = engine.run(
        profile="balanced",
        top_k=5
    )
    
    print("\n=== Neural Engine Test (Mock Data) ===")
    print(f"Domain: {result['metadata']['domain']}")
    print(f"Profile: {result['metadata']['profile']}")
    print(f"Entities scored: {result['metadata']['total_entities_scored']}")
    print(f"\nTop {len(result['ranked_entities'])} entities:")
    print(result['ranked_entities'][['entity_id', 'rank', 'composite_score', 'percentile', 'bucket']])
    print(f"\nBucket statistics: {result['statistics']}")
