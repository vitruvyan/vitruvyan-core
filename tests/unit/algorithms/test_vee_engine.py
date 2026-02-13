"""
Test VEE Engine — Vitruvyan Explainability Engine v3.0
=======================================================

Test unitari per il motore di spiegabilità domain-agnostic.

Copertura:
  - explain()              → output Dict[str, str] con chiavi summary/technical/detailed
  - explain_comprehensive() → output nested Dict con analysis/metadata/context
  - analyze_only()          → restituisce AnalysisResult senza generazione/storage
  - Fallback su errore      → output deterministico con messaggio errore
  - Edge cases              → metriche vuote, entity_id vuoto, provider che fallisce

Dipendenze: ZERO I/O. Tutti i sub-componenti (VEEAnalyzer, VEEGenerator,
VEEMemoryAdapter) sono mockati per isolare il motore.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.vpar.vee.vee_engine import VEEEngine
    from core.vpar.vee.types import AnalysisResult, ExplanationLevels
    HAS_VEE = True
except ImportError:
    HAS_VEE = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.algorithms,
    pytest.mark.skipif(not HAS_VEE, reason="VEE module not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES LOCALI
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_analysis_result():
    """AnalysisResult deterministico per test di generazione."""
    return AnalysisResult(
        entity_id="TEST_001",
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        signals=["quality_high", "volume_stable"],
        signal_strengths={"quality_high": 0.85, "volume_stable": 0.6},
        dominant_factors=[("quality", 0.85), ("volume", 0.6)],
        overall_intensity=0.72,
        direction="positive",
        confidence={"overall": 0.8, "quality": 0.9, "volume": 0.7},
        patterns=["high_quality"],
        anomalies=[],
        metrics_count=6,
        missing_dimensions=[],
    )


@pytest.fixture
def mock_explanation_levels():
    """ExplanationLevels deterministico."""
    return ExplanationLevels(
        entity_id="TEST_001",
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        summary="Entity [TEST_001] shows positive signals. Key: quality.",
        technical="Analysis of [TEST_001]: 6 metrics, intensity=0.72.",
        detailed="Full analysis for [TEST_001]: quality=0.85, volume=0.60.",
        confidence_note="High confidence (0.80)",
        profile_adapted=False,
    )


@pytest.fixture
def vee_engine():
    """VEEEngine con auto_store e use_memory disabilitati (test puro)."""
    return VEEEngine(auto_store=False, use_memory=False)


@pytest.fixture
def vee_engine_with_memory():
    """VEEEngine con memoria attiva (testa enrichment path)."""
    return VEEEngine(auto_store=True, use_memory=True)


# ═══════════════════════════════════════════════════════════════════
# TEST: explain()
# ═══════════════════════════════════════════════════════════════════

class TestVEEExplain:
    """Test per il metodo explain() — output Dict[str, str]."""

    def test_explain_returns_dict_with_required_keys(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """explain() deve restituire almeno summary, technical, detailed."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        assert isinstance(result, dict)
        assert "summary" in result
        assert "technical" in result
        assert "detailed" in result

    def test_explain_summary_contains_entity_id(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """Il summary deve contenere l'ID dell'entità."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        assert "TEST_001" in result["summary"]

    def test_explain_calls_analyzer_with_correct_args(
        self, vee_engine, mock_explainability_provider, sample_metrics,
        mock_analysis_result, mock_explanation_levels,
    ):
        """explain() deve passare entity_id, metrics, provider all'analyzer."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result) as mock_analyze, \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            vee_engine.explain("E1", sample_metrics, mock_explainability_provider)

        mock_analyze.assert_called_once_with("E1", sample_metrics, mock_explainability_provider)

    def test_explain_fallback_on_analyzer_error(
        self, vee_engine, mock_explainability_provider, sample_metrics,
    ):
        """Se l'analyzer solleva un'eccezione, explain() restituisce fallback."""
        with patch.object(vee_engine.analyzer, "analyze", side_effect=ValueError("test error")):
            result = vee_engine.explain(
                "FAIL_001", sample_metrics, mock_explainability_provider
            )

        assert isinstance(result, dict)
        assert "FAIL_001" in result["summary"]
        assert "test error" in result["summary"]

    def test_explain_fallback_keys_are_complete(
        self, vee_engine, mock_explainability_provider, sample_metrics,
    ):
        """Il fallback deve avere summary, technical, detailed."""
        with patch.object(vee_engine.analyzer, "analyze", side_effect=RuntimeError("boom")):
            result = vee_engine.explain(
                "ERR_001", sample_metrics, mock_explainability_provider
            )

        assert set(result.keys()) >= {"summary", "technical", "detailed"}

    def test_explain_with_empty_metrics(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels,
    ):
        """explain() con metriche vuote: non deve crashare."""
        empty_analysis = AnalysisResult(
            entity_id="EMPTY",
            timestamp=datetime.utcnow(),
            signals=[], signal_strengths={},
            dominant_factors=[], overall_intensity=0.0,
            metrics_count=0, missing_dimensions=["quality", "volume"],
        )
        with patch.object(vee_engine.analyzer, "analyze", return_value=empty_analysis), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain("EMPTY", {}, mock_explainability_provider)

        assert isinstance(result, dict)

    def test_explain_no_memory_when_disabled(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """Con use_memory=False, la memoria non deve essere consultata."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels), \
             patch.object(vee_engine.memory, "retrieve") as mock_retrieve:
            vee_engine.explain("E1", sample_metrics, mock_explainability_provider)

        mock_retrieve.assert_not_called()

    def test_explain_no_store_when_disabled(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """Con auto_store=False, lo storage non deve essere invocato."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels), \
             patch.object(vee_engine.memory, "store") as mock_store:
            vee_engine.explain("E1", sample_metrics, mock_explainability_provider)

        mock_store.assert_not_called()


# ═══════════════════════════════════════════════════════════════════
# TEST: explain_comprehensive()
# ═══════════════════════════════════════════════════════════════════

class TestVEEExplainComprehensive:
    """Test per explain_comprehensive() — output nested Dict."""

    def test_comprehensive_has_all_sections(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """Output deve avere summary, technical, detailed, analysis, metadata, context."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain_comprehensive(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        assert "summary" in result
        assert "technical" in result
        assert "detailed" in result
        assert "analysis" in result
        assert "metadata" in result
        assert "context" in result

    def test_comprehensive_analysis_section_structure(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """La sezione analysis deve contenere signals, dominant_factors, direction, etc."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain_comprehensive(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        analysis = result["analysis"]
        assert "signals" in analysis
        assert "dominant_factors" in analysis
        assert "direction" in analysis
        assert "overall_intensity" in analysis
        assert isinstance(analysis["signals"], list)
        assert isinstance(analysis["dominant_factors"], list)

    def test_comprehensive_dominant_factors_format(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """dominant_factors deve essere [{"factor": ..., "strength": ...}]."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain_comprehensive(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        factors = result["analysis"]["dominant_factors"]
        assert len(factors) > 0
        assert "factor" in factors[0]
        assert "strength" in factors[0]

    def test_comprehensive_metadata_has_timestamp(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, mock_explanation_levels, sample_metrics,
    ):
        """metadata deve contenere timestamp ISO."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate", return_value=mock_explanation_levels):
            result = vee_engine.explain_comprehensive(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        assert "timestamp" in result["metadata"]
        # Deve essere parsabile come ISO
        datetime.fromisoformat(result["metadata"]["timestamp"])

    def test_comprehensive_fallback_on_error(
        self, vee_engine, mock_explainability_provider, sample_metrics,
    ):
        """Su errore, deve restituire dict minimale con summary di errore."""
        with patch.object(vee_engine.analyzer, "analyze", side_effect=RuntimeError("crash")):
            result = vee_engine.explain_comprehensive(
                "FAIL", sample_metrics, mock_explainability_provider
            )

        assert "summary" in result
        assert "crash" in result["summary"]


# ═══════════════════════════════════════════════════════════════════
# TEST: analyze_only()
# ═══════════════════════════════════════════════════════════════════

class TestVEEAnalyzeOnly:
    """Test per analyze_only() — restituisce AnalysisResult grezzo."""

    def test_analyze_only_returns_analysis_result(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, sample_metrics,
    ):
        """analyze_only() deve restituire un AnalysisResult."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result):
            result = vee_engine.analyze_only(
                "TEST_001", sample_metrics, mock_explainability_provider
            )

        assert isinstance(result, AnalysisResult)
        assert result.entity_id == "TEST_001"

    def test_analyze_only_does_not_store(
        self, vee_engine, mock_explainability_provider,
        mock_analysis_result, sample_metrics,
    ):
        """analyze_only() non deve invocare store né generate."""
        with patch.object(vee_engine.analyzer, "analyze", return_value=mock_analysis_result), \
             patch.object(vee_engine.generator, "generate") as mock_gen, \
             patch.object(vee_engine.memory, "store") as mock_store:
            vee_engine.analyze_only("E1", sample_metrics, mock_explainability_provider)

        mock_gen.assert_not_called()
        mock_store.assert_not_called()

    def test_analyze_only_propagates_exceptions(
        self, vee_engine, mock_explainability_provider, sample_metrics,
    ):
        """analyze_only() NON cattura le eccezioni (a differenza di explain)."""
        with patch.object(vee_engine.analyzer, "analyze", side_effect=ValueError("bad input")):
            with pytest.raises(ValueError, match="bad input"):
                vee_engine.analyze_only("E1", sample_metrics, mock_explainability_provider)


# ═══════════════════════════════════════════════════════════════════
# TEST: AnalysisResult properties
# ═══════════════════════════════════════════════════════════════════

class TestAnalysisResultProperties:
    """Test per le @property di AnalysisResult."""

    def test_primary_factor(self, mock_analysis_result):
        """primary_factor deve restituire il primo dominant_factor."""
        assert mock_analysis_result.primary_factor == "quality"

    def test_primary_strength(self, mock_analysis_result):
        """primary_strength deve restituire la strength del primo fattore."""
        assert mock_analysis_result.primary_strength == 0.85

    def test_overall_confidence(self, mock_analysis_result):
        """overall_confidence deve restituire confidence['overall']."""
        assert mock_analysis_result.overall_confidence == 0.8

    def test_primary_factor_empty_factors(self):
        """Con dominant_factors vuoto, primary_factor deve restituire 'unknown'."""
        result = AnalysisResult(
            entity_id="EMPTY",
            timestamp=datetime.utcnow(),
            signals=[], signal_strengths={},
            dominant_factors=[], overall_intensity=0.0,
        )
        assert result.primary_factor == "unknown"
        assert result.primary_strength == 0.0

    def test_overall_confidence_missing_key(self):
        """Con confidence senza 'overall', deve restituire 0.0."""
        result = AnalysisResult(
            entity_id="X",
            timestamp=datetime.utcnow(),
            signals=[], signal_strengths={},
            dominant_factors=[], overall_intensity=0.0,
            confidence={"quality": 0.9},
        )
        assert result.overall_confidence == 0.0


# ═══════════════════════════════════════════════════════════════════
# TEST: VEEEngine initialization
# ═══════════════════════════════════════════════════════════════════

class TestVEEInit:
    """Test per l'inizializzazione del motore VEE."""

    def test_default_flags(self):
        """Valori default: auto_store=True, use_memory=True."""
        engine = VEEEngine()
        assert engine.auto_store is True
        assert engine.use_memory is True

    def test_custom_flags(self):
        """Flag personalizzati vengono rispettati."""
        engine = VEEEngine(auto_store=False, use_memory=False, domain_tag="medical")
        assert engine.auto_store is False
        assert engine.use_memory is False

    def test_subcomponents_initialized(self):
        """Il motore deve inizializzare analyzer, generator, memory."""
        engine = VEEEngine()
        assert engine.analyzer is not None
        assert engine.generator is not None
        assert engine.memory is not None
