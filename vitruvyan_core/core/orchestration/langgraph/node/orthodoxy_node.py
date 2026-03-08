"""
Orthodoxy Node — Epistemic Gate for LangGraph
Integrates Orthodoxy Wardens LIVELLO 1 consumers directly into the graph.

Gate Levels (progressive):
  1. Informativo (current): Verdict computed in-process, written to state as
     metadata. Response NEVER blocked. Allows observing tribunal decisions
     on real traffic with zero risk.
  2. Soft (future): heretical → disclaimer appended, non_liquet → uncertainty
     admission. Response still sent but annotated.
  3. Hard (future): heretical → response replaced with refusal. purified →
     corrected version substituted.

Architecture:
  - LIVELLO 1 consumers (Confessor, Inquisitor, VerdictEngine) are pure Python,
    no I/O, imported directly. Total latency: ~7-17ms.
  - Async fire-and-forget on bus REMAINS for audit trail (complementary).
  - _apply_local_blessing() removed — replaced by real tribunal verdict.

Author: Vitruvyan Development Team
Created: 2025-10-18
Refactored: 2026-03-07 (Gate informativo — Phase A)
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

from core.synaptic_conclave.transport.streams import get_stream_bus

# LIVELLO 1 imports — pure Python, no I/O, no infrastructure
from core.governance.orthodoxy_wardens.consumers.confessor import Confessor
from core.governance.orthodoxy_wardens.consumers.inquisitor import Inquisitor
from core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine
from core.governance.orthodoxy_wardens.governance.rule import DEFAULT_RULESET

logger = logging.getLogger(__name__)

# Singleton instances — stateless, thread-safe (pure functions inside)
_confessor = Confessor()
_inquisitor = Inquisitor()
_verdict_engine = VerdictEngine()

def orthodoxy_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orthodoxy Gate (informativo) — in-process tribunal verdict.

    Runs Confessor → Inquisitor → VerdictEngine synchronously (~7-17ms).
    Writes verdict to state as metadata. Response is NEVER blocked at this level.
    Also emits async audit event for downstream consumers (Vault, Conclave).

    Args:
        state: LangGraph state dictionary

    Returns:
        State augmented with real tribunal verdict
    """
    try:
        user_id = state.get("user_id", "anonymous")
        session_start = time.time()

        logger.info(f"[ORTHODOXY][GATE] Tribunal initiated for {user_id}")

        # --- STEP 1: Run in-process tribunal (LIVELLO 1, pure Python) ---
        verdict = _run_tribunal(state)
        state = _apply_verdict_to_state(state, verdict, session_start)

        # --- STEP 2: Emit async audit (complementary, non-blocking) ---
        _emit_audit_event(state, user_id, session_start, verdict)

        # --- STEP 3: Record outcome for Plasticity (non-blocking) ---
        _record_plasticity_outcome(state, verdict)

        execution_ms = (time.time() - session_start) * 1000
        logger.info(
            f"[ORTHODOXY][GATE] Verdict: {verdict.status} "
            f"(confidence={verdict.confidence:.2f}, "
            f"findings={len(verdict.findings)}) in {execution_ms:.1f}ms"
        )

        return state

    except Exception as e:
        logger.error(f"[ORTHODOXY][GATE] Tribunal failed: {e}", exc_info=True)
        return _apply_fallback(state, f"error: {str(e)[:80]}")


def _run_tribunal(state: Dict[str, Any]):
    """
    Run the 3-stage tribunal pipeline in-process.
    Pure Python, no I/O, ~7-17ms total.

    Returns:
        Verdict (frozen dataclass)
    """
    # 1. Confessor: intake → Confession
    confession = _confessor.process({
        "trigger_type": "output_validation",
        "scope": "single_output",
        "urgency": "high",
        "source": "langgraph.orthodoxy_node",
        "correlation_id": state.get("trace_id"),
    })

    # 2. Inquisitor: examine text + code → Findings
    text_to_examine = _build_examination_text(state)
    result = _inquisitor.process({
        "confession": confession,
        "text": text_to_examine,
    })

    # 3. VerdictEngine: findings → Verdict
    verdict = _verdict_engine.render(
        findings=result.findings,
        ruleset=DEFAULT_RULESET,
        confession_id=confession.confession_id,
    )

    return verdict


def _build_examination_text(state: Dict[str, Any]) -> str:
    """Build the text the Inquisitor will examine."""
    parts = []

    response = state.get("response")
    if response:
        parts.append(str(response)[:2000])

    narrative = state.get("narrative")
    if narrative and narrative != response:
        parts.append(str(narrative)[:1000])

    input_text = state.get("input_text")
    if input_text:
        parts.append(str(input_text)[:500])

    return "\n---\n".join(parts) if parts else ""


