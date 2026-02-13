"""
Test VPAR Pipeline Integration
================================

Test di integrazione per la pipeline VPAR completa:
  VEE (Explainability) + VARE (Risk) + VWRE (Attribution)

Verifica che i tre motori possano lavorare sulla stessa entità
e che i loro output siano compatibili.

A differenza dei test unitari, qui i motori REALI sono utilizzati
(non solo mockati). Solo le dipendenze infrastrutturali (memoria, LLM)
sono mockate.

Nota: VSGS è escluso perché richiede httpx + Qdrant (infrastruttura).
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ── Skip se i moduli non sono importabili ────────────────────────────

try:
    from core.vpar.vee.vee_engine import VEEEngine
    from core.vpar.vare.vare_engine import VAREEngine
    from core.vpar.vwre.vwre_engine import VWREEngine
    from core.vpar.vee.types import AnalysisResult, ExplanationLevels
    from core.vpar.vare.types import RiskConfig
    from core.vpar.vwre.types import AttributionConfig
    HAS_VPAR = True
except ImportError:
    HAS_VPAR = False

try:
    from domains.aggregation_contract import AggregationProvider, AggregationProfile
    HAS_AGG = True
except ImportError:
    HAS_AGG = False

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not HAS_VPAR, reason="VPAR modules not importable"),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES — Provider allineato per VWRE
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def aligned_provider():
    """AggregationProvider con chiavi allineate."""
    if not HAS_AGG:
        pytest.skip("AggregationProvider not importable")

    class AlignedProvider(AggregationProvider):
        def get_aggregation_profiles(self):
            return {
                "balanced": AggregationProfile(
                    name="balanced", description="Equal",
                    factor_weights={"alpha": 0.25, "beta": 0.25,
                                    "gamma": 0.25, "delta": 0.25}
                ),
            }

        def get_factor_mappings(self):
            return {"alpha": "alpha", "beta": "beta",
                    "gamma": "gamma", "delta": "delta"}

        def calculate_contribution(self, factor_value, weight, profile):
            return factor_value * weight

        def validate_factors(self, factors):
            return {"valid": True, "factor_count": len(factors)}

        def format_attribution_explanation(self, contributions, primary, composite):
            return {"summary": f"Primary: {primary}", "technical": "OK"}

    return AlignedProvider()


# ═══════════════════════════════════════════════════════════════════
# TEST: Pipeline completa su singola entità
# ═══════════════════════════════════════════════════════════════════

class TestVPARPipeline:
    """Test di integrazione: VEE + VARE + VWRE sulla stessa entità."""

    def test_vee_then_vare_same_entity(
        self, mock_explainability_provider, mock_risk_provider, sample_metrics,
    ):
        """VEE e VARE possono processare la stessa entità indipendentemente."""
        vee = VEEEngine(auto_store=False, use_memory=False)
        vare = VAREEngine(mock_risk_provider, domain_tag="test")

        # VEE: analisi
        with patch.object(vee.analyzer, "analyze") as mock_analyze, \
             patch.object(vee.generator, "generate") as mock_gen:
            mock_analyze.return_value = AnalysisResult(
                entity_id="E1", timestamp=datetime.utcnow(),
                signals=["positive"], signal_strengths={"positive": 0.8},
                dominant_factors=[("quality", 0.8)], overall_intensity=0.7,
            )
            mock_gen.return_value = ExplanationLevels(
                entity_id="E1", timestamp=datetime.utcnow(),
                summary="Good", technical="OK", detailed="Full",
            )
            vee_result = vee.explain("E1", sample_metrics, mock_explainability_provider)

        # VARE: rischio
        risk_data = {"values": [10.0, 12.0, 11.0, 13.0],
                     "weight": [0.25, 0.25, 0.25, 0.25]}
        vare_result = vare.assess_risk("E1", risk_data)

        # Entrambi devono aver prodotto risultati validi
        assert vee_result["summary"]
        assert vare_result.entity_id == "E1"
        assert vare_result.risk_category in {"LOW", "MODERATE", "HIGH", "EXTREME"}

    def test_vare_risk_feeds_attribution(
        self, mock_risk_provider, aligned_provider,
    ):
        """Il risultato di VARE può alimentare l'analisi VWRE."""
        vare = VAREEngine(mock_risk_provider, domain_tag="test")
        vwre = VWREEngine(aligned_provider, domain_tag="test")

        # VARE: calcola rischio
        risk_data = {"values": [10.0, 12.0, 11.0, 13.0],
                     "weight": [0.25, 0.25, 0.25, 0.25]}
        risk_result = vare.assess_risk("E1", risk_data)

        # VWRE: decompone il risk score
        factors = {dim: ds.score for dim, ds in risk_result.dimension_scores.items()}
        # Aggiungiamo i fattori attesi dal provider
        vwre_factors = {
            "alpha": factors.get("volatility", 0.0),
            "beta": factors.get("concentration", 0.0),
            "gamma": 0.5,  # fattore supplementare
            "delta": 0.3,
        }
        wre_result = vwre.analyze(
            "E1", risk_result.overall_risk, vwre_factors,
        )

        assert wre_result.entity_id == "E1"
        assert wre_result.primary_driver is not None

    def test_batch_consistency(
        self, mock_risk_provider, aligned_provider,
    ):
        """Batch VARE e batch VWRE devono produrre risultati coerenti."""
        vare = VAREEngine(mock_risk_provider)
        vwre = VWREEngine(aligned_provider)

        entities_data = [
            {"entity_id": f"E{i}", "raw_data": {
                "values": [10.0 + i, 12.0 + i, 11.0 + i],
                "weight": [0.33, 0.33, 0.34],
            }}
            for i in range(5)
        ]

        risk_results = vare.batch_assess(entities_data)
        assert len(risk_results) == 5

        wre_entries = [
            {
                "entity_id": r.entity_id,
                "composite_score": r.overall_risk,
                "factors": {
                    "alpha": list(r.dimension_scores.values())[0].score if r.dimension_scores else 0.0,
                    "beta": list(r.dimension_scores.values())[1].score if len(r.dimension_scores) > 1 else 0.0,
                    "gamma": 0.5,
                    "delta": 0.3,
                },
            }
            for r in risk_results
        ]
        wre_results = vwre.batch_analyze(wre_entries)
        assert len(wre_results) == 5

        # Tutti devono avere entity_id
        for i, r in enumerate(wre_results):
            assert r.entity_id == f"E{i}"


