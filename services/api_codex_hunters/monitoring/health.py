"""
Codex Hunters Monitoring
========================

Health checks and Prometheus metrics configuration.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# Prometheus Metrics (lazy initialization)
# ============================================================================

_metrics_initialized = False


def init_metrics():
    """Initialize Prometheus metrics (idempotent)."""
    global _metrics_initialized
    if _metrics_initialized:
        return
    
    try:
        from prometheus_client import Counter, Gauge, Histogram, REGISTRY
        
        # Helper to avoid duplicate registration
        def get_or_create(metric_class, name, doc, labels=None):
            for c in list(REGISTRY._collector_to_names.keys()):
                if hasattr(c, "_name") and c._name == name:
                    return c
            return metric_class(name, doc, labels or [])
        
        # Define metrics
        global codex_expeditions_total
        global codex_expeditions_active
        global codex_expedition_duration
        global codex_discoveries_total
        global codex_bindings_total
        
        codex_expeditions_total = get_or_create(
            Counter,
            "codex_expeditions",
            "Total expeditions",
            ["expedition_type", "status"],
        )
        
        codex_expeditions_active = get_or_create(
            Gauge,
            "codex_expeditions_active",
            "Active expeditions",
        )
        
        codex_expedition_duration = get_or_create(
            Histogram,
            "codex_expedition_duration_seconds",
            "Expedition duration",
            ["expedition_type"],
        )
        
        codex_discoveries_total = get_or_create(
            Counter,
            "codex_discoveries_total",
            "Total discoveries",
            ["source_type"],
        )
        
        codex_bindings_total = get_or_create(
            Counter,
            "codex_bindings_total",
            "Total bindings",
            ["storage_type"],
        )
        
        _metrics_initialized = True
        logger.info("✅ Prometheus metrics initialized")
        
    except ImportError:
        logger.warning("⚠️ prometheus_client not available")


def record_expedition_start(expedition_type: str) -> None:
    """Record expedition start metric."""
    if not _metrics_initialized:
        init_metrics()
    try:
        codex_expeditions_total.labels(
            expedition_type=expedition_type,
            status="started",
        ).inc()
        codex_expeditions_active.inc()
    except Exception:
        pass


def record_expedition_complete(expedition_type: str, duration_seconds: float) -> None:
    """Record expedition completion metric."""
    if not _metrics_initialized:
        init_metrics()
    try:
        codex_expeditions_total.labels(
            expedition_type=expedition_type,
            status="completed",
        ).inc()
        codex_expeditions_active.dec()
        codex_expedition_duration.labels(
            expedition_type=expedition_type,
        ).observe(duration_seconds)
    except Exception:
        pass


def record_discovery(source_type: str) -> None:
    """Record discovery metric."""
    if not _metrics_initialized:
        init_metrics()
    try:
        codex_discoveries_total.labels(source_type=source_type).inc()
    except Exception:
        pass


def record_binding(storage_type: str) -> None:
    """Record binding metric."""
    if not _metrics_initialized:
        init_metrics()
    try:
        codex_bindings_total.labels(storage_type=storage_type).inc()
    except Exception:
        pass


# ============================================================================
# Health Check Helpers
# ============================================================================

def get_system_health() -> Dict[str, Any]:
    """
    Get comprehensive system health status.
    
    Returns:
        Dict with health information for all components.
    """
    from ..adapters import get_bus_adapter, get_persistence
    
    persistence = get_persistence()
    bus_adapter = get_bus_adapter()
    
    checks = {
        "database": persistence.check_database_health(),
        "qdrant": persistence.check_qdrant_health(),
        "redis": bus_adapter.check_bus_health(),
        "consumers": bus_adapter.get_consumers_status(),
    }
    
    # Determine overall status
    critical_ok = checks["database"] and checks["redis"]
    all_ok = critical_ok and checks["qdrant"]
    
    if all_ok:
        status = "healthy"
    elif critical_ok:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "checks": checks,
    }
