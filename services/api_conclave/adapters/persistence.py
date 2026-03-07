"""
Synaptic Conclave — Persistence Adapter (LIVELLO 2)

I/O boundary for the Conclave bus observatory.
Handles causal event logging to PostgreSQL (F3.2).

All database access is centralized here per SERVICE_PATTERN.md.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Conclave.Persistence")

_LOG_CAUSAL_SQL = """
    INSERT INTO causal_event_log
        (event_id, trace_id, causation_id, correlation_id,
         event_type, source, channel, payload_hash)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (event_id) DO NOTHING
"""

_FETCH_TRACE_SQL = """
    SELECT event_id, trace_id, causation_id, correlation_id,
           event_type, source, channel, created_at
    FROM causal_event_log
    WHERE trace_id = %s
    ORDER BY created_at
"""

_FETCH_CHILDREN_SQL = """
    SELECT event_id, trace_id, causation_id, correlation_id,
           event_type, source, channel, created_at
    FROM causal_event_log
    WHERE causation_id = %s
    ORDER BY created_at
"""


class PersistenceAdapter:
    """
    I/O boundary for Synaptic Conclave — causal event persistence.

    Provides:
    - log_causal_event(): Persist a CognitiveEvent's causal fields
    - fetch_trace(): Get all events sharing a trace_id
    - fetch_children(): Get all events caused by a specific event
    """

    def __init__(self, pg=None, qdrant=None):
        self._pg = pg
        self._qdrant = qdrant
        logger.debug("PersistenceAdapter initialized")

    @property
    def pg(self):
        if self._pg is None:
            from core.agents.postgres_agent import PostgresAgent
            self._pg = PostgresAgent()
        return self._pg

    def log_causal_event(
        self,
        event_id: str,
        trace_id: str,
        event_type: str,
        source: str,
        causation_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        channel: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Persist a causal event record. Idempotent (ON CONFLICT DO NOTHING)."""
        payload_hash = None
        if payload:
            payload_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

        try:
            self.pg.execute(
                _LOG_CAUSAL_SQL,
                (event_id, trace_id, causation_id, correlation_id,
                 event_type, source, channel, payload_hash),
            )
            return True
        except Exception:
            logger.exception("Failed to log causal event %s", event_id)
            return False

    def fetch_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Fetch all events in a causal tree by trace_id."""
        return self.pg.fetch(_FETCH_TRACE_SQL, (trace_id,))

    def fetch_children(self, event_id: str) -> List[Dict[str, Any]]:
        """Fetch all events directly caused by event_id."""
        return self.pg.fetch(_FETCH_CHILDREN_SQL, (event_id,))
