"""
Comprehension Engine — Unit Tests
==================================

Tests for:
- ComprehensionResult contract (schema enforcement, extra="forbid")
- ComprehensionConsumer (pure JSON parsing, fallback, degradation)
- SignalFusionConsumer (weighted, bayesian, L1 extraction)
- Signal registries (plugin + contributor registration)
- SignalEvidence / FusionResult contracts

> **Last updated**: Feb 26, 2026 14:00 UTC

Run: pytest tests/test_comprehension_engine.py -v
"""

import json
import math
import pytest
import sys
from pathlib import Path

# Ensure vitruvyan_core is importable
_root = Path(__file__).resolve().parents[1] / "vitruvyan_core"
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from vitruvyan_core.contracts.comprehension import (
    ComprehendRequest,
    ComprehendResponse,
    ComprehensionResult,
    EmotionPayload,
    FuseRequest,
    FuseResponse,
    FusionContributor,
    FusionResult,
    FusionStrategy,
    IComprehensionPlugin,
    ISignalContributor,
    LinguisticPayload,
    SemanticPayload,
    SentimentPayload,
    SignalEvidence,
)
from vitruvyan_core.contracts.pattern_weavers import (
    DomainGate,
    GateVerdict,
    OntologyEntity,
    OntologyPayload,
)
from vitruvyan_core.core.cognitive.babel_gardens.consumers.comprehension_consumer import (
    ComprehensionConsumer,
)
from vitruvyan_core.core.cognitive.babel_gardens.consumers.signal_fusion_consumer import (
    SignalFusionConsumer,
)
from vitruvyan_core.core.cognitive.babel_gardens.governance.signal_registry import (
    ComprehensionPluginRegistry,
    GenericComprehensionPlugin,
    SignalContributorRegistry,
    get_comprehension_registry,
    get_signal_contributor_registry,
)


# ═════════════════════════════════════════════════════════════
# 1. Contract Tests — Pydantic Schema Enforcement
# ═════════════════════════════════════════════════════════════


class TestSentimentPayload:
    def test_default(self):
        s = SentimentPayload()
        assert s.label == "neutral"
        assert s.score == 0.0
        assert s.confidence == 0.5
        assert s.magnitude == 0.0
        assert s.aspects == []

    def test_full(self):
        s = SentimentPayload(
            label="negative",
            score=-0.7,
            confidence=0.9,
            magnitude=0.8,
            aspects=[{"aspect": "risk", "sentiment": "negative", "score": -0.8}],
            reasoning="Expressed concern about risk",
        )
        assert s.label == "negative"
        assert s.score == -0.7

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            SentimentPayload(label="positive", hallucinated_field="oops")

    def test_score_bounds(self):
        with pytest.raises(Exception):
            SentimentPayload(score=2.0)
        with pytest.raises(Exception):
            SentimentPayload(score=-1.5)


class TestEmotionPayload:
    def test_default(self):
        e = EmotionPayload()
        assert e.primary == "neutral"
        assert e.secondary == []
        assert e.intensity == 0.0

    def test_full(self):
        e = EmotionPayload(
            primary="frustrated",
            secondary=["anxious"],
            intensity=0.8,
            confidence=0.9,
            cultural_context="Italian expressiveness",
            reasoning="Multiple exclamation marks + negative keywords",
        )
        assert e.primary == "frustrated"

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            EmotionPayload(primary="happy", fake_field=True)


class TestLinguisticPayload:
    def test_default(self):
        lp = LinguisticPayload()
        assert lp.text_register == "neutral"
        assert lp.irony_detected is False
        assert lp.ambiguity_score == 0.0
        assert lp.code_switching is False

    def test_irony(self):
        lp = LinguisticPayload(irony_detected=True, text_register="colloquial")
        assert lp.irony_detected is True


class TestSemanticPayload:
    def test_default(self):
        sp = SemanticPayload()
        assert sp.sentiment.label == "neutral"
        assert sp.emotion.primary == "neutral"
        assert sp.linguistic.text_register == "neutral"

    def test_nested(self):
        sp = SemanticPayload(
            sentiment=SentimentPayload(label="positive", score=0.5),
            emotion=EmotionPayload(primary="excited"),
            linguistic=LinguisticPayload(text_register="informal"),
        )
        assert sp.sentiment.score == 0.5


