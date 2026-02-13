"""
Test VARE Engine — Vitruvyan Adaptive Risk Engine v2.0
=======================================================

Test unitari per il motore di risk profiling domain-agnostic.

Copertura:
  - assess_risk()       → calcolo dimensioni, normalizzazione, aggregazione, categorie
  - batch_assess()      → batch processing, gestione errori per-entity
  - adjust()            → adaptation tracking (EPOCH V)
  - _normalize_score()  → interpolazione lineare con threshold
  - _categorize()       → mappatura score → categoria (LOW/MODERATE/HIGH/EXTREME)
  - _calculate_confidence() → euristica basata su dimensioni valide + dati
  - Edge cases          → dati vuoti, dimensioni fallite, error_result

Dipendenze: ZERO I/O. Il RiskProvider è mockato tramite conftest.py.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.vpar.vare.vare_engine import VAREEngine
    from core.vpar.vare.types import RiskConfig, RiskResult, RiskDimensionScore
    HAS_VARE = True
except ImportError:
    HAS_VARE = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.algorithms,
    pytest.mark.skipif(not HAS_VARE, reason="VARE module not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES LOCALI
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def vare_engine(mock_risk_provider):
    """VAREEngine con mock provider."""
    return VAREEngine(mock_risk_provider, domain_tag="test")


@pytest.fixture
def risk_config():
    """Configurazione rischio di default."""
    return RiskConfig()


@pytest.fixture
def risk_config_conservative():
    """Configurazione rischio conservativa."""
    return RiskConfig(profile="conservative")


# ═══════════════════════════════════════════════════════════════════
# TEST: assess_risk()
# ═══════════════════════════════════════════════════════════════════

class TestVAREAssessRisk:
    """Test per assess_risk() — singola entità."""

    def test_assess_risk_returns_risk_result(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """assess_risk() deve restituire un RiskResult."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert isinstance(result, RiskResult)

    def test_assess_risk_entity_id(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Il risultato deve contenere l'entity_id corretto."""
        result = vare_engine.assess_risk("ENTITY_42", sample_risk_data, risk_config)
        assert result.entity_id == "ENTITY_42"

    def test_assess_risk_has_dimension_scores(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Il risultato deve contenere score per ogni dimensione del provider."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert "volatility" in result.dimension_scores
        assert "concentration" in result.dimension_scores

    def test_assess_risk_overall_is_bounded(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """overall_risk deve essere tra 0 e 100."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert 0.0 <= result.overall_risk <= 100.0

    def test_assess_risk_category_valid(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """risk_category deve essere una delle 4 categorie valide."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert result.risk_category in {"LOW", "MODERATE", "HIGH", "EXTREME"}

    def test_assess_risk_has_explanation(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Il risultato deve avere un'explanation con almeno summary."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert "summary" in result.explanation

    def test_assess_risk_confidence_bounded(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """La confidence deve essere tra 0.0 e 1.0."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert 0.0 <= result.confidence <= 1.0

    def test_assess_risk_domain_tag_propagated(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """domain_tag deve essere propagato nel risultato."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        assert result.domain_tag == "test"

    def test_assess_risk_default_config(
        self, vare_engine, sample_risk_data,
    ):
        """Se config è None, deve usare RiskConfig() di default."""
        result = vare_engine.assess_risk("E1", sample_risk_data)
        assert result.profile == "balanced"

    def test_assess_risk_conservative_profile(
        self, vare_engine, sample_risk_data, risk_config_conservative,
    ):
        """Un profilo conservativo deve usare i pesi corrispondenti."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config_conservative)
        assert result.profile == "conservative"

    def test_assess_risk_primary_factor_is_highest(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """primary_risk_factor deve essere la dimensione con score più alto."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        scores = {n: ds.score for n, ds in result.dimension_scores.items()}
        expected_primary = max(scores, key=scores.get)
        assert result.primary_risk_factor == expected_primary

    def test_assess_risk_timestamp_is_recent(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Il timestamp deve essere recente (entro 5 secondi)."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        delta = (datetime.utcnow() - result.timestamp).total_seconds()
        assert delta < 5.0


# ═══════════════════════════════════════════════════════════════════
# TEST: Dimension score normalization
# ═══════════════════════════════════════════════════════════════════

class TestVARENormalization:
    """Test per la normalizzazione degli score dimensionali."""

    def test_dimension_score_is_bounded(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Ogni dimension score deve essere tra 0 e 100."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        for name, ds in result.dimension_scores.items():
            assert 0.0 <= ds.score <= 100.0, f"{name} score out of range: {ds.score}"

    def test_dimension_has_explanation(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """Ogni dimensione deve avere una spiegazione testuale."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        for name, ds in result.dimension_scores.items():
            assert ds.explanation, f"{name} has empty explanation"
            assert isinstance(ds.explanation, str)


# ═══════════════════════════════════════════════════════════════════
# TEST: _categorize() — mappatura score → categoria
# ═══════════════════════════════════════════════════════════════════

class TestVARECategorize:
    """Test per _categorize() — logica deterministica."""

    def test_low_risk(self):
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(10.0, thresholds) == "LOW"
        assert VAREEngine._categorize(25.0, thresholds) == "LOW"

    def test_moderate_risk(self):
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(30.0, thresholds) == "MODERATE"
        assert VAREEngine._categorize(50.0, thresholds) == "MODERATE"

    def test_high_risk(self):
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(60.0, thresholds) == "HIGH"
        assert VAREEngine._categorize(75.0, thresholds) == "HIGH"

    def test_extreme_risk(self):
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(80.0, thresholds) == "EXTREME"
        assert VAREEngine._categorize(100.0, thresholds) == "EXTREME"

    def test_zero_score(self):
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(0.0, thresholds) == "LOW"

    def test_boundary_exact(self):
        """I boundary sono inclusivi verso la categoria inferiore (<=)."""
        thresholds = {"LOW": 25.0, "MODERATE": 50.0, "HIGH": 75.0}
        assert VAREEngine._categorize(25.0, thresholds) == "LOW"
        assert VAREEngine._categorize(50.0, thresholds) == "MODERATE"
        assert VAREEngine._categorize(75.0, thresholds) == "HIGH"
        assert VAREEngine._categorize(75.1, thresholds) == "EXTREME"


# ═══════════════════════════════════════════════════════════════════
# TEST: batch_assess()
# ═══════════════════════════════════════════════════════════════════

class TestVAREBatch:
    """Test per batch_assess() — elaborazione multipla."""

    def test_batch_returns_list(
        self, vare_engine, sample_risk_data,
    ):
        """batch_assess() deve restituire una lista."""
        entities = [
            {"entity_id": "E1", "raw_data": sample_risk_data},
            {"entity_id": "E2", "raw_data": sample_risk_data},
        ]
        results = vare_engine.batch_assess(entities)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_preserves_order(
        self, vare_engine, sample_risk_data,
    ):
        """I risultati devono essere nello stesso ordine degli input."""
        entities = [
            {"entity_id": "FIRST", "raw_data": sample_risk_data},
            {"entity_id": "SECOND", "raw_data": sample_risk_data},
            {"entity_id": "THIRD", "raw_data": sample_risk_data},
        ]
        results = vare_engine.batch_assess(entities)
        assert results[0].entity_id == "FIRST"
        assert results[1].entity_id == "SECOND"
        assert results[2].entity_id == "THIRD"

    def test_batch_empty_input(self, vare_engine):
        """Con lista vuota, deve restituire lista vuota."""
        results = vare_engine.batch_assess([])
        assert results == []

    def test_batch_one_failure_does_not_block_others(
        self, vare_engine, sample_risk_data,
    ):
        """Se un'entità fallisce, le altre continuano."""
        entities = [
            {"entity_id": "OK1", "raw_data": sample_risk_data},
            {"entity_id": "FAIL", "raw_data": {}},  # dati vuoti
            {"entity_id": "OK2", "raw_data": sample_risk_data},
        ]
        results = vare_engine.batch_assess(entities)
        assert len(results) == 3
        # Le entità OK devono avere risultati normali
        assert results[0].entity_id == "OK1"
        assert results[2].entity_id == "OK2"


# ═══════════════════════════════════════════════════════════════════
# TEST: adjust() e adaptation_history
# ═══════════════════════════════════════════════════════════════════

class TestVAREAdaptation:
    """Test per adjust() — EPOCH V."""

    def test_adjust_returns_true(self, vare_engine):
        """adjust() deve restituire True."""
        result = vare_engine.adjust("LOW", 5.0)
        assert result is True

    def test_adjust_records_history(self, vare_engine):
        """adjust() deve registrare l'adattamento nella cronologia."""
        vare_engine.adjust("LOW", 5.0)
        vare_engine.adjust("HIGH", -10.0)

        history = vare_engine.adaptation_history
        assert len(history) == 2
        assert history[0]["parameter"] == "LOW"
        assert history[0]["delta"] == 5.0
        assert history[1]["parameter"] == "HIGH"
        assert history[1]["delta"] == -10.0

    def test_adaptation_history_is_copy(self, vare_engine):
        """adaptation_history deve restituire una copia (non il riferimento interno)."""
        vare_engine.adjust("LOW", 5.0)
        history1 = vare_engine.adaptation_history
        history1.clear()  # modifica la copia
        assert len(vare_engine.adaptation_history) == 1  # interno invariato

    def test_empty_history_at_init(self, vare_engine):
        """All'inizializzazione, la cronologia deve essere vuota."""
        assert vare_engine.adaptation_history == []


# ═══════════════════════════════════════════════════════════════════
# TEST: Edge cases e confidence
# ═══════════════════════════════════════════════════════════════════

class TestVAREEdgeCases:
    """Test per comportamenti limite."""

    def test_risk_result_to_state_dict(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """to_state_dict() deve restituire un dict serializzabile."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        state = result.to_state_dict()
        assert isinstance(state, dict)
        assert "vare_entity_id" in state

    def test_init_without_domain_tag(self, mock_risk_provider):
        """Il motore deve funzionare senza domain_tag."""
        engine = VAREEngine(mock_risk_provider)
        assert engine.domain_tag is None

    def test_dimension_score_frozen(
        self, vare_engine, sample_risk_data, risk_config,
    ):
        """RiskDimensionScore è frozen (immutabile)."""
        result = vare_engine.assess_risk("E1", sample_risk_data, risk_config)
        ds = list(result.dimension_scores.values())[0]
        with pytest.raises(AttributeError):
            ds.score = 999.0  # type: ignore
