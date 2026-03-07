"""
Synaptic Conclave — API Routes

FastAPI router for all Conclave endpoints.
Thin validation + delegation to ConclaveBusAdapter.
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from api_conclave.models.schemas import (
    EventPayload,
    EventEmission,
    EventReceive,
    HealthResponse,
    DetailedHealthResponse,
    OrdersHealthResponse,
    OrdersHealthSummary,
    StreamStatisticsResponse,
    RecentEventsResponse,
)
from api_conclave.config import settings
from api_conclave.monitoring.metrics import (
    streams_events_emitted_total,
    cognitive_events_published,
    cognitive_event_processing_duration,
    http_requests_total,
    http_request_duration_seconds,
    active_orders_gauge,
    pulse_active_status,
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


# ═════════════════════════════════════════════════════════════
# INFO
# ═════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════
# EMIT
# ═════════════════════════════════════════════════════════════

@router.post("/emit/structured", tags=["streams"])
async def emit_structured_event(emission: EventEmission):
    """
    Emit a structured event (domain + intent → channel).

    The channel is built as ``{domain}.{intent}`` automatically.
    """
    adapter = _get_adapter()
    channel = f"{emission.domain}.{emission.intent}"
    start = datetime.utcnow()

    try:
        event_id = adapter.emit(
            channel=channel,
            data=emission.payload,
            emitter="conclave.api",
        )

        duration = (datetime.utcnow() - start).total_seconds()
        cognitive_events_published.labels(domain=emission.domain, intent=emission.intent).inc()
        cognitive_event_processing_duration.labels(domain=emission.domain).observe(duration)
        http_requests_total.labels(method="POST", endpoint="/emit/structured", status="200").inc()

        return {
            "emitted": True,
            "event_type": channel,
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        http_requests_total.labels(method="POST", endpoint="/emit/structured", status="500").inc()
        raise HTTPException(status_code=500, detail=f"Emission failed: {exc}")


@router.post("/emit/{emission_channel}", tags=["streams"])
async def emit_event(emission_channel: str, payload: EventPayload):
    """
    Emit event to Redis Streams.

    Channel format: domain.action (e.g. 'codex.discovery.mapped')
    """
    adapter = _get_adapter()
    start = datetime.utcnow()

    try:
        event_id = adapter.emit(
            channel=emission_channel,
            data=payload.data,
            emitter=payload.emitter,
        )

        duration = (datetime.utcnow() - start).total_seconds()
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


# ═════════════════════════════════════════════════════════════
# EVENTS
# ═════════════════════════════════════════════════════════════

@router.get("/events/recent", tags=["events"])
async def get_recent_events(
    limit: int = Query(100, ge=1, le=1000),
    domain: Optional[str] = Query(None, description="Filter by domain prefix"),
):
    """
    Get recent events across all sacred channels.

    Uses XRANGE under the hood — no consumer group required.
    """
    adapter = _get_adapter()
    events = adapter.recent_events_all(limit=limit, domain_filter=domain)
    return RecentEventsResponse(
        events=events,
        total_returned=len(events),
        limit=limit,
        domain_filter=domain,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/events/statistics", tags=["events"])
async def get_event_statistics():
    """
    Get per-channel stream statistics (XINFO STREAM).
    """
    adapter = _get_adapter()
    stats = adapter.stream_statistics()
    return StreamStatisticsResponse(
        channels=stats.get("channels", {}),
        total_events=stats.get("total_events", 0),
        total_channels=stats.get("total_channels", 0),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/events/receive", tags=["events"])
async def receive_event(event_data: EventReceive):
    """
    Webhook endpoint: receive events from other Orders.

    Re-emits the event onto Redis Streams so the bus can distribute it.
    """
    adapter = _get_adapter()
    channel = f"{event_data.domain}.{event_data.intent}"

    try:
        event_id = adapter.emit(
            channel=channel,
            data=event_data.payload,
            emitter=f"webhook.{event_data.source}",
        )

        logger.info("Event received via webhook: %s -> %s", channel, event_id)
        return {
            "received": True,
            "channel": channel,
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.error("Webhook receive failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to receive event: {exc}")


# ═════════════════════════════════════════════════════════════
# ORDERS HEALTH
# ═════════════════════════════════════════════════════════════

@router.get("/orders/health", tags=["health"])
async def get_orders_health():
    """
    Check health of all Sacred Orders by inspecting consumer groups
    on each sacred channel.
    """
    adapter = _get_adapter()
    order_health = adapter.orders_health()

    total = len(order_health)
    alive = sum(1 for v in order_health.values() if v.get("status") == "alive")

    # Update Prometheus gauge
    active_orders_gauge.set(alive)

    return OrdersHealthResponse(
        orders=order_health,
        summary=OrdersHealthSummary(
            total_orders=total,
            alive_orders=alive,
            health_percentage=round(alive / total * 100, 1) if total else 0.0,
        ),
        timestamp=datetime.utcnow().isoformat(),
    )


# ═════════════════════════════════════════════════════════════
# ROUTING MAP
# ═════════════════════════════════════════════════════════════

@router.get("/routing/map", tags=["info"])
async def get_routing_map():
    """
    Return the canonical EVENT_ROUTING_MAP from LAYER 1.

    Shows which consumer listens to which events.
    """
    from api_conclave.adapters.bus_adapter import ConclaveBusAdapter

    return {
        "routing_map": ConclaveBusAdapter.routing_map(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ═════════════════════════════════════════════════════════════
# LEXICON
# ═════════════════════════════════════════════════════════════

@router.get("/lexicon/domains", tags=["info"])
async def get_lexicon_domains():
    """
    Return all registered domains and their schemas from SacredLexicon.

    Falls back to a domain listing from EVENT_ROUTING_MAP if
    SacredLexicon construction fails (LAYER 1 default schema mismatch).
    """
    try:
        from core.synaptic_conclave.utils.lexicon import SacredLexicon

        lexicon = SacredLexicon()
        schema_export = lexicon.export_schema()
        return {"lexicon": schema_export, "timestamp": datetime.utcnow().isoformat()}
    except Exception:
        # SacredLexicon's default schemas use str values for intents but
        # DomainSchema expects Dict[str, Dict]. Fall back to routing map
        # which is always valid and provides domain→channel visibility.
        from core.synaptic_conclave.events.event_schema import EVENT_ROUTING_MAP

        domains = set()
        for events in EVENT_ROUTING_MAP.values():
            for ev in events:
                parts = ev.split(".", 1)
                if parts:
                    domains.add(parts[0])

        return {
            "lexicon": {
                "domains": sorted(domains),
                "note": "Derived from EVENT_ROUTING_MAP (full lexicon schema unavailable)",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# ═════════════════════════════════════════════════════════════
# PULSE
# ═════════════════════════════════════════════════════════════

@router.get("/pulse/status", tags=["health"])
async def get_pulse_status():
    """
    Return pulse (liveness) metadata for this Conclave instance.
    """
    adapter = _get_adapter()
    pulse = adapter.pulse_status()
    pulse_active_status.set(1 if pulse.get("is_active") else 0)
    return {
        "pulse": pulse,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/pulse/heartbeat", tags=["health"])
async def force_heartbeat():
    """
    Force an immediate heartbeat event onto conclave.pulse.
    """
    adapter = _get_adapter()
    success = adapter.force_heartbeat()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to force heartbeat")

    return {
        "heartbeat_forced": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ═════════════════════════════════════════════════════════════
# HEALTH (Basic)
# ═════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Lightweight health check: verify Redis connection."""
    connected = _bus_adapter is not None and _bus_adapter.ping()

    return HealthResponse(
        status="healthy" if connected else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        redis_connected=connected,
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
    )


