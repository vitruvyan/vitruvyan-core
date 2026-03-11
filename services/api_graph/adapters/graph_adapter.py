"""
Graph Orchestrator Adapter

Orchestrates LangGraph execution (request-response pattern).
NO event bus integration (graph is HTTP sync, not event-driven).

Concurrency model (Feb 23, 2026):
- ``asyncio.to_thread()`` offloads blocking graph execution so the
  FastAPI event loop stays responsive for N concurrent users.
- Per-user ``asyncio.Lock`` ensures one graph run per user at a time
  (queues subsequent requests instead of racing on shared state).

Layer: LIVELLO 2 (Service — orchestration)
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.orchestration.langgraph.graph_runner import run_graph_once, run_graph
from core.orchestration.langgraph.graph_flow import build_graph, build_minimal_graph
from core.orchestration.langgraph.simple_graph_audit_monitor import get_simple_graph_monitor
from contracts.graph_response import (
    SessionMin,
    GraphResponseMin,
    OrthodoxyStatusType,
    build_correlation_id,
)
from api_graph.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-user lock registry (bounded — evicts oldest when > MAX)
# ---------------------------------------------------------------------------
_USER_LOCKS: Dict[str, asyncio.Lock] = {}
_USER_LOCKS_MAX = 2000


def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Return (or create) an asyncio.Lock for *user_id*.  Evicts oldest if over cap."""
    if user_id not in _USER_LOCKS:
        if len(_USER_LOCKS) > _USER_LOCKS_MAX:
            # Evict first (oldest) key — dict is insertion-ordered in Python 3.7+
            _USER_LOCKS.pop(next(iter(_USER_LOCKS)))
        _USER_LOCKS[user_id] = asyncio.Lock()
    return _USER_LOCKS[user_id]


