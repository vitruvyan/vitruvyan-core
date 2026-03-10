"""
Integration Test — Orthodoxy Wardens audit pipeline.

Tests the full Confessor → Inquisitor → VerdictEngine flow
without Docker, real LLM, or database. Uses mock LLM classifier.

Markers: integration
"""

import pytest
from unittest.mock import MagicMock, patch

from core.governance.orthodoxy_wardens.consumers.confessor import Confessor
from core.governance.orthodoxy_wardens.consumers.inquisitor import Inquisitor
from core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine
from core.governance.orthodoxy_wardens.governance.rule import DEFAULT_RULESET
from core.governance.orthodoxy_wardens.domain.finding import Finding
from core.governance.orthodoxy_wardens.events.orthodoxy_events import OrthodoxyEvent


@pytest.fixture
def confessor():
    return Confessor()


@pytest.fixture
def inquisitor():
    inq = Inquisitor(ruleset=DEFAULT_RULESET, examine_code=True)
    # Mock LLM classifier to avoid real LLM calls
    inq._llm_classifier = MagicMock()
    return inq


@pytest.fixture
def verdict_engine():
    return VerdictEngine()


def _make_finding(severity="low", finding_type="warning", category="quality"):
    return Finding(
        finding_id=f"test_{severity}",
        finding_type=finding_type,
        severity=severity,
        category=category,
        message=f"Test {severity} finding",
        source_rule="test.rule",
    )


class TestOrthodoxyPipeline:
    """Full pipeline: Confessor → Inquisitor → VerdictEngine."""

    def test_clean_text_produces_blessed_verdict(self, confessor, inquisitor, verdict_engine):
        """Clean text with no findings → blessed verdict."""
        # Step 1: Confessor intake
        event = OrthodoxyEvent(
            event_type="langgraph.output.ready",
            source="graph.compose_node",
            payload=("output_text", "The weather today is sunny."),
            timestamp="2026-02-12T00:00:00Z",
        )
        confession = confessor.process(event)
        assert confession.trigger_type == "output_validation"
        assert confession.urgency == "high"

        # Step 2: Inquisitor examination (mock LLM returns no findings)
        inquisitor._llm_classifier.classify.return_value = ([], True)
        result = inquisitor.process({
            "confession": confession,
            "text": "The weather today is sunny.",
        })
        assert result.finding_count == 0
        assert not result.has_violations

        # Step 3: VerdictEngine renders verdict
        verdict = verdict_engine.render(result.findings, DEFAULT_RULESET, confession.confession_id)
        assert verdict.status == "blessed"
        assert verdict.should_send is True
        assert verdict.confidence > 0.5

    def test_critical_finding_produces_heretical_verdict(self, confessor, inquisitor, verdict_engine):
        """Critical finding → heretical verdict, output blocked."""
        confession = confessor.process({
            "trigger_type": "output_validation",
            "source": "test",
        })

        # Mock LLM returns critical finding
        critical = _make_finding(severity="critical", finding_type="violation", category="hallucination")
        inquisitor._llm_classifier.classify.return_value = ([critical], True)
        result = inquisitor.process({"confession": confession, "text": "Buy AAPL now, guaranteed 100% returns!"})

        assert result.has_critical
        assert result.has_violations

        verdict = verdict_engine.render(result.findings, DEFAULT_RULESET)
        assert verdict.status == "heretical"
        assert verdict.should_send is False

    def test_medium_findings_produce_purified_verdict(self, confessor, verdict_engine):
        """Multiple medium findings → purified verdict (score 80-50 range)."""
        # 5 medium findings: 5 × 0.05 × 100 = 25 penalty → score 75 → purified
        findings = tuple(_make_finding(severity="medium") for _ in range(5))
        verdict = verdict_engine.render(findings, DEFAULT_RULESET)
        assert verdict.status == "purified"
        assert verdict.should_send is True

    def test_dict_event_produces_valid_confession(self, confessor):
        """Dict-based events (manual/API triggers) produce valid Confessions."""
        confession = confessor.process({
            "trigger_type": "manual",
            "scope": "complete_realm",
            "urgency": "low",
            "source": "api.admin",
            "metadata": {"reason": "quarterly audit"},
        })
        assert confession.trigger_type == "manual"
        assert confession.scope == "complete_realm"
        assert confession.urgency == "low"

    def test_log_decision_for_heretical(self, verdict_engine):
        """Heretical verdict → critical_audit log decision."""
        findings = (_make_finding(severity="critical", finding_type="violation"),)
        verdict = verdict_engine.render(findings, DEFAULT_RULESET)
        log_decision = verdict_engine.decide_logging(verdict)
        assert log_decision.should_log is True
        assert log_decision.severity == "critical"

    def test_log_decision_for_clean_blessed(self, verdict_engine):
        """Clean blessed (no findings) → skip logging."""
        verdict = verdict_engine.render((), DEFAULT_RULESET)
        log_decision = verdict_engine.decide_logging(verdict)
        assert log_decision.should_log is False

    def test_orthodoxy_event_types_map_correctly(self, confessor):
        """Different event types map to correct trigger/scope/urgency."""
        mappings = [
            ("codex.discovery.mapped", "event", "single_event", "routine"),
            ("langgraph.output.ready", "output_validation", "single_output", "high"),
            ("synaptic.conclave.broadcast", "event", "complete_realm", "low"),
        ]
        for event_type, expected_trigger, expected_scope, expected_urgency in mappings:
            event = OrthodoxyEvent(event_type=event_type, source="test", payload=(), timestamp="2026-02-12T00:00:00Z")
            confession = confessor.process(event)
            assert confession.trigger_type == expected_trigger, f"Failed for {event_type}"
            assert confession.scope == expected_scope, f"Failed for {event_type}"
            assert confession.urgency == expected_urgency, f"Failed for {event_type}"