@router.get("/health/conclave", response_model=DetailedHealthResponse, tags=["health"])
async def health_check_detailed():
    """
    Detailed health check — Redis + pulse + active orders.
    """
    connected = _bus_adapter is not None and _bus_adapter.ping()
    pulse_active = connected and _bus_adapter.is_connected

    # Count alive orders
    alive = 0
    if _bus_adapter and _bus_adapter.is_connected:
        order_health = _bus_adapter.orders_health()
        alive = sum(1 for v in order_health.values() if v.get("status") == "alive")
        active_orders_gauge.set(alive)

    pulse_active_status.set(1 if pulse_active else 0)

    return DetailedHealthResponse(
        status="alive" if connected else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        conclave_version=settings.SERVICE_VERSION,
        redis_connected=connected,
        pulse_active=pulse_active,
        active_orders=alive,
    )


# ═════════════════════════════════════════════════════════════
# METRICS
# ═════════════════════════════════════════════════════════════

@router.get("/metrics", tags=["metrics"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ═════════════════════════════════════════════════════════════
# CAUSAL QUERIES (F3.2)
# ═════════════════════════════════════════════════════════════

_persistence = None


def set_persistence(adapter):
    """Called by main.py startup to inject PersistenceAdapter."""
    global _persistence
    _persistence = adapter


def _get_persistence():
    if _persistence is None:
        raise HTTPException(status_code=503, detail="Persistence not initialized")
    return _persistence


@router.get("/causal/trace/{trace_id}", tags=["causal"])
async def causal_trace(trace_id: str):
    """
    Return all events in a causal tree by trace_id.

    Response includes flat list of events and a reconstructed tree structure.
    """
    from core.synaptic_conclave.events.causal_query import (
        build_causal_tree,
        get_roots,
    )

    persistence = _get_persistence()
    rows = persistence.fetch_trace(trace_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No events for trace {trace_id}")

    tree = build_causal_tree(rows)
    roots = get_roots(tree)

    def _serialize_node(node):
        return {
            "event_id": node.event_id,
            "event_type": node.event_type,
            "source": node.source,
            "channel": node.channel,
            "causation_id": node.causation_id,
            "created_at": node.created_at,
            "children": [_serialize_node(c) for c in node.children],
        }

    return {
        "trace_id": trace_id,
        "event_count": len(rows),
        "roots": [_serialize_node(r) for r in roots],
        "events": rows,
    }


@router.get("/causal/chain/{event_id}", tags=["causal"])
async def causal_chain_endpoint(event_id: str):
    """
    Return the ancestor chain from root to event_id.
    """
    from core.synaptic_conclave.events.causal_query import (
        build_causal_tree,
        causal_chain,
    )

    persistence = _get_persistence()
    # Need the trace_id first — look up the event
    children_rows = persistence.fetch_children(event_id)
    # Also try fetching by the event itself
    # We need a single-event lookup — use a direct query
    all_rows = persistence.pg.fetch(
        "SELECT trace_id FROM causal_event_log WHERE event_id = %s",
        (event_id,),
    )
    if not all_rows:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    trace_id = all_rows[0]["trace_id"]
    rows = persistence.fetch_trace(trace_id)
    tree = build_causal_tree(rows)
    chain = causal_chain(tree, event_id)

    return {
        "event_id": event_id,
        "trace_id": trace_id,
        "chain_length": len(chain),
        "chain": [
            {
                "event_id": n.event_id,
                "event_type": n.event_type,
                "source": n.source,
                "channel": n.channel,
                "created_at": n.created_at,
            }
            for n in chain
        ],
    }
