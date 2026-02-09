"""
Cognitive Bus Prometheus Metrics

📊 Epistemic Order: Truth (Sacred Order #5 - Governance)
🎯 Purpose: Observable metrics for Synaptic Conclave monitoring

Metrics Exposed:
- cognitive_bus_events_total: Total events processed
- cognitive_bus_event_duration_seconds: Event processing latency histogram
- herald_broadcast_total: Herald broadcasts counter
- scribe_write_total: Scribe stream writes counter
- listener_consumed_total: Listener event consumption counter
- stream_consumer_lag: Consumer group lag gauge
- stream_pending_messages: Pending messages per stream gauge

Integration: Phase 2 Metrics Layer Implementation (Jan 26, 2026)
"""

from prometheus_client import Counter, Histogram, Gauge, REGISTRY
import structlog

logger = structlog.get_logger(__name__)


def _safe_counter(name, desc, labels):
    """Register a Counter only if not already registered (idempotent)."""
    try:
        return Counter(name, desc, labels)
    except ValueError:
        # Already registered (dual-path: vitruvyan_core.core.* vs core.*)
        for c in REGISTRY._names_to_collectors.values():
            if hasattr(c, '_name') and (c._name == name or c._name + '_total' == name):
                return c
        raise


def _safe_histogram(name, desc, labels, buckets=None):
    """Register a Histogram only if not already registered (idempotent)."""
    kw = {"buckets": buckets} if buckets else {}
    try:
        return Histogram(name, desc, labels, **kw)
    except ValueError:
        for c in REGISTRY._names_to_collectors.values():
            if hasattr(c, '_name') and c._name == name:
                return c
        raise


def _safe_gauge(name, desc, labels):
    """Register a Gauge only if not already registered (idempotent)."""
    try:
        return Gauge(name, desc, labels)
    except ValueError:
        for c in REGISTRY._names_to_collectors.values():
            if hasattr(c, '_name') and c._name == name:
                return c
        raise

# ============================================================================
# EVENT METRICS
# ============================================================================

cognitive_bus_events_total = _safe_counter(
    'cognitive_bus_events_total',
    'Total Cognitive Bus events processed',
    ['channel', 'status', 'event_type']
)

