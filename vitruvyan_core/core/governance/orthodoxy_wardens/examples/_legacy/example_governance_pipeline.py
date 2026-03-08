"""
Example: Full Governance Engine Pipeline

Demonstrates the complete FASE 2 pipeline:
  Confession → RuleSet → Classifier → Findings → VerdictEngine → Verdict → LogDecision

Run: python -m vitruvyan_core.core.governance.orthodoxy_wardens.examples.example_governance_pipeline
Or:  cd vitruvyan_core && python -c "exec(open('core/governance/orthodoxy_wardens/examples/example_governance_pipeline.py').read())"
"""

import sys
import os
import uuid
from datetime import datetime, timezone

# Add project root to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from vitruvyan_core.core.governance.orthodoxy_wardens.domain import (
    Confession,
    Finding,
    Verdict,
    LogDecision,
)
from vitruvyan_core.core.governance.orthodoxy_wardens.governance import (
    Rule,
    RuleSet,
    DEFAULT_RULESET,
    PatternClassifier,
    ASTClassifier,
    VerdictEngine,
    FULL_AUDIT_WORKFLOW,
    QUICK_VALIDATION_WORKFLOW,
)


def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# =============================================================================
# 1. Inspect the Default RuleSet
# =============================================================================
separator("1. DEFAULT RULESET")

print(f"Version:     {DEFAULT_RULESET.version}")
print(f"Checksum:    {DEFAULT_RULESET.checksum}")
print(f"Total rules: {DEFAULT_RULESET.rule_count}")
print(f"Active:      {DEFAULT_RULESET.active_count}")
print(f"Version tag: {DEFAULT_RULESET.version_tag}")
print()

# Show rules by category
for cat in ("compliance", "security", "performance", "quality", "hallucination"):
    rules = DEFAULT_RULESET.rules_by_category(cat)
    print(f"  {cat:15s}: {len(rules)} rules")


# =============================================================================
# 2. Classify Clean Text (should produce no findings)
# =============================================================================
separator("2. CLASSIFY — Clean text")

clean_text = "ENTITY_A shows strong positive signal with score at 65. The trend is moderately positive."
classifier = PatternClassifier()
findings = classifier.classify(clean_text, DEFAULT_RULESET)

print(f"Text:     {clean_text!r}")
print(f"Findings: {len(findings)}")
assert len(findings) == 0, "Clean text should produce no findings"
print("✅ No findings — text is clean")


# =============================================================================
# 3. Classify Problematic Text (compliance violations)
# =============================================================================
separator("3. CLASSIFY — Compliance violations")

bad_text = "You should act now on ENTITY_A — guaranteed returns, this entity can't lose! api_key='sk-1234'"
findings = classifier.classify(bad_text, DEFAULT_RULESET)

print(f"Text:     {bad_text!r}")
print(f"Findings: {len(findings)}")
for f in findings:
    print(f"  [{f.severity:8s}] [{f.category:12s}] {f.message}")
print()

# Verify we got the expected violations
assert len(findings) >= 3, f"Expected >=3 findings, got {len(findings)}"
severities = [f.severity for f in findings]
assert "critical" in severities, "Should have at least one critical finding"
print(f"✅ {len(findings)} findings detected, including critical violations")


# =============================================================================
# 4. Render Verdict — Heretical
# =============================================================================
separator("4. VERDICT — Heretical content")

engine = VerdictEngine()
verdict = engine.render(findings, DEFAULT_RULESET)

print(f"Status:      {verdict.status}")
print(f"Confidence:  {verdict.confidence:.2f}")
print(f"Is blocking: {verdict.is_blocking}")
print(f"Should send: {verdict.should_send}")
print(f"RuleSet ver: {verdict.ruleset_version}")
print(f"Findings:    {len(verdict.findings)}")
print(f"Critical:    {verdict.critical_count}")
print()

assert verdict.status == "heretical", f"Expected heretical, got {verdict.status}"
assert verdict.is_blocking is True
print("✅ Verdict is HERETICAL — content blocked")


# =============================================================================
# 5. Render Verdict — Blessed (clean text)
# =============================================================================
separator("5. VERDICT — Clean content")

clean_findings = classifier.classify(clean_text, DEFAULT_RULESET)
clean_verdict = engine.render(clean_findings, DEFAULT_RULESET)

print(f"Status:      {clean_verdict.status}")
print(f"Confidence:  {clean_verdict.confidence:.2f}")
print(f"Is blocking: {clean_verdict.is_blocking}")
print(f"Findings:    {len(clean_verdict.findings)}")
print()

assert clean_verdict.status == "blessed"
assert clean_verdict.is_blocking is False
print("✅ Verdict is BLESSED — content approved")


# =============================================================================
# 6. LogDecision — Critical audit vs Skip
# =============================================================================
separator("6. LOG DECISIONS")

log_heretical = engine.decide_logging(verdict)
log_blessed = engine.decide_logging(clean_verdict)