class TestComprehensionResult:
    def test_default(self):
        cr = ComprehensionResult(raw_query="hello")
        assert cr.schema_version == "1.0.0"
        assert cr.ontology.gate.verdict == GateVerdict.AMBIGUOUS
        assert cr.semantics.sentiment.label == "neutral"
        assert cr.raw_query == "hello"

    def test_full(self):
        cr = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(
                    verdict=GateVerdict.IN_DOMAIN,
                    domain="finance",
                    confidence=0.95,
                ),
                entities=[
                    OntologyEntity(raw="AAPL", canonical="Apple Inc.", entity_type="ticker"),
                ],
                intent_hint="analysis",
                topics=["equity"],
                raw_query="analyze AAPL",
            ),
            semantics=SemanticPayload(
                sentiment=SentimentPayload(label="neutral", score=0.0),
                emotion=EmotionPayload(primary="curious"),
            ),
            raw_query="analyze AAPL",
            language="en",
        )
        assert cr.ontology.gate.domain == "finance"
        assert len(cr.ontology.entities) == 1
        assert cr.semantics.emotion.primary == "curious"

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            ComprehensionResult(raw_query="hi", hallucinated="nope")

    def test_ontology_reuses_pw_v3(self):
        """OntologyPayload in ComprehensionResult is the exact PW v3 contract."""
        cr = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(verdict=GateVerdict.IN_DOMAIN, domain="security"),
                entities=[
                    OntologyEntity(raw="CVE-2024-1234", canonical="CVE-2024-1234", entity_type="vulnerability"),
                ],
                intent_hint="threat_analysis",
                topics=["cybersecurity", "patch_management"],
                raw_query="check CVE-2024-1234",
            ),
            raw_query="check CVE-2024-1234",
        )
        assert cr.ontology.gate.domain == "security"
        assert cr.ontology.entities[0].entity_type == "vulnerability"


class TestSignalEvidence:
    def test_basic(self):
        se = SignalEvidence(
            signal_name="finbert_sentiment",
            value=-0.73,
            confidence=0.88,
            source="finbert",
            method="transformer_inference",
        )
        assert se.signal_name == "finbert_sentiment"
        assert se.value == -0.73

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            SignalEvidence(signal_name="x", value=0.0, oops=True)


class TestFusionResult:
    def test_basic(self):
        fr = FusionResult(
            signal_name="sentiment",
            fused_value=-0.4,
            fused_label="negative",
            fused_confidence=0.8,
        )
        assert fr.signal_name == "sentiment"
        assert fr.strategy_used == FusionStrategy.WEIGHTED


class TestHTTPContracts:
    def test_comprehend_request(self):
        req = ComprehendRequest(query="what is risk?")
        assert req.user_id == "anonymous"
        assert req.domain == "auto"

    def test_fuse_request(self):
        cr = ComprehensionResult(raw_query="test")
        req = FuseRequest(comprehension=cr)
        assert req.strategy == FusionStrategy.WEIGHTED


# ═════════════════════════════════════════════════════════════
# 2. ComprehensionConsumer Tests (LIVELLO 1 — Pure)
# ═════════════════════════════════════════════════════════════


