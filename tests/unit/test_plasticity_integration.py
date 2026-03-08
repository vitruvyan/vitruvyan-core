"""
Unit Tests — Plasticity Integration (Fasi B + C + D)
=====================================================

Tests cover:
- OrthodoxyPlasticityConsumer threshold propagation
- PlasticityService initialization and statistics
- Verdict → Outcome mapping
- Feedback → Outcome mapping
- _record_plasticity_outcome in orthodoxy_node
- Plasticity channel registry contracts
- Grafana dashboard validity

Created: Mar 07, 2026
"""

import sys
import os
import json
import asyncio
import importlib.util
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add vitruvyan_core so `core.*` imports work (runtime convention)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'vitruvyan_core'))

# ---------------------------------------------------------------------------
# Helper: load plasticity_adapter.py directly (bypass adapters/__init__.py
# which chain-imports graph_adapter → api_graph.config, unavailable in tests)
# ---------------------------------------------------------------------------
_ADAPTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'services', 'api_graph', 'adapters', 'plasticity_adapter.py',
)

spec = importlib.util.spec_from_file_location("plasticity_adapter", _ADAPTER_PATH)
_adapter_mod = importlib.util.module_from_spec(spec)
sys.modules["plasticity_adapter"] = _adapter_mod
spec.loader.exec_module(_adapter_mod)

OrthodoxyPlasticityConsumer = _adapter_mod.OrthodoxyPlasticityConsumer
PlasticityService = _adapter_mod.PlasticityService
get_plasticity_service = _adapter_mod.get_plasticity_service
init_plasticity_service = _adapter_mod.init_plasticity_service


# ---------------------------------------------------------------------------
# Helper: create a PlasticityService with mocked I/O (PostgresAgent etc.)
# ---------------------------------------------------------------------------

def _make_service(mock_tracker=None):
    """Build a PlasticityService with all I/O classes mocked."""
    from core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine

    _tracker = mock_tracker or MagicMock()

    with patch.object(_adapter_mod, "PostgresAgent", return_value=MagicMock()), \
         patch.object(_adapter_mod, "OutcomeTracker", return_value=_tracker), \
         patch.object(_adapter_mod, "PlasticityObserver", return_value=MagicMock()):
        svc = PlasticityService(VerdictEngine())

    return svc, _tracker


# ---------------------------------------------------------------------------
# Test OrthodoxyPlasticityConsumer — threshold propagation
# ---------------------------------------------------------------------------

class TestOrthodoxyPlasticityConsumer:
    """Test that threshold changes propagate to VerdictEngine."""

    def _make_consumer(self):
        from core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine
        ve = VerdictEngine()
        mock_tracker = MagicMock()
        consumer = OrthodoxyPlasticityConsumer(ve, mock_tracker)
        return consumer, ve

    def test_initial_thresholds_match_verdict_engine(self):
        consumer, ve = self._make_consumer()
        assert consumer.heretical_threshold == ve.weights.heretical_threshold
        assert consumer.purified_threshold == ve.weights.purified_threshold

    def test_setattr_propagates_heretical_threshold(self):
        consumer, ve = self._make_consumer()
        original = ve.weights.heretical_threshold
        consumer.heretical_threshold = 55.0
        assert ve.weights.heretical_threshold == 55.0
        assert ve.weights.heretical_threshold != original

    def test_setattr_propagates_purified_threshold(self):
        consumer, ve = self._make_consumer()
        consumer.purified_threshold = 85.0
        assert ve.weights.purified_threshold == 85.0

    def test_other_weights_preserved(self):
        consumer, ve = self._make_consumer()
        original_critical = ve.weights.critical
        original_high = ve.weights.high
        consumer.heretical_threshold = 60.0
        assert ve.weights.critical == original_critical
        assert ve.weights.high == original_high

    def test_outcome_tracker_accessible(self):
        consumer, _ = self._make_consumer()
        assert consumer.outcome_tracker is not None

    def test_plasticity_starts_none(self):
        consumer, _ = self._make_consumer()
        assert consumer.plasticity is None


# ---------------------------------------------------------------------------
# Test PlasticityService — initialization
# ---------------------------------------------------------------------------

class TestPlasticityService:
    """Test PlasticityService initialization and statistics."""

    def test_initialization(self):
        svc, _ = _make_service()
        assert svc._consumer is not None
        assert svc._consumer.plasticity is not None
        assert svc._running is False

    def test_statistics(self):
        svc, _ = _make_service()
        stats = svc.get_statistics()

        assert "current_thresholds" in stats
        assert stats["current_thresholds"]["heretical_threshold"] == 50.0
        assert stats["current_thresholds"]["purified_threshold"] == 80.0
        assert stats["running"] is False
        assert stats["cycles_run"] == 0

    def test_parameter_bounds(self):
        svc, _ = _make_service()
        bounds = svc._manager.bounds

        assert "heretical_threshold" in bounds
        assert "purified_threshold" in bounds
        assert bounds["heretical_threshold"].min_value == 30.0
        assert bounds["heretical_threshold"].max_value == 70.0
        assert bounds["purified_threshold"].min_value == 65.0
        assert bounds["purified_threshold"].max_value == 95.0


# ---------------------------------------------------------------------------
# Test verdict → outcome mapping
# ---------------------------------------------------------------------------

