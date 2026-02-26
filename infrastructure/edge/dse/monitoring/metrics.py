"""
DSE Monitoring — Metric Name Constants
========================================

RULE (LIVELLO 1): constants ONLY.
No prometheus_client, no instrumentation here.
Actual Prometheus counters/gauges live in LIVELLO 2: services/api_edge_dse/monitoring/health.py

Usage (in LIVELLO 2):
    from infrastructure.edge.dse.monitoring import DSEMetrics
    from prometheus_client import Counter
    runs_total = Counter(DSEMetrics.RUNS_TOTAL, "DSE runs completed")

Last updated: Feb 26, 2026
"""


class DSEMetrics:
    """Canonical Prometheus metric names for the DSE service."""

    # Counters
    RUNS_TOTAL = "dse_runs_total"
    RUNS_FAILED = "dse_runs_failed_total"
    DESIGN_POINTS_GENERATED = "dse_design_points_generated_total"
    PARETO_POINTS_COMPUTED = "dse_pareto_points_computed_total"
    SAMPLING_STRATEGY_SELECTED = "dse_sampling_strategy_selected_total"
    EVENTS_CONSUMED = "dse_events_consumed_total"
    EVENTS_PRODUCED = "dse_events_produced_total"

    # Histograms / Summaries
    RUN_DURATION_SECONDS = "dse_run_duration_seconds"
    SAMPLING_DURATION_SECONDS = "dse_sampling_duration_seconds"
    PARETO_DURATION_SECONDS = "dse_pareto_duration_seconds"

    # Gauges
    DESIGN_POINTS_LAST_RUN = "dse_design_points_last_run"
    PARETO_RATIO_LAST_RUN = "dse_pareto_ratio_last_run"
