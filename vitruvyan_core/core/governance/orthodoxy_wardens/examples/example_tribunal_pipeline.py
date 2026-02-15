"""
Example: Full Tribunal Pipeline (FASE 3)

Demonstrates the complete Orthodoxy Wardens judgment chain:
  Raw Event → Confessor → Inquisitor → VerdictEngine → Penitent → Chronicler

Every step is pure, deterministic, and side-effect free.
The service layer would wrap this in StreamBus adapters for production.
"""

from vitruvyan_core.core.governance.orthodoxy_wardens.consumers import (
    Confessor,
    Inquisitor,
    Penitent,
    Chronicler,
)
from vitruvyan_core.core.governance.orthodoxy_wardens.governance import (
    VerdictEngine,
    DEFAULT_RULESET,
)
from vitruvyan_core.core.governance.orthodoxy_wardens.events.orthodoxy_events import (
    OrthodoxyEvent,
)
from datetime import datetime, timezone


def run_tribunal_pipeline():
    """Run a complete tribunal judgment pipeline."""

    print("=" * 70)
    print("ORTHODOXY WARDENS — FULL TRIBUNAL PIPELINE")
    print("=" * 70)

    # --- Step 0: Create roles ---
    confessor = Confessor()
    inquisitor = Inquisitor()
    verdict_engine = VerdictEngine()
    penitent = Penitent()
    chronicler = Chronicler()

    print(f"\n📋 Tribunal assembled:")
    print(f"   {confessor}")
    print(f"   {inquisitor}")
    print(f"   {penitent}")
    print(f"   {chronicler}")

    # --- Step 1: Raw event arrives ---
    raw_event = OrthodoxyEvent(
        event_type="langgraph.output.ready",
        payload=(
            ("entity_id", "ENTITY_A"),
            ("output_text", "Act now on ENTITY_A! Guaranteed 500% returns!"),
            ("source_node", "compose_node"),
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="langgraph.compose",
    )
    print(f"\n📨 Raw event: {raw_event.event_type}")
    print(f"   Payload: {dict(raw_event.payload)}")

    # --- Step 2: Confessor intake ---
    assert confessor.can_handle(raw_event), "Confessor should handle OrthodoxyEvent"
    confession = confessor.process(raw_event)
    print(f"\n📝 Confession created:")
    print(f"   ID: {confession.confession_id}")
    print(f"   Trigger: {confession.trigger_type}")
    print(f"   Scope: {confession.scope}")
    print(f"   Urgency: {confession.urgency}")

    # --- Step 3: Inquisitor examination ---
    examination_input = {
        "confession": confession,
        "text": "Act now on ENTITY_A! Guaranteed 500% returns! This is a sure thing, no risk at all.",
        "code": None,
    }
    assert inquisitor.can_handle(examination_input), "Inquisitor should handle dict"
    result = inquisitor.process(examination_input)
    print(f"\n🔍 Inquisitor result:")
    print(f"   {result}")
    print(f"   Text examined: {result.text_examined}")
    print(f"   Violations: {len(result.violations)}")
    print(f"   Warnings: {len(result.warnings)}")
    for i, f in enumerate(result.findings, 1):
        print(f"   [{i}] {f.severity}/{f.category}: {f.message[:60]}...")

    # --- Step 4: VerdictEngine renders judgment ---
    verdict = verdict_engine.render(
        findings=result.findings,
        ruleset=DEFAULT_RULESET,
        confession_id=confession.confession_id,
    )
    print(f"\n⚖️  Verdict rendered:")
    print(f"   Status: {verdict.status}")
    print(f"   Confidence: {verdict.confidence}")
    print(f"   Explanation: {verdict.explanation[:80]}...")
    print(f"   Blocking: {verdict.is_blocking}")

    # --- Step 5: Penitent advises corrections ---
    assert penitent.can_handle(verdict), "Penitent should handle Verdict"
    plan = penitent.process(verdict)
    print(f"\n🔧 Correction plan:")
    print(f"   {plan}")
    for i, req in enumerate(plan.requests, 1):
        print(f"   [{i}] {req.strategy} ({req.priority}) → {req.description[:50]}...")
    print(f"   Requires human: {plan.requires_human}")

    # --- Step 6: Chronicler decides logging strategy ---
    assert chronicler.can_handle(verdict), "Chronicler should handle Verdict"
    chronicle = chronicler.process(verdict)
    print(f"\n📖 Chronicle decision:")
    print(f"   {chronicle}")
    print(f"   Should log: {chronicle.should_log}")
    print(f"   Destinations: {chronicle.destinations}")
    print(f"   Requires blockchain: {chronicle.requires_blockchain}")
    for directive in chronicle.directives:
        print(f"   → {directive}")

    print("\n" + "=" * 70)
    print("✅ Pipeline complete — all pure, no side effects, no I/O")
    print("=" * 70)

    return {
        "confession": confession,
        "findings": result,
        "verdict": verdict,
        "correction_plan": plan,
        "chronicle": chronicle,
    }


def run_blessed_pipeline():
    """Run pipeline with clean content → blessed verdict."""
    print("\n\n" + "=" * 70)
    print("BLESSED PIPELINE — Clean content")
    print("=" * 70)

    confessor = Confessor()
    inquisitor = Inquisitor()
    verdict_engine = VerdictEngine()
    penitent = Penitent()
    chronicler = Chronicler()

    # Clean event
    event = {
        "event_type": "engine.eval.completed",
        "source": "neural_engine",
        "metadata": {"entity_ids": ["ENTITY_A", "ENTITY_B"], "profile": "balanced_mid"},
    }

    confession = confessor.process(event)
    print(f"\n📝 Confession: {confession.confession_id}")

    result = inquisitor.process({
        "confession": confession,
        "text": "ENTITY_A shows strong positive signal with z-score 1.2 based on analysis.",
    })
    print(f"🔍 Findings: {result.finding_count}")

    verdict = verdict_engine.render(result.findings, DEFAULT_RULESET, confession.confession_id)
    print(f"⚖️  Verdict: {verdict.status} (confidence: {verdict.confidence})")

    plan = penitent.process(verdict)
    print(f"🔧 Corrections: {plan.total_requests}")

    chronicle = chronicler.process(verdict)
    print(f"📖 Log: {chronicle.should_log}, Destinations: {chronicle.destinations}")
    print(f"   Blockchain: {chronicle.requires_blockchain}")

    assert verdict.status == "blessed", f"Expected blessed, got {verdict.status}"
    assert plan.is_empty, "Blessed verdict should have no corrections"
    assert not chronicle.requires_blockchain, "Blessed should not require blockchain"

    print("\n✅ Blessed pipeline verified")


if __name__ == "__main__":
    run_tribunal_pipeline()
    run_blessed_pipeline()
