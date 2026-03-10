"""
⚖️ Orthodoxy Wardens — Bus Adapter (LIVELLO 2)

Bridges infrastructure events (StreamBus, HTTP) to pure domain consumers (LIVELLO 1).

Pipeline: Confessor → Inquisitor → VerdictEngine → Penitent → Chronicler

The adapter does NOT contain business logic. It:
1. Receives raw events (dict/JSON)
2. Feeds them through the pure consumer pipeline
3. Delegates persistence to PersistenceAdapter
4. Returns results as dicts

"Il giudice (core) non tocca mai il database. Il cancelliere (service) lo fa per lui."
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, Optional

from core.governance.orthodoxy_wardens.consumers.confessor import (
    Confessor,
)
from core.governance.orthodoxy_wardens.consumers.inquisitor import (
    Inquisitor,
)
from core.governance.orthodoxy_wardens.consumers.penitent import (
    Penitent,
)
from core.governance.orthodoxy_wardens.consumers.chronicler import (
    Chronicler,
)
from core.governance.orthodoxy_wardens.governance.verdict_engine import (
    VerdictEngine,
)
from core.governance.orthodoxy_wardens.governance.rule import (
    DEFAULT_RULESET,
)
from core.governance.orthodoxy_wardens.governance.workflow import (
    FULL_AUDIT_WORKFLOW,
    QUICK_VALIDATION_WORKFLOW,
)

logger = logging.getLogger("OrthodoxyWardens.BusAdapter")


class OrthodoxyBusAdapter:
    """
    Bridges infrastructure to pure domain consumers.

    Instantiate once at service startup. Thread-safe (consumers are stateless).

    Usage:
        adapter = OrthodoxyBusAdapter()
        result = adapter.handle_event({"trigger_type": "commit", "text": "import os"})
    """

    def __init__(self, ruleset=None):
        self.confessor = Confessor()
        self.ruleset = ruleset or DEFAULT_RULESET
        self.inquisitor = Inquisitor(ruleset=self.ruleset)
        self.verdict_engine = VerdictEngine()
        self.penitent = Penitent()
        self.chronicler = Chronicler()
        logger.info(
            "OrthodoxyBusAdapter initialized with ruleset=%s total_rules=%d",
            self.ruleset.version,
            self.ruleset.rule_count,
        )

    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full audit pipeline: event → confession → findings → verdict → plan → chronicle.

        Args:
            event: Raw event dict. Expected keys:
                - trigger_type (str): "commit", "api_call", "scheduled", etc.
                - text (str, optional): Text content to audit
                - code (str, optional): Code content to audit
                - scope (str, optional): Audit scope
                - source (str, optional): Event source service

        Returns:
            Dict with confession_id, verdict, correction_plan, chronicle_decision.
        """
        # 1. INTAKE: event → Confession
        confession = self.confessor.process(event)
        logger.info(
            "Confession %s created (trigger=%s, urgency=%s)",
            confession.confession_id,
            confession.trigger_type,
            confession.urgency,
        )

        # 2. EXAMINE: confession + content → InquisitorResult
        inquisitor_input = {
            "confession": confession,
            "text": event.get("text", ""),
            "code": event.get("code", ""),
        }
        result = self.inquisitor.process(inquisitor_input)
        logger.info(
            "Inquisitor found %d findings for %s",
            len(result.findings),
            confession.confession_id,
        )

        # 3. JUDGE: findings → Verdict
        verdict = self.verdict_engine.render(
            findings=result.findings,
            ruleset=self.ruleset,
            confession_id=confession.confession_id,
        )
        logger.info(
            "Verdict: %s (confidence=%.2f) for %s",
            verdict.status,
            verdict.confidence,
            confession.confession_id,
        )

        # 4. CORRECT: verdict → CorrectionPlan (if needed)
        plan = self.penitent.process(verdict)

        # 5. ARCHIVE: verdict → ChronicleDecision
        chronicle = self.chronicler.process(verdict)

        return {
            "confession_id": confession.confession_id,
            "verdict": _serialize(verdict),
            "correction_plan": _serialize(plan),
            "chronicle_decision": _serialize(chronicle),
            "findings_count": len(result.findings),
        }

    def handle_quick_validation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick validation: Confessor → Inquisitor → Verdict only.
        No correction plan, no chronicle. For high-throughput checks.
        """
        confession = self.confessor.process(event)

        result = self.inquisitor.process({
            "confession": confession,
            "text": event.get("text", ""),
            "code": event.get("code", ""),
        })

        verdict = self.verdict_engine.render(
            findings=result.findings,
            ruleset=self.ruleset,
            confession_id=confession.confession_id,
        )

        return {
            "confession_id": confession.confession_id,
            "verdict": _serialize(verdict),
            "findings_count": len(result.findings),
        }


def _serialize(obj: Any) -> Optional[Dict]:
    """Safely serialize a domain object to dict."""
    if obj is None:
        return None
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    # Frozen dataclasses (Verdict, Finding, Confession) — use asdict
    try:
        return asdict(obj)
    except TypeError:
        pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)
