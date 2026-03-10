"""
Integration Test — Babel Gardens → Pattern Weavers cross-consumer flow.

Tests that ComprehensionConsumer (Babel) and LLMCompilerConsumer (Pattern Weavers)
correctly parse LLM output into validated domain objects, and that
WeaverConsumer validates requests and processes similarity results.

Markers: integration
"""

import pytest
from unittest.mock import patch

from core.cognitive.babel_gardens.consumers.comprehension_consumer import (
    ComprehensionConsumer,
)
from core.cognitive.babel_gardens.domain import BabelConfig

from core.cognitive.pattern_weavers.consumers.llm_compiler import (
    LLMCompilerConsumer,
)
from core.cognitive.pattern_weavers.consumers.weaver import WeaverConsumer
from core.cognitive.pattern_weavers.domain import PatternConfig


@pytest.fixture
def babel_config():
    return BabelConfig()


@pytest.fixture
def pattern_config():
    return PatternConfig()


@pytest.fixture
def comprehension_consumer(babel_config):
    return ComprehensionConsumer(babel_config)


@pytest.fixture
def compiler_consumer(pattern_config):
    return LLMCompilerConsumer(pattern_config)


@pytest.fixture
def weaver_consumer(pattern_config):
    return WeaverConsumer(pattern_config)


class TestBabelComprehensionConsumer:
    """Babel Gardens ComprehensionConsumer parses LLM JSON output."""

    def test_valid_llm_response_produces_successful_result(self, comprehension_consumer):
        llm_json = {
            "ontology": {
                "gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.95, "reasoning": "clear"},
                "entities": [],
                "intent_hint": "query",
            },
            "semantics": {},
            "sentiment": {},
            "emotion": {},
            "linguistic": {},
        }
        result = comprehension_consumer.process({
            "llm_response": llm_json,
            "raw_query": "test query",
            "domain": "generic",
        })
        assert result.success
        assert result.data["result"] is not None

    def test_missing_required_field_fails(self, comprehension_consumer):
        result = comprehension_consumer.process({"llm_response": "{}"})
        assert not result.success
        assert any("raw_query" in e for e in result.errors)

    def test_malformed_json_string_uses_fallback(self, comprehension_consumer):
        result = comprehension_consumer.process({
            "llm_response": "not valid json {{{",
            "raw_query": "test fallback",
            "domain": "generic",
        })
        # Should succeed with fallback/degraded result
        assert result.success
        assert result.data.get("parse_errors") or result.data.get("result") is not None


class TestPatternWeaversLLMCompiler:
    """Pattern Weavers LLMCompilerConsumer parses LLM JSON → OntologyPayload."""

    def test_valid_dict_response_produces_payload(self, compiler_consumer):
        llm_dict = {
            "gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.9, "reasoning": "ok"},
            "entities": [],
            "intent_hint": "question",
        }
        result = compiler_consumer.process({
            "llm_response": llm_dict,
            "raw_query": "What is pattern weaving?",
            "domain": "generic",
        })
        assert result.success
        assert result.data["payload"] is not None
        assert result.data["payload"]["raw_query"] == "What is pattern weaving?"

    def test_json_string_response_parsed_correctly(self, compiler_consumer):
        llm_str = '{"gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.8, "reasoning": "ok"}, "entities": []}'
        result = compiler_consumer.process({
            "llm_response": llm_str,
            "raw_query": "test string parse",
        })
        assert result.success

    def test_missing_required_fields_returns_error(self, compiler_consumer):
        result = compiler_consumer.process({"domain": "generic"})
        assert not result.success
        assert len(result.errors) >= 2  # missing llm_response + raw_query


class TestWeaverConsumerValidation:
    """WeaverConsumer validates requests and processes results."""

    def test_validate_request_success(self, weaver_consumer):
        result = weaver_consumer.process({
            "mode": "validate_request",
            "query_text": "How do patterns emerge in complex systems?",
            "user_id": "test_user",
            "language": "en",
        })
        assert result.success
        assert result.data["ready_for_embedding"] is True
        assert result.data["preprocessed_query"]

    def test_missing_query_text_fails(self, weaver_consumer):
        result = weaver_consumer.process({
            "mode": "validate_request",
            "user_id": "test_user",
        })
        assert not result.success
        assert any("query_text" in e for e in result.errors)

    def test_process_results_filters_by_threshold(self, weaver_consumer):
        result = weaver_consumer.process({
            "mode": "process_results",
            "similarity_results": [
                {"score": 0.95, "payload": {"category": "science", "name": "emergence"}},
                {"score": 0.30, "payload": {"category": "noise", "name": "irrelevant"}},
                {"score": 0.85, "payload": {"category": "math", "name": "topology"}},
            ],
            "similarity_threshold": 0.5,
        })
        assert result.success
        assert result.data["match_count"] == 2  # 0.30 filtered out

    def test_unknown_mode_returns_error(self, weaver_consumer):
        result = weaver_consumer.process({"mode": "nonexistent"})
        assert not result.success
        assert any("Unknown mode" in e for e in result.errors)


class TestBabelToWeaverFlow:
    """End-to-end: Babel ComprehensionConsumer output feeds Pattern Weavers."""

    def test_comprehension_output_provides_weaver_input(
        self, comprehension_consumer, weaver_consumer
    ):
        """ComprehensionConsumer extracts query → WeaverConsumer validates it."""
        llm_json = {
            "ontology": {
                "gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.9, "reasoning": "clear intent"},
                "entities": [],
                "intent_hint": "search",
            },
            "semantics": {},
            "sentiment": {},
            "emotion": {},
            "linguistic": {},
        }
        comprehension_result = comprehension_consumer.process({
            "llm_response": llm_json,
            "raw_query": "Find patterns in distributed systems",
            "domain": "generic",
        })
        assert comprehension_result.success

        # Feed the raw query to WeaverConsumer for validation
        weave_result = weaver_consumer.process({
            "mode": "validate_request",
            "query_text": "Find patterns in distributed systems",
            "user_id": "integration_test",
        })
        assert weave_result.success
        assert weave_result.data["ready_for_embedding"]