class GraphOrchestrationAdapter:
    """
    Adapter for orchestrating LangGraph execution.
    
    Responsibilities:
    - Execute graph with run_graph_once() (input_text, user_id)
    - Execute graph with run_graph() (raw dict payload)
    - Optional audit monitoring integration
    - Add execution metadata (timestamp, audit status)
    
    Pattern: Request-Response (HTTP sync, NOT event-driven)
    """
    
    def __init__(self):
        """Initialize graph adapter."""
        self.monitor = get_simple_graph_monitor()
        self.audit_enabled = settings.AUDIT_ENABLED
        
        if settings.ENABLE_MINIMAL_GRAPH:
            self.graph = build_minimal_graph()
        else:
            self.graph = build_graph()
        
        logger.info(f"GraphOrchestrationAdapter initialized (audit={self.audit_enabled}, minimal={settings.ENABLE_MINIMAL_GRAPH})")
    
    async def execute_graph(
        self,
        input_text: str,
        user_id: str,
        validated_entities: list = None,
        language: str = None,
        inline_context: str = None,
        persist_document: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute graph with per-user locking and thread offload.

        Concurrency guarantees:
        - ``asyncio.to_thread()`` keeps the event loop free for other users.
        - Per-user ``asyncio.Lock`` serialises requests for the same user.
        - Different users run truly in parallel.

        Returns:
            Dict matching GraphResponseMin schema (+ legacy ``json`` key for
            backward-compat until clients migrate).
        """
        lock = _get_user_lock(user_id)
        async with lock:
            try:
                # Offload blocking graph execution to a worker thread
                raw_result = await asyncio.to_thread(
                    run_graph_once,
                    input_text,
                    user_id=user_id,
                    validated_entities=validated_entities,
                    language=language,
                    inline_context=inline_context,
                )
                audit_monitored = self.audit_enabled

                return self._transform_to_api_schema(raw_result, audit_monitored)

            except Exception as e:
                logger.error(f"Graph execution failed: {e}", exc_info=True)
                error_result = {
                    "status": "error",
                    "error": str(e),
                    "narrative": f"Errore durante l'esecuzione del grafo: {str(e)}",
                }
                return self._transform_to_api_schema(error_result, self.audit_enabled)
    
    def execute_graph_dispatch(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with raw dispatch payload.
        
        Args:
            payload: Raw dict payload (used by dispatcher)
        
        Returns:
            Graph execution result transformed to GraphResponseSchema
        """
        try:
            raw_result = run_graph(payload)
            
            # Transform to API schema
            return self._transform_to_api_schema(raw_result, self.audit_enabled)
            
        except Exception as e:
            logger.error(f"Graph dispatch execution failed: {e}", exc_info=True)
            # Return error in API schema format
            error_result = {
                "status": "error",
                "error": str(e),
                "narrative": f"Errore durante l'esecuzione del grafo: {str(e)}"
            }
            return self._transform_to_api_schema(error_result, self.audit_enabled)
    
    async def execute_graph_with_audit(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with explicit audit monitoring.
        Used by /graph/dispatch endpoint.
        
        Args:
            payload: Graph payload dict
        
        Returns:
            Result with audit metadata (GraphResponseSchema format)
        """
        async with self.monitor.monitor_graph_execution(payload):
            raw_result = run_graph(payload)
            
            # Transform to API schema with audit enabled
            return self._transform_to_api_schema(raw_result, audit_monitored=True)
    
    def _transform_to_api_schema(self, raw_result: Dict[str, Any], audit_monitored: bool) -> Dict[str, Any]:
        """
        Transform core graph output → GraphResponseMin contract.

        Backward-compatible: legacy ``json``, ``human``, ``audit_monitored``,
        ``execution_timestamp`` keys are still present alongside the contract
        fields so existing clients keep working until migrated.
        """
        now = datetime.now(timezone.utc)

        # ---- human message (primary field for UI) ----
        human_message = raw_result.get("narrative", "")
        if not human_message:
            if "message" in raw_result:
                human_message = raw_result["message"]
            elif "error" in raw_result:
                human_message = f"Errore: {raw_result['error']}"
            elif "can_response" in raw_result and isinstance(raw_result["can_response"], dict):
                human_message = raw_result["can_response"].get("narrative", "Risposta non disponibile")
            else:
                human_message = "Risposta generata dal sistema"

        # ---- follow-ups ----
        follow_ups = raw_result.get("follow_ups") or []
        if isinstance(follow_ups, str):
            follow_ups = [follow_ups]

        # ---- orthodoxy status (canonical 5-value enum) ----
        raw_status = raw_result.get("orthodoxy_status", "") or raw_result.get("orthodoxy_verdict", "")
        _CANONICAL_MAP = {
            "blessed": "blessed",
            "purified": "purified",
            "heretical": "heretical",
            "non_liquet": "non_liquet",
            "clarification_needed": "clarification_needed",
            # Legacy fallback mappings (from refactored orthodoxy node)
            "locally_blessed": "blessed",
            "locally_flagged": "non_liquet",
            "under_review": "non_liquet",
            "absolution_granted": "blessed",
        }
        orthodoxy_status: OrthodoxyStatusType = _CANONICAL_MAP.get(raw_status, "non_liquet")  # type: ignore[arg-type]
        if raw_status and raw_status not in _CANONICAL_MAP:
            logger.warning(
                f"[graph_adapter] Unknown orthodoxy status '{raw_status}' — defaulting to 'non_liquet'"
            )

        # ---- route ----
        route_taken = raw_result.get("route", "unknown") or "unknown"

        # ---- session min ----
        user_id = raw_result.get("user_id", "demo") or "demo"
        intent = raw_result.get("intent")
        entities = raw_result.get("entity_ids") or []
        if isinstance(entities, str):
            entities = [entities]

        turn_id = raw_result.get("trace_id") or str(uuid.uuid4())

        session_min = SessionMin(
            user_id=user_id,
            session_id=user_id,   # stable per conversation window
            turn_id=turn_id,
            turn_count=1,         # TODO: track monotonic counter in _SESSION_STATE
            updated_at=now,
            language=raw_result.get("language", "en") or "en",
            last_intent=intent,
            entities=entities,
            emotion=raw_result.get("emotion_detected"),
            context_ref=None,     # populated when PG returns row id
        )

        correlation_id = build_correlation_id(user_id, intent, entities, now)

        # ---- build contract response ----
        response_min = GraphResponseMin(
            human=human_message,
            follow_ups=follow_ups,
            orthodoxy_status=orthodoxy_status,
            route_taken=route_taken,
            correlation_id=correlation_id,
            as_of=now,
            session_min=session_min,
            full_payload=raw_result,
        )

        # Serialize to dict — includes both contract fields AND legacy keys
        result = response_min.model_dump(mode="json")

        # Legacy backward-compat keys (remove after client migration)
        result["json"] = json.dumps(raw_result, ensure_ascii=False, separators=(",", ":"), default=str)
        result["audit_monitored"] = audit_monitored
        result["execution_timestamp"] = now.isoformat()

        return result
