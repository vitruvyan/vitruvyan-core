"""
Integration Test — Memory Orders ↔ Vault Keepers coherence flow.

Tests the cross-Sacred Order interaction between Memory coherence analysis
and Vault Keepers integrity validation, without Docker or real databases.

Markers: integration
"""

import pytest
from core.governance.memory_orders.consumers.coherence_analyzer import CoherenceAnalyzer
from core.governance.memory_orders.domain.memory_objects import CoherenceInput, CoherenceReport
from core.governance.vault_keepers.consumers.sentinel import Sentinel


@pytest.fixture
def coherence_analyzer():
    return CoherenceAnalyzer()


@pytest.fixture
def sentinel():
    return Sentinel()


DEFAULT_THRESHOLDS = (("healthy", 5.0), ("warning", 15.0))


class TestMemoryVaultFlow:
    """End-to-end flow: CoherenceAnalyzer produces report → Sentinel validates integrity."""

    def test_healthy_coherence_produces_sacred_integrity(self, coherence_analyzer, sentinel):
        """When memory coherence is healthy, Sentinel should report sacred integrity."""
        inp = CoherenceInput(pg_count=100, qdrant_count=98, thresholds=DEFAULT_THRESHOLDS)
        report = coherence_analyzer.process(inp)

        assert report.status == "healthy"
        assert report.drift_percentage < 5.0

        # Feed coherence report into Sentinel as part of integrity check
        integrity_event = {
            "postgresql": {"status": "healthy", "tables": {}},
            "qdrant": {"status": "healthy", "collections": {}},
            "coherence": {"status": "coherent", "coherence_ratio": 1 - report.drift_percentage / 100},
        }
        integrity = sentinel.process(integrity_event)

        assert integrity.overall_status == "sacred"
        assert integrity.warden_blessing == "integrity_verified"
        assert len(integrity.findings) == 0

    def test_critical_coherence_triggers_corruption_detection(self, coherence_analyzer, sentinel):
        """When drift exceeds warning threshold, Sentinel should detect corruption."""
        inp = CoherenceInput(pg_count=100, qdrant_count=50, thresholds=DEFAULT_THRESHOLDS)
        report = coherence_analyzer.process(inp)

        assert report.status == "critical"
        assert report.drift_percentage == 50.0

        integrity_event = {
            "postgresql": {"status": "healthy", "tables": {}},
            "qdrant": {"status": "healthy", "collections": {}},
            "coherence": {"status": "critical", "coherence_ratio": 0.5},
        }
        integrity = sentinel.process(integrity_event)

        assert integrity.overall_status == "corruption_detected"
        assert integrity.warden_blessing == "integrity_violation_detected"

    def test_warning_coherence_with_degraded_db(self, coherence_analyzer, sentinel):
        """Warning drift + degraded postgres → blessed_with_concerns."""
        inp = CoherenceInput(pg_count=100, qdrant_count=90, thresholds=DEFAULT_THRESHOLDS)
        report = coherence_analyzer.process(inp)

        assert report.status == "warning"

        integrity_event = {
            "postgresql": {"status": "degraded", "tables": {"events": {"status": "error"}}},
            "qdrant": {"status": "healthy", "collections": {}},
            "coherence": {"status": "drift_detected", "coherence_ratio": 0.9},
        }
        integrity = sentinel.process(integrity_event)

        assert integrity.overall_status == "blessed_with_concerns"
        assert len(integrity.findings) > 0

    def test_both_systems_empty_is_healthy(self, coherence_analyzer, sentinel):
        """Edge case: both pg and qdrant empty → healthy (0% drift)."""
        inp = CoherenceInput(pg_count=0, qdrant_count=0, thresholds=DEFAULT_THRESHOLDS)
        report = coherence_analyzer.process(inp)

        assert report.status == "healthy"
        assert report.drift_percentage == 0.0

        integrity_event = {
            "postgresql": {"status": "healthy", "tables": {}},
            "qdrant": {"status": "healthy", "collections": {}},
            "coherence": {"status": "coherent", "coherence_ratio": 1.0},
        }
        integrity = sentinel.process(integrity_event)
        assert integrity.overall_status == "sacred"
