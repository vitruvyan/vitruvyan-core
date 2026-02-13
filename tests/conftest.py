"""
Vitruvyan Core — Global Test Configuration
============================================

Shared fixtures, mock factories, and test utilities used across
all test types (unit, integration, architectural, e2e).

Pattern:
  - Fixtures are scoped appropriately (session, module, function)
  - Mock providers implement domain contracts (ABC) with controlled data
  - No real I/O in unit-level fixtures

Usage:
  Fixtures are auto-discovered by pytest. Just use them as function args:

    def test_something(mock_explainability_provider):
        engine = VEEEngine()
        result = engine.explain("E1", {"score": 0.8}, mock_explainability_provider)
"""

import os
import sys
import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime

# ─── Ensure vitruvyan_core is importable ────────────────────────────
# This mirrors what Docker containers do via PYTHONPATH=/app/vitruvyan_core
_core_path = os.path.join(os.path.dirname(__file__), "..", "vitruvyan_core")
if _core_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_core_path))


# ═══════════════════════════════════════════════════════════════════
# MOCK PROVIDERS — Implement domain contracts for testing
# ═══════════════════════════════════════════════════════════════════

# --- ExplainabilityProvider (for VEE) ---
try:
    from domains.explainability_contract import (
        ExplainabilityProvider, ExplanationTemplate, NormalizationRule,
        AnalysisDimension, PatternRule, ConfidenceCriteria, MetricDefinition
    )

    class MockExplainabilityProvider(ExplainabilityProvider):
        """Deterministic mock provider for VEE testing."""

        def get_explanation_templates(self) -> ExplanationTemplate:
            return ExplanationTemplate(
                summary_template="Entity {entity_ref} shows {direction} signals. Key: {primary_factor}.",
                technical_template="Analysis of {entity_ref}: {metrics_count} metrics, intensity={intensity:.2f}.",
                detailed_template="Full analysis for {entity_ref}: {factor_details}.",
            )

        def format_entity_reference(self, entity_id: str) -> str:
            return f"[{entity_id}]"

        def get_normalization_rules(self) -> List[NormalizationRule]:
            return [
                NormalizationRule(metric_pattern="score", method="linear"),
                NormalizationRule(metric_pattern="ratio", method="linear", min_value=0.0, max_value=1.0),
                NormalizationRule(metric_pattern="volume", method="log"),
            ]

        def get_analysis_dimensions(self) -> List[AnalysisDimension]:
            return [
                AnalysisDimension(name="quality", metric_keys=["score", "accuracy"], display_name="Quality"),
                AnalysisDimension(name="volume", metric_keys=["count", "throughput"], display_name="Volume"),
            ]

        def get_pattern_rules(self) -> List[PatternRule]:
            return [
                PatternRule(name="high_quality", display_text="High quality signal detected"),
                PatternRule(name="low_volume", display_text="Low volume warning"),
            ]

        def get_intensity_weights(self) -> Dict[str, float]:
            return {"score": 0.4, "accuracy": 0.3, "count": 0.2, "throughput": 0.1}

        def get_confidence_criteria(self) -> ConfidenceCriteria:
            return ConfidenceCriteria(
                min_metrics_high=3, min_metrics_moderate=2,
                min_signals_high=2, consistency_threshold=0.3
            )

        def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
            return {
                "score": MetricDefinition(name="score", description="Composite score", unit="points",
                                          interpretation="higher is better", normal_range=(0.0, 100.0)),
            }
except ImportError:
    MockExplainabilityProvider = None


# --- RiskProvider (for VARE) ---
try:
    from domains.risk_contract import RiskProvider, RiskDimension, RiskProfile
    import pandas as pd

    class MockRiskProvider(RiskProvider):
        """Deterministic mock provider for VARE testing."""

        def get_risk_dimensions(self) -> List[RiskDimension]:
            return [
                RiskDimension(
                    name="volatility", description="Price volatility",
                    calculation_fn=lambda df: float(df["values"].std()) if "values" in df.columns else 0.0,
                    threshold_low=10.0, threshold_moderate=25.0, threshold_high=50.0,
                    unit="percent", higher_is_riskier=True
                ),
                RiskDimension(
                    name="concentration", description="Concentration risk",
                    calculation_fn=lambda df: float(df["weight"].max()) if "weight" in df.columns else 0.0,
                    threshold_low=20.0, threshold_moderate=40.0, threshold_high=60.0,
                    unit="percent", higher_is_riskier=True
                ),
            ]

        def get_risk_profiles(self) -> Dict[str, RiskProfile]:
            return {
                "conservative": RiskProfile(
                    name="conservative", description="Low risk tolerance",
                    dimension_weights={"volatility": 0.6, "concentration": 0.4}
                ),
                "balanced": RiskProfile(
                    name="balanced", description="Moderate risk tolerance",
                    dimension_weights={"volatility": 0.5, "concentration": 0.5}
                ),
            }

        def prepare_entity_data(self, entity_id: str, raw_data: Dict[str, Any]) -> "pd.DataFrame":
            return pd.DataFrame(raw_data)

        def get_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
            return {
                "volatility": {"LOW": 10.0, "MODERATE": 25.0, "HIGH": 50.0},
                "concentration": {"LOW": 20.0, "MODERATE": 40.0, "HIGH": 60.0},
            }

        def format_risk_explanation(self, dimension_scores, overall_risk, risk_category) -> Dict[str, str]:
            return {
                "summary": f"Risk level: {risk_category} ({overall_risk:.1f})",
                "technical": f"Dimensions: {len(dimension_scores)} evaluated",
            }
except ImportError:
    MockRiskProvider = None


