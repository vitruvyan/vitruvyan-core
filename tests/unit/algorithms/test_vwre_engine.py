"""
Test VWRE Engine — Vitruvyan Weighted Reverse Engineering v2.0
===============================================================

Test unitari per il motore di attribution analysis domain-agnostic.

Copertura:
  - analyze()       → decomposizione composite score in contributi fattoriali
  - compare()       → analisi contrastiva tra due entità
  - batch_analyze() → elaborazione multipla con gestione errori
  - _verify()       → verifica residuo (verified/warning/error)
  - _z_narrative()  → narrativa qualitativa per z-score
  - Edge cases      → fattori vuoti, profilo mancante, zero total, error_result

Dipendenze: ZERO I/O. L'AggregationProvider è mockato tramite conftest.py.

NOTA IMPORTANTE: Il MockAggregationProvider in conftest.py usa factor_mappings
che mappano raw_key → display_name (es. "alpha" → "Alpha Factor"). Il motore
VWRE cerca i pesi nel profilo usando weight_key (= display_name), quindi i
pesi del profilo devono usare le stesse chiavi del factor_mappings values.
Il mock attuale usa raw_key nei pesi — questo causa un mismatch intenzionalmente
testato qui.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Skip se il modulo non è importabile ──────────────────────────────────

try:
    from core.vpar.vwre.vwre_engine import VWREEngine
    from core.vpar.vwre.types import (
        AttributionConfig, AttributionResult,
        ComparisonResult, FactorAttribution,
    )
    HAS_VWRE = True
except ImportError:
    HAS_VWRE = False

# Try to import the AggregationProfile for the fixed provider
try:
    from domains.aggregation_contract import AggregationProvider, AggregationProfile
    HAS_AGG_CONTRACT = True
except ImportError:
    HAS_AGG_CONTRACT = False

pytestmark = [
    pytest.mark.unit,
    pytest.mark.algorithms,
    pytest.mark.skipif(not HAS_VWRE, reason="VWRE module not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES — Provider con chiavi allineate
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def aligned_aggregation_provider():
    """Provider con factor_mappings e profile weights allineati.

    factor_mappings: raw_key → weight_key (identici in questo caso)
    profile weights: usa le stesse chiavi dei factor_mappings values
    """
    if not HAS_AGG_CONTRACT:
        pytest.skip("AggregationProvider contract not importable")

    class AlignedProvider(AggregationProvider):
        def get_aggregation_profiles(self):
            return {
                "balanced": AggregationProfile(
                    name="balanced", description="Equal weight",
                    factor_weights={"alpha": 0.25, "beta": 0.25,
                                    "gamma": 0.25, "delta": 0.25}
                ),
                "aggressive": AggregationProfile(
                    name="aggressive", description="High alpha",
                    factor_weights={"alpha": 0.5, "beta": 0.2,
                                    "gamma": 0.2, "delta": 0.1}
                ),
            }

        def get_factor_mappings(self):
            # Identity mapping: raw key → same key (no display name transform)
            return {"alpha": "alpha", "beta": "beta",
                    "gamma": "gamma", "delta": "delta"}

        def calculate_contribution(self, factor_value, weight, profile):
            return factor_value * weight

        def validate_factors(self, factors):
            known = {"alpha", "beta", "gamma", "delta"}
            unknown = set(factors.keys()) - known
            return {"valid": len(unknown) == 0, "unknown_factors": list(unknown),
                    "factor_count": len(factors)}

        def format_attribution_explanation(self, contributions, primary_driver, composite_score):
            return {
                "summary": f"Primary: {primary_driver} (composite={composite_score:.2f})",
                "technical": f"{len(contributions)} factors analyzed",
            }

    return AlignedProvider()


@pytest.fixture
def vwre_engine(aligned_aggregation_provider):
    """VWREEngine con provider allineato."""
    return VWREEngine(aligned_aggregation_provider, domain_tag="test")


@pytest.fixture
def sample_composite():
    """Composite score deterministico: sum(factor * weight) per balanced profile."""
    # alpha=1.2*0.25 + beta=-0.5*0.25 + gamma=0.8*0.25 + delta=0.3*0.25
    # = 0.3 + (-0.125) + 0.2 + 0.075 = 0.45
    return 0.45


# ═══════════════════════════════════════════════════════════════════
# TEST: analyze()
# ═══════════════════════════════════════════════════════════════════

class TestVWREAnalyze:
    """Test per analyze() — decomposizione composite score."""

    def test_analyze_returns_attribution_result(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """analyze() deve restituire un AttributionResult."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert isinstance(result, AttributionResult)

    def test_analyze_entity_id(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Il risultato deve contenere l'entity_id corretto."""
        result = vwre_engine.analyze("ENTITY_99", sample_composite, sample_factors)
        assert result.entity_id == "ENTITY_99"

    def test_analyze_has_factors(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Il risultato deve contenere i fattori analizzati."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert len(result.factors) > 0

    def test_analyze_factors_are_factor_attribution(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Ogni fattore deve essere un FactorAttribution."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        for name, fa in result.factors.items():
            assert isinstance(fa, FactorAttribution)

    def test_analyze_primary_driver_is_highest_contribution(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """primary_driver deve essere il fattore con |contribution| massima."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        if result.factors:
            highest = max(result.factors.values(), key=lambda f: abs(f.contribution))
            assert result.primary_driver == highest.name

    def test_analyze_verification_verified(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Con composite_score = sum(contributions), verification deve essere 'verified'."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert result.verification_status == "verified"

    def test_analyze_verification_warning(
        self, vwre_engine, sample_factors,
    ):
        """Con residuo medio, verification deve essere 'warning'."""
        # Composite score molto diverso dalla somma reale
        result = vwre_engine.analyze(
            "E1", 0.80, sample_factors,
            config=AttributionConfig(residual_tolerance=0.1, residual_warning=0.5),
        )
        assert result.verification_status in {"warning", "error"}

    def test_analyze_verification_error(
        self, vwre_engine, sample_factors,
    ):
        """Con residuo elevato, verification deve essere 'error'."""
        result = vwre_engine.analyze(
            "E1", 100.0, sample_factors,
            config=AttributionConfig(residual_tolerance=0.1, residual_warning=0.5),
        )
        assert result.verification_status == "error"

    def test_analyze_default_config(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Senza config, deve usare AttributionConfig() default."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert result.profile == "balanced"

    def test_analyze_domain_tag_propagated(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """domain_tag deve essere propagato nel risultato."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert result.domain_tag == "test"

    def test_analyze_percentages_sum_to_100(
        self, vwre_engine, sample_composite,
    ):
        """Le percentuali dei fattori devono sommare ~100%."""
        factors = {"alpha": 1.0, "beta": 1.0, "gamma": 1.0, "delta": 1.0}
        result = vwre_engine.analyze("E1", sample_composite, factors)
        total_pct = sum(f.percentage for f in result.factors.values())
        assert abs(total_pct - 100.0) < 0.1

    def test_analyze_has_rank_explanation(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Il risultato deve avere rank_explanation e technical_summary."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        assert result.rank_explanation
        assert result.technical_summary

    def test_analyze_timestamp_is_recent(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Il timestamp deve essere recente."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        delta = (datetime.utcnow() - result.timestamp).total_seconds()
        assert delta < 5.0


# ═══════════════════════════════════════════════════════════════════
# TEST: analyze() — edge cases
# ═══════════════════════════════════════════════════════════════════

class TestVWREEdgeCases:
    """Test per i casi limite di analyze()."""

    def test_empty_factors(self, vwre_engine):
        """Con factors vuoto, deve restituire error result."""
        result = vwre_engine.analyze("E1", 1.0, {})
        assert result.verification_status == "error"
        assert len(result.factors) == 0

    def test_unknown_factors(self, vwre_engine):
        """Fattori sconosciuti vengono filtrati dal factor_mappings."""
        result = vwre_engine.analyze("E1", 1.0, {"xyz": 5.0, "abc": 3.0})
        # xyz e abc non sono in factor_mappings → fattori vuoti → error
        assert result.verification_status == "error"

    def test_none_factor_values(self, vwre_engine):
        """Fattori con valore None vengono saltati."""
        result = vwre_engine.analyze("E1", 1.0, {
            "alpha": 1.0, "beta": None, "gamma": 0.5, "delta": None,
        })
        # Solo alpha e gamma contribuiscono
        assert "alpha" in result.factors
        assert "gamma" in result.factors

    def test_to_state_dict(self, vwre_engine, sample_factors, sample_composite):
        """to_state_dict() deve restituire un dict serializzabile."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        state = result.to_state_dict()
        assert isinstance(state, dict)


# ═══════════════════════════════════════════════════════════════════
# TEST: compare()
# ═══════════════════════════════════════════════════════════════════

class TestVWRECompare:
    """Test per compare() — analisi contrastiva."""

    def test_compare_returns_comparison_result(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """compare() deve restituire un ComparisonResult."""
        result_a = vwre_engine.analyze("A", sample_composite, sample_factors)
        result_b = vwre_engine.analyze("B", sample_composite * 0.5,
                                        {"alpha": 0.5, "beta": 0.0, "gamma": 0.3, "delta": 0.1})
        comparison = vwre_engine.compare(result_a, result_b)
        assert isinstance(comparison, ComparisonResult)

    def test_compare_entity_ids(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """I ComparisonResult deve contenere i due entity_id."""
        a = vwre_engine.analyze("ALPHA", sample_composite, sample_factors)
        b = vwre_engine.analyze("BETA", sample_composite, sample_factors)
        comp = vwre_engine.compare(a, b)
        assert comp.entity_a == "ALPHA"
        assert comp.entity_b == "BETA"

    def test_compare_delta_composite(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """delta_composite = score_a - score_b."""
        a = vwre_engine.analyze("A", 10.0, sample_factors)
        b = vwre_engine.analyze("B", 5.0, sample_factors)
        comp = vwre_engine.compare(a, b)
        assert abs(comp.delta_composite - 5.0) < 0.01

    def test_compare_has_explanation(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Il comparison deve avere una spiegazione testuale."""
        a = vwre_engine.analyze("A", sample_composite, sample_factors)
        b = vwre_engine.analyze("B", sample_composite, sample_factors)
        comp = vwre_engine.compare(a, b)
        assert comp.explanation
        assert isinstance(comp.explanation, str)


# ═══════════════════════════════════════════════════════════════════
# TEST: batch_analyze()
# ═══════════════════════════════════════════════════════════════════

class TestVWREBatch:
    """Test per batch_analyze()."""

    def test_batch_returns_list(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        entries = [
            {"entity_id": "E1", "composite_score": sample_composite, "factors": sample_factors},
            {"entity_id": "E2", "composite_score": sample_composite, "factors": sample_factors},
        ]
        results = vwre_engine.batch_analyze(entries)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_preserves_order(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        entries = [
            {"entity_id": "FIRST", "composite_score": sample_composite, "factors": sample_factors},
            {"entity_id": "SECOND", "composite_score": sample_composite, "factors": sample_factors},
        ]
        results = vwre_engine.batch_analyze(entries)
        assert results[0].entity_id == "FIRST"
        assert results[1].entity_id == "SECOND"

    def test_batch_empty_input(self, vwre_engine):
        results = vwre_engine.batch_analyze([])
        assert results == []

    def test_batch_one_failure_does_not_block(
        self, vwre_engine, sample_factors, sample_composite,
    ):
        """Se un'entità fallisce, le altre continuano."""
        entries = [
            {"entity_id": "OK", "composite_score": sample_composite, "factors": sample_factors},
            {"entity_id": "EMPTY", "composite_score": 0.0, "factors": {}},
            {"entity_id": "OK2", "composite_score": sample_composite, "factors": sample_factors},
        ]
        results = vwre_engine.batch_analyze(entries)
        assert len(results) == 3
        assert results[0].entity_id == "OK"
        assert results[2].entity_id == "OK2"


# ═══════════════════════════════════════════════════════════════════
# TEST: _verify() e _z_narrative()
# ═══════════════════════════════════════════════════════════════════

class TestVWREInternals:
    """Test per i metodi statici interni."""

    def test_verify_small_residual(self):
        config = AttributionConfig(residual_tolerance=0.1, residual_warning=0.5)
        assert VWREEngine._verify(0.05, config) == "verified"

    def test_verify_medium_residual(self):
        config = AttributionConfig(residual_tolerance=0.1, residual_warning=0.5)
        assert VWREEngine._verify(0.3, config) == "warning"

    def test_verify_large_residual(self):
        config = AttributionConfig(residual_tolerance=0.1, residual_warning=0.5)
        assert VWREEngine._verify(1.0, config) == "error"

    def test_z_narrative_exceptional(self):
        narrative = VWREEngine._z_narrative("alpha", 2.0, 0.25, 0.5)
        assert "exceptional" in narrative

    def test_z_narrative_strong(self):
        narrative = VWREEngine._z_narrative("alpha", 1.2, 0.25, 0.3)
        assert "strong" in narrative

    def test_z_narrative_neutral(self):
        narrative = VWREEngine._z_narrative("alpha", -0.1, 0.25, -0.025)
        assert "neutral" in narrative

    def test_z_narrative_weak(self):
        narrative = VWREEngine._z_narrative("alpha", -1.5, 0.25, -0.375)
        assert "weak" in narrative

    def test_factor_attribution_frozen(self, vwre_engine, sample_factors, sample_composite):
        """FactorAttribution è frozen (immutabile)."""
        result = vwre_engine.analyze("E1", sample_composite, sample_factors)
        if result.factors:
            fa = list(result.factors.values())[0]
            with pytest.raises(AttributeError):
                fa.weight = 999.0  # type: ignore
