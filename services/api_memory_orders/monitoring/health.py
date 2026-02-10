"""
Memory Orders — Health Monitoring

Prometheus metrics collectors for Memory Orders service.

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — monitoring)
"""

import logging
from datetime import datetime
from prometheus_client import Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from core.governance.memory_orders.monitoring import (
    COHERENCE_DRIFT_PCT,
    COHERENCE_STATUS,
    HEALTH_STATUS,
    ARCHIVARIUM_CONNECTED,
    MNEMOSYNE_CONNECTED,
    REDIS_CONNECTED,
    SYNC_OPERATIONS_TOTAL,
)


logger = logging.getLogger(__name__)


# ========================================
#  Prometheus Collectors
# ========================================

# Coherence metrics
coherence_drift_gauge = Gauge(
    COHERENCE_DRIFT_PCT,
    "Drift percentage between PostgreSQL and Qdrant"
)

coherence_status_gauge = Gauge(
    COHERENCE_STATUS,
    "Coherence status (0=critical, 1=warning, 2=healthy)"
)

# Health metrics
health_status_gauge = Gauge(
    HEALTH_STATUS,
    "Overall RAG system health (0=critical, 1=degraded, 2=healthy)"
)

archivarium_connected_gauge = Gauge(
    ARCHIVARIUM_CONNECTED,
    "PostgreSQL connection status (0=down, 1=up)"
)

mnemosyne_connected_gauge = Gauge(
    MNEMOSYNE_CONNECTED,
    "Qdrant connection status (0=down, 1=up)"
)

redis_connected_gauge = Gauge(
    REDIS_CONNECTED,
    "Redis connection status (0=down, 1=up)"
)

# Sync metrics
sync_operations_counter = Counter(
    SYNC_OPERATIONS_TOTAL,
    "Total synchronization operations executed"
)


# ========================================
#  Metric Updaters
# ========================================

def update_coherence_metrics(report):
    """Update Prometheus metrics from CoherenceReport."""
    coherence_drift_gauge.set(report.drift_percentage)
    
    # Map status to numeric value
    status_map = {"healthy": 2, "warning": 1, "critical": 0}
    coherence_status_gauge.set(status_map.get(report.status, 0))


def update_health_metrics(health):
    """Update Prometheus metrics from SystemHealth."""
    # Map overall status
    status_map = {"healthy": 2, "degraded": 1, "critical": 0}
    health_status_gauge.set(status_map.get(health.overall_status, 0))
    
    # Map component statuses
    for comp in health.components:
        if comp.component == "archivarium":
            archivarium_connected_gauge.set(1 if comp.status == "healthy" else 0)
        elif comp.component == "mnemosyne":
            mnemosyne_connected_gauge.set(1 if comp.status == "healthy" else 0)
        elif comp.component == "redis":
            redis_connected_gauge.set(1 if comp.status == "healthy" else 0)


def update_sync_metrics(plan):
    """Update Prometheus metrics from SyncPlan."""
    sync_operations_counter.inc(plan.total_operations)


# ========================================
#  Metrics Endpoint
# ========================================

async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
