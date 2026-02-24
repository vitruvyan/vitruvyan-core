"""
Pattern Weavers v3 — Unit Tests
================================

Tests for:
- OntologyPayload contract (schema enforcement, extra="forbid")
- LLMCompilerConsumer (pure JSON parsing, fallback handling)
- SemanticPluginRegistry (registration, lookup, generic fallback)
- DomainGate and GateVerdict semantics

> **Last updated**: Feb 24, 2026 18:00 UTC

Run: pytest tests/test_pattern_weavers_v3.py -v
"""

import json
import pytest

# ─── Import contracts ────────────────────────────────────────
import sys
from pathlib import Path

# Ensure vitruvyan_core is importable
_root = Path(__file__).resolve().parents[1] / "vitruvyan_core"
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from vitruvyan_core.contracts.pattern_weavers import (
    CompileRequest,
    CompileResponse,
    DomainGate,
    GateVerdict,
    ISemanticPlugin,
    OntologyEntity,
    OntologyPayload,
)
from vitruvyan_core.core.cognitive.pattern_weavers.consumers.llm_compiler import (
    LLMCompilerConsumer,
)
from vitruvyan_core.core.cognitive.pattern_weavers.governance.semantic_plugin import (
    GenericSemanticPlugin,
    SemanticPluginRegistry,
)


# ═════════════════════════════════════════════════════════════
# 1. OntologyPayload Contract Tests
# ═════════════════════════════════════════════════════════════


class TestOntologyPayload:
    """Test the strict Pydantic schema."""

    def test_default_construction(self):
        """Minimal valid payload."""
        p = OntologyPayload(raw_query="hello")
        assert p.schema_version == "1.0.0"
        assert p.gate.verdict == GateVerdict.AMBIGUOUS
        assert p.entities == []
        assert p.intent_hint == "unknown"
        assert p.raw_query == "hello"

    def test_full_construction(self):
        """All fields populated."""
        p = OntologyPayload(
            gate=DomainGate(
                verdict=GateVerdict.IN_DOMAIN,
                domain="finance",
                confidence=0.95,
                reasoning="Contains ticker symbols",
            ),
            entities=[
                OntologyEntity(
                    raw="AAPL",
                    canonical="Apple Inc.",
                    entity_type="ticker",
                    confidence=0.99,
                ),
            ],
            intent_hint="screening",
            topics=["technology", "earnings"],
            sentiment_hint="positive",
            temporal_context="forward_looking",
            language="en",
            complexity="compound",
            raw_query="What about AAPL earnings?",
            compile_metadata={"model": "gpt-4o-mini", "llm_time_ms": 342.5},
        )
        assert p.gate.verdict == GateVerdict.IN_DOMAIN
        assert len(p.entities) == 1
        assert p.entities[0].canonical == "Apple Inc."
        assert p.intent_hint == "screening"

    def test_extra_field_forbidden(self):
        """extra='forbid' — unknown fields rejected."""
        with pytest.raises(Exception):  # ValidationError
            OntologyPayload(
                raw_query="test",
                bogus_field="should_fail",
            )

    def test_gate_extra_forbidden(self):
        """Gate also forbids extra fields."""
        with pytest.raises(Exception):
            DomainGate(
                verdict=GateVerdict.IN_DOMAIN,
                confidence=0.9,
                my_extra="nope",
            )

    def test_entity_extra_forbidden(self):
        """Entity also forbids extra fields."""
        with pytest.raises(Exception):
            OntologyEntity(
                raw="x",
                canonical="x",
                entity_type="concept",
                confidence=0.5,
                color="blue",
            )

    def test_confidence_bounds(self):
        """Confidence must be 0.0–1.0."""
        with pytest.raises(Exception):
            OntologyEntity(
                raw="x", canonical="x", entity_type="t", confidence=1.5
            )

    def test_serialization_roundtrip(self):
        """model_dump() → model_validate() roundtrip."""
        original = OntologyPayload(
            gate=DomainGate(
                verdict=GateVerdict.IN_DOMAIN,
                domain="test",
                confidence=0.8,
            ),
            entities=[
                OntologyEntity(raw="a", canonical="A", entity_type="concept", confidence=0.7)
            ],
            raw_query="test query",
        )
        data = original.model_dump()
        restored = OntologyPayload.model_validate(data)
        assert restored.gate.verdict == GateVerdict.IN_DOMAIN
        assert restored.entities[0].canonical == "A"
        assert restored.raw_query == "test query"


# ═════════════════════════════════════════════════════════════
# 2. LLMCompilerConsumer Tests
# ═════════════════════════════════════════════════════════════


