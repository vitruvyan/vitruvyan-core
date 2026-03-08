"""
FastAPI routes for Graph Orchestrator service.
Extracted endpoints from main.py following SACRED_ORDER_PATTERN.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..config import settings
from ..models.schemas import (
    GraphInputSchema,
    GraphResponseSchema,
    HealthResponseSchema,
    AuditHealthSchema,
    FeedbackSignalSchema,
)
from ..adapters.graph_adapter import GraphOrchestrationAdapter
from ..adapters.persistence import GraphPersistence
from ..adapters.plasticity_adapter import get_plasticity_service
from ..monitoring.health import metrics_endpoint

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Router & Dependency Injection
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# Global adapters (initialized on startup via set_adapters)
_graph_adapter: Optional[GraphOrchestrationAdapter] = None
_persistence: Optional[GraphPersistence] = None


def set_adapters(
    graph_adapter: GraphOrchestrationAdapter,
    persistence: GraphPersistence,
):
    """Initialize global adapters (called from main.py startup)"""
    global _graph_adapter, _persistence
    _graph_adapter = graph_adapter
    _persistence = persistence


def get_graph_adapter() -> GraphOrchestrationAdapter:
    """Dependency injection for graph orchestration adapter"""
    if _graph_adapter is None:
        raise RuntimeError("Graph adapter not initialized")
    return _graph_adapter


def get_persistence() -> GraphPersistence:
    """Dependency injection for persistence layer"""
    if _persistence is None:
        raise RuntimeError("Persistence layer not initialized")
    return _persistence


# ─────────────────────────────────────────────────────────────────────────────
# Health & Monitoring Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponseSchema)
async def health():
    """
    Health check endpoint for container monitoring.
    Returns service status, version, and audit monitoring state.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "timestamp": datetime.now().isoformat(),
        "version": settings.SERVICE_VERSION,
        "audit_monitoring": "enabled" if settings.AUDIT_ENABLED else "disabled",
        "heartbeat_count": 0,  # Not implemented in refactored service
        "last_heartbeat": "N/A",
        "portainer_anti_restart": "refactored",
    }


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    Exposes all collected metrics in Prometheus format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ─────────────────────────────────────────────────────────────────────────────
# Graph Execution Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/graph/dispatch")
async def graph_dispatch(
    payload: dict = Body(...),
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Execute Leonardo graph with audit monitoring.
    Returns JSON one-line + human message + audit metadata.

    Payload: Generic dict (flexible input format)
    Returns: {json: str, human: str, audit_monitored: bool, timestamp: str}
    """
    if settings.AUDIT_ENABLED:
        return await adapter.execute_graph_with_audit(payload)
    else:
        # Fallback: executeenza audit
        result = adapter.execute_graph_dispatch(payload)
        return {
            "json": str(result),
            "human": "Leonardo: grafo eseguito senza audit monitoring.",
            "audit_monitored": False,
            "timestamp": datetime.now().isoformat(),
        }


@router.post("/dispatch")
async def graph_dispatch_alias(
    payload: dict = Body(...),
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Alias for backward compatibility with test dispatcher.
    Directly calls run_graph without audit wrapper.
    """
    return adapter.execute_graph_dispatch(payload)


@router.post("/run", response_model=GraphResponseSchema)
async def run_graph_endpoint(
    data: GraphInputSchema,
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Main graph execution endpoint compatible with pipeline.
    Receives {input_text, user_id} and executes graph with audit monitoring.

    Returns: {json: dict, human: str, audit_monitored: bool, execution_timestamp: str}
    """
    return await adapter.execute_graph(
        input_text=data.input_text,
        user_id=data.user_id or settings.DEFAULT_USER_ID,
        validated_entities=data.validated_tickers or data.validated_entities,
        language=data.language,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Persistence Health Checks (Placeholders)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/pg/health")
async def pg_health():
    """PostgreSQL health check (placeholder)"""
    return {"status": "pg_placeholder", "service": "postgres"}


@router.get("/qdrant/health")
async def qdrant_health():
    """Qdrant health check (placeholder)"""
    return {"status": "qdrant_placeholder", "service": "qdrant"}


# ─────────────────────────────────────────────────────────────────────────────
# Audit & Monitoring Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/audit/graph/health", response_model=AuditHealthSchema)
async def graph_audit_health(
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Get health status of graph audit monitoring.
    Returns monitoring state, session ID, and performance metrics.
    """
    if not settings.AUDIT_ENABLED or adapter.monitor is None:
        return {
            "status": "disabled",
            "monitoring_active": False,
            "current_session_id": None,
            "performance_metrics": {},
            "timestamp": datetime.now().isoformat(),
        }

    monitor = adapter.monitor
    return {
        "status": "healthy" if monitor.monitoring_active else "inactive",
        "monitoring_active": monitor.monitoring_active,
        "current_session_id": monitor.audit_session_id,
        "performance_metrics": monitor.performance_metrics,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/audit/graph/metrics")
async def get_graph_metrics(
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Get current graph performance metrics.
    Returns metrics, monitoring state, and session ID.
    """
    if not settings.AUDIT_ENABLED or adapter.monitor is None:
        return {
            "metrics": {},
            "monitoring_active": False,
            "session_id": None,
            "timestamp": datetime.now().isoformat(),
        }

    monitor = adapter.monitor
    return {
        "metrics": monitor.performance_metrics,
        "monitoring_active": monitor.monitoring_active,
        "session_id": monitor.audit_session_id,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/audit/graph/trigger")
async def trigger_graph_audit(
    adapter: GraphOrchestrationAdapter = Depends(get_graph_adapter),
):
    """
    Manually trigger a comprehensive graph audit.
    Performs basic health checks and logs findings.
    """
    if not settings.AUDIT_ENABLED or adapter.monitor is None:
        return {
            "status": "disabled",
            "message": "Audit monitoring not enabled",
            "timestamp": datetime.now().isoformat(),
        }

    try:
        monitor = adapter.monitor
        findings = []

        # Basic health checks
        current_executions = monitor.performance_metrics.get("executions", 0)
        if current_executions > 1000:
            findings.append(
                {
                    "category": "high_load",
                    "severity": "medium",
                    "description": f"High execution count: {current_executions}",
                }
            )

        # Check for recent errors
        errors = monitor.performance_metrics.get("errors", [])
        recent_errors = []
        now = datetime.now()
        for err in errors:
            try:
                err_time = datetime.fromisoformat(err["timestamp"])
                if (now - err_time).total_seconds() < 3600:  # Last hour
                    recent_errors.append(err)
            except (ValueError, KeyError):
                continue

        if len(recent_errors) > 5:
            findings.append(
                {
                    "category": "high_error_rate",
                    "severity": "high",
                    "description": f"High error rate: {len(recent_errors)} errors in last hour",
                }
            )

        # Log findings
        for finding in findings:
            logger.info(
                f"🔍 Manual audit finding: {finding['category']} - {finding['description']}"
            )

        return {
            "status": "completed",
            "session_id": monitor.audit_session_id,
            "findings_count": len(findings),
            "execution_count": current_executions,
            "recent_errors": len(recent_errors),
            "findings": findings,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Manual graph audit failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.post("/audit/grafana/webhook")
async def grafana_alert_webhook(payload: dict = Body(...)):
    """
    Webhook endpoint for Grafana alerts.
    Receives alerts from Grafana and forwards them to notification system.

    Grafana payload structure:
    {
        "title": "Alert Title",
        "state": "alerting" | "ok" | "no_data",
        "message": "Alert description",
        "ruleName": "Rule name",
        "ruleUrl": "Link to rule",
        "evalMatches": [...],
        "tags": {...}
    }
    """
    try:
        logger.info(f"📨 Received Grafana webhook: {payload.get('title', 'No title')}")

        # Extract alert data
        alert_data = {
            "title": payload.get("title", payload.get("ruleName", "Grafana Alert")),
            "state": payload.get("state", "alerting"),
            "message": payload.get(
                "message", "Nessuna descrizione disponibile"
            ),
            "severity": (
                "critical" if payload.get("state") == "alerting" else "info"
            ),
            "dashboard_url": payload.get(
                "ruleUrl", "https://dash.vitruvyan.com"
            ),
            "tags": payload.get("tags", {}),
        }

        # Extract value and threshold from evalMatches
        eval_matches = payload.get("evalMatches", [])
        if eval_matches and len(eval_matches) > 0:
            first_match = eval_matches[0]
            alert_data["value"] = first_match.get("value")
            alert_data["threshold"] = payload.get("threshold")

        # TODO: Implement send_grafana_alert when notifier module is ready
        # from core.notifier.grafana_alerts import send_grafana_alert
        # send_grafana_alert(alert_data)

        logger.info(
            f"✅ Grafana alert processed: {alert_data['title']} (notification pending implementation)"
        )

        return {
            "status": "success",
            "message": "Alert received (notification pending implementation)",
            "alert_title": alert_data["title"],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to process Grafana webhook: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Data Query Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/clusters/semantic")
async def get_semantic_clusters(
    persistence: GraphPersistence = Depends(get_persistence),
):
    """
    Get semantic clusters from documentation.
    Returns clustered knowledge organization from docs_archive.
    """
    return persistence.get_semantic_clusters()


@router.get("/api/entity_ids/search")
async def search_entities(
    q: str = Query("", min_length=2, description="Query string (min 2 chars)"),
    persistence: GraphPersistence = Depends(get_persistence),
):
    """
    Fuzzy entity_id search endpoint for UI autocomplete.
    Searches both entity_id symbols and company names.

    Args:
        q: Query string (partial entity_id or company name, min 2 chars)

    Returns:
        List of matching entity_ids with metadata:
        {
            "status": "success",
            "query": "citi",
            "results": [
                {
                    "entity_id": "C",
                    "name": "Citigroup Inc.",
                    "sector": "Finance",
                    "match_score": 0.95
                }
            ],
            "total": 1,
            "duration_ms": 12
        }

    Examples:
        /api/entity_ids/search?q=citi → Returns Citigroup (C)
        /api/entity_ids/search?q=micro → Returns Microsoft (MSFT), MicroStrategy (MSTR)
    """
    if len(q) < 2:
        return {
            "status": "error",
            "message": "Query must be at least 2 characters",
            "results": [],
            "total": 0,
        }

    return persistence.search_entities(query=q, limit=10)


# ─────────────────────────────────────────────────────────────────────────────
# Feedback endpoint — Plasticity integration
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/feedback")
async def submit_feedback(signal: FeedbackSignalSchema):
    """
    Receive user feedback (thumbs up/down) on an AI response.

    The signal is forwarded to OutcomeTracker for the Plasticity learning loop.
    Maps: positive → outcome_value 1.0, negative → outcome_value 0.0.

    This endpoint is fire-and-forget from the UI perspective — it always
    returns 200. Failures are logged but never surfaced to the user.
    """
    try:
        outcome_value = 1.0 if signal.feedback == "positive" else 0.0

        # Record outcome directly via PlasticityService (if available)
        svc = get_plasticity_service()
        if svc:
            try:
                await svc.record_feedback_outcome(
                    message_id=signal.message_id,
                    trace_id=signal.trace_id,
                    feedback=signal.feedback,
                    outcome_value=outcome_value,
                    comment=signal.comment,
                )
            except Exception as plas_err:
                logger.warning(f"Plasticity outcome failed (non-fatal): {plas_err}")

        # Emit to bus for async processing by other Plasticity consumers
        try:
            from core.synaptic_conclave.transport.streams import get_stream_bus

            get_stream_bus().emit(
                channel="plasticity.feedback.received",
                payload={
                    "message_id": signal.message_id,
                    "trace_id": signal.trace_id,
                    "feedback": signal.feedback,
                    "outcome_value": outcome_value,
                    "comment": signal.comment,
                    "timestamp": signal.timestamp,
                    "source": "ui.chat.feedback",
                },
                emitter="api_graph.feedback",
                correlation_id=signal.trace_id,
            )
        except Exception as bus_err:
            logger.warning(f"Feedback bus emit failed (non-fatal): {bus_err}")

        logger.info(
            f"[FEEDBACK] {signal.feedback} for message={signal.message_id} "
            f"trace={signal.trace_id}"
        )

        return {
            "status": "accepted",
            "message_id": signal.message_id,
            "feedback": signal.feedback,
        }

    except Exception as e:
        logger.error(f"[FEEDBACK] Error: {e}", exc_info=True)
        return {"status": "accepted", "message_id": signal.message_id}


# ─────────────────────────────────────────────────────────────────────────────
# Plasticity endpoints — Learning system observability
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/plasticity/stats")
async def plasticity_stats():
    """Return PlasticityManager statistics and current thresholds."""
    svc = get_plasticity_service()
    if not svc:
        return {"status": "unavailable", "reason": "Plasticity not initialized"}
    return svc.get_statistics()


@router.get("/api/plasticity/health")
async def plasticity_health():
    """Run Observer analysis and return learning health report."""
    svc = get_plasticity_service()
    if not svc:
        return {"status": "unavailable", "reason": "Plasticity not initialized"}
    return await svc.get_health()


@router.post("/api/plasticity/cycle")
async def plasticity_run_cycle():
    """Manually trigger one learning cycle (admin/testing)."""
    svc = get_plasticity_service()
    if not svc:
        return {"status": "unavailable", "reason": "Plasticity not initialized"}
    result = await svc.run_learning_cycle()
    return {"status": "completed", "result": result}


@router.get("/api/plasticity/success-rate")
async def plasticity_success_rate(parameter: str = "heretical_threshold"):
    """Get current success rate for a parameter."""
    svc = get_plasticity_service()
    if not svc:
        return {"status": "unavailable", "reason": "Plasticity not initialized"}
    rate = await svc.get_success_rate(parameter)
    return {"parameter": parameter, "success_rate": rate}
