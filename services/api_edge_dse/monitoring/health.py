"""
DSE Service — Health and Prometheus Metrics (LIVELLO 2)
========================================================

Prometheus instrumentation lives HERE (not in LIVELLO 1 domain).
Metric names imported from LIVELLO 1 constants.

Last updated: Feb 26, 2026
"""

import logging
from typing import Dict, Any

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

from infrastructure.edge.dse.monitoring.metrics import DSEMetrics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prometheus instruments
# ---------------------------------------------------------------------------

dse_runs_total = Counter(
    DSEMetrics.RUNS_TOTAL,
    "Total DSE runs completed",
    ["status"],
)
dse_design_points_generated = Counter(
    DSEMetrics.DESIGN_POINTS_GENERATED,
    "Total design points generated",
    ["strategy"],
)
dse_pareto_points = Counter(
    DSEMetrics.PARETO_POINTS_COMPUTED,
    "Total Pareto-optimal points computed",
)
dse_run_duration = Histogram(
    DSEMetrics.RUN_DURATION_SECONDS,
    "DSE run duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
)
dse_pareto_ratio = Gauge(
    DSEMetrics.PARETO_RATIO_LAST_RUN,
    "Pareto ratio of the last DSE run",
)


def record_run(status: str, design_points: int, pareto_count: int,
               strategy: str, duration_s: float) -> None:
    """Update all metrics after a DSE run."""
    dse_runs_total.labels(status=status).inc()
    dse_design_points_generated.labels(strategy=strategy).inc(design_points)
    dse_pareto_points.inc(pareto_count)
    dse_run_duration.observe(duration_s)
    if design_points > 0:
        dse_pareto_ratio.set(pareto_count / design_points)


def metrics_endpoint() -> Response:
    """FastAPI endpoint: GET /metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def liveness() -> Dict[str, Any]:
    """Simple liveness probe."""
    return {"alive": True}


def readiness(bus_ok: bool, postgres_ok: bool) -> Dict[str, Any]:
    """Readiness probe — checks infrastructure connectivity."""
    healthy = bus_ok and postgres_ok
    return {
        "ready":    healthy,
        "redis":    "ok" if bus_ok else "error",
        "postgres": "ok" if postgres_ok else "error",
    }
