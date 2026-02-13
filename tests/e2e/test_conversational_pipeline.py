"""
E2E Test: Conversational Pipeline
===================================
Tests the full LangGraph pipeline via the Graph API (/run endpoint).
Verifies: routing, intent detection, emotion, orthodoxy, vault, CAN output.

Requires: Graph API (localhost:9004) + all dependent services.
"""
import json

import pytest

pytestmark = [pytest.mark.e2e]


class TestConversationalGreeting:
    """Basic conversational inputs — greetings, simple questions."""

    def test_greeting_returns_valid_response(self, graph_run):
        """A simple greeting must return a parseable response with all OS fields."""
        data = graph_run("Ciao, come stai?")
        assert "human" in data
        assert "parsed" in data
        assert len(data["human"]) > 0

    def test_greeting_has_intent(self, graph_run):
        """Every graph response must include a detected intent."""
        parsed = graph_run("Buongiorno!")["parsed"]
        assert "intent" in parsed
        assert parsed["intent"] is not None

    def test_greeting_has_route(self, graph_run):
        """Every graph response must include the routing decision."""
        parsed = graph_run("Come va?")["parsed"]
        assert "route" in parsed
        assert isinstance(parsed["route"], str)
        assert len(parsed["route"]) > 0

    def test_greeting_has_emotion(self, graph_run):
        """Emotion detection must run on every input."""
        parsed = graph_run("Che bella giornata!")["parsed"]
        assert "emotion_detected" in parsed
        # emotion can be null/neutral but the field must exist


class TestSlotFiller:
    """Tests that ambiguous/incomplete inputs trigger slot-filling."""

    def test_vague_input_triggers_slot_filler(self, graph_run):
        """A vague analytical request should trigger slot-filling or conversational."""
        parsed = graph_run("Vorrei un'analisi")["parsed"]
        # Should go to slot_filler, clarify, or handle conversationally
        route = parsed.get("route", "")
        action = parsed.get("action", "")
        intent = parsed.get("intent", "")
        # Valid outcomes: slot_filler, clarify, or conversational handling
        assert (
            "slot_filler" in route
            or action == "clarify"
            or "needed_slots" in parsed
            or action == "conversation"
            or intent in ("soft", "unknown")
        ), f"Unexpected routing: route={route}, action={action}, intent={intent}"

    def test_slot_filler_lists_needed_slots(self, graph_run):
        """When slot-filling triggers, needed_slots should be populated."""
        parsed = graph_run("Analizza qualcosa per me")["parsed"]
        if parsed.get("action") == "clarify":
            assert "needed_slots" in parsed
            assert isinstance(parsed["needed_slots"], list)


class TestOrthodoxyBlessing:
    """Every graph output must pass through Orthodoxy validation."""

    def test_orthodoxy_verdict_present(self, graph_run):
        """orthodoxy_verdict must exist in every response."""
        parsed = graph_run("Dammi un consiglio")["parsed"]
        assert "orthodoxy_verdict" in parsed
        assert parsed["orthodoxy_verdict"] is not None

    def test_orthodoxy_has_confidence(self, graph_run):
        """Orthodoxy must report a confidence level."""
        parsed = graph_run("Cosa ne pensi?")["parsed"]
        assert "orthodoxy_confidence" in parsed
        confidence = parsed["orthodoxy_confidence"]
        assert isinstance(confidence, (int, float))
        assert 0 <= confidence <= 1.0

    def test_orthodoxy_has_timestamp(self, graph_run):
        """Orthodoxy validation must be timestamped."""
        parsed = graph_run("Verifica questa risposta")["parsed"]
        assert "orthodoxy_timestamp" in parsed


class TestVaultBlessing:
    """Every graph output must pass through Vault archival."""

    def test_vault_blessing_present(self, graph_run):
        """vault_blessing must exist in every response."""
        parsed = graph_run("Archivia questa conversazione")["parsed"]
        assert "vault_blessing" in parsed
        vault = parsed["vault_blessing"]
        assert isinstance(vault, dict)
        assert "vault_status" in vault