class TestComprehensionConsumer:

    def _make_consumer(self):
        return ComprehensionConsumer(config=None)

    def test_parse_valid_full_response(self):
        """Parse complete LLM JSON into ComprehensionResult."""
        consumer = self._make_consumer()

        llm_output = {
            "ontology": {
                "gate": {
                    "verdict": "in_domain",
                    "domain": "generic",
                    "confidence": 0.9,
                    "reasoning": "Clear topic",
                },
                "entities": [
                    {"raw": "Python", "canonical": "Python", "entity_type": "concept", "confidence": 0.95}
                ],
                "intent_hint": "question",
                "topics": ["programming"],
                "sentiment_hint": "neutral",
                "temporal_context": "real_time",
                "language": "en",
                "complexity": "simple",
            },
            "semantics": {
                "sentiment": {
                    "label": "neutral",
                    "score": 0.1,
                    "confidence": 0.85,
                    "magnitude": 0.2,
                    "aspects": [],
                    "reasoning": "Factual question",
                },
                "emotion": {
                    "primary": "curious",
                    "secondary": [],
                    "intensity": 0.6,
                    "confidence": 0.8,
                    "cultural_context": "neutral",
                    "reasoning": "Question implies curiosity",
                },
                "linguistic": {
                    "text_register": "neutral",
                    "irony_detected": False,
                    "ambiguity_score": 0.1,
                    "code_switching": False,
                },
            },
        }

        result = consumer.process({
            "llm_response": llm_output,
            "raw_query": "What is Python?",
            "domain": "generic",
        })

        assert result.success is True
        cr = ComprehensionResult.model_validate(result.data["result"])
        assert cr.ontology.gate.verdict == GateVerdict.IN_DOMAIN
        assert len(cr.ontology.entities) == 1
        assert cr.ontology.entities[0].raw == "Python"
        assert cr.semantics.sentiment.label == "neutral"
        assert cr.semantics.emotion.primary == "curious"
        assert cr.raw_query == "What is Python?"

    def test_parse_json_string(self):
        """Parse LLM output as JSON string."""
        consumer = self._make_consumer()

        llm_json = json.dumps({
            "ontology": {"gate": {"verdict": "ambiguous", "domain": "generic", "confidence": 0.5, "reasoning": ""}},
            "semantics": {
                "sentiment": {"label": "neutral", "score": 0.0, "confidence": 0.5, "magnitude": 0.0, "aspects": [], "reasoning": ""},
                "emotion": {"primary": "neutral", "secondary": [], "intensity": 0.0, "confidence": 0.5, "cultural_context": "neutral", "reasoning": ""},
                "linguistic": {"text_register": "neutral", "irony_detected": False, "ambiguity_score": 0.0, "code_switching": False},
            },
        })

        result = consumer.process({
            "llm_response": llm_json,
            "raw_query": "ciao",
        })

        assert result.success is True
        cr = ComprehensionResult.model_validate(result.data["result"])
        assert cr.raw_query == "ciao"

    def test_fallback_on_invalid_json(self):
        """Unparseable JSON triggers fallback (still returns valid result)."""
        consumer = self._make_consumer()

        result = consumer.process({
            "llm_response": "this is not json at all",
            "raw_query": "test query",
        })

        assert result.success is True  # Degraded but valid
        cr = ComprehensionResult.model_validate(result.data["result"])
        assert cr.ontology.gate.verdict == GateVerdict.AMBIGUOUS
        assert cr.ontology.gate.confidence == 0.0
        assert cr.raw_query == "test query"
        assert len(result.data["parse_errors"]) > 0

    def test_missing_semantics_section(self):
        """Missing semantics → defaults, with warning."""
        consumer = self._make_consumer()

        result = consumer.process({
            "llm_response": {
                "ontology": {
                    "gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.8, "reasoning": "ok"},
                    "intent_hint": "question",
                    "topics": ["test"],
                    "sentiment_hint": "neutral",
                    "temporal_context": "real_time",
                    "language": "en",
                    "complexity": "simple",
                },
            },
            "raw_query": "test",
        })

        assert result.success is True
        cr = ComprehensionResult.model_validate(result.data["result"])
        assert cr.semantics.sentiment.label == "neutral"  # Default
        assert cr.semantics.emotion.primary == "neutral"   # Default

    def test_missing_required_fields(self):
        """Missing raw_query → validation error."""
        consumer = self._make_consumer()
        result = consumer.process({"llm_response": "{}"})
        assert result.success is False
        assert any("raw_query" in e for e in result.errors)

    def test_json_in_code_fences(self):
        """Extract JSON from markdown code fences."""
        consumer = self._make_consumer()

        fenced = '```json\n{"ontology":{}, "semantics":{}}\n```'
        result = consumer.process({
            "llm_response": fenced,
            "raw_query": "test",
        })

        assert result.success is True

    def test_domain_injection(self):
        """Domain name injected into gate if generic but domain specified."""
        consumer = self._make_consumer()

        result = consumer.process({
            "llm_response": {
                "ontology": {
                    "gate": {"verdict": "in_domain", "domain": "generic", "confidence": 0.9, "reasoning": "ok"},
                    "intent_hint": "question",
                    "topics": [],
                    "sentiment_hint": "neutral",
                    "temporal_context": "real_time",
                    "language": "en",
                    "complexity": "simple",
                },
                "semantics": {
                    "sentiment": {"label": "neutral", "score": 0.0, "confidence": 0.5, "magnitude": 0.0, "aspects": [], "reasoning": ""},
                    "emotion": {"primary": "neutral", "secondary": [], "intensity": 0.0, "confidence": 0.5, "cultural_context": "neutral", "reasoning": ""},
                    "linguistic": {"text_register": "neutral", "irony_detected": False, "ambiguity_score": 0.0, "code_switching": False},
                },
            },
            "raw_query": "analyze AAPL",
            "domain": "finance",
        })

        assert result.success is True
        cr = ComprehensionResult.model_validate(result.data["result"])
        assert cr.ontology.gate.domain == "finance"


