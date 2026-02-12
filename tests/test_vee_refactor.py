#!/usr/bin/env python3
"""
Test VEE 3.0 — Domain-agnostic explainability pipeline.

Uses a mock provider to prove VEE works with ANY domain,
not just finance. No external dependencies required.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vitruvyan_core'))

from domains.explainability_contract import (
    ExplainabilityProvider, ExplanationTemplate, NormalizationRule,
    AnalysisDimension, PatternRule, ConfidenceCriteria
)
from core.vpar.vee import VEEEngine, VEEAnalyzer


class MockProvider(ExplainabilityProvider):
    """Minimal provider for testing — not tied to any domain."""

    def get_explanation_templates(self):
        return ExplanationTemplate(
            summary_template="{entity_reference}: {signals_text} ({direction}).",
            technical_template="Analysis of {entity_reference}: dominant={dominant_factor}, intensity={intensity:.2f}.",
            detailed_template="Full analysis for {entity_reference}: {signals_text}. {patterns_text}{confidence_text}",
        )

    def format_entity_reference(self, entity_id):
        return f"Entity({entity_id})"

    def get_normalization_rules(self):
        return [
            NormalizationRule("_z", "zscore_tanh"),
            NormalizationRule("_score", "linear_100"),
        ]

    def get_analysis_dimensions(self):
        return [
            AnalysisDimension("alpha", ["alpha_z", "beta_z"], "alpha dimension"),
            AnalysisDimension("gamma", ["gamma_score"], "gamma dimension"),
        ]

    def get_pattern_rules(self):
        return [
            PatternRule("high_alpha", "Strong alpha signal detected",
                        condition=lambda m: m.get("alpha_z", 0) > 0.8),
        ]

    def get_intensity_weights(self):
        return {"alpha": 1.5, "gamma": 1.0}

    def get_confidence_criteria(self):
        return ConfidenceCriteria()


def test_vee_analyzer():
    """Test VEEAnalyzer produces valid AnalysisResult."""
    analyzer = VEEAnalyzer()
    provider = MockProvider()
    metrics = {"alpha_z": 2.0, "beta_z": 0.5, "gamma_score": 75}

    result = analyzer.analyze("TEST_1", metrics, provider)

    assert result.entity_id == "TEST_1"
    assert result.metrics_count == 3
    assert len(result.dominant_factors) >= 1
    assert 0.0 <= result.overall_intensity <= 1.0
    assert "overall" in result.confidence
    assert result.missing_dimensions == []


def test_vee_engine_explain():
    """Test full VEEEngine.explain pipeline."""
    engine = VEEEngine(auto_store=False, use_memory=False)
    provider = MockProvider()
    metrics = {"alpha_z": 2.0, "beta_z": 0.5, "gamma_score": 75}

    output = engine.explain("TEST_1", metrics, provider)

    assert isinstance(output, dict)
    assert "summary" in output
    assert "technical" in output
    assert "detailed" in output
    assert "Entity(TEST_1)" in output["summary"]


def test_vee_engine_comprehensive():
    """Test VEEEngine.explain_comprehensive with profile."""
    engine = VEEEngine(auto_store=False, use_memory=False)
    provider = MockProvider()
    metrics = {"alpha_z": 2.0, "beta_z": 0.5, "gamma_score": 75}

    output = engine.explain_comprehensive(
        "TEST_1", metrics, provider, profile={"level": "expert"})

    assert "analysis" in output
    assert "metadata" in output
    assert output["metadata"]["profile_adapted"] is True
    assert output["analysis"]["confidence"]["overall"] > 0


def test_vee_empty_metrics():
    """Test graceful handling of empty metrics."""
    analyzer = VEEAnalyzer()
    provider = MockProvider()

    result = analyzer.analyze("EMPTY", {}, provider)
    assert result.entity_id == "EMPTY"
    assert result.overall_intensity == 0.0
    assert result.overall_confidence == 0.0


def test_vee_pattern_detection():
    """Test pattern detection via provider rules."""
    analyzer = VEEAnalyzer()
    provider = MockProvider()
    # alpha_z = 3.0 → normalized ~0.905 → triggers "high_alpha" pattern
    metrics = {"alpha_z": 3.0, "beta_z": 0.1, "gamma_score": 50}

    result = analyzer.analyze("PAT_1", metrics, provider)
    assert any("Strong alpha signal" in p for p in result.patterns)


if __name__ == "__main__":
    test_vee_analyzer()
    print("✅ test_vee_analyzer passed")
    test_vee_engine_explain()
    print("✅ test_vee_engine_explain passed")
    test_vee_engine_comprehensive()
    print("✅ test_vee_engine_comprehensive passed")
    test_vee_empty_metrics()
    print("✅ test_vee_empty_metrics passed")
    test_vee_pattern_detection()
    print("✅ test_vee_pattern_detection passed")
    print("\n🎉 All VEE 3.0 tests PASSED")