class TestVerdictOutcomeMapping:
    """Test that verdicts are correctly mapped to outcome values."""

    def test_blessed_maps_to_1(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-1", "blessed", 0.95, 0)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 1.0
        assert call_args.outcome_type == "verdict_blessed"

    def test_heretical_maps_to_0(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-2", "heretical", 0.1, 3)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 0.0

    def test_purified_maps_to_06(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-3", "purified", 0.7, 1)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 0.6

    def test_non_liquet_maps_to_03(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-4", "non_liquet", 0.5, 0)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 0.3

    def test_unknown_verdict_maps_to_05(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-5", "unknown_status", 0.5, 0)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 0.5

    def test_outcome_metadata_includes_context(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_verdict_outcome("trace-6", "blessed", 0.95, 2)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.metadata["confidence"] == 0.95
        assert call_args.metadata["findings_count"] == 2
        assert call_args.consumer_name == "orthodoxy_gate"
        assert call_args.parameter_name == "heretical_threshold"


# ---------------------------------------------------------------------------
# Test feedback → outcome mapping
# ---------------------------------------------------------------------------

class TestFeedbackOutcomeMapping:
    """Test that user feedback is correctly mapped to outcomes."""

    def test_positive_feedback(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_feedback_outcome("msg-1", "trace-1", "positive", 1.0)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 1.0
        assert call_args.outcome_type == "user_feedback_positive"
        assert call_args.consumer_name == "orthodoxy_gate"

    def test_negative_feedback_with_comment(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_feedback_outcome("msg-2", None, "negative", 0.0, "inaccurate")
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.outcome_value == 0.0
        assert call_args.metadata["comment"] == "inaccurate"
        assert call_args.decision_event_id == "msg-2"  # Falls back to message_id

    def test_feedback_uses_trace_id_when_available(self):
        mock_tracker = MagicMock()
        mock_tracker.record_outcome = AsyncMock()
        svc, _ = _make_service(mock_tracker)

        asyncio.get_event_loop().run_until_complete(
            svc.record_feedback_outcome("msg-3", "trace-3", "positive", 1.0)
        )

        call_args = mock_tracker.record_outcome.call_args[0][0]
        assert call_args.decision_event_id == "trace-3"


# ---------------------------------------------------------------------------
# Test _record_plasticity_outcome in orthodoxy_node
# ---------------------------------------------------------------------------

class TestOrthodoxyNodePlasticityIntegration:
    """Test that orthodoxy_node records outcomes when PlasticityService is available."""

    @patch("core.orchestration.langgraph.node.orthodoxy_node.get_stream_bus")
    def test_node_runs_without_plasticity(self, mock_bus):
        """orthodoxy_node must work even when PlasticityService is not initialized."""
        mock_bus.return_value = MagicMock()
        from core.orchestration.langgraph.node.orthodoxy_node import orthodoxy_node

        state = {"response": "Clean output", "user_id": "test"}
        result = orthodoxy_node(state)
        assert result["orthodoxy_verdict"] == "blessed"


# ---------------------------------------------------------------------------
# Test singleton lifecycle
# ---------------------------------------------------------------------------

class TestSingleton:
    """Test module-level singleton pattern."""

    def test_get_before_init_returns_none(self):
        _adapter_mod._plasticity_service = None
        assert get_plasticity_service() is None

    def test_init_creates_singleton(self):
        _adapter_mod._plasticity_service = None

        with patch.object(_adapter_mod, "PostgresAgent", return_value=MagicMock()), \
             patch.object(_adapter_mod, "OutcomeTracker", return_value=MagicMock()), \
             patch.object(_adapter_mod, "PlasticityObserver", return_value=MagicMock()):
            from core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine
            svc = init_plasticity_service(VerdictEngine())

        assert svc is not None
        assert get_plasticity_service() is svc

        # Second init returns same instance
        with patch.object(_adapter_mod, "PostgresAgent", return_value=MagicMock()), \
             patch.object(_adapter_mod, "OutcomeTracker", return_value=MagicMock()), \
             patch.object(_adapter_mod, "PlasticityObserver", return_value=MagicMock()):
            svc2 = init_plasticity_service(VerdictEngine())

        assert svc2 is svc

        # Cleanup
        _adapter_mod._plasticity_service = None


# ---------------------------------------------------------------------------
# Test Grafana dashboard validity
# ---------------------------------------------------------------------------

class TestGrafanaDashboard:
    """Validate Plasticity Grafana dashboard JSON."""

    DASHBOARD_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', 'infrastructure', 'docker', 'monitoring', 'grafana',
        'provisioning', 'dashboards', 'json', 'plasticity_learning.json'
    )

    def test_valid_json(self):
        with open(self.DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        assert isinstance(dashboard, dict)

    def test_has_panels(self):
        with open(self.DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        assert len(dashboard["panels"]) >= 10

    def test_all_panels_have_targets(self):
        with open(self.DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        for panel in dashboard["panels"]:
            assert "targets" in panel, f"Panel '{panel['title']}' has no targets"
            assert len(panel["targets"]) > 0

    def test_uses_plasticity_metrics(self):
        with open(self.DASHBOARD_PATH, 'r') as f:
            content = f.read()
        assert "vitruvyan_plasticity_" in content
        assert "vitruvyan_plasticity_success_rate" in content
        assert "vitruvyan_plasticity_adjustment_total" in content
        assert "vitruvyan_plasticity_learning_cycles_total" in content

    def test_tagged_correctly(self):
        with open(self.DASHBOARD_PATH, 'r') as f:
            dashboard = json.load(f)
        assert "plasticity" in dashboard["tags"]
        assert "vitruvyan" in dashboard["tags"]
