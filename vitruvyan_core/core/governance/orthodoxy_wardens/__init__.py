"""
Orthodoxy Wardens — Sacred Order #5: Truth & Governance

Epistemic tribunal for validation, compliance, and verdict rendering.
This package provides the foundational decision engine for system governance.
It does NOT execute corrections, restart services, or write to databases.
It JUDGES inputs and renders verdicts.

Public API — import from submodules:

    from core.governance.orthodoxy_wardens.domain import Confession, Finding, Verdict, LogDecision
    from core.governance.orthodoxy_wardens.events import OrthodoxyEvent
    from core.governance.orthodoxy_wardens.consumers import SacredRole

See philosophy/charter.md for the Decision Engine Charter.
See ../../SACRED_ORDER_PATTERN.md for the canonical template used by all Sacred Orders.
"""