# --- AggregationProvider (for VWRE) ---
try:
    from domains.aggregation_contract import AggregationProvider, AggregationProfile

    class MockAggregationProvider(AggregationProvider):
        """Deterministic mock provider for VWRE testing."""

        def get_aggregation_profiles(self) -> Dict[str, AggregationProfile]:
            return {
                "balanced": AggregationProfile(
                    name="balanced", description="Equal weight",
                    factor_weights={"alpha": 0.25, "beta": 0.25, "gamma": 0.25, "delta": 0.25}
                ),
                "aggressive": AggregationProfile(
                    name="aggressive", description="High alpha weight",
                    factor_weights={"alpha": 0.5, "beta": 0.2, "gamma": 0.2, "delta": 0.1}
                ),
            }

        def get_factor_mappings(self) -> Dict[str, str]:
            return {"alpha": "Alpha Factor", "beta": "Beta Factor",
                    "gamma": "Gamma Factor", "delta": "Delta Factor"}

        def calculate_contribution(self, factor_value: float, weight: float, profile: str) -> float:
            return factor_value * weight

        def validate_factors(self, factors: Dict[str, float]) -> Dict[str, Any]:
            known = {"alpha", "beta", "gamma", "delta"}
            unknown = set(factors.keys()) - known
            return {"valid": len(unknown) == 0, "unknown_factors": list(unknown),
                    "factor_count": len(factors)}

        def format_attribution_explanation(self, contributions, primary_driver, composite_score) -> Dict[str, str]:
            return {
                "summary": f"Primary driver: {primary_driver} (composite={composite_score:.2f})",
                "technical": f"{len(contributions)} factors analyzed",
            }
except ImportError:
    MockAggregationProvider = None


# --- Neural Engine Mocks (IDataProvider, IScoringStrategy) ---
try:
    from contracts.data_provider import IDataProvider
    from contracts.scoring_strategy import IScoringStrategy

    class MockDataProvider(IDataProvider):
        """Returns controlled data for Neural Engine tests."""

        def __init__(self, entities=None, features=None):
            self._entities = entities or ["E1", "E2", "E3"]
            self._features = features or {
                "E1": {"score": 80.0, "volume": 50.0, "quality": 70.0},
                "E2": {"score": 60.0, "volume": 80.0, "quality": 40.0},
                "E3": {"score": 90.0, "volume": 30.0, "quality": 85.0},
            }

        def get_entities(self, filters=None) -> List[str]:
            return self._entities

        def get_features(self, entity_id: str) -> Dict[str, float]:
            return self._features.get(entity_id, {})

        def get_domain_metadata(self) -> Dict[str, Any]:
            return {"domain": "test", "version": "1.0"}

    class MockScoringStrategy(IScoringStrategy):
        """Simple weighted sum scoring."""

        def get_profiles(self) -> Dict[str, Dict[str, float]]:
            return {
                "balanced": {"score": 0.4, "volume": 0.3, "quality": 0.3},
                "quality_first": {"score": 0.2, "volume": 0.1, "quality": 0.7},
            }

        def calculate_score(self, features: Dict[str, float], profile: str = "balanced") -> float:
            weights = self.get_profiles().get(profile, self.get_profiles()["balanced"])
            total = sum(features.get(k, 0) * w for k, w in weights.items())
            return total

        def get_feature_names(self) -> List[str]:
            return ["score", "volume", "quality"]

        def get_domain_metadata(self) -> Dict[str, Any]:
            return {"strategy": "weighted_sum", "version": "1.0"}
except ImportError:
    MockDataProvider = None
    MockScoringStrategy = None


# ═══════════════════════════════════════════════════════════════════
# PYTEST FIXTURES — Available to all tests
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_explainability_provider():
    """Provides a deterministic ExplainabilityProvider for VEE tests."""
    if MockExplainabilityProvider is None:
        pytest.skip("ExplainabilityProvider contract not importable")
    return MockExplainabilityProvider()


@pytest.fixture
def mock_risk_provider():
    """Provides a deterministic RiskProvider for VARE tests."""
    if MockRiskProvider is None:
        pytest.skip("RiskProvider contract not importable")
    return MockRiskProvider()


@pytest.fixture
def mock_aggregation_provider():
    """Provides a deterministic AggregationProvider for VWRE tests."""
    if MockAggregationProvider is None:
        pytest.skip("AggregationProvider contract not importable")
    return MockAggregationProvider()


@pytest.fixture
def mock_data_provider():
    """Provides a deterministic IDataProvider for Neural Engine tests."""
    if MockDataProvider is None:
        pytest.skip("IDataProvider contract not importable")
    return MockDataProvider()


@pytest.fixture
def mock_scoring_strategy():
    """Provides a deterministic IScoringStrategy for Neural Engine tests."""
    if MockScoringStrategy is None:
        pytest.skip("IScoringStrategy contract not importable")
    return MockScoringStrategy()


@pytest.fixture
def sample_metrics():
    """Standard set of test metrics for VEE/VWRE tests."""
    return {
        "score": 75.0,
        "accuracy": 0.85,
        "count": 1200,
        "throughput": 450.0,
        "ratio": 0.62,
        "latency": 23.5,
    }


@pytest.fixture
def sample_factors():
    """Standard set of factor values for VWRE tests."""
    return {
        "alpha": 1.2,
        "beta": -0.5,
        "gamma": 0.8,
        "delta": 0.3,
    }


@pytest.fixture
def sample_risk_data():
    """Standard raw data for VARE risk assessment."""
    return {
        "values": [10.0, 12.0, 9.5, 11.0, 13.0, 10.5, 14.0, 8.5],
        "weight": [0.15, 0.25, 0.10, 0.20, 0.05, 0.10, 0.10, 0.05],
    }