class TestLLMCompilerConsumer:
    """Test pure JSON parsing consumer."""

    @pytest.fixture
    def consumer(self):
        return LLMCompilerConsumer()

    def _valid_llm_response(self) -> dict:
        """A valid LLM JSON response matching OntologyPayload schema."""
        return {
            "gate": {
                "verdict": "in_domain",
                "domain": "finance",
                "confidence": 0.92,
                "reasoning": "Financial query about stock performance",
            },
            "entities": [
                {
                    "raw": "Tesla",
                    "canonical": "TSLA",
                    "entity_type": "ticker",
                    "confidence": 0.95,
                }
            ],
            "intent_hint": "screening",
            "topics": ["technology", "ev"],
            "sentiment_hint": "neutral",
            "temporal_context": "real_time",
            "language": "en",
            "complexity": "simple",
        }

    def test_parse_valid_dict(self, consumer):
        """Valid dict input → success."""
        result = consumer.process({
            "llm_response": self._valid_llm_response(),
            "raw_query": "How is Tesla doing?",
            "domain": "finance",
        })
        assert result.success
        payload = result.data["payload"]
        assert payload["gate"]["verdict"] == "in_domain"
        assert len(payload["entities"]) == 1
        assert payload["entities"][0]["canonical"] == "TSLA"
        assert payload["raw_query"] == "How is Tesla doing?"

    def test_parse_valid_json_string(self, consumer):
        """Valid JSON string input → success."""
        result = consumer.process({
            "llm_response": json.dumps(self._valid_llm_response()),
            "raw_query": "How is Tesla doing?",
        })
        assert result.success
        assert result.data["payload"]["gate"]["verdict"] == "in_domain"

    def test_parse_json_in_code_fences(self, consumer):
        """JSON wrapped in ```json ... ``` → extracted."""
        wrapped = f"```json\n{json.dumps(self._valid_llm_response())}\n```"
        result = consumer.process({
            "llm_response": wrapped,
            "raw_query": "test",
        })
        assert result.success
        assert result.data["payload"]["gate"]["verdict"] == "in_domain"

    def test_parse_json_with_preamble(self, consumer):
        """JSON with leading text → extracted."""
        text = f"Here is the analysis:\n{json.dumps(self._valid_llm_response())}"
        result = consumer.process({
            "llm_response": text,
            "raw_query": "test",
        })
        assert result.success

    def test_invalid_json_fallback(self, consumer):
        """Unparseable string → fallback payload (degraded but valid)."""
        result = consumer.process({
            "llm_response": "This is not JSON at all",
            "raw_query": "test",
            "domain": "finance",
        })
        # Fallback still returns success=True (degraded)
        assert result.success
        payload = result.data["payload"]
        assert payload["gate"]["verdict"] == "ambiguous"
        assert payload["compile_metadata"]["fallback"] is True

    def test_extra_fields_trigger_fallback(self, consumer):
        """LLM returns extra fields → ValidationError → fallback."""
        bad = self._valid_llm_response()
        bad["hallucinated_field"] = "oops"
        result = consumer.process({
            "llm_response": bad,
            "raw_query": "test",
        })
        # extra="forbid" catches it, consumer falls back
        assert result.success
        payload = result.data["payload"]
        assert payload["compile_metadata"].get("fallback") is True

    def test_missing_required_input(self, consumer):
        """Missing llm_response → failure."""
        result = consumer.process({"raw_query": "test"})
        assert not result.success
        assert "llm_response" in str(result.errors)

    def test_metadata_injection(self, consumer):
        """compile_meta is injected into payload."""
        result = consumer.process({
            "llm_response": self._valid_llm_response(),
            "raw_query": "test",
            "compile_meta": {"request_id": "abc123", "llm_time_ms": 200},
        })
        assert result.success
        meta = result.data["payload"]["compile_metadata"]
        assert meta["request_id"] == "abc123"
        assert meta["llm_time_ms"] == 200
        assert "parse_time_ms" in meta


# ═════════════════════════════════════════════════════════════
# 3. SemanticPluginRegistry Tests
# ═════════════════════════════════════════════════════════════


class TestSemanticPluginRegistry:
    """Test plugin registration and lookup."""

    def test_generic_always_registered(self):
        registry = SemanticPluginRegistry()
        assert registry.has_domain("generic")
        plugin = registry.get("generic")
        assert plugin.get_domain_name() == "generic"

    def test_auto_resolves_to_generic(self):
        registry = SemanticPluginRegistry()
        plugin = registry.resolve_domain("auto")
        assert plugin.get_domain_name() == "generic"

    def test_unknown_domain_falls_back_to_generic(self):
        registry = SemanticPluginRegistry()
        plugin = registry.get("nonexistent")
        assert plugin.get_domain_name() == "generic"

    def test_register_custom_plugin(self):
        """Register and retrieve a custom domain plugin."""

        class TestPlugin(ISemanticPlugin):
            def get_domain_name(self): return "test"
            def get_system_prompt(self): return "Test prompt"
            def get_entity_types(self): return ["concept"]
            def get_gate_keywords(self): return ["test"]

        registry = SemanticPluginRegistry()
        registry.register(TestPlugin())
        assert registry.has_domain("test")
        assert registry.get("test").get_domain_name() == "test"
        assert "test" in registry.registered_domains

    def test_generic_plugin_has_system_prompt(self):
        plugin = GenericSemanticPlugin()
        prompt = plugin.get_system_prompt()
        assert "semantic compiler" in prompt.lower()
        assert "JSON" in prompt

    def test_generic_plugin_entity_types(self):
        plugin = GenericSemanticPlugin()
        types = plugin.get_entity_types()
        assert "concept" in types
        assert "person" in types

    def test_validate_payload_passthrough(self):
        """Default validate_payload returns payload unchanged."""
        plugin = GenericSemanticPlugin()
        payload = OntologyPayload(raw_query="test")
        result = plugin.validate_payload(payload)
        assert result.raw_query == "test"


# ═════════════════════════════════════════════════════════════
# 4. CompileRequest / CompileResponse Tests
# ═════════════════════════════════════════════════════════════


class TestCompileRequestResponse:
    def test_compile_request_defaults(self):
        req = CompileRequest(query="hello")
        assert req.user_id == "anonymous"
        assert req.language == "auto"
        assert req.domain == "auto"

    def test_compile_request_validation(self):
        with pytest.raises(Exception):
            CompileRequest(query="")  # min_length=1

    def test_compile_response_structure(self):
        payload = OntologyPayload(raw_query="test")
        resp = CompileResponse(
            request_id="abc",
            payload=payload,
            fallback_used=False,
            processing_time_ms=50.0,
        )
        assert resp.request_id == "abc"
        assert resp.payload.raw_query == "test"
