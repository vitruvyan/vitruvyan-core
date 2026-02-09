"""
🕯 Synaptic Conclave — Sacred API Routes

FastAPI router for all Conclave endpoints.
Thin validation + delegation to ConclaveBusAdapter.
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from api_conclave.models.schemas import EventPayload, HealthResponse
from api_conclave.config import settings
from api_conclave.monitoring.metrics import (
    streams_events_emitted_total,
    http_requests_total,
    http_request_duration_seconds,
)

logger = logging.getLogger("Conclave.Routes")

router = APIRouter()

# ── Module-level reference, injected by main.py at startup ──
_bus_adapter = None


def set_bus_adapter(adapter):
    """Called by main.py startup to inject the ConclaveBusAdapter."""
    global _bus_adapter
    _bus_adapter = adapter


def _get_adapter():
    """Return bus adapter or raise 503."""
    if _bus_adapter is None or not _bus_adapter.is_connected:
        raise HTTPException(status_code=503, detail="StreamBus not initialized")
    return _bus_adapter


# ─────────────────────────────────────────────────────────────
# INFO
# ─────────────────────────────────────────────────────────────

@router.get("/", tags=["info"])
async def root():
    """Service information."""
    return {
        "service": settings.SERVICE_NAME,
        "role": "epistemic_observatory",
        "architecture": "redis_streams",
        "version": settings.SERVICE_VERSION,
        "philosophy": "octopus_mycelium",
        "sacred_invariants": [
            "no_payload_inspection",
            "no_correlation",
            "no_semantic_routing",
            "no_synthesis",
        ],
    }


# ─────────────────────────────────────────────────────────────
# EMIT
# ─────────────────────────────────────────────────────────────

@router.post("/emit/{emission_channel}", tags=["streams"])
async def emit_event(emission_channel: str, payload: EventPayload):
    """
    Emit event to Redis Streams.

    Channel format: domain.action (e.g. 'codex.discovery.mapped')
    """
    adapter = _get_adapter()
    start_time = datetime.utcnow()

    try:
        event_id = adapter.emit(
            channel=emission_channel,
            data=payload.data,
            emitter=payload.emitter,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        streams_events_emitted_total.labels(channel=emission_channel).inc()
        http_requests_total.labels(method="POST", endpoint="/emit", status="200").inc()
        http_request_duration_seconds.labels(method="POST", endpoint="/emit").observe(duration)

        logger.info("Event emitted: %s -> %s", emission_channel, event_id)

        return {
            "emitted": True,
            "channel": emission_channel,
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except RuntimeError as exc:
        http_requests_total.labels(method="POST", endpoint="/emit", status="503").inc()
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        http_requests_total.labels(method="POST", endpoint="/emit", status="500").inc()
        logger.error("Emission failed: %s — %s", emission_channel, exc)
        raise HTTPException(status_code=500, detail=f"Emission failed: {exc}")


# ─────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check: verify Redis connection."""
    connected = _bus_adapter is not None and _bus_adapter.ping()

    return HealthResponse(
        status="healthy" if connected else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        redis_connected=connected,
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
    )


# ─────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────

@router.get("/metrics", tags=["metrics"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