# ═══════════════════════════════════════════════════════════════════
# TEST: Domain contracts — validazione implementazione
# ═══════════════════════════════════════════════════════════════════

class TestDomainContractsIntegration:
    """Verifica che i mock provider soddisfino i contratti ABC."""

    def test_explainability_provider_contract(self, mock_explainability_provider):
        """Il mock deve implementare tutti i metodi del contratto."""
        p = mock_explainability_provider
        assert p.get_explanation_templates() is not None
        assert p.format_entity_reference("E1")
        assert isinstance(p.get_normalization_rules(), list)
        assert isinstance(p.get_analysis_dimensions(), list)
        assert isinstance(p.get_pattern_rules(), list)
        assert isinstance(p.get_intensity_weights(), dict)
        assert p.get_confidence_criteria() is not None

    def test_risk_provider_contract(self, mock_risk_provider):
        """Il mock deve implementare tutti i metodi del contratto."""
        p = mock_risk_provider
        dims = p.get_risk_dimensions()
        assert isinstance(dims, list)
        assert len(dims) > 0

        profiles = p.get_risk_profiles()
        assert isinstance(profiles, dict)
        assert "balanced" in profiles

        df = p.prepare_entity_data("E1", {"values": [1.0], "weight": [1.0]})
        assert hasattr(df, "columns")  # pd.DataFrame

        thresholds = p.get_risk_thresholds()
        assert isinstance(thresholds, dict)

        explanation = p.format_risk_explanation({"vol": 50.0}, 50.0, "MODERATE")
        assert "summary" in explanation

    def test_aggregation_provider_contract(self, aligned_provider):
        """Il mock deve implementare tutti i metodi del contratto."""
        p = aligned_provider
        profiles = p.get_aggregation_profiles()
        assert isinstance(profiles, dict)
        assert "balanced" in profiles

        mappings = p.get_factor_mappings()
        assert isinstance(mappings, dict)

        contribution = p.calculate_contribution(1.0, 0.5, profiles["balanced"])
        assert isinstance(contribution, float)

        validation = p.validate_factors({"alpha": 1.0})
        assert "valid" in validation

        explanation = p.format_attribution_explanation({"a": 0.5}, "a", 1.0)
        assert "summary" in explanation
