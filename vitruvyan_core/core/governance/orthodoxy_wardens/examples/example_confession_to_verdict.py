"""
Orthodoxy Wardens — Example: Confession to Verdict Pipeline

Demonstrates the complete domain flow:
  Confession → Findings → Verdict

Run standalone: python -m examples.example_confession_to_verdict
Requires: NO infrastructure (no Redis, no PostgreSQL, no Docker)

Sacred Order: Truth & Governance
Layer: Foundational (examples)
"""

import sys
import os

# Add vitruvyan_core to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from core.governance.orthodoxy_wardens.domain.confession import Confession
from core.governance.orthodoxy_wardens.domain.finding import Finding
from core.governance.orthodoxy_wardens.domain.verdict import Verdict
from core.governance.orthodoxy_wardens.domain.log_decision import LogDecision


def main():
    print("=" * 60)
    print("Orthodoxy Wardens — Confession to Verdict Pipeline")
    print("=" * 60)

    # ─────────────────────────────────────────────────────────────
    # 1. Confession: an LLM output needs validation before delivery
    # ─────────────────────────────────────────────────────────────
    confession = Confession(
        confession_id="confession_20260209_143000",
        trigger_type="output_validation",
        scope="single_output",
        urgency="critical",
        source="langgraph.compose_node",
        timestamp="2026-02-09T14:30:00Z",
        correlation_id="req_abc123",
        metadata=(
            ("ticker", "AAPL"),
            ("query", "analyze AAPL momentum"),
            ("model", "gpt-4o-mini"),
        ),
    )
    print(f"\n1. Confession received: {confession.confession_id}")
    print(f"   Trigger: {confession.trigger_type}, Urgency: {confession.urgency}")

    # ─────────────────────────────────────────────────────────────
    # 2. Examination: the Inquisitor checks rules, finds issues
    # ─────────────────────────────────────────────────────────────
    findings = (
        Finding(
            finding_id="finding_20260209_143001_001",
            finding_type="blessing",
            severity="low",
            category="compliance",
            message="No forward-looking claims detected",
            source_rule="rule_no_predictions_v2",
        ),
        Finding(
            finding_id="finding_20260209_143001_002",
            finding_type="warning",
            severity="medium",
            category="data_quality",
            message="Momentum z-score based on 12 data points (minimum 20 recommended)",
            source_rule="rule_min_data_points_v1",
            context=(("data_points", 12), ("minimum", 20)),
        ),
    )
    for f in findings:
        print(f"\n2. Finding: [{f.severity}] {f.finding_type} — {f.message}")

    # ─────────────────────────────────────────────────────────────
    # 3. Verdict: the Abbot aggregates findings into final judgment
    # ─────────────────────────────────────────────────────────────
    # Case A: Blessed (all good)
    verdict_blessed = Verdict.blessed(
        confidence=0.92,
        findings=findings,
        explanation="Output passed compliance (1 blessing, 1 non-critical warning)",
        ruleset_version="ruleset_v2.3_sha256_a1b2c3",
    )
    print(f"\n3a. Verdict: {verdict_blessed.status} (confidence: {verdict_blessed.confidence})")
    print(f"    Send to user: {verdict_blessed.should_send}")
    print(f"    Blocking: {verdict_blessed.is_blocking}")

    # Case B: Heretical (hallucination detected)
    hallucination_finding = Finding(
        finding_id="finding_20260209_143002_001",
        finding_type="violation",
        severity="critical",
        category="hallucination",
        message="LLM claimed AAPL revenue of $10 trillion (actual: $383B)",
        source_rule="rule_numeric_bounds_v1",
        context=(("claimed", "10T"), ("actual", "383B")),
    )
    verdict_heretical = Verdict.heretical(
        findings=(hallucination_finding,),
        explanation="BLOCKED: Numeric hallucination detected in revenue figure",
    )
    print(f"\n3b. Verdict: {verdict_heretical.status} (confidence: {verdict_heretical.confidence})")
    print(f"    Send to user: {verdict_heretical.should_send}")
    print(f"    Blocking: {verdict_heretical.is_blocking}")
    print(f"    Critical findings: {verdict_heretical.critical_count}")

    # Case C: Non liquet (uncertain)
    verdict_non_liquet = Verdict.non_liquet(
        confidence=0.35,
        what_we_know=("AAPL momentum z-score is 0.86", "Based on 12 data points"),
        what_is_uncertain=("Whether 12 points is statistically significant",),
        uncertainty_sources=("Insufficient data for z-score normalization",),
        best_guess="Momentum appears positive but confidence is low",
    )
    print(f"\n3c. Verdict: {verdict_non_liquet.status} (confidence: {verdict_non_liquet.confidence})")
    print(f"    Send to user: {verdict_non_liquet.should_send} (with uncertainty caveat)")
    print(f"    What we know: {verdict_non_liquet.what_we_know}")
    print(f"    What is uncertain: {verdict_non_liquet.what_is_uncertain}")

    # ─────────────────────────────────────────────────────────────
    # 4. LogDecision: the Chronicler decides what to remember
    # ─────────────────────────────────────────────────────────────
    log_heresy = LogDecision.critical_audit(
        category="hallucination_blocked",
        reason="Heretical verdict on numeric hallucination — permanent audit record",
    )
    log_routine = LogDecision.standard(
        category="routine_validation",
        reason="Blessed verdict on standard momentum query",
    )
    log_skip = LogDecision.skip(
        reason="Duplicate confession within 5-second window",
    )
    print(f"\n4. LogDecisions:")
    print(f"   Heresy:  log={log_heresy.should_log}, retention={log_heresy.retention}")
    print(f"   Routine: log={log_routine.should_log}, retention={log_routine.retention}")
    print(f"   Skip:    log={log_skip.should_log}, reason='{log_skip.reason}'")

    # ─────────────────────────────────────────────────────────────
    # 5. Immutability proof
    # ─────────────────────────────────────────────────────────────
    print("\n5. Immutability proof:")
    try:
        verdict_blessed.status = "heretical"  # type: ignore
        print("   ERROR: Mutation should have failed!")
    except AttributeError:
        print("   ✅ Verdict is frozen — cannot mutate after creation")

    try:
        confession.urgency = "low"  # type: ignore
        print("   ERROR: Mutation should have failed!")
    except AttributeError:
        print("   ✅ Confession is frozen — cannot mutate after creation")

    print("\n" + "=" * 60)
    print("Pipeline complete. All domain objects working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
