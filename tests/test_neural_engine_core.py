"""
Unit tests for Neural Engine Core.

Tests the domain-agnostic computational substrate with mock implementations.
"""

import pytest
import pandas as pd
from datetime import datetime, timezone

from vitruvyan_core.core.cognitive.neural_engine import (
    AbstractFactor,
    NormalizerStrategy,
    AggregationProfile,
    EvaluationContext,
    EvaluationOrchestrator,
    ZScoreNormalizer
)

# Optional patterns for extended tests
from vitruvyan_core.patterns.neural_engine import (
    FactorRegistry,
    ProfileRegistry,
    NormalizerRegistry,
    MinMaxNormalizer,
    RankNormalizer
)


# Mock Factor Implementation
class MockFactor(AbstractFactor):
    """Simple mock factor for testing."""
    
    def __init__(self, factor_name: str, values: dict, higher_better: bool = True):
        self._name = factor_name
        self._values = values
        self._higher_better = higher_better
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def higher_is_better(self) -> bool:
        return self._higher_better
    
    def compute(self, entities: pd.DataFrame, context: EvaluationContext) -> pd.Series:
        return pd.Series(self._values)


# Mock Aggregation Profile
class MockProfile(AggregationProfile):
    """Simple weighted average profile for testing."""
    
    def __init__(self, profile_name: str, weights: dict):
        self._name = profile_name
        self._weights = weights
    
    @property
    def name(self) -> str:
        return self._name
    
    def get_weights(self, available_factors: list) -> dict:
        # Return weights for available factors, recalibrated to sum to 1.0
        weights = {f: self._weights.get(f, 0.0) for f in available_factors}
        total = sum(weights.values())
        if total > 0:
            weights = {f: w / total for f, w in weights.items()}
        return weights
    
    def aggregate(self, factor_scores: dict) -> pd.Series:
        weights = self.get_weights(list(factor_scores.keys()))
        composite = None
        
        for factor_name, scores in factor_scores.items():
            weight = weights.get(factor_name, 0.0)
            if composite is None:
                composite = scores * weight
            else:
                composite = composite + (scores * weight)
        
        return composite


class TestNormalizers:
    """Test normalization strategies."""
    
    def test_zscore_normalizer(self):
        """Test z-score normalization."""
        normalizer = ZScoreNormalizer()
        assert normalizer.name == "zscore"
        
        # Test with known values
        raw = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = normalizer.normalize(raw)
        
        # Z-scores should have mean=0, std=1
        assert abs(normalized.mean()) < 0.001
        assert abs(normalized.std() - 1.0) < 0.001
    
    def test_zscore_zero_variance(self):
        """Test z-score with zero variance."""
        normalizer = ZScoreNormalizer()
        raw = pd.Series([5.0, 5.0, 5.0])
        normalized = normalizer.normalize(raw)
        
        # All values should be 0.0
        assert all(normalized == 0.0)
    
    def test_minmax_normalizer(self):
        """Test min-max normalization."""
        normalizer = MinMaxNormalizer()
        assert normalizer.name == "minmax"
        
        raw = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = normalizer.normalize(raw)
        
        # Should be scaled to [0, 1]
        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
    
    def test_minmax_no_variance(self):
        """Test min-max with no variance."""
        normalizer = MinMaxNormalizer()
        raw = pd.Series([5.0, 5.0, 5.0])
        normalized = normalizer.normalize(raw)
        
        # All values should be 0.5
        assert all(normalized == 0.5)
    
    def test_rank_normalizer(self):
        """Test rank normalization."""
        normalizer = RankNormalizer()
        assert normalizer.name == "rank"
        
        raw = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized = normalizer.normalize(raw)
        
        # Should be percentile ranks in [0, 1]
        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
    
    def test_normalizer_invert_direction(self):
        """Test normalizers with lower_is_better."""
        raw = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Min-max with lower is better
        normalizer = MinMaxNormalizer()
        normalized = normalizer.normalize(raw, higher_is_better=False)
        
        # Highest raw value should have lowest normalized value
        assert normalized.iloc[0] == 1.0  # raw=1 -> norm=1
        assert normalized.iloc[-1] == 0.0  # raw=5 -> norm=0


class TestRegistries:
    """Test registration mechanisms."""
    
    def test_factor_registry(self):
        """Test factor registration and retrieval."""
        registry = FactorRegistry()
        
        factor = MockFactor("test_factor", {"A": 1.0, "B": 2.0})
        registry.register(factor)
        
        # Retrieve factor
        retrieved = registry.get("test_factor")
        assert retrieved is not None
        assert retrieved.name == "test_factor"
        
        # List names
        names = registry.list_names()
        assert "test_factor" in names
        
        # Duplicate registration should fail
        with pytest.raises(ValueError):
            registry.register(factor)
    
    def test_profile_registry(self):
        """Test profile registration and retrieval."""
        registry = ProfileRegistry()
        
        profile = MockProfile("test_profile", {"factor_a": 0.6, "factor_b": 0.4})
        registry.register(profile)
        
        retrieved = registry.get("test_profile")
        assert retrieved is not None
        assert retrieved.name == "test_profile"
    
    def test_normalizer_registry(self):
        """Test normalizer registration."""
        registry = NormalizerRegistry()
        
        normalizer = ZScoreNormalizer()
        registry.register(normalizer)
        
        retrieved = registry.get("zscore")
        assert retrieved is not None
        assert retrieved.name == "zscore"


