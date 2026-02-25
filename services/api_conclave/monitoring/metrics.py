"""
Synaptic Conclave — Prometheus Metrics

Centralized metric definitions.
Uses _safe_* wrappers to prevent double-registration errors.
Follows SERVICE_PATTERN.md (LIVELLO 2).
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY


def _safe_counter(name: str, doc: str, labels: list[str] | None = None) -> Counter:
    """Create Counter, return existing if already registered."""
    try:
        return Counter(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors.get(name, Counter(name, doc, labels or []))


def _safe_histogram(name: str, doc: str, labels: list[str] | None = None) -> Histogram:
    """Create Histogram, return existing if already registered."""
    try:
        return Histogram(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors.get(name, Histogram(name, doc, labels or []))


def _safe_gauge(name: str, doc: str, labels: list[str] | None = None) -> Gauge:
    """Create Gauge, return existing if already registered."""
    try:
        return Gauge(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors.get(name, Gauge(name, doc, labels or []))


# ── Streams ──────────────────────────────────────────────────
streams_events_emitted_total = _safe_counter(
    "conclave_streams_events_emitted_total",
    "Total events emitted to Redis Streams",
    ["channel"],
)

# ── Cognitive Bus ────────────────────────────────────────────
cognitive_events_published = _safe_counter(
    "conclave_cognitive_events_published_total",
    "Total cognitive events published to Redis",
    ["domain", "intent"],
)

cognitive_events_subscribed = _safe_counter(
    "conclave_cognitive_events_subscribed_total",
    "Total cognitive events subscribed to",
    ["domain"],
)

cognitive_event_processing_duration = _safe_histogram(
    "conclave_cognitive_event_processing_seconds",
    "Time to process and publish cognitive events",
    ["domain"],
)

# ── HTTP ─────────────────────────────────────────────────────
http_requests_total = _safe_counter(
    "conclave_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = _safe_histogram(
    "conclave_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# ── Infrastructure ───────────────────────────────────────────
redis_connection_status = _safe_gauge(
    "conclave_redis_connected",
    "Redis connection status (1=connected, 0=disconnected)",
)

active_orders_gauge = _safe_gauge(
    "conclave_active_orders",
    "Number of active orchestration orders",
)

pulse_active_status = _safe_gauge(
    "conclave_pulse_active",
    "System pulse status (1=active, 0=inactive)",
)
