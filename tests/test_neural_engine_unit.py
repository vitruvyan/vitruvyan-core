"""
Neural Engine — Unit Tests
===========================

Covers all core components with non-regression, edge case, and parametrization tests.

Author: vitruvyan-core
Date: February 11, 2026
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from vitruvyan_core.core.neural_engine.scoring import ZScoreCalculator
from vitruvyan_core.core.neural_engine.composite import CompositeScorer
from vitruvyan_core.core.neural_engine.ranking import RankingEngine


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_df():
    """Standard 6-entity DataFrame with 2 features and a stratification group."""
    return pd.DataFrame({
        "entity_id": ["E001", "E002", "E003", "E004", "E005", "E006"],
        "group": ["A", "A", "A", "B", "B", "B"],
        "momentum": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "trend": [5.0, 15.0, 25.0, 35.0, 45.0, 55.0],
    })


@pytest.fixture
def sample_df_with_nan():
    """DataFrame with NaN values for edge-case testing."""
    return pd.DataFrame({
        "entity_id": ["E001", "E002", "E003", "E004"],
        "group": ["A", "A", "B", "B"],
        "momentum": [10.0, np.nan, 30.0, 40.0],
        "trend": [np.nan, 15.0, 25.0, np.nan],
    })


@pytest.fixture
def mock_strategy():
    """Mock IScoringStrategy with 2 profiles."""
    strategy = MagicMock()
    strategy.validate_profile.return_value = True
    strategy.get_profile_weights.return_value = {
        "momentum": 0.6,
        "trend": 0.4,
    }
    strategy.get_available_profiles.return_value = ["balanced", "aggressive"]
    strategy.apply_risk_adjustment.side_effect = lambda df, **kw: df
    return strategy


# ============================================================================
# Z-SCORE CALCULATOR TESTS
# ============================================================================

class TestZScoreCalculator:

    def test_global_z_scores_mean_zero(self, sample_df):
        """Global z-scores must have mean ≈ 0."""
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(sample_df, ["momentum", "trend"])

        assert "momentum_z" in out.columns
        assert "trend_z" in out.columns
        assert abs(out["momentum_z"].mean()) < 1e-10
        assert abs(out["trend_z"].mean()) < 1e-10

    def test_global_z_scores_std_one(self, sample_df):
        """Global z-scores on uniform data must have std ≈ 1 (population std)."""
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(sample_df, ["momentum"])
        # With ddof=0 (population), std of z-scores should be 1.0
        assert abs(out["momentum_z"].std(ddof=0) - 1.0) < 1e-10

    def test_stratified_z_scores(self, sample_df):
        """Stratified z-scores computed per group."""
        calc = ZScoreCalculator(
            stratification_mode="stratified",
            stratification_field="group"
        )
        out = calc.compute_z_scores(sample_df, ["momentum"])
        # Within each group, mean should be ~0
        for g in ["A", "B"]:
            group_z = out.loc[out["group"] == g, "momentum_z"]
            assert abs(group_z.mean()) < 1e-10

    def test_composite_z_default_weights(self, sample_df):
        """Composite mode should blend 30% global + 70% stratified by default."""
        calc = ZScoreCalculator(
            stratification_mode="composite",
            stratification_field="group"
        )
        out = calc.compute_z_scores(sample_df, ["momentum"])

        # Verify manually
        calc_g = ZScoreCalculator(stratification_mode="global")
        calc_s = ZScoreCalculator(stratification_mode="stratified", stratification_field="group")
        out_g = calc_g.compute_z_scores(sample_df, ["momentum"])
        out_s = calc_s.compute_z_scores(sample_df, ["momentum"])

        expected = 0.3 * out_g["momentum_z"] + 0.7 * out_s["momentum_z"]
        pd.testing.assert_series_equal(
            out["momentum_z"], expected, check_names=False, atol=1e-10
        )

    def test_composite_z_custom_weight(self, sample_df):
        """Composite mode with custom 50/50 weight."""
        calc = ZScoreCalculator(
            stratification_mode="composite",
            stratification_field="group",
            composite_global_weight=0.5
        )
        out = calc.compute_z_scores(sample_df, ["momentum"])

        calc_g = ZScoreCalculator(stratification_mode="global")
        calc_s = ZScoreCalculator(stratification_mode="stratified", stratification_field="group")
        out_g = calc_g.compute_z_scores(sample_df, ["momentum"])
        out_s = calc_s.compute_z_scores(sample_df, ["momentum"])

        expected = 0.5 * out_g["momentum_z"] + 0.5 * out_s["momentum_z"]
        pd.testing.assert_series_equal(
            out["momentum_z"], expected, check_names=False, atol=1e-10
        )

    def test_composite_global_weight_validation(self):
        """Invalid composite_global_weight raises ValueError."""
        with pytest.raises(ValueError, match="composite_global_weight"):
            ZScoreCalculator(
                stratification_mode="global",
                composite_global_weight=1.5
            )
        with pytest.raises(ValueError, match="composite_global_weight"):
            ZScoreCalculator(
                stratification_mode="global",
                composite_global_weight=-0.1
            )

    def test_missing_stratification_field_raises(self):
        """Stratified/composite without field raises ValueError."""
        with pytest.raises(ValueError, match="stratification_field"):
            ZScoreCalculator(stratification_mode="stratified")
        with pytest.raises(ValueError, match="stratification_field"):
            ZScoreCalculator(stratification_mode="composite")

    def test_single_entity(self):
        """Single entity returns NaN z-scores (no variance)."""
        df = pd.DataFrame({"entity_id": ["E001"], "x": [42.0]})
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(df, ["x"])
        assert pd.isna(out["x_z"].iloc[0])

    def test_constant_values(self):
        """Constant values return 0.0 z-scores (sigma=0)."""
        df = pd.DataFrame({"entity_id": ["E001", "E002", "E003"], "x": [5.0, 5.0, 5.0]})
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(df, ["x"])
        assert (out["x_z"] == 0.0).all()

    def test_nan_handling(self, sample_df_with_nan):
        """NaN values in features are propagated as NaN z-scores."""
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(sample_df_with_nan, ["momentum", "trend"])
        assert pd.isna(out.loc[1, "momentum_z"])  # E002 momentum is NaN
        assert pd.isna(out.loc[0, "trend_z"])      # E001 trend is NaN

    def test_custom_output_suffix(self, sample_df):
        """Custom suffix produces correctly named columns."""
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(sample_df, ["momentum"], output_suffix="_zscore")
        assert "momentum_zscore" in out.columns
        assert "momentum_z" not in out.columns

    def test_missing_column_skipped(self, sample_df):
        """Non-existent column is silently skipped."""
        calc = ZScoreCalculator(stratification_mode="global")
        out = calc.compute_z_scores(sample_df, ["momentum", "nonexistent"])
        assert "momentum_z" in out.columns
        assert "nonexistent_z" not in out.columns


# ============================================================================
# COMPOSITE SCORER TESTS
# ============================================================================

class TestCompositeScorer:

    def _make_z_df(self):
        """Helper: 4-entity DataFrame with pre-computed z-scores."""
        return pd.DataFrame({
            "entity_id": ["E001", "E002", "E003", "E004"],
            "momentum_z": [1.5, -0.5, 0.0, 2.0],
            "trend_z": [0.8, 1.2, -1.0, 0.5],
        })

    def test_composite_score_values(self, mock_strategy):
        """Verify composite score = weighted average of z-scores."""
        scorer = CompositeScorer(mock_strategy)
        df = self._make_z_df()
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        out = scorer.compute_composite_scores(df, "balanced", mapping)

        # Manual check for E001: (1.5*0.6 + 0.8*0.4) / (0.6+0.4) = 1.22
        expected_e001 = (1.5 * 0.6 + 0.8 * 0.4) / 1.0
        assert abs(out.loc[0, "composite_score"] - expected_e001) < 1e-10

    def test_vectorized_matches_manual(self, mock_strategy):
        """Vectorized implementation matches manual per-row calculation."""
        scorer = CompositeScorer(mock_strategy)
        df = self._make_z_df()
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        weights = mock_strategy.get_profile_weights("balanced")
        out = scorer.compute_composite_scores(df, "balanced", mapping)

        for idx, row in df.iterrows():
            expected = (
                row["momentum_z"] * weights["momentum"]
                + row["trend_z"] * weights["trend"]
            ) / sum(weights.values())
            assert abs(out.loc[idx, "composite_score"] - expected) < 1e-10

    def test_nan_z_score_dynamic_normalization(self, mock_strategy):
        """NaN z-scores excluded; weights renormalized dynamically."""
        scorer = CompositeScorer(mock_strategy)
        df = pd.DataFrame({
            "entity_id": ["E001"],
            "momentum_z": [1.5],
            "trend_z": [np.nan],  # trend missing
        })
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        out = scorer.compute_composite_scores(df, "balanced", mapping)

        # Only momentum present: composite = 1.5 * (0.6/0.6) = 1.5
        assert abs(out.loc[0, "composite_score"] - 1.5) < 1e-10

    def test_all_nan_returns_nan(self, mock_strategy):
        """All z-scores NaN → composite_score = NaN."""
        scorer = CompositeScorer(mock_strategy)
        df = pd.DataFrame({
            "entity_id": ["E001"],
            "momentum_z": [np.nan],
            "trend_z": [np.nan],
        })
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        out = scorer.compute_composite_scores(df, "balanced", mapping)
        assert pd.isna(out.loc[0, "composite_score"])

    def test_weights_used_column(self, mock_strategy):
        """weights_used column contains normalized per-entity weights."""
        scorer = CompositeScorer(mock_strategy)
        df = self._make_z_df()
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        out = scorer.compute_composite_scores(df, "balanced", mapping)

        assert "weights_used" in out.columns
        # All entities have both features → weights should be {momentum: 0.6, trend: 0.4}
        for wu in out["weights_used"]:
            assert abs(wu["momentum"] - 0.6) < 0.01
            assert abs(wu["trend"] - 0.4) < 0.01

    def test_invalid_profile_raises(self, mock_strategy):
        """Invalid profile raises ValueError."""
        mock_strategy.validate_profile.return_value = False
        scorer = CompositeScorer(mock_strategy)
        df = self._make_z_df()
        with pytest.raises(ValueError, match="Invalid profile"):
            scorer.compute_composite_scores(df, "nonexistent", {})

    def test_empty_dataframe(self, mock_strategy):
        """Empty DataFrame returns empty with score columns."""
        scorer = CompositeScorer(mock_strategy)
        df = pd.DataFrame(columns=["entity_id", "momentum_z", "trend_z"])
        mapping = {"momentum": "momentum_z", "trend": "trend_z"}
        out = scorer.compute_composite_scores(df, "balanced", mapping)
        assert len(out) == 0
        assert "composite_score" in out.columns


# ============================================================================
# RANKING ENGINE TESTS
# ============================================================================

class TestRankingEngine:

    def _make_scored_df(self):
        """Helper: 5-entity DataFrame with composite scores."""
        return pd.DataFrame({
            "entity_id": ["E001", "E002", "E003", "E004", "E005"],
            "composite_score": [1.5, 0.3, 2.0, -0.5, 0.8],
        })

    def test_ranking_order(self):
        """Entities ranked correctly (highest score = rank 1)."""
        ranker = RankingEngine()
        df = self._make_scored_df()
        out = ranker.rank_entities(df)

        assert out.iloc[0]["entity_id"] == "E003"  # score 2.0 → rank 1
        assert out.iloc[1]["entity_id"] == "E001"  # score 1.5 → rank 2
        assert out.iloc[0]["rank"] == 1
        assert out.iloc[1]["rank"] == 2

    def test_top_k_selection(self):
        """Top-K returns only K entities."""
        ranker = RankingEngine()
        df = self._make_scored_df()
        out = ranker.rank_entities(df, top_k=2)
        assert len(out) == 2
        assert out.iloc[0]["rank"] == 1

    def test_percentile_range(self):
        """Percentiles in [0, 100]."""
        ranker = RankingEngine()
        df = self._make_scored_df()
        out = ranker.rank_entities(df)
        assert out["percentile"].min() >= 0
        assert out["percentile"].max() <= 100

    def test_bucket_classification_default(self):
        """Default thresholds: top>=70, bottom<30."""
        ranker = RankingEngine()
        # 10 entities → rank 1 = 100th pct (top), rank 10 = 10th pct (bottom)
        df = pd.DataFrame({
            "entity_id": [f"E{i:03d}" for i in range(1, 11)],
            "composite_score": list(range(10, 0, -1)),
        })
        out = ranker.rank_entities(df)
        assert (out.loc[out["percentile"] >= 70, "bucket"] == "top").all()
        assert (out.loc[out["percentile"] < 30, "bucket"] == "bottom").all()
        mid = out.loc[(out["percentile"] >= 30) & (out["percentile"] < 70)]
        assert (mid["bucket"] == "middle").all()

    def test_bucket_custom_thresholds(self):
        """Custom thresholds change bucket assignment."""
        ranker = RankingEngine(bucket_top_threshold=80.0, bucket_bottom_threshold=20.0)
        df = pd.DataFrame({
            "entity_id": [f"E{i:03d}" for i in range(1, 11)],
            "composite_score": list(range(10, 0, -1)),
        })
        out = ranker.rank_entities(df)
        assert (out.loc[out["percentile"] >= 80, "bucket"] == "top").all()
        assert (out.loc[out["percentile"] < 20, "bucket"] == "bottom").all()

    def test_invalid_thresholds(self):
        """Invalid bucket thresholds raise ValueError."""
        with pytest.raises(ValueError, match="Invalid bucket thresholds"):
            RankingEngine(bucket_top_threshold=30, bucket_bottom_threshold=70)
        with pytest.raises(ValueError, match="Invalid bucket thresholds"):
            RankingEngine(bucket_top_threshold=50, bucket_bottom_threshold=50)

    def test_nan_scores_excluded(self):
        """Entities with NaN scores are excluded from ranking."""
        ranker = RankingEngine()
        df = pd.DataFrame({
            "entity_id": ["E001", "E002", "E003"],
            "composite_score": [1.0, np.nan, 0.5],
        })
        out = ranker.rank_entities(df)
        assert len(out) == 2
        assert "E002" not in out["entity_id"].values

    def test_empty_scores_returns_empty(self):
        """All NaN scores returns empty DataFrame."""
        ranker = RankingEngine()
        df = pd.DataFrame({
            "entity_id": ["E001", "E002"],
            "composite_score": [np.nan, np.nan],
        })
        out = ranker.rank_entities(df)
        assert len(out) == 0

    def test_single_entity(self):
        """Single entity gets rank=1, percentile=100, bucket=top."""
        ranker = RankingEngine()
        df = pd.DataFrame({
            "entity_id": ["E001"],
            "composite_score": [1.0],
        })
        out = ranker.rank_entities(df)
        assert out.iloc[0]["rank"] == 1
        assert out.iloc[0]["percentile"] == 100.0
        assert out.iloc[0]["bucket"] == "top"

    def test_bucket_statistics(self):
        """Bucket statistics sum correctly."""
        ranker = RankingEngine()
        df = pd.DataFrame({
            "entity_id": [f"E{i:03d}" for i in range(1, 11)],
            "composite_score": list(range(10, 0, -1)),
        })
        ranked = ranker.rank_entities(df)
        stats = ranker.get_bucket_statistics(ranked)
        assert stats["total"] == 10
        assert stats["top_count"] + stats["middle_count"] + stats["bottom_count"] == 10


# ============================================================================
# INTEGRATION: NeuralEngine end-to-end
# ============================================================================

class TestNeuralEngineIntegration:
    """End-to-end tests using mock provider + strategy."""

    def test_run_default_params(self):
        """NeuralEngine.run() with defaults produces valid output."""
        from vitruvyan_core.core.neural_engine import NeuralEngine
        from vitruvyan_core.core.neural_engine.domain_examples import (
            MockDataProvider, MockScoringStrategy
        )

        engine = NeuralEngine(
            data_provider=MockDataProvider(num_entities=20),
            scoring_strategy=MockScoringStrategy(),
            stratification_mode="global"
        )

        result = engine.run(profile="balanced", top_k=5)

        assert len(result["ranked_entities"]) == 5
        assert result["metadata"]["profile"] == "balanced"
        assert result["metadata"]["top_k"] == 5
        assert result["ranked_entities"].iloc[0]["rank"] == 1
        assert "composite_score" in result["ranked_entities"].columns
        assert "bucket" in result["ranked_entities"].columns

    def test_run_composite_stratification(self):
        """Composite stratification mode with custom weight."""
        from vitruvyan_core.core.neural_engine import NeuralEngine
        from vitruvyan_core.core.neural_engine.domain_examples import (
            MockDataProvider, MockScoringStrategy
        )

        provider = MockDataProvider(num_entities=20)
        # Mock provider metadata must include stratification_field for composite mode
        original_meta = provider.get_metadata()
        original_meta["stratification_field"] = "group"
        provider.get_metadata = lambda: original_meta

        engine = NeuralEngine(
            data_provider=provider,
            scoring_strategy=MockScoringStrategy(),
            stratification_mode="composite",
            composite_global_weight=0.5
        )

        result = engine.run(profile="balanced")
        assert len(result["ranked_entities"]) > 0

    def test_run_custom_bucket_thresholds(self):
        """Custom bucket thresholds propagated to RankingEngine."""
        from vitruvyan_core.core.neural_engine import NeuralEngine
        from vitruvyan_core.core.neural_engine.domain_examples import (
            MockDataProvider, MockScoringStrategy
        )

        engine = NeuralEngine(
            data_provider=MockDataProvider(num_entities=50),
            scoring_strategy=MockScoringStrategy(),
            bucket_top_threshold=80.0,
            bucket_bottom_threshold=20.0
        )

        result = engine.run(profile="balanced")
        ranked = result["ranked_entities"]

        # With 80/20 thresholds, fewer entities in "top" than default 70/30
        top_pct = (ranked["bucket"] == "top").mean() * 100
        assert top_pct <= 25  # ~20% should be in top with 80 threshold

    def test_invalid_profile_raises(self):
        """Invalid profile raises ValueError."""
        from vitruvyan_core.core.neural_engine import NeuralEngine
        from vitruvyan_core.core.neural_engine.domain_examples import (
            MockDataProvider, MockScoringStrategy
        )

        engine = NeuralEngine(
            data_provider=MockDataProvider(),
            scoring_strategy=MockScoringStrategy(),
        )

        with pytest.raises(ValueError, match="Invalid profile"):
            engine.run(profile="nonexistent_profile")