# ═════════════════════════════════════════════════════════════
# 3. SignalFusionConsumer Tests (LIVELLO 1 — Pure)
# ═════════════════════════════════════════════════════════════


class TestSignalFusionConsumer:

    def _make_consumer(self):
        return SignalFusionConsumer(config=None)

    def _make_comprehension(self, sentiment_score=0.0, emotion="neutral"):
        return ComprehensionResult(
            semantics=SemanticPayload(
                sentiment=SentimentPayload(label="neutral" if sentiment_score == 0 else "positive", score=sentiment_score, confidence=0.85),
                emotion=EmotionPayload(primary=emotion, intensity=0.7, confidence=0.8),
            ),
            raw_query="test",
        ).model_dump()

    def test_weighted_fusion_single_evidence(self):
        """Single evidence → fused value equals evidence value."""
        consumer = self._make_consumer()
        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=0.0),
            "evidences": [
                SignalEvidence(
                    signal_name="sentiment",
                    value=-0.5,
                    confidence=0.9,
                    source="finbert",
                    method="transformer",
                ).model_dump(),
            ],
            "strategy": "weighted",
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        assert len(fusions) >= 1
        # Find sentiment fusion
        sent = next(f for f in fusions if f.signal_name == "sentiment")
        assert sent.fused_value < 0  # Negative

    def test_weighted_fusion_multiple_evidences(self):
        """Multiple evidences with different confidences → weighted average."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=0.3),
            "evidences": [
                SignalEvidence(
                    signal_name="sentiment",
                    value=-0.8,
                    confidence=0.95,
                    source="finbert",
                    method="transformer",
                ).model_dump(),
            ],
            "strategy": "weighted",
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sent = next(f for f in fusions if f.signal_name == "sentiment")
        # LLM says +0.3 (conf 0.85), FinBERT says -0.8 (conf 0.95)
        # FinBERT has higher confidence → should pull toward negative
        assert sent.fused_value < 0.3
        assert len(sent.contributors) == 2

    def test_bayesian_fusion(self):
        """Bayesian strategy produces valid fusion."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=-0.5),
            "evidences": [
                SignalEvidence(
                    signal_name="sentiment",
                    value=-0.6,
                    confidence=0.9,
                    source="finbert",
                    method="transformer",
                ).model_dump(),
            ],
            "strategy": "bayesian",
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sent = next(f for f in fusions if f.signal_name == "sentiment")
        assert sent.strategy_used == FusionStrategy.BAYESIAN
        assert sent.fused_value < 0  # Both agree on negative

    def test_l1_signal_extraction_from_emotion(self):
        """Emotion from Layer 1 is extracted as evidence."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(
                sentiment_score=0.0, emotion="frustrated"
            ),
            "evidences": [],
            "strategy": "weighted",
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        # Should have emotion fusion with negative value (frustrated = negative)
        emo = next((f for f in fusions if f.signal_name == "emotion"), None)
        assert emo is not None
        assert emo.fused_value < 0  # Frustrated → negative

    def test_llm_arbitrated_deferred(self):
        """LLM_ARBITRATED strategy marks as pending (pure consumer can't call LLM)."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=0.5),
            "evidences": [
                SignalEvidence(
                    signal_name="sentiment",
                    value=-0.5,
                    confidence=0.9,
                    source="finbert",
                    method="transformer",
                ).model_dump(),
            ],
            "strategy": "llm_arbitrated",
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sent = next(f for f in fusions if f.signal_name == "sentiment")
        assert sent.strategy_used == FusionStrategy.LLM_ARBITRATED
        assert sent.fused_label == "pending_arbitration"

    def test_weight_overrides(self):
        """Per-source weight overrides affect fusion."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=0.5),
            "evidences": [
                SignalEvidence(
                    signal_name="sentiment",
                    value=-0.8,
                    confidence=0.9,
                    source="finbert",
                    method="transformer",
                ).model_dump(),
            ],
            "strategy": "weighted",
            "weights": {"finbert": 0.1},  # Heavily downweight FinBERT
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        sent = next(f for f in fusions if f.signal_name == "sentiment")
        # LLM at normal weight, FinBERT at 0.1 → should be closer to LLM's 0.5
        assert sent.fused_value > 0

    def test_empty_evidences(self):
        """No external evidences → only L1 signals."""
        consumer = self._make_consumer()

        result = consumer.process({
            "comprehension": self._make_comprehension(sentiment_score=0.7),
            "evidences": [],
        })

        assert result.success is True
        fusions = [FusionResult.model_validate(r) for r in result.data["results"]]
        assert len(fusions) >= 1  # At least L1 sentiment if non-zero


# ═════════════════════════════════════════════════════════════
# 4. Registry Tests
# ═════════════════════════════════════════════════════════════


class TestComprehensionPluginRegistry:

    def test_generic_always_registered(self):
        registry = ComprehensionPluginRegistry()
        assert registry.has_domain("generic")
        plugin = registry.get("generic")
        assert plugin.get_domain_name() == "generic"

    def test_auto_resolves_to_generic(self):
        registry = ComprehensionPluginRegistry()
        plugin = registry.resolve("auto")
        assert plugin.get_domain_name() == "generic"

    def test_register_custom_domain(self):
        registry = ComprehensionPluginRegistry()

        class TestPlugin(IComprehensionPlugin):
            def get_domain_name(self): return "test_domain"
            def get_ontology_prompt_section(self): return "test ontology"
            def get_semantics_prompt_section(self): return "test semantics"
            def get_entity_types(self): return ["test_entity"]

        registry.register(TestPlugin())
        assert registry.has_domain("test_domain")
        plugin = registry.resolve("test_domain")
        assert plugin.get_entity_types() == ["test_entity"]

    def test_unknown_domain_falls_back_to_generic(self):
        registry = ComprehensionPluginRegistry()
        plugin = registry.resolve("nonexistent")
        assert plugin.get_domain_name() == "generic"

    def test_registered_domains(self):
        registry = ComprehensionPluginRegistry()
        assert "generic" in registry.registered_domains


class TestSignalContributorRegistry:

    def test_empty_by_default(self):
        registry = SignalContributorRegistry()
        assert registry.registered_names == []
        assert registry.get_all() == []

    def test_register_and_get(self):
        registry = SignalContributorRegistry()

        class DummyContributor(ISignalContributor):
            def get_contributor_name(self): return "dummy"
            def get_signal_names(self): return ["dummy_signal"]
            def contribute(self, text, context=None):
                return [SignalEvidence(signal_name="dummy_signal", value=0.5, confidence=0.8, source="dummy")]

        registry.register(DummyContributor())
        assert registry.has_contributor("dummy")
        assert len(registry.get_all()) == 1
        assert len(registry.get_available()) == 1

    def test_unavailable_contributor_filtered(self):
        registry = SignalContributorRegistry()

        class UnavailableContributor(ISignalContributor):
            def get_contributor_name(self): return "offline"
            def get_signal_names(self): return ["x"]
            def contribute(self, text, context=None): return []
            def is_available(self): return False

        registry.register(UnavailableContributor())
        assert len(registry.get_all()) == 1
        assert len(registry.get_available()) == 0


class TestGenericComprehensionPlugin:
    def test_domain_name(self):
        p = GenericComprehensionPlugin()
        assert p.get_domain_name() == "generic"

    def test_prompt_sections(self):
        p = GenericComprehensionPlugin()
        assert "ontology" in p.get_ontology_prompt_section().lower()
        assert "semantics" in p.get_semantics_prompt_section().lower()

    def test_validate_result_passthrough(self):
        p = GenericComprehensionPlugin()
        cr = ComprehensionResult(raw_query="test")
        assert p.validate_result(cr) is cr


# ═════════════════════════════════════════════════════════════
# 5. Cross-domain scenario: Security + Finance
# ═════════════════════════════════════════════════════════════


class TestCrossDomainScenarios:
    """Verify contracts work across different domains."""

    def test_security_domain(self):
        cr = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(verdict=GateVerdict.IN_DOMAIN, domain="security", confidence=0.93),
                entities=[
                    OntologyEntity(raw="CVE-2024-1234", canonical="CVE-2024-1234", entity_type="vulnerability"),
                    OntologyEntity(raw="Apache", canonical="Apache HTTP Server", entity_type="software"),
                ],
                intent_hint="threat_analysis",
                topics=["vulnerability", "patch_management"],
                raw_query="analyze CVE-2024-1234 impact on Apache",
            ),
            semantics=SemanticPayload(
                sentiment=SentimentPayload(label="negative", score=-0.6, confidence=0.85),
                emotion=EmotionPayload(primary="anxious", intensity=0.7),
            ),
            raw_query="analyze CVE-2024-1234 impact on Apache",
        )

        assert cr.ontology.gate.domain == "security"
        assert cr.semantics.sentiment.label == "negative"
        d = cr.model_dump()
        assert d["ontology"]["entities"][0]["entity_type"] == "vulnerability"

    def test_healthcare_domain(self):
        cr = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(verdict=GateVerdict.IN_DOMAIN, domain="healthcare"),
                entities=[
                    OntologyEntity(raw="diabetes type 2", canonical="T2DM", entity_type="condition"),
                ],
                intent_hint="question",
                raw_query="latest treatment for diabetes type 2",
            ),
            semantics=SemanticPayload(
                emotion=EmotionPayload(primary="curious"),
            ),
            raw_query="latest treatment for diabetes type 2",
        )

        assert cr.ontology.entities[0].entity_type == "condition"



# ═════════════════════════════════════════════════════════════
# 6. Serialization round-trip
# ═════════════════════════════════════════════════════════════


class TestSerialization:

    def test_comprehension_result_roundtrip(self):
        orig = ComprehensionResult(
            ontology=OntologyPayload(
                gate=DomainGate(verdict=GateVerdict.IN_DOMAIN, domain="generic", confidence=0.88),
                entities=[OntologyEntity(raw="Python", canonical="Python", entity_type="concept")],
                intent_hint="question",
                topics=["programming"],
                raw_query="what is Python?",
            ),
            semantics=SemanticPayload(
                sentiment=SentimentPayload(label="neutral", score=0.1, confidence=0.8, magnitude=0.2),
                emotion=EmotionPayload(primary="curious", intensity=0.6, confidence=0.75),
                linguistic=LinguisticPayload(text_register="neutral"),
            ),
            raw_query="what is Python?",
            language="en",
        )

        d = orig.model_dump()
        j = json.dumps(d)
        restored = ComprehensionResult.model_validate(json.loads(j))

        assert restored.ontology.gate.verdict == GateVerdict.IN_DOMAIN
        assert restored.semantics.emotion.primary == "curious"
        assert restored.raw_query == "what is Python?"

    def test_fusion_result_roundtrip(self):
        orig = FusionResult(
            signal_name="sentiment",
            fused_value=-0.45,
            fused_label="negative",
            fused_confidence=0.82,
            strategy_used=FusionStrategy.WEIGHTED,
            contributors=[
                FusionContributor(
                    evidence=SignalEvidence(signal_name="sentiment", value=0.3, confidence=0.85, source="llm"),
                    applied_weight=0.85,
                ),
                FusionContributor(
                    evidence=SignalEvidence(signal_name="sentiment", value=-0.8, confidence=0.95, source="finbert"),
                    applied_weight=0.95,
                ),
            ],
            reasoning="Weighted fusion of 2 signals",
        )

        d = orig.model_dump()
        restored = FusionResult.model_validate(d)
        assert len(restored.contributors) == 2
        assert restored.strategy_used == FusionStrategy.WEIGHTED