class TestCANOutput:
    """CAN (Contextual Adaptive Narrator) node output validation."""

    def test_can_mode_present(self, graph_run):
        """CAN must report its operating mode."""
        parsed = graph_run("Spiegami cosa sai fare")["parsed"]
        assert "can_mode" in parsed
        assert parsed["can_mode"] in ("conversational", "analytical", "executive", "exploratory")

    def test_can_route_present(self, graph_run):
        """CAN must report its internal route."""
        parsed = graph_run("Fammi un riassunto")["parsed"]
        assert "can_route" in parsed

    def test_can_response_structure(self, graph_run):
        """CAN response must have the expected structure."""
        parsed = graph_run("Come funziona il sistema?")["parsed"]
        can = parsed.get("can_response", {})
        assert isinstance(can, dict)
        # CAN response should have at minimum a mode and route
        if can:
            assert "mode" in can


class TestUserIdPropagation:
    """user_id must be respected and propagated."""

    def test_custom_user_id_propagated(self, graph_run):
        """A custom user_id must appear in the response."""
        parsed = graph_run("Test user id", user_id="e2e_custom_user_42")["parsed"]
        assert parsed.get("user_id") == "e2e_custom_user_42"


class TestLanguageDetection:
    """Multilingual input detection via Babel Gardens integration."""

    def test_italian_detected(self, graph_run):
        """Italian input should have language_detected field."""
        parsed = graph_run("Quanto costa il servizio?")["parsed"]
        assert "language_detected" in parsed

    def test_english_detected(self, graph_run):
        """English input should be processed correctly."""
        parsed = graph_run("What is the current status of the system?")["parsed"]
        assert "language_detected" in parsed
        # Response should still be valid regardless of language
        assert "intent" in parsed


class TestWeaverContextInPipeline:
    """Pattern Weavers context must be present in graph output."""

    def test_weaver_context_present(self, graph_run):
        """weaver_context must exist in every response."""
        parsed = graph_run("Analisi semantica avanzata")["parsed"]
        assert "weaver_context" in parsed
        ctx = parsed["weaver_context"]
        assert isinstance(ctx, dict)
        assert "status" in ctx

    def test_weaver_context_has_concepts(self, graph_run):
        """weaver_context must include concepts list."""
        parsed = graph_run("Valutazione del rischio operativo")["parsed"]
        ctx = parsed.get("weaver_context", {})
        assert "concepts" in ctx
        assert isinstance(ctx["concepts"], list)


class TestVSGSIntegration:
    """Semantic Grounding (VSGS) status in pipeline."""

    def test_vsgs_status_present(self, graph_run):
        """VSGS status must be reported."""
        parsed = graph_run("Cerca informazioni sul contesto")["parsed"]
        assert "vsgs_status" in parsed

    def test_vsgs_elapsed_tracked(self, graph_run):
        """VSGS must report processing time."""
        parsed = graph_run("Grounding semantico")["parsed"]
        if parsed.get("vsgs_status") == "enabled":
            assert "vsgs_elapsed_ms" in parsed
            assert isinstance(parsed["vsgs_elapsed_ms"], (int, float))


class TestResponseCompleteness:
    """Every response must contain all critical OS fields."""

    def test_execution_timestamp(self, graph_run):
        """execution_timestamp must be present in the outer response."""
        data = graph_run("Test completezza")
        assert "execution_timestamp" in data

    def test_audit_monitored_field(self, graph_run):
        """audit_monitored field must be present."""
        data = graph_run("Test audit")
        assert "audit_monitored" in data

    def test_explainability_present(self, graph_run):
        """Explainability breakdown must be present."""
        parsed = graph_run("Spiega il risultato")["parsed"]
        assert "explainability" in parsed
        expl = parsed["explainability"]
        assert isinstance(expl, dict)
        # Should have at least simple + technical levels
        assert "simple" in expl or "technical" in expl