def _apply_verdict_to_state(
    state: Dict[str, Any], verdict, session_start: float
) -> Dict[str, Any]:
    """
    Write real tribunal verdict into LangGraph state.
    Gate informativo: metadata only, response never modified.
    """
    state["orthodoxy_verdict"] = verdict.status
    state["orthodoxy_findings"] = len(verdict.findings)
    state["orthodoxy_confidence"] = verdict.confidence
    state["orthodoxy_should_send"] = verdict.should_send
    state["orthodoxy_explanation"] = verdict.explanation
    state["orthodoxy_status"] = verdict.status
    state["orthodoxy_message"] = verdict.explanation
    state["orthodoxy_timestamp"] = datetime.now(timezone.utc).isoformat()
    state["orthodoxy_duration_ms"] = (time.time() - session_start) * 1000
    state["orthodoxy_ruleset_version"] = verdict.ruleset_version

    # Non-liquet specific metadata (epistemic humility)
    if verdict.status == "non_liquet":
        state["orthodoxy_what_we_know"] = verdict.what_we_know
        state["orthodoxy_what_is_uncertain"] = verdict.what_is_uncertain

    state["theological_metadata"] = {
        "sacred_order": "orthodoxy_wardens",
        "audit_cycle": "gate_informativo",
        "gate_level": "informativo",
        "divine_oversight": True,
        "cognitive_integration": True,
        "verdict_real": True,
    }

    return state


def _emit_audit_event(
    state: Dict[str, Any], user_id: str, session_start: float, verdict
) -> None:
    """Emit async audit event for downstream (Vault, Conclave). Non-blocking."""
    try:
        correlation_id = f"graph_audit_{user_id}_{int(session_start)}"
        get_stream_bus().emit(
            channel="orthodoxy.audit.requested",
            payload={
                "source": "langgraph_orthodoxy_node",
                "session_id": user_id,
                "audit_type": "graph_response_validation",
                "verdict_status": verdict.status,
                "verdict_confidence": verdict.confidence,
                "verdict_findings_count": len(verdict.findings),
                "gate_level": "informativo",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": correlation_id,
            },
            emitter="langgraph_orthodoxy_node",
            correlation_id=correlation_id,
        )
    except Exception as e:
        logger.warning(f"[ORTHODOXY][GATE] Audit emit failed (non-fatal): {e}")


def _record_plasticity_outcome(state: Dict[str, Any], verdict) -> None:
    """Record verdict as Plasticity outcome. Non-blocking, fire-and-forget."""
    try:
        import asyncio
        from api_graph.adapters.plasticity_adapter import get_plasticity_service

        svc = get_plasticity_service()
        if svc is None:
            return

        trace_id = state.get("trace_id", f"gate_{id(state)}")
        coro = svc.record_verdict_outcome(
            trace_id=trace_id,
            verdict_status=verdict.status,
            confidence=verdict.confidence,
            findings_count=len(verdict.findings),
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            pass  # No event loop — skip (pure test context)
    except Exception as e:
        logger.debug(f"[ORTHODOXY][GATE] Plasticity outcome skipped: {e}")


def _apply_fallback(state: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Fallback when tribunal itself fails. Should be extremely rare."""
    logger.warning(f"[ORTHODOXY][GATE] Applying fallback: {reason}")

    state["orthodoxy_verdict"] = "fallback"
    state["orthodoxy_findings"] = 0
    state["orthodoxy_confidence"] = 0.0
    state["orthodoxy_should_send"] = True
    state["orthodoxy_explanation"] = f"Tribunal fallback: {reason}"
    state["orthodoxy_status"] = "fallback"
    state["orthodoxy_message"] = f"Tribunal unavailable: {reason}"
    state["orthodoxy_timestamp"] = datetime.now(timezone.utc).isoformat()
    state["orthodoxy_fallback_reason"] = reason
    state["theological_metadata"] = {
        "sacred_order": "orthodoxy_wardens",
        "audit_cycle": "fallback",
        "gate_level": "fallback",
        "divine_oversight": False,
        "cognitive_integration": False,
    }
    return state


def _get_orthodoxy_summary(state: Dict[str, Any]) -> str:
    """
    Get a summary of orthodoxy status for logging
    
    Args:
        state: LangGraph state with orthodoxy information
        
    Returns:
        Human-readable orthodoxy summary
    """
    
    status = state.get("orthodoxy_status", "unknown")
    findings = state.get("orthodoxy_findings", 0)
    confidence = state.get("orthodoxy_confidence", 0.0)
    
    return f"Status: {status}, Findings: {findings}, Confidence: {confidence:.2f}"