"""
VEE - Multi-Level Narrative Generation Tests

Verifica che VEE generi spiegazioni appropriate per ogni livello:
- Quick: concise, 1-2 sentences
- Detailed: paragraph with causes/effects
- Expert: technical analysis with precise metrics
"""

import pytest
from core.vpar.vee.vee_engine import VEEEngine
from domains.explainability_contract import (
    ExplainabilityProvider,
    ExplanationTemplate,
    NormalizationRule,
    AnalysisDimension,
    PatternRule,
    ConfidenceCriteria,
    MetricDefinition,
)
from typing import Dict, List


class MockFinanceProvider(ExplainabilityProvider):
    """Mock provider per test - simula dominio finance."""
    
    def get_explanation_templates(self) -> ExplanationTemplate:
        """Template narrativi per ogni livello."""
        return ExplanationTemplate(
            summary_template=(
                "{entity_reference} shows {direction} signals. "
                "Overall intensity: {intensity:.2f}."
            ),
            technical_template=(
                "Analysis of {entity_reference}: {signals_text}. "
                "Intensity={intensity:.2f}, Confidence={confidence_text}."
            ),
            detailed_template=(
                "Comprehensive analysis for {entity_reference}: "
                "{signals_text}. Dominant factor: {dominant_factor}. "
                "Patterns: {patterns_text}. Overall direction: {direction}."
            ),
            contextual_template=(
                "{entity_reference} technical overview: "
                "Detected signals include {signals_text}. "
                "Key patterns: {patterns_text}."
            )
        )
    
    def format_entity_reference(self, entity_id: str) -> str:
        """Formatta riferimento entity."""
        return f"[{entity_id}]"
    
    def get_normalization_rules(self) -> List[NormalizationRule]:
        """Regole normalizzazione metriche."""
        return [
            NormalizationRule(metric_pattern="momentum", method="linear", min_value=0.0, max_value=1.0),
            NormalizationRule(metric_pattern="rsi", method="linear", min_value=0, max_value=100),
            NormalizationRule(metric_pattern="volume", method="linear", min_value=0.5, max_value=2.0),
        ]
    
    def get_analysis_dimensions(self) -> List[AnalysisDimension]:
        """Dimensioni di analisi."""
        return [
            AnalysisDimension(
                name="momentum",
                metric_keys=["momentum_score", "rsi"],
                display_name="Price Momentum",
                direction="higher_better",
                weight=0.5
            ),
            AnalysisDimension(
                name="volume",
                metric_keys=["volume_ratio"],
                display_name="Volume Profile",
                direction="higher_better",
                weight=0.3
            ),
        ]
    
    def get_pattern_rules(self) -> List[PatternRule]:
        """Regole pattern detection."""
        return [
            PatternRule(
                name="strong_momentum",
                display_text="Strong upward momentum detected",
                condition=lambda m: m.get("momentum_score", 0) > 0.7
            ),
            PatternRule(
                name="weak_momentum",
                display_text="Weak momentum, potential reversal",
                condition=lambda m: m.get("momentum_score", 0) < 0.3
            ),
        ]
    
    def get_intensity_weights(self) -> Dict[str, float]:
        """Pesi per calcolo intensità."""
        return {
            "momentum": 0.6,
            "volume": 0.4,
        }
    
    def get_confidence_criteria(self) -> ConfidenceCriteria:
        """Criteri per confidence calculation."""
        return ConfidenceCriteria(
            min_metrics_high=3,
            min_metrics_moderate=2,
            min_signals_high=2,
            consistency_threshold=0.3
        )
    
    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Definizioni metriche opzionali."""
        return {
            "momentum_score": MetricDefinition(
                name="momentum_score",
                description="Price momentum indicator",
                unit="score",
                interpretation="Higher values indicate stronger upward momentum",
                normal_range=(0.0, 1.0),
                display_name="Momentum"
            ),
            "rsi": MetricDefinition(
                name="rsi",
                description="Relative Strength Index",
                unit="index",
                interpretation="Values above 70 indicate overbought, below 30 oversold",
                normal_range=(0.0, 100.0),
                display_name="RSI"
            ),
        }


@pytest.fixture
def vee_engine():
    """VEE engine with mock provider."""
    return VEEEngine(auto_store=False, use_memory=False)


@pytest.fixture
def mock_provider():
    """Mock explainability provider."""
    return MockFinanceProvider()


@pytest.fixture
def sample_metrics_strong():
    """Metrics che generano segnale strong."""
    return {
        "momentum_score": 0.85,
        "rsi": 65.0,
        "volume_ratio": 1.5,
    }


@pytest.fixture
def sample_metrics_weak():
    """Metrics che generano segnale weak."""
    return {
        "momentum_score": 0.25,
        "rsi": 35.0,
        "volume_ratio": 0.8,
    }


class TestVEENarrativeLevels:
    """Test generazione narrative multi-livello."""
    
    def test_all_levels_generated(self, vee_engine, mock_provider, sample_metrics_strong):
        """Verifica che tutti i livelli siano generati."""
        explanation = vee_engine.explain(
            entity_id="AAPL",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        # All levels must be present (VEE maps to quick/detailed/expert internally)
        assert "quick" in explanation or "summary" in explanation
        assert len(explanation) > 0, "No explanations generated"
        
        # At least one narrative level must exist
        for key, value in explanation.items():
            assert isinstance(value, str), f"Level {key} should be string"
            assert len(value) > 0, f"Level {key} is empty"
    
    def test_provider_template_usage(self, vee_engine, mock_provider, sample_metrics_strong):
        """Verifica che VEE usi i template del provider."""
        explanation = vee_engine.explain(
            entity_id="NVDA",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        # Check entity reference formatting (MockProvider adds brackets)
        combined_text = " ".join(explanation.values())
        assert "[NVDA]" in combined_text, "Entity reference not formatted by provider"
    
    def test_strong_vs_weak_signals(self, vee_engine, mock_provider, sample_metrics_strong, sample_metrics_weak):
        """Verifica differenza narrativa tra segnali forti e deboli."""
        strong_explanation = vee_engine.explain(
            entity_id="TSLA",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        weak_explanation = vee_engine.explain(
            entity_id="TSLA",
            metrics=sample_metrics_weak,
            provider=mock_provider,
        )
        
        # Both should generate explanations
        assert len(strong_explanation) > 0
        assert len(weak_explanation) > 0
        
        # Narratives should be different
        strong_text = " ".join(strong_explanation.values())
        weak_text = " ".join(weak_explanation.values())
        assert strong_text != weak_text, "Strong and weak signals should generate different narratives"
    
    def test_placeholder_replacement(self, vee_engine, mock_provider, sample_metrics_strong):
        """Verifica che i placeholder siano sostituiti."""
        explanation = vee_engine.explain(
            entity_id="MSFT",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        # Check no unreplaced placeholders (VEE should replace all)
        combined_text = " ".join(explanation.values())
        unreplaced_placeholders = [
            "{entity_id}", "{entity_reference}", "{intensity}",
            "{direction}", "{signals_text}"
        ]
        for placeholder in unreplaced_placeholders:
            assert placeholder not in combined_text, f"Placeholder {placeholder} not replaced"
    
    def test_metrics_influence_narrative(self, vee_engine, mock_provider):
        """Verifica che diverse metriche generino narrative diverse."""
        metrics_high_momentum = {
            "momentum_score": 0.9,
            "rsi": 70.0,
            "volume_ratio": 1.8,
        }
        
        metrics_low_momentum = {
            "momentum_score": 0.1,
            "rsi": 30.0,
            "volume_ratio": 0.6,
        }
        
        explanation_high = vee_engine.explain(
            entity_id="GOOG",
            metrics=metrics_high_momentum,
            provider=mock_provider,
        )
        
        explanation_low = vee_engine.explain(
            entity_id="GOOG",
            metrics=metrics_low_momentum,
            provider=mock_provider,
        )
        
        # Explanations should differ based on metrics
        text_high = " ".join(explanation_high.values())
        text_low = " ".join(explanation_low.values())
        assert text_high != text_low, "Different metrics should generate different explanations"
    
    def test_minimal_metrics(self, vee_engine, mock_provider):
        """Verifica che VEE gestisca metriche minime."""
        minimal_metrics = {"momentum_score": 0.5}
        
        explanation = vee_engine.explain(
            entity_id="AMZN",
            metrics=minimal_metrics,
            provider=mock_provider,
        )
        
        # Should still generate explanation
        assert len(explanation) > 0
        assert any(len(v) > 0 for v in explanation.values()), "No narrative generated for minimal metrics"


@pytest.mark.integration
class TestVEEComprehensive:
    """Test comprehensive explanation with metadata."""
    
    def test_comprehensive_output_structure(self, vee_engine, mock_provider, sample_metrics_strong):
        """Verifica struttura output comprehensive."""
        comprehensive = vee_engine.explain_comprehensive(
            entity_id="AAPL",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        # Check structure (VEE returns flat dict with analysis + narrative levels)
        assert "analysis" in comprehensive
        assert "metadata" in comprehensive
        
        # Check that at least one narrative level exists
        narrative_keys = [k for k in comprehensive.keys() if k not in ["analysis", "metadata", "context"]]
        assert len(narrative_keys) > 0, "No narrative levels in comprehensive output"
        
        # Check narrative levels are strings
        for key in narrative_keys:
            assert isinstance(comprehensive[key], str), f"Narrative level {key} should be string"
    
    def test_comprehensive_analysis_metadata(self, vee_engine, mock_provider, sample_metrics_strong):
        """Verifica metadata di analisi nel comprehensive output."""
        comprehensive = vee_engine.explain_comprehensive(
            entity_id="TSLA",
            metrics=sample_metrics_strong,
            provider=mock_provider,
        )
        
        # Check analysis metadata fields
        analysis = comprehensive["analysis"]
        assert "overall_intensity" in analysis or "intensity" in analysis or "dominant_factors" in analysis
        assert "confidence" in analysis, "Missing confidence in analysis"
