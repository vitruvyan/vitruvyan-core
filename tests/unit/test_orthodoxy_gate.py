"""
Unit Tests — Orthodoxy Gate (informativo)
==========================================

Tests for the rewritten orthodoxy_node that runs an in-process tribunal
(Confessor → Inquisitor → VerdictEngine) instead of fire-and-forget.

Tests cover:
- _build_examination_text() concatenation logic
- _run_tribunal() produces real Verdict objects
- _apply_verdict_to_state() writes correct state fields
- _apply_fallback() for error scenarios
- orthodoxy_node() end-to-end (mocked bus)
- Various verdict states: blessed, heretical, purified

Created: Mar 07, 2026
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'vitruvyan_core'))


# ---------------------------------------------------------------------------
# Test _build_examination_text
# ---------------------------------------------------------------------------

class TestBuildExaminationText:
    """Tests for text assembly before Inquisitor examination."""

    def _build(self, state):
        from core.orchestration.langgraph.node.orthodoxy_node import _build_examination_text
        return _build_examination_text(state)

    def test_empty_state(self):
        assert self._build({}) == ""

    def test_response_only(self):
        text = self._build({"response": "Hello world"})
        assert text == "Hello world"

    def test_response_and_narrative(self):
        text = self._build({"response": "resp", "narrative": "narr"})
        assert "resp" in text
        assert "narr" in text
        assert "\n---\n" in text

    def test_same_response_and_narrative_deduplicates(self):
        text = self._build({"response": "same", "narrative": "same"})
        # narrative == response, so narrative is excluded
        assert text == "same"

    def test_all_parts(self):
        text = self._build({
            "response": "AI response",
            "narrative": "Story narrative",
            "input_text": "User question",
        })
        assert "AI response" in text
        assert "Story narrative" in text
        assert "User question" in text

    def test_response_truncated_at_2000(self):
        long_resp = "x" * 5000
        text = self._build({"response": long_resp})
        assert len(text) == 2000

    def test_narrative_truncated_at_1000(self):
        text = self._build({
            "response": "r",
            "narrative": "n" * 3000,
        })
        # narrative part should be 1000 chars max
        parts = text.split("\n---\n")
        assert len(parts) == 2
        assert len(parts[1]) == 1000

    def test_input_text_truncated_at_500(self):
        text = self._build({"input_text": "q" * 1000})
        assert len(text) == 500


# ---------------------------------------------------------------------------
# Test _run_tribunal (integration with LIVELLO 1 consumers)
# ---------------------------------------------------------------------------

class TestRunTribunal:
    """Tests that the tribunal pipeline produces real Verdict objects."""

    def _run(self, state):
        from core.orchestration.langgraph.node.orthodoxy_node import _run_tribunal
        return _run_tribunal(state)

    def test_clean_text_returns_blessed(self):
        state = {
            "response": "The current analysis shows stable performance metrics.",
            "trace_id": "test-trace-001",
        }
        verdict = self._run(state)
        assert verdict.status == "blessed"
        assert verdict.confidence > 0.5
        assert verdict.should_send is True
        assert verdict.ruleset_version is not None

    def test_security_violation_returns_heretical_or_purified(self):
        # Inject text that triggers security regex (quoted secrets patterns)
        state = {
            "response": 'password = "admin123" and api_key = "sk-live-abc123"',
            "trace_id": "test-trace-002",
        }
        verdict = self._run(state)
        # Should trigger security findings
        assert len(verdict.findings) > 0
        assert verdict.status in ("heretical", "purified")

    def test_empty_state_returns_blessed(self):
        verdict = self._run({})
        assert verdict.status == "blessed"
        assert len(verdict.findings) == 0

    def test_verdict_has_explanation(self):
        state = {"response": "Normal output with no issues."}
        verdict = self._run(state)
        assert isinstance(verdict.explanation, str)
        assert len(verdict.explanation) > 0


# ---------------------------------------------------------------------------
# Test _apply_verdict_to_state
# ---------------------------------------------------------------------------

class TestApplyVerdictToState:
    """Tests that verdict metadata is correctly written to state."""

    def _apply(self, state, verdict):
        from core.orchestration.langgraph.node.orthodoxy_node import _apply_verdict_to_state
        import time
        return _apply_verdict_to_state(state, verdict, time.time())

    def _make_verdict(self, status="blessed", findings=(), confidence=0.95,
                      ruleset_version="v1.0_test", **kwargs):
        from core.governance.orthodoxy_wardens.domain.verdict import Verdict
        if status == "blessed":
            return Verdict.blessed(
                findings=findings,
                confidence=confidence,
                ruleset_version=ruleset_version,
            )
        elif status == "non_liquet":
            return Verdict.non_liquet(
                findings=findings,
                confidence=confidence,
                ruleset_version=ruleset_version,
                what_we_know=kwargs.get("what_we_know", ("fact1",)),
                what_is_uncertain=kwargs.get("what_is_uncertain", ("uncertain1",)),
                uncertainty_sources=kwargs.get("uncertainty_sources", ("source1",)),
                best_guess=kwargs.get("best_guess", "probably ok"),
            )
        else:
            return Verdict.heretical(
                findings=findings,
                explanation="Test heretical verdict",
                confidence=confidence,
                ruleset_version=ruleset_version,
            )

    def test_blessed_verdict_sets_state_keys(self):
        state = {}
        verdict = self._make_verdict("blessed")
        result = self._apply(state, verdict)

        assert result["orthodoxy_verdict"] == "blessed"
        assert result["orthodoxy_findings"] == 0
        assert result["orthodoxy_confidence"] == 0.95
        assert result["orthodoxy_should_send"] is True
        assert result["orthodoxy_status"] == "blessed"
        assert "orthodoxy_timestamp" in result
        assert "orthodoxy_duration_ms" in result
        assert result["orthodoxy_ruleset_version"] == "v1.0_test"

    def test_theological_metadata_present(self):
        state = {}
        verdict = self._make_verdict("blessed")
        result = self._apply(state, verdict)

        meta = result["theological_metadata"]
        assert meta["sacred_order"] == "orthodoxy_wardens"
        assert meta["gate_level"] == "informativo"
        assert meta["verdict_real"] is True
        assert meta["divine_oversight"] is True

    def test_non_liquet_adds_epistemic_fields(self):
        state = {}
        verdict = self._make_verdict(
            "non_liquet",
            what_we_know=("the input was valid",),
            what_is_uncertain=("output accuracy",),
        )
        result = self._apply(state, verdict)

        assert result["orthodoxy_verdict"] == "non_liquet"
        assert result["orthodoxy_what_we_know"] is not None
        assert result["orthodoxy_what_is_uncertain"] is not None

    def test_heretical_verdict(self):
        state = {}
        verdict = self._make_verdict("heretical", confidence=0.1)
        result = self._apply(state, verdict)
        assert result["orthodoxy_verdict"] == "heretical"
        assert result["orthodoxy_confidence"] == 0.1

    def test_existing_state_preserved(self):
        state = {"response": "Some AI output", "trace_id": "abc"}
        verdict = self._make_verdict("blessed")
        result = self._apply(state, verdict)
        # Original keys must survive
        assert result["response"] == "Some AI output"
        assert result["trace_id"] == "abc"


# ---------------------------------------------------------------------------
# Test _apply_fallback
# ---------------------------------------------------------------------------

class TestApplyFallback:
    """Tests for the emergency fallback when tribunal itself fails."""

    def _fallback(self, state, reason):
        from core.orchestration.langgraph.node.orthodoxy_node import _apply_fallback
        return _apply_fallback(state, reason)

    def test_fallback_sets_correct_status(self):
        result = self._fallback({}, "import error")
        assert result["orthodoxy_verdict"] == "fallback"
        assert result["orthodoxy_status"] == "fallback"
        assert result["orthodoxy_should_send"] is True
        assert result["orthodoxy_confidence"] == 0.0

    def test_fallback_includes_reason(self):
        result = self._fallback({}, "module not found")
        assert "module not found" in result["orthodoxy_explanation"]
        assert result["orthodoxy_fallback_reason"] == "module not found"

    def test_fallback_metadata_no_oversight(self):
        result = self._fallback({}, "crash")
        meta = result["theological_metadata"]
        assert meta["divine_oversight"] is False
        assert meta["gate_level"] == "fallback"

    def test_fallback_preserves_existing_state(self):
        state = {"response": "output", "user_id": "user1"}
        result = self._fallback(state, "error")
        assert result["response"] == "output"
        assert result["user_id"] == "user1"


# ---------------------------------------------------------------------------
# Test orthodoxy_node end-to-end
# ---------------------------------------------------------------------------

class TestOrthodoxyNodeEndToEnd:
    """End-to-end test of the orthodoxy_node function."""

    @patch("core.orchestration.langgraph.node.orthodoxy_node.get_stream_bus")
    def test_clean_input_blessed(self, mock_bus):
        mock_bus.return_value = MagicMock()
        from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node

        state = {
            "response": "Market analysis indicates moderate growth.",
            "user_id": "test_user",
            "trace_id": "test-e2e-001",
        }
        result = orthodoxy_node(state)

        assert result["orthodoxy_verdict"] == "blessed"
        assert result["orthodoxy_should_send"] is True
        assert result["theological_metadata"]["verdict_real"] is True

    @patch("core.orchestration.langgraph.node.orthodoxy_node.get_stream_bus")
    def test_bus_emit_called(self, mock_bus):
        bus_instance = MagicMock()
        mock_bus.return_value = bus_instance
        from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node

        state = {
            "response": "Test output",
            "user_id": "user_audit",
            "trace_id": "audit-001",
        }
        orthodoxy_node(state)

        # Audit emit should have been called
        bus_instance.emit.assert_called_once()
        call_kwargs = bus_instance.emit.call_args
        assert call_kwargs.kwargs["channel"] == "orthodoxy.audit.requested"

    @patch("core.orchestration.langgraph.node.orthodoxy_node.get_stream_bus")
    def test_bus_failure_does_not_crash(self, mock_bus):
        bus_instance = MagicMock()
        bus_instance.emit.side_effect = ConnectionError("Redis down")
        mock_bus.return_value = bus_instance
        from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node

        state = {
            "response": "Normal output",
            "user_id": "user_bus_fail",
        }
        # Should not raise — bus failure is non-fatal
        result = orthodoxy_node(state)
        assert result["orthodoxy_verdict"] == "blessed"

    @patch("core.orchestration.langgraph.node.orthodoxy_node._run_tribunal")
    @patch("core.orchestration.langgraph.node.orthodoxy_node.get_stream_bus")
    def test_tribunal_exception_triggers_fallback(self, mock_bus, mock_tribunal):
        mock_bus.return_value = MagicMock()
        mock_tribunal.side_effect = RuntimeError("Inquisitor crashed")
        from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node

        state = {"response": "Test", "user_id": "fallback_user"}
        result = orthodoxy_node(state)

        assert result["orthodoxy_verdict"] == "fallback"
        assert "Inquisitor crashed" in result["orthodoxy_explanation"]


# ---------------------------------------------------------------------------
# Test channel registry
# ---------------------------------------------------------------------------

class TestPlasticityChannelRegistry:
    """Verify plasticity channels are registered."""

    def test_feedback_channel_registered(self):
        from core.synaptic_conclave.channels.channel_registry import (
            CHANNEL_REGISTRY, validate_channel
        )
        assert "plasticity.feedback.received" in CHANNEL_REGISTRY
        assert validate_channel("plasticity.feedback.received") is True

    def test_outcome_channel_registered(self):
        from core.synaptic_conclave.channels.channel_registry import (
            CHANNEL_REGISTRY, validate_channel
        )
        assert "plasticity.outcome.recorded" in CHANNEL_REGISTRY
        assert validate_channel("plasticity.outcome.recorded") is True

    def test_feedback_channel_contract(self):
        from core.synaptic_conclave.channels.channel_registry import CHANNEL_REGISTRY
        contract = CHANNEL_REGISTRY["plasticity.feedback.received"]
        assert contract.producer == "api_graph"
        assert "plasticity" in contract.consumers
        assert contract.direction == "event"

    def test_outcome_channel_contract(self):
        from core.synaptic_conclave.channels.channel_registry import CHANNEL_REGISTRY
        contract = CHANNEL_REGISTRY["plasticity.outcome.recorded"]
        assert contract.producer == "plasticity"
        assert "orthodoxy_wardens" in contract.consumers


# ---------------------------------------------------------------------------
# Test FeedbackSignalSchema validation
# ---------------------------------------------------------------------------

class TestFeedbackSignalSchema:
    """Tests for the Pydantic feedback schema."""

    def test_valid_positive_feedback(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'services', 'api_graph'))
        from models.schemas import FeedbackSignalSchema

        signal = FeedbackSignalSchema(
            message_id="msg-001",
            trace_id="trace-001",
            feedback="positive",
            timestamp="2026-03-07T12:00:00Z",
        )
        assert signal.feedback == "positive"
        assert signal.message_id == "msg-001"

    def test_valid_negative_feedback(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'services', 'api_graph'))
        from models.schemas import FeedbackSignalSchema

        signal = FeedbackSignalSchema(
            message_id="msg-002",
            feedback="negative",
            comment="Response was inaccurate",
            timestamp="2026-03-07T12:00:00Z",
        )
        assert signal.feedback == "negative"
        assert signal.comment == "Response was inaccurate"

    def test_invalid_feedback_value_rejected(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'services', 'api_graph'))
        from models.schemas import FeedbackSignalSchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FeedbackSignalSchema(
                message_id="msg-003",
                feedback="neutral",  # Invalid — must be positive|negative
                timestamp="2026-03-07T12:00:00Z",
            )

    def test_optional_fields(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'services', 'api_graph'))
        from models.schemas import FeedbackSignalSchema

        signal = FeedbackSignalSchema(
            message_id="msg-004",
            feedback="positive",
            timestamp="2026-03-07T12:00:00Z",
        )
        assert signal.trace_id is None
        assert signal.comment is None
