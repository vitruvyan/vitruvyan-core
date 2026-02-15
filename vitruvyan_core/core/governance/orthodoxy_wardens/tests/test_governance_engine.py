"""
Tests for FASE 2 — Governance Engine

Tests Rule/RuleSet, PatternClassifier, ASTClassifier, VerdictEngine, Workflows.
All tests are pure — no I/O, no network, no database.

Run: pytest vitruvyan_core/core/governance/orthodoxy_wardens/tests/test_governance_engine.py -v
"""

import sys
import os
import re
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from vitruvyan_core.core.governance.orthodoxy_wardens.domain import (
    Confession, Finding, Verdict, LogDecision,
)
from vitruvyan_core.core.governance.orthodoxy_wardens.governance import (
    Rule, RuleSet, DEFAULT_RULESET, DEFAULT_RULES,
    PatternClassifier, ASTClassifier, classify_text,
    VerdictEngine, ScoringWeights, DEFAULT_WEIGHTS,
    Workflow, WorkflowStep,
    FULL_AUDIT_WORKFLOW, QUICK_VALIDATION_WORKFLOW, AVAILABLE_WORKFLOWS,
)


# =============================================================================
# Rule Tests
# =============================================================================

class TestRule:
    """Test Rule frozen dataclass."""

    def test_rule_creation(self):
        rule = Rule(
            rule_id="test.001",
            category="compliance",
            subcategory="test",
            severity="critical",
            pattern=r"\bbuy now\b",
            description="Test rule",
        )
        assert rule.rule_id == "test.001"
        assert rule.enabled is True

    def test_rule_is_frozen(self):
        rule = Rule("test.001", "compliance", "test", "critical", r"pattern", "desc")
        try:
            rule.severity = "low"
            assert False, "Should not allow mutation"
        except AttributeError:
            pass  # Expected — frozen

    def test_rule_invalid_category(self):
        try:
            Rule("test.001", "invalid_cat", "test", "critical", r"p", "d")
            assert False, "Should reject invalid category"
        except ValueError as e:
            assert "invalid_cat" in str(e)

    def test_rule_invalid_severity(self):
        try:
            Rule("test.001", "compliance", "test", "extreme", r"p", "d")
            assert False, "Should reject invalid severity"
        except ValueError as e:
            assert "extreme" in str(e)

    def test_rule_disabled(self):
        rule = Rule("test.001", "compliance", "t", "low", r"p", "d", enabled=False)
        assert rule.enabled is False


# =============================================================================
# RuleSet Tests
# =============================================================================

class TestRuleSet:
    """Test RuleSet frozen dataclass."""

    def _make_rules(self, n=3):
        return tuple(
            Rule(f"test.{i:03d}", "compliance", "test", "medium", f"pattern_{i}", f"desc_{i}")
            for i in range(n)
        )

    def test_ruleset_creation(self):
        rules = self._make_rules()
        rs = RuleSet.create(version="v1.0", rules=rules, description="test")
        assert rs.version == "v1.0"
        assert rs.rule_count == 3
        assert len(rs.checksum) == 16

    def test_ruleset_is_frozen(self):
        rules = self._make_rules()
        rs = RuleSet.create(version="v1.0", rules=rules)
        try:
            rs.version = "v2.0"
            assert False, "Should not allow mutation"
        except AttributeError:
            pass

    def test_ruleset_checksum_deterministic(self):
        rules = self._make_rules()
        rs1 = RuleSet.create(version="v1.0", rules=rules)
        rs2 = RuleSet.create(version="v1.0", rules=rules)
        assert rs1.checksum == rs2.checksum

    def test_ruleset_checksum_changes_with_rules(self):
        rules1 = self._make_rules(3)
        rules2 = self._make_rules(4)
        rs1 = RuleSet.create(version="v1.0", rules=rules1)
        rs2 = RuleSet.create(version="v1.0", rules=rules2)
        assert rs1.checksum != rs2.checksum

    def test_active_rules_filter(self):
        rules = (
            Rule("t.001", "compliance", "t", "low", "p1", "d1", enabled=True),
            Rule("t.002", "compliance", "t", "low", "p2", "d2", enabled=False),
            Rule("t.003", "compliance", "t", "low", "p3", "d3", enabled=True),
        )
        rs = RuleSet.create(version="v1.0", rules=rules)
        assert rs.rule_count == 3
        assert rs.active_count == 2

    def test_rules_by_category(self):
        rules = (
            Rule("t.001", "compliance", "t", "low", "p1", "d1"),
            Rule("t.002", "security", "t", "low", "p2", "d2"),
            Rule("t.003", "compliance", "t", "low", "p3", "d3"),
        )
        rs = RuleSet.create(version="v1.0", rules=rules)
        compliance = rs.rules_by_category("compliance")
        assert len(compliance) == 2

    def test_version_tag(self):
        rules = self._make_rules()
        rs = RuleSet.create(version="v1.0", rules=rules)
        assert rs.version_tag.startswith("ruleset_v1.0_")


