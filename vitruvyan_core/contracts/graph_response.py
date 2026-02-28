"""
Graph Response Contract — Session & Response Minimum Viable Contract
====================================================================

Channel-agnostic contract for all Graph API consumers (Telegram, webchat, app).
Every adapter renders ONLY `human` + `follow_ups` and persists `session_min`.

Design:  COO + Engineering convergence (Feb 23, 2026)
Layer:   Contracts (stable, versioned, service-layer agnostic)

Orthodoxy statuses are the 5 canonical Socratic verdicts from
``core.governance.orthodoxy_wardens.domain.verdict.Verdict``:
    blessed | purified | heretical | non_liquet | clarification_needed

Rules:
    - ``context_ref`` MUST point to the PG ``conversations`` record id.
    - ``correlation_id`` MUST be deterministic (dedup/cache-safe).
    - ``orthodoxy_status`` MUST be set even on early-exit (lightweight governance).
    - ``as_of`` is always present; for greetings it equals ``datetime.utcnow()``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Canonical Orthodoxy statuses (source of truth: Verdict._VALID_STATUSES)
# ---------------------------------------------------------------------------

OrthodoxyStatusType = Literal[
    "blessed",
    "purified",
    "heretical",
    "non_liquet",
    "clarification_needed",
]

# Importable string constants — use these instead of hardcoded strings
ORTHODOXY_BLESSED: OrthodoxyStatusType = "blessed"
ORTHODOXY_PURIFIED: OrthodoxyStatusType = "purified"
ORTHODOXY_HERETICAL: OrthodoxyStatusType = "heretical"
ORTHODOXY_NON_LIQUET: OrthodoxyStatusType = "non_liquet"
ORTHODOXY_CLARIFICATION_NEEDED: OrthodoxyStatusType = "clarification_needed"


# ---------------------------------------------------------------------------
# SessionMin — per-turn session snapshot (channel-agnostic)
# ---------------------------------------------------------------------------

class SessionMin(BaseModel):
    """
    Minimal session snapshot returned to every channel after each turn.

    Channels persist ``session_id`` + ``user_id`` locally; the rest is
    informational or used for render decisions (emotion, turn_count).
    """

    user_id: str = Field(..., description="Canonical user identifier")
    session_id: str = Field(
        ...,
        description="Stable within a conversation window (derived from user_id)",
    )
    turn_id: str = Field(..., description="UUID4 unique to this turn")
    turn_count: int = Field(1, ge=1, description="Monotonic turn counter")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server timestamp (UTC)",
    )
    language: str = Field("en", description="Resolved language (ISO-639-1)")
    last_intent: Optional[str] = Field(None, description="Detected intent name")
    entities: List[str] = Field(
        default_factory=list,
        description="Resolved entity ids (tickers, topics, …)",
    )
    emotion: Optional[str] = Field(
        None,
        description="Primary emotion from Babel Gardens (joy, fear, …)",
    )
    context_ref: Optional[str] = Field(
        None,
        description="Pointer to PG conversations record (id or snapshot_id)",
    )


# ---------------------------------------------------------------------------
# GraphResponseMin — the ONE response every adapter receives
# ---------------------------------------------------------------------------

class GraphResponseMin(BaseModel):
    """
    Minimum viable response from the Graph API.

    Contract:
    - ``human`` + ``follow_ups`` are the ONLY fields an adapter should render.
    - ``session_min`` is the only field a client should persist locally.
    - ``full_payload`` is optional (debug, logging, admin dashboard).
    """

    human: str = Field(..., description="Human-readable narrative for the user")
    follow_ups: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up prompts",
    )
    orthodoxy_status: OrthodoxyStatusType = Field(
        ...,
        description="Canonical verdict: blessed|purified|heretical|non_liquet|clarification_needed",
    )
    route_taken: str = Field(
        ...,
        description="Graph route taken (llm_soft, dispatcher_exec, early_exit, …)",
    )
    correlation_id: str = Field(
        ...,
        description="Deterministic dedup key: hash(user_id, intent, entities, timebucket)",
    )
    as_of: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When facts were computed (or when greeting was produced)",
    )
    session_min: SessionMin
    full_payload: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional full graph output (existing behavior)",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_correlation_id(
    user_id: str,
    intent: Optional[str],
    entities: List[str],
    as_of: datetime,
) -> str:
    """
    Deterministic correlation key for dedup / cache.

    hash(user_id + intent + sorted(entities) + date_trunc('minute', as_of))
    """
    bucket = as_of.strftime("%Y-%m-%dT%H:%M")
    raw = f"{user_id}|{intent or 'none'}|{','.join(sorted(entities))}|{bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
