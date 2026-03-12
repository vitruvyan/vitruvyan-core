"""
Finance Comprehension Plugin — Unit Tests
==========================================

Tests for FinanceComprehensionPlugin + FinBERTContributor
(Comprehension Engine v3, mercator finance vertical).

> **Last updated**: Feb 28, 2026 12:00 UTC

Run: pytest tests/test_finance_comprehension_plugin.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure imports work
_root = Path(__file__).resolve().parents[1] / "vitruvyan_core"
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from contracts.comprehension import (
    ComprehensionResult,
    ComprehendRequest,
    EmotionPayload,
    FuseRequest,
    FusionResult,
    FusionStrategy,
    IComprehensionPlugin,
    ISignalContributor,
    LinguisticPayload,
    SemanticPayload,
    SentimentPayload,
    SignalEvidence,
)
from contracts.pattern_weavers import (
    DomainGate,
    GateVerdict,
    OntologyEntity,
    OntologyPayload,
)
from vitruvyan_core.domains.finance.babel_gardens.finance_comprehension_plugin import (
    FinanceComprehensionPlugin,
)
from vitruvyan_core.core.cognitive.babel_gardens.governance.signal_registry import (
    ComprehensionPluginRegistry,
    SignalContributorRegistry,
)
from vitruvyan_core.core.cognitive.babel_gardens.consumers.comprehension_consumer import (
    ComprehensionConsumer,
)
from vitruvyan_core.core.cognitive.babel_gardens.consumers.signal_fusion_consumer import (
    SignalFusionConsumer,
)


# ─────────────────────────────────────────────────────────────
# FinanceComprehensionPlugin tests
# ─────────────────────────────────────────────────────────────

class TestFinanceComprehensionPlugin:
    """Test finance domain comprehension plugin."""

    @pytest.fixture
    def plugin(self):
        return FinanceComprehensionPlugin()

    def test_domain_name(self, plugin):
        assert plugin.get_domain_name() == "finance"

    def test_implements_interface(self, plugin):
        assert isinstance(plugin, IComprehensionPlugin)

    def test_ontology_prompt_contains_entity_types(self, plugin):
        prompt = plugin.get_ontology_prompt_section()
        for etype in ["ticker", "sector", "index", "currency", "commodity",
                       "crypto", "fund", "region", "indicator", "analyst", "concept"]:
            assert etype in prompt

    def test_ontology_prompt_contains_intents(self, plugin):
        prompt = plugin.get_ontology_prompt_section()
        for intent in ["screening", "risk_analysis", "portfolio_review",
                        "earnings", "technical_analysis", "fundamental_analysis"]:
            assert intent in prompt

    def test_semantics_prompt_contains_sentiment_labels(self, plugin):
        prompt = plugin.get_semantics_prompt_section()
        for label in ["bullish", "bearish", "hold"]:
            assert label in prompt

    def test_semantics_prompt_contains_market_emotions(self, plugin):
        prompt = plugin.get_semantics_prompt_section()
        for emotion in ["fear", "greed", "confidence", "uncertainty"]:
            assert emotion in prompt

    def test_semantics_prompt_contains_irony_detection(self, plugin):
        prompt = plugin.get_semantics_prompt_section()
        assert "irony" in prompt.lower() or "sarcas" in prompt.lower()

    def test_gate_keywords_multilingual(self, plugin):
        keywords = plugin.get_gate_keywords()
        # English
        assert "stock" in keywords
        assert "portfolio" in keywords
        assert "volatility" in keywords
        # Italian
        assert "borsa" in keywords
        assert "azioni" in keywords
        # Spanish
        assert "bolsa" in keywords

    def test_entity_types(self, plugin):
        types = plugin.get_entity_types()
        assert "ticker" in types
        assert "sector" in types
        assert "crypto" in types
        assert len(types) == 11

    def test_signal_schemas(self, plugin):
        schemas = plugin.get_signal_schemas()
        assert "sentiment_valence" in schemas
        assert "market_fear_index" in schemas
        assert "volatility_perception" in schemas
        # All have range and source
        for name, schema in schemas.items():
            assert "range" in schema
            assert "source" in schema
            assert schema["source"] == "finbert"

    def test_validate_result_normalizes_tickers(self, plugin):
        """Tickers must be uppercase after validation."""
        result = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.IN_DOMAIN,
                    domain="finance",
                    confidence=0.95,
                    reasoning="test",
                ),
                entities=[
                    OntologyEntity(raw="apple", canonical="aapl", entity_type="ticker", confidence=0.9),
                    OntologyEntity(raw="Tesla", canonical="tsla", entity_type="ticker", confidence=0.85),
                    OntologyEntity(raw="Technology", canonical="Technology", entity_type="sector", confidence=0.8),
                ],
            ),
            raw_query="compare apple and tesla",
            language="en",
        )

        validated = plugin.validate_result(result)
        tickers = [e for e in validated.ontology.entities if e.entity_type == "ticker"]
        assert tickers[0].canonical == "AAPL"
        assert tickers[1].canonical == "TSLA"
        # Non-tickers unchanged
        sectors = [e for e in validated.ontology.entities if e.entity_type == "sector"]
        assert sectors[0].canonical == "Technology"

    def test_validate_result_enforces_finance_domain(self, plugin):
        """If LLM set domain to 'generic', validation corrects to 'finance'."""
        result = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.IN_DOMAIN,
                    domain="generic",
                    confidence=0.9,
                    reasoning="test",
                ),
            ),
            raw_query="how is the market?",
            language="en",
        )

        validated = plugin.validate_result(result)
        assert validated.ontology.gate.domain == "finance"


# ─────────────────────────────────────────────────────────────
# Registry integration tests
# ─────────────────────────────────────────────────────────────

class TestFinanceRegistryIntegration:
    """Test finance plugin integration with registries."""

    def test_register_finance_plugin(self):
        registry = ComprehensionPluginRegistry()
        plugin = FinanceComprehensionPlugin()
        registry.register(plugin)

        resolved = registry.resolve("finance")
        assert resolved.get_domain_name() == "finance"

    def test_finance_takes_priority_over_generic(self):
        registry = ComprehensionPluginRegistry()
        plugin = FinanceComprehensionPlugin()
        registry.register(plugin)

        # Auto should resolve to finance (single non-generic domain)
        auto = registry.resolve("auto")
        assert auto.get_domain_name() == "finance"

        # Finance explicit
        fin = registry.resolve("finance")
        assert fin.get_domain_name() == "finance"

    def test_registered_domains_includes_finance(self):
        registry = ComprehensionPluginRegistry()
        registry.register(FinanceComprehensionPlugin())

        domains = registry.registered_domains
        assert "generic" in domains
        assert "finance" in domains


# ─────────────────────────────────────────────────────────────
# Comprehension consumer with finance LLM output
# ─────────────────────────────────────────────────────────────

class TestFinanceComprehensionConsumer:
    """Test ComprehensionConsumer with finance-specific LLM output."""

    @pytest.fixture
    def consumer(self):
        return ComprehensionConsumer(config=None)

    def test_parse_finance_llm_response(self, consumer):
        """Full finance LLM response: ontology + semantics."""
        llm_output = {
            "ontology": {
                "gate": {
                    "verdict": "in_domain",
                    "domain": "finance",
                    "confidence": 0.97,
                    "reasoning": "Earnings analysis query about AAPL",
                },
                "entities": [
                    {"raw": "Apple", "canonical": "AAPL", "entity_type": "ticker", "confidence": 0.95},
                    {"raw": "earnings", "canonical": "earnings", "entity_type": "concept", "confidence": 0.8},
                ],
                "intent_hint": "earnings",
                "topics": ["technology", "earnings"],
                "language": "en",
            },
            "semantics": {
                "sentiment": {
                    "label": "positive",
                    "score": 0.72,
                    "confidence": 0.88,
                    "magnitude": 0.65,
                    "aspects": [{"aspect": "AAPL_earnings", "label": "positive", "score": 0.8}],
                    "reasoning": "Earnings beat expectations, bullish language",
                },
                "emotion": {
                    "primary": "confidence",
                    "secondary": ["excitement"],
                    "intensity": 0.7,
                    "confidence": 0.82,
                    "reasoning": "Strong institutional trust language",
                },
                "linguistic": {
                    "text_register": "formal",
                    "irony_detected": False,
                    "ambiguity_score": 0.1,
                },
            },
        }

        result = consumer.process(
            {"llm_response": llm_output, "raw_query": "How were Apple earnings?", "query_language": "en"}
        )
        assert result.success is True
        comp = ComprehensionResult.model_validate(result.data["result"])

        # Ontology checks
        assert comp.ontology.gate.domain == "finance"
        assert comp.ontology.gate.verdict == GateVerdict.IN_DOMAIN
        assert len(comp.ontology.entities) == 2
        assert comp.ontology.entities[0].canonical == "AAPL"
        assert comp.ontology.intent_hint == "earnings"

        # Semantics checks
        assert comp.semantics.sentiment.label == "positive"
        assert comp.semantics.sentiment.score == 0.72
        assert len(comp.semantics.sentiment.aspects) == 1
        assert comp.semantics.emotion.primary == "confidence"
        assert comp.semantics.linguistic.text_register == "formal"
        assert comp.semantics.linguistic.irony_detected is False

    def test_parse_italian_finance_query(self, consumer):
        """Italian financial query with mixed sentiment."""
        llm_output = {
            "ontology": {
                "gate": {
                    "verdict": "in_domain",
                    "domain": "finance",
                    "confidence": 0.93,
                    "reasoning": "Domanda su mercato italiano e titoli",
                },
                "entities": [
                    {"raw": "Unicredit", "canonical": "UCG.MI", "entity_type": "ticker", "confidence": 0.88},
                    {"raw": "Intesa", "canonical": "ISP.MI", "entity_type": "ticker", "confidence": 0.85},
                ],
                "intent_hint": "comparison",
                "topics": ["financials"],
                "language": "it",
            },
            "semantics": {
                "sentiment": {
                    "label": "mixed",
                    "score": 0.1,
                    "confidence": 0.75,
                    "magnitude": 0.4,
                    "aspects": [
                        {"aspect": "UCG.MI", "label": "positive", "score": 0.6},
                        {"aspect": "ISP.MI", "label": "negative", "score": -0.3},
                    ],
                    "reasoning": "Unicredit positivo, Intesa sotto pressione",
                },
                "emotion": {
                    "primary": "uncertainty",
                    "intensity": 0.5,
                    "confidence": 0.7,
                },
                "linguistic": {
                    "text_register": "formal",
                    "irony_detected": False,
                    "ambiguity_score": 0.3,
                },
            },
        }

        result = consumer.process(
            {"llm_response": llm_output, "raw_query": "Come va Unicredit rispetto a Intesa?", "query_language": "it"}
        )
        assert result.success is True
        comp = ComprehensionResult.model_validate(result.data["result"])

        assert comp.language == "it"
        assert comp.ontology.gate.domain == "finance"
        assert len(comp.ontology.entities) == 2
        assert comp.semantics.sentiment.label == "mixed"
        assert len(comp.semantics.sentiment.aspects) == 2
        assert comp.semantics.emotion.primary == "uncertainty"


# ─────────────────────────────────────────────────────────────
# Signal fusion with FinBERT evidences
# ─────────────────────────────────────────────────────────────

class TestFinanceSignalFusion:
    """Test signal fusion with finance-specific FinBERT evidences."""

    @pytest.fixture
    def fusion_consumer(self):
        return SignalFusionConsumer(config=None)

    def _make_comprehension(self, sentiment_score=0.6, emotion="confidence"):
        """Helper: create a ComprehensionResult for fusion."""
        return ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.IN_DOMAIN,
                    domain="finance",
                    confidence=0.95,
                    reasoning="test",
                ),
                entities=[
                    OntologyEntity(raw="AAPL", canonical="AAPL", entity_type="ticker", confidence=0.9),
                ],
            ),
            semantics=SemanticPayload(
                sentiment=SentimentPayload(
                    label="positive", score=sentiment_score,
                    confidence=0.85, magnitude=0.6,
                ),
                emotion=EmotionPayload(
                    primary=emotion, intensity=0.65, confidence=0.8,
                ),
            ),
            raw_query="How is AAPL doing?",
            language="en",
        )

    def test_fuse_llm_plus_finbert_sentiment(self, fusion_consumer):
        """Fuse LLM L1 sentiment with FinBERT L2 sentiment."""
        comp = self._make_comprehension(sentiment_score=0.6)

        finbert_evidence = SignalEvidence(
            signal_name="sentiment",
            value=0.7,
            confidence=0.9,
            source="finbert",
            method="model:ProsusAI/finbert",
        )

        result = fusion_consumer.process({
            "comprehension": comp,
            "evidences": [finbert_evidence],
            "strategy": FusionStrategy.WEIGHTED,
            "weights": {"llm": 0.45, "finbert": 0.35},
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        # Should have sentiment fusion result
        sentiment_results = [r for r in fusions if r.signal_name == "sentiment"]
        assert len(sentiment_results) == 1
        fused = sentiment_results[0]
        assert fused.fused_confidence > 0
        assert len(fused.contributors) >= 2  # LLM + FinBERT

    def test_fuse_with_finbert_market_fear(self, fusion_consumer):
        """FinBERT-only signal (market_fear_index) passes through."""
        comp = self._make_comprehension()

        finbert_evidences = [
            SignalEvidence(
                signal_name="sentiment_valence",
                value=0.65,
                confidence=0.88,
                source="finbert",
                method="model:ProsusAI/finbert",
            ),
            SignalEvidence(
                signal_name="market_fear_index",
                value=0.35,
                confidence=0.82,
                source="finbert",
                method="model:ProsusAI/finbert",
            ),
        ]

        result = fusion_consumer.process({
            "comprehension": comp,
            "evidences": finbert_evidences,
            "strategy": FusionStrategy.WEIGHTED,
            "weights": {},
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        signal_names = {r.signal_name for r in fusions}
        # Should have sentiment + emotion (from L1) + sentiment_valence + market_fear_index (from FinBERT)
        assert "market_fear_index" in signal_names

    def test_bayesian_fusion_with_finance_signals(self, fusion_consumer):
        """Bayesian fusion combines LLM + FinBERT with posterior update."""
        comp = self._make_comprehension(sentiment_score=0.5)

        finbert_evidence = SignalEvidence(
            signal_name="sentiment",
            value=0.8,
            confidence=0.92,
            source="finbert",
            method="model:ProsusAI/finbert",
        )

        result = fusion_consumer.process({
            "comprehension": comp,
            "evidences": [finbert_evidence],
            "strategy": FusionStrategy.BAYESIAN,
            "weights": {},
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sentiment_results = [r for r in fusions if r.signal_name == "sentiment"]
        assert len(sentiment_results) == 1
        fused = sentiment_results[0]
        assert fused.strategy_used == "bayesian"
        # Bayesian with high-confidence FinBERT should pull toward 0.8
        assert fused.fused_value > 0.5

    def test_finbert_weights_override(self, fusion_consumer):
        """Finance-specific weight overrides (LLM: 0.45, FinBERT: 0.35)."""
        comp = self._make_comprehension(sentiment_score=0.3)

        finbert_evidence = SignalEvidence(
            signal_name="sentiment",
            value=0.9,
            confidence=0.85,
            source="finbert",
            method="model:ProsusAI/finbert",
        )

        result = fusion_consumer.process({
            "comprehension": comp,
            "evidences": [finbert_evidence],
            "strategy": FusionStrategy.WEIGHTED,
            "weights": {"llm": 0.45, "finbert": 0.35},
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sentiment_results = [r for r in fusions if r.signal_name == "sentiment"]
        assert len(sentiment_results) == 1


# ─────────────────────────────────────────────────────────────
# FinBERTContributor contract tests (without actual model)
# ─────────────────────────────────────────────────────────────

_torch_available = True
try:
    import torch  # noqa: F401
except ImportError:
    _torch_available = False


@pytest.mark.skipif(not _torch_available, reason="torch not installed")
class TestFinBERTContributorContract:
    """Test FinBERTContributor implements ISignalContributor correctly."""

    @pytest.fixture(autouse=True)
    def _mock_pg(self):
        """Mock PostgresAgent to avoid real DB connections during import."""
        with patch("core.agents.postgres_agent.PostgresAgent.__init__", return_value=None):
            yield

    def test_contributor_name(self):
        from services.api_babel_gardens.plugins.finbert_contributor import FinBERTContributor
        contributor = FinBERTContributor()
        assert contributor.get_contributor_name() == "finbert"

    def test_signal_names(self):
        from services.api_babel_gardens.plugins.finbert_contributor import FinBERTContributor
        contributor = FinBERTContributor()
        names = contributor.get_signal_names()
        assert "sentiment_valence" in names
        assert "market_fear_index" in names
        assert "volatility_perception" in names

    def test_implements_interface(self):
        from services.api_babel_gardens.plugins.finbert_contributor import FinBERTContributor
        contributor = FinBERTContributor()
        assert isinstance(contributor, ISignalContributor)

    def test_is_available_when_transformers_missing(self):
        """When transformers not installed, is_available() returns False."""
        from services.api_babel_gardens.plugins.finbert_contributor import FinBERTContributor
        contributor = FinBERTContributor()

        with patch("importlib.import_module", side_effect=ImportError("no transformers")):
            assert contributor.is_available() is False

    def test_contribute_returns_empty_when_no_config(self):
        """When signal config YAML not found, returns empty list."""
        from services.api_babel_gardens.plugins.finbert_contributor import FinBERTContributor
        contributor = FinBERTContributor()
        # Force _config to return None
        contributor._signal_config = None
        with patch.object(type(contributor), '_config', new_callable=lambda: property(lambda self: None)):
            result = contributor.contribute("test text")
            assert result == []


# ─────────────────────────────────────────────────────────────
# End-to-end comprehension flow (mock LLM)
# ─────────────────────────────────────────────────────────────

class TestFinanceComprehensionFlow:
    """Test full finance comprehension flow: plugin → consumer → validation."""

    def test_full_finance_flow(self):
        """Plugin prompt → consumer parse → plugin validate."""
        plugin = FinanceComprehensionPlugin()

        # 1. Plugin provides prompt sections
        ontology_prompt = plugin.get_ontology_prompt_section()
        semantics_prompt = plugin.get_semantics_prompt_section()
        assert "ticker" in ontology_prompt
        assert "bullish" in semantics_prompt

        # 2. Simulated LLM output (what LLM would produce given the prompts)
        llm_output = {
            "ontology": {
                "gate": {
                    "verdict": "in_domain",
                    "domain": "finance",
                    "confidence": 0.96,
                    "reasoning": "Stock screening query",
                },
                "entities": [
                    {"raw": "tech stocks", "canonical": "Technology", "entity_type": "sector", "confidence": 0.9},
                ],
                "intent_hint": "screening",
                "topics": ["technology"],
                "language": "en",
            },
            "semantics": {
                "sentiment": {
                    "label": "positive",
                    "score": 0.55,
                    "confidence": 0.78,
                    "magnitude": 0.4,
                    "reasoning": "Moderately bullish inquiry",
                },
                "emotion": {
                    "primary": "excitement",
                    "intensity": 0.5,
                    "confidence": 0.7,
                },
                "linguistic": {
                    "text_register": "informal",
                    "irony_detected": False,
                    "ambiguity_score": 0.15,
                },
            },
        }

        # 3. Consumer parses
        consumer = ComprehensionConsumer(config=None)
        result = consumer.process({
            "llm_response": llm_output,
            "raw_query": "show me the best tech stocks",
            "query_language": "en",
        })
        assert result.success is True

        # 4. Plugin validates
        comp = ComprehensionResult.model_validate(result.data["result"])
        validated = plugin.validate_result(comp)
        assert validated.ontology.gate.domain == "finance"
        assert validated.semantics.sentiment.label == "positive"
        assert validated.semantics.linguistic.text_register == "informal"

    def test_finance_to_generic_degradation(self):
        """When LLM fails, consumer returns fallback but plugin still validates."""
        plugin = FinanceComprehensionPlugin()
        consumer = ComprehensionConsumer(config=None)

        # Broken LLM output
        result = consumer.process({
            "llm_response": "This is not JSON at all",
            "raw_query": "show me AAPL",
            "query_language": "en",
        })

        # Falls back to default ComprehensionResult
        assert result.success is True
        comp = ComprehensionResult.model_validate(result.data["result"])
        assert comp.ontology.gate.verdict == GateVerdict.AMBIGUOUS

        # Plugin validation still works on fallback
        validated = plugin.validate_result(comp)
        assert validated.ontology.gate.domain == "finance"


# ─────────────────────────────────────────────────────────────
# Serialization round-trip with finance data
# ─────────────────────────────────────────────────────────────

class TestFinanceSerialization:
    """Test that finance comprehension results survive JSON round-trip."""

    def test_finance_result_roundtrip(self):
        result = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.IN_DOMAIN,
                    domain="finance",
                    confidence=0.96,
                    reasoning="Earnings query",
                ),
                entities=[
                    OntologyEntity(raw="AAPL", canonical="AAPL", entity_type="ticker", confidence=0.95),
                    OntologyEntity(raw="GOOGL", canonical="GOOGL", entity_type="ticker", confidence=0.9),
                ],
                intent_hint="earnings",
                topics=["technology", "earnings"],
            ),
            semantics=SemanticPayload(
                sentiment=SentimentPayload(
                    label="positive", score=0.7, confidence=0.88, magnitude=0.6,
                    aspects=[{"aspect": "AAPL", "label": "positive", "score": 0.8}],
                ),
                emotion=EmotionPayload(
                    primary="confidence", secondary=["excitement"],
                    intensity=0.7, confidence=0.82,
                ),
                linguistic=LinguisticPayload(text_register="formal"),
            ),
            raw_query="How were AAPL and GOOGL earnings?",
            language="en",
            comprehension_metadata={"domain_plugin": "finance", "model": "gpt-4o-mini"},
        )

        d = result.model_dump()
        j = json.dumps(d)
        restored = ComprehensionResult.model_validate(json.loads(j))

        assert restored.ontology.gate.domain == "finance"
        assert len(restored.ontology.entities) == 2
        assert restored.ontology.entities[0].canonical == "AAPL"
        assert restored.semantics.sentiment.label == "positive"
        assert restored.semantics.emotion.primary == "confidence"
        assert restored.language == "en"
        assert restored.comprehension_metadata["domain_plugin"] == "finance"


__all__ = []