# =============================================================================
# Default RuleSet Tests
# =============================================================================

class TestDefaultRuleSet:
    """Test the built-in default ruleset."""

    def test_default_rules_count(self):
        assert DEFAULT_RULESET.rule_count == 35

    def test_default_version(self):
        assert DEFAULT_RULESET.version == "v1.0"

    def test_compliance_rules_exist(self):
        rules = DEFAULT_RULESET.rules_by_category("compliance")
        assert len(rules) >= 10

    def test_security_rules_exist(self):
        rules = DEFAULT_RULESET.rules_by_category("security")
        assert len(rules) >= 5

    def test_hallucination_rules_exist(self):
        rules = DEFAULT_RULESET.rules_by_category("hallucination")
        assert len(rules) >= 2

    def test_all_rules_have_valid_regex(self):
        for rule in DEFAULT_RULESET.rules:
            try:
                re.compile(rule.pattern)
            except re.error:
                assert False, f"Rule {rule.rule_id} has invalid regex: {rule.pattern}"

    def test_all_rule_ids_unique(self):
        ids = [r.rule_id for r in DEFAULT_RULESET.rules]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"


# =============================================================================
# PatternClassifier Tests
# =============================================================================

class TestPatternClassifier:
    """Test regex-based classification."""

    def setup_method(self):
        self.classifier = PatternClassifier()

    def test_clean_text_no_findings(self):
        findings = self.classifier.classify(
            "ENTITY_A shows strong positive signal with score at 65",
            DEFAULT_RULESET,
        )
        assert len(findings) == 0

    def test_prescriptive_language_detected(self):
        findings = self.classifier.classify(
            "You must buy now this stock",
            DEFAULT_RULESET,
        )
        assert len(findings) >= 1
        assert any(f.severity == "critical" for f in findings)

    def test_guaranteed_returns_detected(self):
        findings = self.classifier.classify(
            "This investment is guaranteed and risk-free",
            DEFAULT_RULESET,
        )
        assert len(findings) >= 1
        assert any("compliance" in f.category for f in findings)

    def test_hardcoded_secret_detected(self):
        findings = self.classifier.classify(
            'api_key = "sk-abc123def456"',
            DEFAULT_RULESET,
        )
        assert len(findings) >= 1
        assert any(f.category == "security" for f in findings)

    def test_hallucination_detected(self):
        findings = self.classifier.classify(
            "Apple has $50 trillion revenue this quarter",
            DEFAULT_RULESET,
        )
        assert len(findings) >= 1
        assert any(f.category == "hallucination" for f in findings)

    def test_findings_are_frozen(self):
        findings = self.classifier.classify("buy now", DEFAULT_RULESET)
        if findings:
            try:
                findings[0].severity = "low"
                assert False, "Findings should be frozen"
            except AttributeError:
                pass

    def test_findings_have_source_rule(self):
        findings = self.classifier.classify("act now on ENTITY_A", DEFAULT_RULESET)
        for f in findings:
            assert f.source_rule, f"Finding missing source_rule: {f}"

    def test_invalid_regex_produces_anomaly(self):
        bad_rule = Rule("bad.001", "quality", "test", "low", r"[invalid", "bad regex")
        rs = RuleSet.create(version="test", rules=(bad_rule,))
        findings = self.classifier.classify("any text", rs)
        assert len(findings) == 1
        assert findings[0].finding_type == "anomaly"

    def test_classify_by_category(self):
        text = 'act now on ENTITY_A, password = "secret123"'
        compliance_only = self.classifier.classify_by_category(
            text, DEFAULT_RULESET, "compliance"
        )
        all_findings = self.classifier.classify(text, DEFAULT_RULESET)
        # compliance-only should have fewer than all categories combined
        assert len(compliance_only) <= len(all_findings)
        assert all(f.category == "compliance" for f in compliance_only)


# =============================================================================
# ASTClassifier Tests
# =============================================================================