print("Heretical verdict logging:")
print(f"  Should log:  {log_heretical.should_log}")
print(f"  Severity:    {log_heretical.severity}")
print(f"  Retention:   {log_heretical.retention}")
print(f"  Category:    {log_heretical.category}")
print(f"  Reason:      {log_heretical.reason}")
print()

print("Blessed verdict logging:")
print(f"  Should log:  {log_blessed.should_log}")
print(f"  Severity:    {log_blessed.severity}")
print(f"  Reason:      {log_blessed.reason}")
print()

assert log_heretical.should_log is True
assert log_heretical.severity == "critical"
assert log_blessed.should_log is False
print("✅ Logging decisions correct")


# =============================================================================
# 7. AST Classifier (Python code analysis)
# =============================================================================
separator("7. AST CLASSIFIER — Python code")

bad_code = '''
import os

password = "super_secret_123"

def complex_function(a, b, c, d, e, f, g, h):
    global shared_state
    shared_state = a + b
    
    if a > 0:
        for i in range(10):
            if b > 0:
                while True:
                    if c > 0:
                        eval("print('danger')")
                        break

os.system("rm -rf " + user_input)
'''

ast_classifier = ASTClassifier()
ast_findings = ast_classifier.classify(bad_code)

print(f"Code findings: {len(ast_findings)}")
for f in ast_findings:
    print(f"  [{f.severity:8s}] {f.message}")
print()

assert len(ast_findings) >= 3, f"Expected >=3 AST findings, got {len(ast_findings)}"
print(f"✅ {len(ast_findings)} structural issues detected via AST analysis")

# Combine AST + Pattern findings for final verdict
pattern_findings = classifier.classify(bad_code, DEFAULT_RULESET)
all_findings = pattern_findings + ast_findings

combined_verdict = engine.render(all_findings, DEFAULT_RULESET)
print(f"\nCombined verdict: {combined_verdict.status} "
      f"(confidence: {combined_verdict.confidence:.2f}, "
      f"findings: {len(combined_verdict.findings)})")


# =============================================================================
# 8. Full Pipeline: Confession → Verdict
# =============================================================================
separator("8. FULL PIPELINE: Confession → Classify → Verdict → LogDecision")

# Step 1: Create a Confession (audit request)
confession = Confession(
    confession_id=f"confession_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
    trigger_type="output_validation",
    scope="single_output",
    urgency="high",
    source="can_node",
    timestamp=datetime.now(timezone.utc).isoformat(),
    metadata=(
        ("entity_id", "ENTITY_A"),
        ("user_id", "test_user"),
        ("query", "should I act on ENTITY_A?"),
    ),
)
print(f"Step 1 — Confession: {confession.confession_id} ({confession.trigger_type})")

# Step 2: Classify the LLM output
llm_output = "Based on my analysis, you should definitely act on ENTITY_A. It's guaranteed to rise."
findings = classifier.classify(llm_output, DEFAULT_RULESET)
print(f"Step 2 — Classify:   {len(findings)} finding(s)")

# Step 3: Render verdict
verdict = engine.render(findings, DEFAULT_RULESET, confession_id=confession.confession_id)
print(f"Step 3 — Verdict:    {verdict.status} (conf: {verdict.confidence:.2f})")

# Step 4: Decide logging
log_decision = engine.decide_logging(verdict)
print(f"Step 4 — LogDecision: log={log_decision.should_log}, sev={log_decision.severity}")
print()

assert verdict.status == "heretical"
assert log_decision.should_log is True
print("✅ Complete pipeline: Confession → Classify → Heretical Verdict → Critical Log")


# =============================================================================
# 9. Inspect Workflows
# =============================================================================
separator("9. DECLARATIVE WORKFLOWS")

for wf in (FULL_AUDIT_WORKFLOW, QUICK_VALIDATION_WORKFLOW):
    print(f"\n  Workflow: {wf.workflow_id} ({wf.version})")
    print(f"  Steps:    {wf.step_count}")
    print(f"  Entry:    {wf.entry_step}")
    errors = wf.validate()
    print(f"  Valid:    {'✅ Yes' if not errors else '❌ ' + str(errors)}")
    for step in wf.steps:
        arrow = "→" if step.next_step else "⊣"
        cond = f" [conditional: {len(step.conditional)} routes]" if step.conditional else ""
        print(f"    {arrow} {step.name:20s} role={step.role:15s}{cond}")


# =============================================================================
# Summary
# =============================================================================
separator("SUMMARY")
print("""
FASE 2 Governance Engine — All components verified:

  ✅ Rule + RuleSet:       35 rules, frozen, versioned, checksum'd
  ✅ PatternClassifier:    Regex matching → Finding[]
  ✅ ASTClassifier:        Python AST analysis → Finding[]
  ✅ VerdictEngine:        Finding[] → Verdict (status + confidence)
  ✅ LogDecision:          Verdict → should_log/severity/retention
  ✅ Workflows:            2 declarative pipelines (full_audit, quick_validation)
  ✅ Full Pipeline:        Confession → Classify → Verdict → LogDecision

The judge is never the executioner. — philosophy/charter.md
""")
