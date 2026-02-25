"""
Finance Semantic Plugin — Unit Tests
=====================================

Tests for FinanceSemanticPlugin (Pattern Weavers v3, mercator finance vertical).

> **Last updated**: Feb 24, 2026 18:00 UTC

Run: pytest tests/test_finance_semantic_plugin.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure imports work
_root = Path(__file__).resolve().parents[1] / "vitruvyan_core"
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from contracts.pattern_weavers import (
    DomainGate,
    GateVerdict,
    ISemanticPlugin,
    OntologyEntity,
    OntologyPayload,
)
from vitruvyan_core.domains.finance.pattern_weavers.finance_semantic_plugin import (
    FinanceSemanticPlugin,
)
from vitruvyan_core.core.cognitive.pattern_weavers.consumers.llm_compiler import (
    LLMCompilerConsumer,
)
from vitruvyan_core.core.cognitive.pattern_weavers.governance.semantic_plugin import (
    SemanticPluginRegistry,
)


class TestFinanceSemanticPlugin:
    """Test finance domain plugin."""

    @pytest.fixture
    def plugin(self):
        return FinanceSemanticPlugin()

    def test_domain_name(self, plugin):
        assert plugin.get_domain_name() == "finance"

    def test_implements_interface(self, plugin):
        assert isinstance(plugin, ISemanticPlugin)

    def test_system_prompt_contains_entity_types(self, plugin):
        prompt = plugin.get_system_prompt()
        for etype in ["ticker", "sector", "index", "currency", "commodity"]:
            assert etype in prompt

    def test_system_prompt_contains_intents(self, plugin):
        prompt = plugin.get_system_prompt()
        for intent in ["screening", "risk_analysis", "earnings"]:
            assert intent in prompt

    def test_gate_keywords_multilingual(self, plugin):
        keywords = plugin.get_gate_keywords()
        # English
        assert "stock" in keywords
        assert "portfolio" in keywords
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
        assert len(types) == 11  # 11 finance entity types

    def test_intent_vocabulary(self, plugin):
        intents = plugin.get_intent_vocabulary()
        assert "screening" in intents
        assert "unknown" in intents
        assert len(intents) == 11

    def test_validate_ticker_uppercase(self, plugin):
        """Ticker canonicals are uppercased."""
        payload = OntologyPayload(
            gate=DomainGate(
                verdict=GateVerdict.IN_DOMAIN,
                domain="finance",
                confidence=0.9,
            ),
            entities=[
                OntologyEntity(
                    raw="apple",
                    canonical="aapl",  # Lowercase
                    entity_type="ticker",
                    confidence=0.95,
                ),
                OntologyEntity(
                    raw="Technology",
                    canonical="Technology",
                    entity_type="sector",
                    confidence=0.85,
                ),
            ],
            raw_query="analyze apple stock",
        )
        validated = plugin.validate_payload(payload)
        assert validated.entities[0].canonical == "AAPL"  # Uppercased
        assert validated.entities[1].canonical == "Technology"  # Sector unchanged

    def test_registry_integration(self, plugin):
        """Finance plugin registers and resolves correctly."""
        registry = SemanticPluginRegistry()
        registry.register(plugin)
        assert registry.has_domain("finance")
        resolved = registry.get("finance")
        assert resolved.get_domain_name() == "finance"

    def test_consumer_with_finance_response(self, plugin):
        """End-to-end: simulated LLM response → consumer → validated payload."""
        consumer = LLMCompilerConsumer()

        llm_response = {
            "gate": {
                "verdict": "in_domain",
                "domain": "finance",
                "confidence": 0.95,
                "reasoning": "User asking about Tesla stock performance",
            },
            "entities": [
                {
                    "raw": "Tesla",
                    "canonical": "tsla",  # LLM might return lowercase
                    "entity_type": "ticker",
                    "confidence": 0.98,
                },
                {
                    "raw": "tech",
                    "canonical": "Technology",
                    "entity_type": "sector",
                    "confidence": 0.80,
                },
            ],
            "intent_hint": "screening",
            "topics": ["technology", "earnings"],
            "sentiment_hint": "neutral",
            "temporal_context": "real_time",
            "language": "en",
            "complexity": "simple",
        }

        result = consumer.process({
            "llm_response": llm_response,
            "raw_query": "How is Tesla doing?",
            "domain": "finance",
        })

        assert result.success
        payload = OntologyPayload.model_validate(result.data["payload"])

        # Now validate with finance plugin
        validated = plugin.validate_payload(payload)
        assert validated.entities[0].canonical == "TSLA"  # Uppercased!
        assert validated.gate.verdict == GateVerdict.IN_DOMAIN
        assert validated.intent_hint == "screening"
        assert "technology" in validated.topics


class TestFinanceCompileEndToEnd:
    """Test full pipeline simulation (without actual LLM)."""

    def test_italian_query_simulation(self):
        """Simulated Italian finance query."""
        consumer = LLMCompilerConsumer()
        plugin = FinanceSemanticPlugin()

        llm_response = {
            "gate": {
                "verdict": "in_domain",
                "domain": "finance",
                "confidence": 0.88,
                "reasoning": "Domanda su azioni italiane",
            },
            "entities": [
                {
                    "raw": "Enel",
                    "canonical": "ENEL.MI",
                    "entity_type": "ticker",
                    "confidence": 0.90,
                },
            ],
            "intent_hint": "fundamental_analysis",
            "topics": ["energy", "utilities", "dividends"],
            "sentiment_hint": "positive",
            "temporal_context": "forward_looking",
            "language": "it",
            "complexity": "simple",
        }

        result = consumer.process({
            "llm_response": llm_response,
            "raw_query": "Come va Enel? Distribuzione dividendi?",
            "domain": "finance",
        })

        assert result.success
        payload = OntologyPayload.model_validate(result.data["payload"])
        validated = plugin.validate_payload(payload)

        assert validated.language == "it"
        assert validated.entities[0].canonical == "ENEL.MI"
        assert "dividends" in validated.topics

    def test_out_of_domain_query(self):
        """Non-financial query should gate out."""
        consumer = LLMCompilerConsumer()

        llm_response = {
            "gate": {
                "verdict": "out_of_domain",
                "domain": "generic",
                "confidence": 0.92,
                "reasoning": "Query about weather, not finance",
            },
            "entities": [],
            "intent_hint": "unknown",
            "topics": [],
            "sentiment_hint": "neutral",
            "temporal_context": "real_time",
            "language": "en",
            "complexity": "simple",
        }

        result = consumer.process({
            "llm_response": llm_response,
            "raw_query": "What's the weather like?",
            "domain": "finance",
        })

        assert result.success
        payload = OntologyPayload.model_validate(result.data["payload"])
        assert payload.gate.verdict == GateVerdict.OUT_OF_DOMAIN
        assert len(payload.entities) == 0