class TestASTClassifier:
    """Test AST-based structural analysis."""

    def setup_method(self):
        self.classifier = ASTClassifier()

    def test_eval_detected(self):
        code = "result = eval('2 + 2')"
        findings = self.classifier.classify(code)
        assert len(findings) >= 1
        assert any(f.severity == "critical" for f in findings)

    def test_exec_detected(self):
        code = "exec('import os')"
        findings = self.classifier.classify(code)
        assert len(findings) >= 1
        assert any("exec" in f.message for f in findings)

    def test_global_mutation(self):
        code = """
def bad_function():
    global shared
    shared = 42
"""
        findings = self.classifier.classify(code)
        assert any("global" in f.message.lower() for f in findings)

    def test_excessive_args(self):
        code = "def big(a, b, c, d, e, f, g, h): pass"
        findings = self.classifier.classify(code)
        assert any("argument" in f.message.lower() for f in findings)

    def test_clean_code_no_findings(self):
        code = """
def add(a, b):
    return a + b

result = add(1, 2)
"""
        findings = self.classifier.classify(code)
        assert len(findings) == 0

    def test_syntax_error_handled(self):
        code = "def broken(:"
        findings = self.classifier.classify(code)
        assert len(findings) == 1
        assert findings[0].finding_type == "anomaly"


# =============================================================================
# classify_text convenience function
# =============================================================================

class TestClassifyText:
    """Test the one-shot convenience function."""

    def test_clean(self):
        assert len(classify_text("normal text here")) == 0

    def test_violation(self):
        assert len(classify_text("buy now guaranteed returns")) >= 1


# =============================================================================
# VerdictEngine Tests
# =============================================================================

class TestVerdictEngine:
    """Test verdict rendering logic."""

    def setup_method(self):
        self.engine = VerdictEngine()
        self.classifier = PatternClassifier()

    def test_blessed_verdict_for_clean_text(self):
        findings = self.classifier.classify("clean text", DEFAULT_RULESET)
        verdict = self.engine.render(findings, DEFAULT_RULESET)
        assert verdict.status == "blessed"
        assert verdict.is_blocking is False

    def test_heretical_verdict_for_violations(self):
        findings = self.classifier.classify(
            "buy now, guaranteed, can't lose, risk-free",
            DEFAULT_RULESET,
        )
        verdict = self.engine.render(findings, DEFAULT_RULESET)
        assert verdict.status == "heretical"
        assert verdict.is_blocking is True

    def test_verdict_has_ruleset_version(self):
        findings = ()
        verdict = self.engine.render(findings, DEFAULT_RULESET)
        assert "v1.0" in verdict.ruleset_version

    def test_verdict_confidence_range(self):
        for text in ("clean text", "buy now guaranteed"):
            findings = self.classifier.classify(text, DEFAULT_RULESET)
            verdict = self.engine.render(findings, DEFAULT_RULESET)
            assert 0.0 <= verdict.confidence <= 1.0

    def test_custom_weights(self):
        weights = ScoringWeights(
            critical=0.50,  # Harsher on critical
            high=0.25,
            medium=0.10,
            low=0.05,
        )
        engine = VerdictEngine(weights=weights)
        # Even a medium finding hits harder
        finding = Finding(
            finding_id="test",
            finding_type="warning",
            severity="medium",
            category="quality",
            message="test warning",
            source_rule="test.001",
        )
        verdict = engine.render((finding,), DEFAULT_RULESET)
        assert verdict.status in ("blessed", "purified")  # medium not critical


# =============================================================================
# LogDecision Tests
# =============================================================================

class TestLogDecision:
    """Test logging decision logic."""

    def setup_method(self):
        self.engine = VerdictEngine()

    def test_heretical_logs_critical(self):
        verdict = Verdict.heretical(
            findings=(),
            explanation="Test heretical verdict",
            confidence=0.9,
            ruleset_version="test",
        )
        ld = self.engine.decide_logging(verdict)
        assert ld.should_log is True
        assert ld.severity == "critical"
        assert ld.retention == "permanent"

    def test_blessed_clean_skips_log(self):
        verdict = Verdict.blessed(
            findings=(),
            confidence=0.9,
            explanation="Clean output",
            ruleset_version="test",
        )
        ld = self.engine.decide_logging(verdict)
        assert ld.should_log is False

    def test_purified_logs_standard(self):
        finding = Finding(
            finding_id="f1",
            finding_type="warning",
            severity="medium",
            category="quality",
            message="test",
            source_rule="test.001",
        )
        verdict = Verdict.purified(
            findings=(finding,),
            confidence=0.8,
            explanation="Purified with warnings",
            ruleset_version="test",
        )
        ld = self.engine.decide_logging(verdict)
        assert ld.should_log is True
        assert ld.severity in ("medium", "high")


