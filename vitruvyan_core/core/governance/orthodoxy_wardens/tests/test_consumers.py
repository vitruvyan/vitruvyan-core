"""
Tests for FASE 3 — Consumers (Confessor, Inquisitor, Penitent, Chronicler)

All consumers are pure decision engines: same input → same output, no I/O.
"""

import pytest
from datetime import datetime, timezone

from core.governance.orthodoxy_wardens.consumers import (
    SacredRole,
    Confessor,
    Inquisitor,
    InquisitorResult,
    Penitent,
    CorrectionRequest,
    CorrectionPlan,
    Chronicler,
    ArchiveDirective,
    ChronicleDecision,
)
from core.governance.orthodoxy_wardens.domain.confession import Confession
from core.governance.orthodoxy_wardens.domain.finding import Finding
from core.governance.orthodoxy_wardens.domain.verdict import Verdict
from core.governance.orthodoxy_wardens.domain.log_decision import LogDecision
from core.governance.orthodoxy_wardens.events.orthodoxy_events import (
    OrthodoxyEvent,
)
from core.governance.orthodoxy_wardens.governance import (
    VerdictEngine,
    DEFAULT_RULESET,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def confessor():
    return Confessor()


@pytest.fixture
def inquisitor():
    return Inquisitor()


@pytest.fixture
def penitent():
    return Penitent()


@pytest.fixture
def chronicler():
    return Chronicler()


@pytest.fixture
def sample_event():
    return OrthodoxyEvent(
        event_type="langgraph.output.ready",
        payload=(("entity_id", "ENTITY_A"), ("text", "Act now!")),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="test",
    )


@pytest.fixture
def sample_confession():
    return Confession(
        confession_id="test_confession_001",
        trigger_type="output_validation",
        scope="single_output",
        urgency="high",
        source="test",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def clean_findings():
    return ()


@pytest.fixture
def violation_findings():
    return (
        Finding(
            finding_id="f_001",
            finding_type="violation",
            severity="critical",
            category="hallucination",
            message="Guaranteed returns claim detected",
            source_rule="hallucination.guaranteed_returns",
        ),
        Finding(
            finding_id="f_002",
            finding_type="violation",
            severity="high",
            category="compliance",
            message="Missing risk disclaimer",
            source_rule="compliance.risk_disclaimer",
        ),
    )


@pytest.fixture
def warning_findings():
    return (
        Finding(
            finding_id="f_003",
            finding_type="warning",
            severity="medium",
            category="quality",
            message="Output could be more specific",
            source_rule="quality.specificity",
        ),
    )


@pytest.fixture
def blessed_verdict(clean_findings):
    return Verdict.blessed(
        confidence=0.95,
        findings=clean_findings,
        explanation="All checks passed",
        ruleset_version="v1.0",
    )


@pytest.fixture
def heretical_verdict(violation_findings):
    return Verdict.heretical(
        findings=violation_findings,
        explanation="Critical hallucination detected",
        confidence=0.95,
        ruleset_version="v1.0",
    )


@pytest.fixture
def purified_verdict(warning_findings):
    return Verdict.purified(
        confidence=0.80,
        findings=warning_findings,
        explanation="Minor warnings found, acceptable with caveats",
        ruleset_version="v1.0",
    )


@pytest.fixture
def non_liquet_verdict(clean_findings):
    return Verdict.non_liquet(
        confidence=0.40,
        what_we_know=("Input received", "Partial analysis done"),
        what_is_uncertain=("Model confidence low", "Insufficient context"),
        uncertainty_sources=("external_api_timeout",),
        best_guess="Likely acceptable but cannot confirm",
        findings=clean_findings,
        ruleset_version="v1.0",
    )


# =============================================================================
# Confessor Tests
# =============================================================================


class TestConfessorABC:
    """Verify Confessor satisfies SacredRole contract."""

    def test_inherits_sacred_role(self, confessor):
        assert isinstance(confessor, SacredRole)

    def test_role_name(self, confessor):
        assert confessor.role_name == "confessor"

    def test_description_nonempty(self, confessor):
        assert len(confessor.description) > 0

    def test_repr(self, confessor):
        assert "confessor" in repr(confessor)


class TestConfessorCanHandle:
    def test_handles_orthodoxy_event(self, confessor, sample_event):
        assert confessor.can_handle(sample_event) is True

    def test_handles_dict_with_event_type(self, confessor):
        assert confessor.can_handle({"event_type": "test"}) is True

    def test_handles_dict_with_trigger_type(self, confessor):
        assert confessor.can_handle({"trigger_type": "manual"}) is True

    def test_rejects_empty_dict(self, confessor):
        assert confessor.can_handle({}) is False

    def test_rejects_string(self, confessor):
        assert confessor.can_handle("not an event") is False

    def test_rejects_none(self, confessor):
        assert confessor.can_handle(None) is False

    def test_rejects_int(self, confessor):
        assert confessor.can_handle(42) is False


class TestConfessorProcess:
    def test_from_orthodoxy_event(self, confessor, sample_event):
        confession = confessor.process(sample_event)
        assert isinstance(confession, Confession)
        assert confession.confession_id.startswith("confession_")
        assert confession.trigger_type == "output_validation"
        assert confession.urgency == "high"
        assert confession.source == "test"

    def test_from_dict_manual(self, confessor):
        data = {
            "trigger_type": "manual",
            "scope": "complete_realm",
            "urgency": "routine",
            "source": "admin_api",
            "metadata": {"reason": "scheduled audit"},
        }
        confession = confessor.process(data)
        assert isinstance(confession, Confession)
        assert confession.trigger_type == "manual"
        assert confession.scope == "complete_realm"

    def test_from_dict_defaults(self, confessor):
        confession = confessor.process({"event_type": "test"})
        assert confession.trigger_type == "manual"  # Default
        assert confession.scope == "single_output"  # Default
        assert confession.urgency == "routine"  # Default

    def test_metadata_tuple_conversion(self, confessor):
        data = {
            "trigger_type": "manual",
            "source": "test",
            "metadata": {"key1": "value1", "key2": "value2"},
        }
        confession = confessor.process(data)
        assert isinstance(confession.metadata, tuple)

    def test_event_type_mapping(self, confessor):
        """Verify different event types map to correct trigger/scope/urgency."""
        codex_event = OrthodoxyEvent(
            event_type="codex.discovery.mapped",
            payload=(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="codex",
        )
        confession = confessor.process(codex_event)
        assert confession.trigger_type == "event"
        assert confession.scope == "single_event"
        assert confession.urgency == "routine"

    def test_unknown_event_type_defaults(self, confessor):
        event = OrthodoxyEvent(
            event_type="unknown.channel",
            payload=(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="test",
        )
        confession = confessor.process(event)
        assert confession.trigger_type == "event"  # Default fallback

    def test_raises_on_invalid_input(self, confessor):
        with pytest.raises(ValueError, match="cannot process"):
            confessor.process(42)

    def test_correlation_id_preserved(self, confessor):
        event = OrthodoxyEvent(
            event_type="langgraph.output.ready",
            payload=(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="test",
            correlation_id="corr_123",
        )
        confession = confessor.process(event)
        assert confession.correlation_id == "corr_123"


# =============================================================================
# Inquisitor Tests
# =============================================================================


class TestInquisitorABC:
    def test_inherits_sacred_role(self, inquisitor):
        assert isinstance(inquisitor, SacredRole)

    def test_role_name(self, inquisitor):
        assert inquisitor.role_name == "inquisitor"

    def test_description_nonempty(self, inquisitor):
        assert len(inquisitor.description) > 0


class TestInquisitorCanHandle:
    def test_handles_dict_with_confession(self, inquisitor, sample_confession):
        assert inquisitor.can_handle({"confession": sample_confession}) is True

    def test_handles_dict_with_text(self, inquisitor):
        assert inquisitor.can_handle({"text": "some text"}) is True

    def test_handles_dict_with_code(self, inquisitor):
        assert inquisitor.can_handle({"code": "x = 1"}) is True

    def test_handles_confession_directly(self, inquisitor, sample_confession):
        assert inquisitor.can_handle(sample_confession) is True

    def test_rejects_empty_dict(self, inquisitor):
        assert inquisitor.can_handle({}) is False

    def test_rejects_string(self, inquisitor):
        assert inquisitor.can_handle("not valid") is False


class TestInquisitorProcess:
    def test_clean_text_no_findings(self, inquisitor, sample_confession):
        result = inquisitor.process({
            "confession": sample_confession,
            "text": "ENTITY_A shows signal z-score of 1.2 based on analysis.",
        })
        assert isinstance(result, InquisitorResult)
        assert result.text_examined is True
        assert result.code_examined is False

    def test_hallucination_text_produces_findings(self, inquisitor, sample_confession):
        result = inquisitor.process({
            "confession": sample_confession,
            "text": "Act now! Guaranteed 500% returns with no risk!",
        })
        assert result.finding_count > 0
        assert result.has_violations is True

    def test_code_examination(self, inquisitor, sample_confession):
        result = inquisitor.process({
            "confession": sample_confession,
            "text": "",
            "code": "import os\nos.system('rm -rf /')\neval('malicious')",
        })
        assert result.code_examined is True
        assert result.finding_count > 0

    def test_syntax_error_code(self, inquisitor, sample_confession):
        result = inquisitor.process({
            "confession": sample_confession,
            "text": "",
            "code": "def broken(:\n    pass",
        })
        assert result.code_examined is True
        # ASTClassifier returns anomaly for syntax errors
        assert result.finding_count > 0
        assert any(f.finding_type == "anomaly" for f in result.findings)

    def test_confession_id_preserved(self, inquisitor, sample_confession):
        result = inquisitor.process({
            "confession": sample_confession,
            "text": "test",
        })
        assert result.confession_id == "test_confession_001"

    def test_confession_direct_input(self, inquisitor, sample_confession):
        result = inquisitor.process(sample_confession)
        assert isinstance(result, InquisitorResult)

    def test_no_code_examination_when_disabled(self, sample_confession):
        inq = Inquisitor(examine_code=False)
        result = inq.process({
            "confession": sample_confession,
            "text": "",
            "code": "eval('hack')",
        })
        assert result.code_examined is False

    def test_custom_ruleset(self, sample_confession):
        from core.governance.orthodoxy_wardens.governance import RuleSet, Rule
        custom_ruleset = RuleSet.create(
            version="custom_v1",
            rules=(
                Rule(
                    rule_id="custom_001",
                    category="compliance",
                    subcategory="test",
                    severity="critical",
                    pattern=r"FORBIDDEN",
                    description="Test forbidden pattern",
                ),
            ),
            description="Custom test ruleset",
        )
        inq = Inquisitor(ruleset=custom_ruleset)
        result = inq.process({
            "confession": sample_confession,
            "text": "This contains FORBIDDEN content",
        })
        assert result.has_violations is True

    def test_raises_on_invalid_input(self, inquisitor):
        with pytest.raises(ValueError, match="expects dict or Confession"):
            inquisitor.process(42)


class TestInquisitorResult:
    def test_frozen(self, inquisitor, sample_confession):
        result = inquisitor.process({"confession": sample_confession, "text": "test"})
        with pytest.raises(AttributeError, match="frozen"):
            result._findings = ()

    def test_findings_by_category(self):
        findings = (
            Finding(finding_id="f1", finding_type="violation", severity="high", category="compliance", message="msg1", source_rule="rule1"),
            Finding(finding_id="f2", finding_type="violation", severity="medium", category="security", message="msg2", source_rule="rule2"),
            Finding(finding_id="f3", finding_type="warning", severity="low", category="compliance", message="msg3", source_rule="rule3"),
        )
        result = InquisitorResult("test", findings, 10, True, False)
        compliance = result.findings_by_category("compliance")
        assert len(compliance) == 2

    def test_findings_by_severity(self):
        findings = (
            Finding(finding_id="f1", finding_type="violation", severity="high", category="compliance", message="msg1", source_rule="rule1"),
            Finding(finding_id="f2", finding_type="violation", severity="high", category="security", message="msg2", source_rule="rule2"),
            Finding(finding_id="f3", finding_type="warning", severity="low", category="compliance", message="msg3", source_rule="rule3"),
        )
        result = InquisitorResult("test", findings, 10, True, False)
        high = result.findings_by_severity("high")
        assert len(high) == 2


# =============================================================================
# Penitent Tests
# =============================================================================


class TestPenitentABC:
    def test_inherits_sacred_role(self, penitent):
        assert isinstance(penitent, SacredRole)

    def test_role_name(self, penitent):
        assert penitent.role_name == "penitent"

    def test_description_nonempty(self, penitent):
        assert len(penitent.description) > 0


class TestPenitentCanHandle:
    def test_handles_verdict(self, penitent, blessed_verdict):
        assert penitent.can_handle(blessed_verdict) is True

    def test_handles_dict_with_verdict(self, penitent, blessed_verdict):
        assert penitent.can_handle({"verdict": blessed_verdict}) is True

    def test_rejects_empty_dict(self, penitent):
        assert penitent.can_handle({}) is False

    def test_rejects_string(self, penitent):
        assert penitent.can_handle("not a verdict") is False


class TestPenitentProcess:
    def test_blessed_empty_plan(self, penitent, blessed_verdict):
        plan = penitent.process(blessed_verdict)
        assert isinstance(plan, CorrectionPlan)
        assert plan.is_empty is True
        assert plan.total_requests == 0
        assert plan.requires_human is False

    def test_heretical_produces_corrections(self, penitent, heretical_verdict):
        plan = penitent.process(heretical_verdict)
        assert plan.total_requests > 0
        assert plan.verdict_status == "heretical"

    def test_heretical_critical_requires_human(self, penitent, heretical_verdict):
        plan = penitent.process(heretical_verdict)
        assert plan.requires_human is True

    def test_purified_produces_corrections(self, penitent, purified_verdict):
        plan = penitent.process(purified_verdict)
        # Purified may have corrections for warnings
        assert isinstance(plan, CorrectionPlan)

    def test_critical_findings_escalated(self, penitent):
        findings = (
            Finding(finding_id="f1", finding_type="violation", severity="critical", category="hallucination", message="Guaranteed returns", source_rule="rule1"),
        )
        verdict = Verdict.heretical(
            findings=findings,
            explanation="Critical hallucination",
            ruleset_version="v1.0",
        )
        plan = penitent.process(verdict)
        assert plan.requires_human is True
        assert len(plan.critical_requests) > 0

    def test_security_findings_require_human(self, penitent):
        findings = (
            Finding(finding_id="f1", finding_type="violation", severity="high", category="security", message="SQL injection risk", source_rule="rule1"),
        )
        verdict = Verdict.heretical(
            findings=findings,
            explanation="Security issue",
            ruleset_version="v1.0",
        )
        plan = penitent.process(verdict)
        assert plan.requires_human is True

    def test_correction_priority_order(self, penitent):
        findings = (
            Finding(finding_id="f1", finding_type="violation", severity="low", category="quality", message="Minor style issue", source_rule="rule1"),
            Finding(finding_id="f2", finding_type="violation", severity="critical", category="security", message="SQL injection", source_rule="rule2"),
            Finding(finding_id="f3", finding_type="violation", severity="medium", category="compliance", message="Missing disclaimer", source_rule="rule3"),
        )
        verdict = Verdict.heretical(
            findings=findings,
            explanation="Multiple issues",
            ruleset_version="v1.0",
        )
        plan = penitent.process(verdict)
        priorities = [r.priority for r in plan.requests]
        assert priorities == sorted(
            priorities,
            key=lambda p: {"critical": 0, "high": 1, "medium": 2, "low": 3}[p],
        )

    def test_dict_input_extraction(self, penitent, heretical_verdict):
        plan = penitent.process({"verdict": heretical_verdict})
        assert plan.total_requests > 0

    def test_raises_on_invalid_input(self, penitent):
        with pytest.raises(ValueError, match="expects Verdict"):
            penitent.process(42)


class TestCorrectionRequest:
    def test_frozen(self):
        finding = Finding(finding_id="f1", finding_type="violation", severity="high", category="compliance", message="msg", source_rule="rule")
        req = CorrectionRequest(finding, "add_guard", "high", "desc")
        with pytest.raises(AttributeError, match="frozen"):
            req._strategy = "other"

    def test_invalid_strategy_raises(self):
        finding = Finding(finding_id="f1", finding_type="violation", severity="high", category="compliance", message="msg", source_rule="rule")
        with pytest.raises(ValueError, match="Invalid strategy"):
            CorrectionRequest(finding, "invalid_strategy", "high", "desc")

    def test_invalid_priority_raises(self):
        finding = Finding(finding_id="f1", finding_type="violation", severity="high", category="compliance", message="msg", source_rule="rule")
        with pytest.raises(ValueError, match="Invalid priority"):
            CorrectionRequest(finding, "add_guard", "invalid", "desc")


# =============================================================================
# Chronicler Tests
# =============================================================================


class TestChroniclerABC:
    def test_inherits_sacred_role(self, chronicler):
        assert isinstance(chronicler, SacredRole)

    def test_role_name(self, chronicler):
        assert chronicler.role_name == "chronicler"

    def test_description_nonempty(self, chronicler):
        assert len(chronicler.description) > 0


class TestChroniclerCanHandle:
    def test_handles_verdict(self, chronicler, blessed_verdict):
        assert chronicler.can_handle(blessed_verdict) is True

    def test_handles_dict_with_verdict(self, chronicler, blessed_verdict):
        assert chronicler.can_handle({"verdict": blessed_verdict}) is True

    def test_rejects_empty_dict(self, chronicler):
        assert chronicler.can_handle({}) is False

    def test_rejects_string(self, chronicler):
        assert chronicler.can_handle("not valid") is False


class TestChroniclerProcess:
    def test_heretical_all_destinations(self, chronicler, heretical_verdict):
        decision = chronicler.process(heretical_verdict)
        assert isinstance(decision, ChronicleDecision)
        assert decision.should_log is True
        assert "postgresql" in decision.destinations
        assert "qdrant" in decision.destinations
        assert "blockchain" in decision.destinations
        assert "cognitive_bus" in decision.destinations
        assert decision.requires_blockchain is True

    def test_purified_no_blockchain(self, chronicler, purified_verdict):
        decision = chronicler.process(purified_verdict)
        assert decision.should_log is True
        assert "postgresql" in decision.destinations
        assert "qdrant" in decision.destinations
        assert "cognitive_bus" in decision.destinations
        assert decision.requires_blockchain is False

    def test_blessed_minimal(self, chronicler, blessed_verdict):
        decision = chronicler.process(blessed_verdict)
        assert "postgresql" in decision.destinations
        assert "blockchain" not in decision.destinations
        assert "qdrant" not in decision.destinations
        assert decision.requires_blockchain is False

    def test_non_liquet_for_future_retrieval(self, chronicler, non_liquet_verdict):
        decision = chronicler.process(non_liquet_verdict)
        assert "postgresql" in decision.destinations
        assert "qdrant" in decision.destinations
        assert decision.requires_blockchain is False

    def test_heretical_retention_365(self, chronicler, heretical_verdict):
        decision = chronicler.process(heretical_verdict)
        pg_directive = [d for d in decision.directives if d.destination == "postgresql"][0]
        assert pg_directive.retention_days == 365

    def test_blessed_retention_30(self, chronicler, blessed_verdict):
        decision = chronicler.process(blessed_verdict)
        pg_directive = [d for d in decision.directives if d.destination == "postgresql"][0]
        assert pg_directive.retention_days == 30

    def test_dict_input_extraction(self, chronicler, heretical_verdict):
        decision = chronicler.process({"verdict": heretical_verdict})
        assert decision.requires_blockchain is True

    def test_raises_on_invalid_input(self, chronicler):
        with pytest.raises(ValueError, match="expects Verdict"):
            chronicler.process(42)


class TestArchiveDirective:
    def test_frozen(self):
        d = ArchiveDirective("postgresql", 30, "low", "test")
        with pytest.raises(AttributeError, match="frozen"):
            d._destination = "other"

    def test_invalid_destination_raises(self):
        with pytest.raises(ValueError, match="Invalid destination"):
            ArchiveDirective("elasticsearch", 30, "low", "test")


# =============================================================================
# Full Pipeline Integration Tests
# =============================================================================


class TestFullPipeline:
    """Test the complete tribunal pipeline end-to-end."""

    def test_heretical_pipeline(self, confessor, inquisitor, penitent, chronicler):
        """Full pipeline with hallucination text → heretical verdict."""
        event = OrthodoxyEvent(
            event_type="langgraph.output.ready",
            payload=(("text", "Guaranteed profits!"),),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="test",
        )

        # Confessor
        confession = confessor.process(event)
        assert isinstance(confession, Confession)

        # Inquisitor
        result = inquisitor.process({
            "confession": confession,
            "text": "Act now! Guaranteed 500% returns! No risk at all!",
        })
        assert result.finding_count > 0

        # VerdictEngine
        engine = VerdictEngine()
        verdict = engine.render(result.findings, DEFAULT_RULESET, confession.confession_id)
        assert verdict.status in ("heretical", "purified")

        # Penitent
        plan = penitent.process(verdict)
        assert isinstance(plan, CorrectionPlan)

        # Chronicler
        decision = chronicler.process(verdict)
        assert isinstance(decision, ChronicleDecision)
        assert decision.should_log is True

    def test_blessed_pipeline(self, confessor, inquisitor, penitent, chronicler):
        """Full pipeline with clean text → blessed verdict."""
        event = {
            "event_type": "engine.eval.completed",
            "source": "neural_engine",
        }

        confession = confessor.process(event)
        result = inquisitor.process({
            "confession": confession,
            "text": "ENTITY_A signal z-score is 1.2 with above-average trend strength.",
        })

        engine = VerdictEngine()
        verdict = engine.render(result.findings, DEFAULT_RULESET, confession.confession_id)
        assert verdict.status == "blessed"

        plan = penitent.process(verdict)
        assert plan.is_empty is True

        decision = chronicler.process(verdict)
        assert not decision.requires_blockchain

    def test_determinism(self, confessor, inquisitor, penitent, chronicler):
        """Same input → same output across multiple runs."""
        event = {
            "event_type": "test.determinism",
            "source": "test",
            "metadata": {"key": "value"},
        }

        results = []
        for _ in range(3):
            confession = confessor.process(event)
            result = inquisitor.process({
                "confession": confession,
                "text": "Guaranteed returns with certainty!",
            })
            engine = VerdictEngine()
            verdict = engine.render(result.findings, DEFAULT_RULESET, confession.confession_id)
            plan = penitent.process(verdict)
            decision = chronicler.process(verdict)

            results.append({
                "finding_count": result.finding_count,
                "verdict_status": verdict.status,
                "plan_requests": plan.total_requests,
                "destinations": decision.destinations,
            })

        # All 3 runs should produce identical structural results
        assert results[0]["finding_count"] == results[1]["finding_count"] == results[2]["finding_count"]
        assert results[0]["verdict_status"] == results[1]["verdict_status"] == results[2]["verdict_status"]
        assert results[0]["plan_requests"] == results[1]["plan_requests"] == results[2]["plan_requests"]
        assert results[0]["destinations"] == results[1]["destinations"] == results[2]["destinations"]