class TestOrchestrator:
    """Test evaluation orchestration."""
    
    def test_basic_evaluation(self):
        """Test complete evaluation pipeline."""
        # Setup entities
        entities = pd.DataFrame({
            'entity_id': ['A', 'B', 'C'],
        })
        
        # Setup factors
        factor1 = MockFactor("factor1", {"A": 10.0, "B": 20.0, "C": 30.0})
        factor2 = MockFactor("factor2", {"A": 5.0, "B": 15.0, "C": 25.0})
        factors = [factor1, factor2]
        
        # Setup normalizer and profile
        normalizer = ZScoreNormalizer()
        profile = MockProfile("balanced", {"factor1": 0.5, "factor2": 0.5})
        
        # Create context
        context = EvaluationContext(
            entity_ids=['A', 'B', 'C'],
            profile_name="balanced"
        )
        
        # Execute evaluation
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(entities, context, factors, normalizer, profile)
        
        # Verify result structure
        assert result.entity_count == 3
        assert len(result.evaluations) == 3
        assert result.normalizer_used == "zscore"
        assert result.profile_used == "balanced"
        assert result.factors_used == ["factor1", "factor2"]
        
        # Verify entity evaluations
        for eval in result.evaluations:
            assert eval.entity_id in ['A', 'B', 'C']
            assert eval.composite_score is not None
            assert eval.rank is not None
            assert len(eval.factor_contributions) == 2
            
            # Verify contributions sum to composite
            total_contribution = sum(c.contribution for c in eval.factor_contributions)
            assert abs(total_contribution - eval.composite_score) < 0.001
    
    def test_empty_entities(self):
        """Test evaluation with no entities."""
        entities = pd.DataFrame({'entity_id': []})
        
        factor = MockFactor("factor1", {})
        normalizer = ZScoreNormalizer()
        profile = MockProfile("balanced", {"factor1": 1.0})
        context = EvaluationContext(entity_ids=[], profile_name="balanced")
        
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(entities, context, [factor], normalizer, profile)
        
        assert result.entity_count == 0
        assert len(result.evaluations) == 0
    
    def test_single_entity(self):
        """Test evaluation with single entity."""
        entities = pd.DataFrame({'entity_id': ['A']})
        
        factor = MockFactor("factor1", {"A": 42.0})
        normalizer = MinMaxNormalizer()
        profile = MockProfile("balanced", {"factor1": 1.0})
        context = EvaluationContext(entity_ids=['A'], profile_name="balanced")
        
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(entities, context, [factor], normalizer, profile)
        
        assert result.entity_count == 1
        assert result.evaluations[0].entity_id == 'A'
        assert result.evaluations[0].rank == 1
    
    def test_missing_entity_id_column(self):
        """Test that missing entity_id column raises error."""
        entities = pd.DataFrame({'some_other_column': ['A', 'B']})
        
        factor = MockFactor("factor1", {})
        normalizer = ZScoreNormalizer()
        profile = MockProfile("balanced", {"factor1": 1.0})
        context = EvaluationContext(entity_ids=[], profile_name="balanced")
        
        orchestrator = EvaluationOrchestrator()
        
        with pytest.raises(ValueError, match="entity_id"):
            orchestrator.evaluate(entities, context, [factor], normalizer, profile)


class TestIntegration:
    """Integration tests with full pipeline."""
    
    def test_ranking_order(self):
        """Test that entities are ranked correctly."""
        entities = pd.DataFrame({'entity_id': ['LOW', 'MED', 'HIGH']})
        
        # Single factor with clear ordering
        factor = MockFactor("score", {"LOW": 10.0, "MED": 50.0, "HIGH": 90.0})
        normalizer = ZScoreNormalizer()
        profile = MockProfile("simple", {"score": 1.0})
        context = EvaluationContext(entity_ids=['LOW', 'MED', 'HIGH'], profile_name="simple")
        
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(entities, context, [factor], normalizer, profile)
        
        # Find ranks
        ranks = {e.entity_id: e.rank for e in result.evaluations}
        
        assert ranks['HIGH'] == 1
        assert ranks['MED'] == 2
        assert ranks['LOW'] == 3
    
    def test_weight_recalibration(self):
        """Test that weights are recalibrated when factor missing."""
        entities = pd.DataFrame({'entity_id': ['A']})
        
        factor1 = MockFactor("present", {"A": 10.0})
        normalizer = ZScoreNormalizer()
        
        # Profile expects two factors but only one provided
        profile = MockProfile("unbalanced", {"present": 0.3, "missing": 0.7})
        context = EvaluationContext(entity_ids=['A'], profile_name="unbalanced")
        
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(entities, context, [factor1], normalizer, profile)
        
        # Weight for present factor should be 1.0 (recalibrated)
        contrib = result.evaluations[0].factor_contributions[0]
        assert contrib.weight == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