# =============================================================================
# Workflow Tests
# =============================================================================

class TestWorkflows:
    """Test declarative workflow definitions."""

    def test_full_audit_valid(self):
        errors = FULL_AUDIT_WORKFLOW.validate()
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_quick_validation_valid(self):
        errors = QUICK_VALIDATION_WORKFLOW.validate()
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_full_audit_steps(self):
        assert FULL_AUDIT_WORKFLOW.step_count == 7
        assert FULL_AUDIT_WORKFLOW.entry_step == "intake"

    def test_quick_validation_steps(self):
        assert QUICK_VALIDATION_WORKFLOW.step_count == 3
        assert QUICK_VALIDATION_WORKFLOW.entry_step == "classify"

    def test_workflow_frozen(self):
        try:
            FULL_AUDIT_WORKFLOW.version = "hacked"
            assert False, "Should be frozen"
        except AttributeError:
            pass

    def test_available_workflows_registry(self):
        assert len(AVAILABLE_WORKFLOWS) == 2
        assert "orthodoxy.full_audit" in AVAILABLE_WORKFLOWS
        assert "orthodoxy.quick_validation" in AVAILABLE_WORKFLOWS

    def test_get_step(self):
        step = FULL_AUDIT_WORKFLOW.get_step("judge")
        assert step is not None
        assert step.role == "verdict_engine"

    def test_invalid_workflow_detected(self):
        bad_wf = Workflow(
            workflow_id="broken",
            version="v0.1",
            description="broken",
            entry_step="nonexistent",
            steps=(
                WorkflowStep("step1", "role", "desc", next_step="also_nonexistent"),
            ),
        )
        errors = bad_wf.validate()
        assert len(errors) >= 2  # entry step + next_step both invalid


# =============================================================================
# Integration: Full Pipeline
# =============================================================================

class TestFullPipeline:
    """End-to-end pipeline: Confession → Classify → Verdict → LogDecision."""

    def test_heretical_pipeline(self):
        # Step 1: Confession
        now = datetime.now(timezone.utc)
        confession = Confession(
            confession_id=f"confession_{now.strftime('%Y%m%d_%H%M%S')}",
            trigger_type="output_validation",
            scope="single_output",
            urgency="high",
            source="test",
            timestamp=now.isoformat(),
        )

        # Step 2: Classify
        classifier = PatternClassifier()
        findings = classifier.classify(
            "You must buy now — guaranteed returns, can't lose!",
            DEFAULT_RULESET,
        )
        assert len(findings) >= 2

        # Step 3: Verdict
        engine = VerdictEngine()
        verdict = engine.render(findings, DEFAULT_RULESET, confession.confession_id)
        assert verdict.status == "heretical"

        # Step 4: LogDecision
        ld = engine.decide_logging(verdict)
        assert ld.should_log is True
        assert ld.severity == "critical"

    def test_blessed_pipeline(self):
        now = datetime.now(timezone.utc)
        confession = Confession(
            confession_id=f"confession_{now.strftime('%Y%m%d_%H%M%S')}_b",
            trigger_type="scheduled",
            scope="single_output",
            urgency="routine",
            source="test",
            timestamp=now.isoformat(),
        )

        classifier = PatternClassifier()
        findings = classifier.classify(
            "ENTITY_A shows moderate positive signal with score at 58",
            DEFAULT_RULESET,
        )
        assert len(findings) == 0

        engine = VerdictEngine()
        verdict = engine.render(findings, DEFAULT_RULESET, confession.confession_id)
        assert verdict.status == "blessed"

        ld = engine.decide_logging(verdict)
        assert ld.should_log is False


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    print("Running governance engine tests...\n")

    test_classes = [
        TestRule, TestRuleSet, TestDefaultRuleSet,
        TestPatternClassifier, TestASTClassifier, TestClassifyText,
        TestVerdictEngine, TestLogDecision,
        TestWorkflows, TestFullPipeline,
    ]

    passed = 0
    failed = 0

    for cls in test_classes:
        instance = cls()
        if hasattr(instance, "setup_method"):
            instance.setup_method()

        for name in dir(instance):
            if name.startswith("test_"):
                try:
                    getattr(instance, name)()
                    passed += 1
                    print(f"  ✅ {cls.__name__}.{name}")
                except Exception as e:
                    failed += 1
                    print(f"  ❌ {cls.__name__}.{name}: {e}")

    print(f"\n{'='*50}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")

    if failed > 0:
        sys.exit(1)
