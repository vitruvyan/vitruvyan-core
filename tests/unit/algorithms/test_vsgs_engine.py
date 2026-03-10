"""
Test VSGS Engine — Vitruvyan Semantic Grounding System
=======================================================

Test unitari per il motore di grounding semantico.

Copertura:
  - ground()        → pipeline completa (embed → search → classify)
  - ground() disabled → short-circuit con status "disabled"
  - ground() empty   → short-circuit con status "skipped"
  - embed_only()     → embedding senza ricerca
  - _classify()      → classificazione qualità match (high/medium/low)
  - Error handling   → GroundingResult con status "error" su eccezione
  - GroundingResult  → proprietà top_score, match_count, to_state_dict()
  - SemanticMatch    → to_dict()

NOTA: VSGS ha dipendenze infrastrutturali (httpx, QdrantAgent).
I test mockano _embed() e _search() per isolamento completo.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.vpar.vsgs.vsgs_engine import VSGSEngine
    from core.vpar.vsgs.types import GroundingConfig, GroundingResult, SemanticMatch
    HAS_VSGS = True
except ImportError:
    HAS_VSGS = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.algorithms,
    pytest.mark.skipif(not HAS_VSGS, reason="VSGS module not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES LOCALI
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def config_enabled():
    """GroundingConfig abilitato con threshold di test."""
    return GroundingConfig(
        enabled=True,
        top_k=3,
        collection="test_collection",
        high_threshold=0.8,
        medium_threshold=0.6,
    )


@pytest.fixture
def config_disabled():
    """GroundingConfig disabilitato."""
    return GroundingConfig(enabled=False)


@pytest.fixture
def vsgs_enabled(config_enabled):
    """VSGSEngine con config abilitato."""
    return VSGSEngine(
        config=config_enabled,
        embedding_url="http://fake-embed:8003",
        qdrant_agent=MagicMock(),
    )


@pytest.fixture
def vsgs_disabled(config_disabled):
    """VSGSEngine con config disabilitato."""
    return VSGSEngine(config=config_disabled)


@pytest.fixture
def mock_embedding():
    """Embedding fittizio (vettore 768-dim)."""
    return [0.1] * 768


@pytest.fixture
def mock_qdrant_results():
    """Risultati Qdrant fittizi."""
    return [
        {
            "score": 0.92,
            "payload": {
                "query_text": "Previous analysis of entity X",
                "intent": "analysis",
                "language": "en",
                "timestamp": "2026-02-10T12:00:00",
                "trace_id": "trace_001",
            },
        },
        {
            "score": 0.71,
            "payload": {
                "query_text": "Related context for entity Y",
                "intent": "overview",
                "language": "en",
            },
        },
        {
            "score": 0.45,
            "payload": {
                "query_text": "Weak match",
            },
        },
    ]


# ═══════════════════════════════════════════════════════════════════
# TEST: ground() — pipeline completa
# ═══════════════════════════════════════════════════════════════════

class TestVSGSGround:
    """Test per la pipeline ground()."""

    def test_ground_returns_grounding_result(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """ground() deve restituire un GroundingResult."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        assert isinstance(result, GroundingResult)

    def test_ground_status_enabled(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """Con config enabled, status deve essere "enabled"."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        assert result.status == "enabled"

    def test_ground_matches_count(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """Il numero di match deve corrispondere ai risultati Qdrant."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        assert result.match_count == 3

    def test_ground_top_score(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """top_score deve essere il primo match (0.92)."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        assert result.top_score == 0.92

    def test_ground_matches_are_semantic_match(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """Ogni match deve essere un SemanticMatch."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        for m in result.matches:
            assert isinstance(m, SemanticMatch)

    def test_ground_elapsed_ms_positive(
        self, vsgs_enabled, mock_embedding, mock_qdrant_results,
    ):
        """elapsed_ms deve essere positivo."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", return_value=mock_qdrant_results):
            result = vsgs_enabled.ground("test query")

        assert result.elapsed_ms >= 0.0


# ═══════════════════════════════════════════════════════════════════
# TEST: ground() — short-circuit
# ═══════════════════════════════════════════════════════════════════

class TestVSGSShortCircuit:
    """Test per i casi di short-circuit in ground()."""

    def test_disabled_returns_disabled_status(self, vsgs_disabled):
        """Con config.enabled=False, status deve essere "disabled"."""
        result = vsgs_disabled.ground("any query")
        assert result.status == "disabled"
        assert result.matches == []

    def test_empty_text_returns_skipped(self, vsgs_enabled):
        """Con testo vuoto, status deve essere "skipped"."""
        result = vsgs_enabled.ground("")
        assert result.status == "skipped"
        assert result.matches == []

    def test_whitespace_only_returns_skipped(self, vsgs_enabled):
        """Con solo spazi, status deve essere "skipped"."""
        result = vsgs_enabled.ground("   ")
        assert result.status == "skipped"

    def test_none_text_returns_skipped(self, vsgs_enabled):
        """Con None, must return "skipped" (not crash)."""
        result = vsgs_enabled.ground(None)
        assert result.status == "skipped"


# ═══════════════════════════════════════════════════════════════════
# TEST: ground() — error handling
# ═══════════════════════════════════════════════════════════════════

class TestVSGSErrors:
    """Test per la gestione degli errori in ground()."""

    def test_embed_failure_returns_error(self, vsgs_enabled):
        """Se _embed fallisce, ground() restituisce status "error"."""
        with patch.object(vsgs_enabled, "_embed", side_effect=RuntimeError("API down")):
            result = vsgs_enabled.ground("test query")

        assert result.status == "error"
        assert "API down" in result.error
        assert result.matches == []

    def test_search_failure_returns_error(self, vsgs_enabled, mock_embedding):
        """Se _search fallisce, ground() restituisce status "error"."""
        with patch.object(vsgs_enabled, "_embed", return_value=mock_embedding), \
             patch.object(vsgs_enabled, "_search", side_effect=Exception("Qdrant unreachable")):
            result = vsgs_enabled.ground("test query")

        assert result.status == "error"
        assert result.matches == []

    def test_error_result_has_elapsed(self, vsgs_enabled):
        """Anche su errore, elapsed_ms deve essere registrato."""
        with patch.object(vsgs_enabled, "_embed", side_effect=RuntimeError("fail")):
            result = vsgs_enabled.ground("test query")

        assert result.elapsed_ms >= 0.0


# ═══════════════════════════════════════════════════════════════════
# TEST: _classify() — classificazione qualità
# ═══════════════════════════════════════════════════════════════════

class TestVSGSClassify:
    """Test per _classify() — threshold-based quality classification."""

    def test_high_quality(self, vsgs_enabled):
        assert vsgs_enabled._classify(0.95) == "high"
        assert vsgs_enabled._classify(0.81) == "high"

    def test_medium_quality(self, vsgs_enabled):
        assert vsgs_enabled._classify(0.75) == "medium"
        assert vsgs_enabled._classify(0.61) == "medium"

    def test_low_quality(self, vsgs_enabled):
        assert vsgs_enabled._classify(0.5) == "low"
        assert vsgs_enabled._classify(0.0) == "low"

    def test_boundary_high(self, vsgs_enabled):
        """Esattamente a high_threshold è "medium" (> non >=)."""
        assert vsgs_enabled._classify(0.8) == "medium"

    def test_boundary_medium(self, vsgs_enabled):
        """Esattamente a medium_threshold è "low" (> non >=)."""
        assert vsgs_enabled._classify(0.6) == "low"


# ═══════════════════════════════════════════════════════════════════
# TEST: GroundingResult properties
# ═══════════════════════════════════════════════════════════════════

class TestGroundingResult:
    """Test per le proprietà di GroundingResult."""

    def test_top_score_with_matches(self):
        matches = [
            SemanticMatch(text="a", score=0.9, quality="high"),
            SemanticMatch(text="b", score=0.5, quality="low"),
        ]
        result = GroundingResult(matches=matches, status="enabled")
        assert result.top_score == 0.9

    def test_top_score_empty(self):
        result = GroundingResult(matches=[], status="disabled")
        assert result.top_score == 0.0

    def test_match_count(self):
        matches = [SemanticMatch(text="x", score=0.5, quality="low")]
        result = GroundingResult(matches=matches, status="enabled")
        assert result.match_count == 1

    def test_to_state_dict(self):
        result = GroundingResult(matches=[], status="disabled", elapsed_ms=0.0)
        state = result.to_state_dict()
        assert isinstance(state, dict)
        assert "vsgs_status" in state


# ═══════════════════════════════════════════════════════════════════
# TEST: SemanticMatch
# ═══════════════════════════════════════════════════════════════════

class TestSemanticMatch:
    """Test per SemanticMatch."""

    def test_to_dict(self):
        match = SemanticMatch(
            text="test text", score=0.85, quality="high",
            intent="analysis", language="en",
        )
        d = match.to_dict()
        assert d["text"] == "test text"
        assert d["score"] == 0.85
        assert d["quality"] == "high"

    def test_default_values(self):
        match = SemanticMatch(text="", score=0.0, quality="low")
        assert match.intent is None
        assert match.language is None
        assert match.metadata == {}


# ═══════════════════════════════════════════════════════════════════
# TEST: close()
# ═══════════════════════════════════════════════════════════════════

class TestVSGSClose:
    """Test per la pulizia risorse."""

    def test_close_without_client(self, vsgs_enabled):
        """close() non deve crashare se il client non è stato creato."""
        vsgs_enabled.close()  # nessun errore

    def test_close_clears_client(self, vsgs_enabled):
        """close() deve azzerare il client HTTP."""
        vsgs_enabled._http_client = MagicMock()
        vsgs_enabled.close()
        assert vsgs_enabled._http_client is None