cognitive_bus_event_duration = _safe_histogram(
    'cognitive_bus_event_duration_seconds',
    'Cognitive Bus event processing latency',
    ['channel', 'status'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# ============================================================================
# HERALD METRICS (Event Broadcasting)
# ============================================================================

herald_broadcast_total = _safe_counter(
    'herald_broadcast_total',
    'Total Herald broadcasts (pub/sub)',
    ['channel', 'status']
)

herald_broadcast_duration = _safe_histogram(
    'herald_broadcast_duration_seconds',
    'Herald broadcast latency',
    ['channel'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# ============================================================================
# SCRIBE METRICS (Stream Writing)
# ============================================================================

scribe_write_total = _safe_counter(
    'scribe_write_total',
    'Total Scribe stream writes',
    ['stream', 'status']
)

scribe_write_duration = _safe_histogram(
    'scribe_write_duration_seconds',
    'Scribe stream write latency',
    ['stream'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# ============================================================================
# LISTENER METRICS (Event Consumption)
# ============================================================================

listener_consumed_total = _safe_counter(
    'listener_consumed_total',
    'Total events consumed by listeners',
    ['stream', 'consumer', 'status']
)

listener_consumption_duration = _safe_histogram(
    'listener_consumption_duration_seconds',
    'Listener event consumption latency',
    ['stream', 'consumer'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

listener_handler_duration = _safe_histogram(
    'listener_handler_duration_seconds',
    'Listener legacy handler execution latency',
    ['consumer', 'status'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# ============================================================================
# STREAM HEALTH METRICS
# ============================================================================

stream_consumer_lag = _safe_gauge(
    'stream_consumer_lag',
    'Consumer group lag (pending messages)',
    ['stream', 'group', 'consumer']
)

stream_pending_messages = _safe_gauge(
    'stream_pending_messages',
    'Pending messages per stream',
    ['stream', 'group']
)

stream_last_event_timestamp = _safe_gauge(
    'stream_last_event_timestamp',
    'Unix timestamp of last event in stream',
    ['stream']
)

# ============================================================================
# BUS HEALTH METRICS
# ============================================================================

bus_connected_listeners = _safe_gauge(
    'bus_connected_listeners',
    'Number of active listeners connected to bus',
    ['listener_type']
)

bus_health_score = _safe_gauge(
    'bus_health_score',
    'Composite bus health score (0-100)',
    ['component']
)

# ============================================================================
# WORKING MEMORY METRICS (Plasticity System)
# ============================================================================

working_memory_size = _safe_gauge(
    'working_memory_size_bytes',
    'Working memory size per consumer',
    ['consumer']
)

working_memory_updates = _safe_counter(
    'working_memory_updates_total',
    'Working memory update operations',
    ['consumer', 'operation']
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def record_event(channel: str, status: str, event_type: str, duration: float = None):
    """
    Record cognitive bus event processing.
    
    Args:
        channel: Event channel (e.g., "memory.write.requested")
        status: Event status ("success", "failed", "rejected")
        event_type: Event type (e.g., "command", "query", "notification")
        duration: Event processing duration in seconds (optional)
    """
    cognitive_bus_events_total.labels(
        channel=channel,
        status=status,
        event_type=event_type
    ).inc()
    
    if duration is not None:
        cognitive_bus_event_duration.labels(
            channel=channel,
            status=status
        ).observe(duration)


def record_herald_broadcast(channel: str, status: str, duration: float = None):
    """Record Herald broadcast event."""
    herald_broadcast_total.labels(channel=channel, status=status).inc()
    
    if duration is not None:
        herald_broadcast_duration.labels(channel=channel).observe(duration)


def record_scribe_write(stream: str, status: str, duration: float = None):
    """Record Scribe stream write."""
    scribe_write_total.labels(stream=stream, status=status).inc()
    
    if duration is not None:
        scribe_write_duration.labels(stream=stream).observe(duration)


def record_listener_consumption(stream: str, consumer: str, status: str, 
                               consumption_duration: float = None,
                               handler_duration: float = None):
    """
    Record listener event consumption.
    
    Args:
        stream: Stream name
        consumer: Consumer ID
        status: Consumption status ("success", "failed", "ack_failed")
        consumption_duration: Time to consume from stream (seconds)
        handler_duration: Time for handler execution (seconds)
    """
    listener_consumed_total.labels(
        stream=stream,
        consumer=consumer,
        status=status
    ).inc()
    
    if consumption_duration is not None:
        listener_consumption_duration.labels(
            stream=stream,
            consumer=consumer
        ).observe(consumption_duration)
    
    if handler_duration is not None:
        listener_handler_duration.labels(
            consumer=consumer,
            status=status
        ).observe(handler_duration)


def update_stream_health(stream: str, group: str, consumer: str = None,
                        lag: int = None, pending: int = None,
                        last_event_ts: float = None):
    """Update stream health metrics."""
    if lag is not None and consumer is not None:
        stream_consumer_lag.labels(
            stream=stream,
            group=group,
            consumer=consumer
        ).set(lag)
    
    if pending is not None:
        stream_pending_messages.labels(
            stream=stream,
            group=group
        ).set(pending)
    
    if last_event_ts is not None:
        stream_last_event_timestamp.labels(stream=stream).set(last_event_ts)


def update_bus_health(component: str, score: float):
    """
    Update bus health score (0-100).
    
    Args:
        component: Component name ("herald", "scribe", "streams", "listeners", "overall")
        score: Health score 0-100 (100 = perfect health)
    """
    bus_health_score.labels(component=component).set(score)


def update_listener_count(listener_type: str, count: int):
    """Update connected listeners count."""
    bus_connected_listeners.labels(listener_type=listener_type).set(count)


def record_working_memory(consumer: str, size_bytes: int, operation: str = None):
    """
    Record working memory metrics.
    
    Args:
        consumer: Consumer ID
        size_bytes: Working memory size in bytes
        operation: Memory operation type ("write", "read", "merge", "prune")
    """
    working_memory_size.labels(consumer=consumer).set(size_bytes)
    
    if operation is not None:
        working_memory_updates.labels(
            consumer=consumer,
            operation=operation
        ).inc()


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_metrics():
    """Initialize metrics with default values."""
    logger.info("🎯 Cognitive Bus metrics initialized", 
                metrics_count=18,
                phase="Phase 2 Metrics Layer")
    
    # Initialize health scores to 100 (perfect health)
    for component in ["herald", "scribe", "streams", "listeners", "overall"]:
        update_bus_health(component, 100.0)
    
    # Initialize listener counts to 0
    for listener_type in ["native", "adapter"]:
        update_listener_count(listener_type, 0)


# Auto-initialize on import
init_metrics()
