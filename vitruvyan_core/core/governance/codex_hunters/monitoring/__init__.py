"""
Codex Hunters - Monitoring Constants
====================================

Metric name constants for Prometheus/monitoring.
NO prometheus_client imports - just string constants.

Actual metric instantiation happens in LIVELLO 2 (service layer).

Author: Vitruvyan Core Team
Created: February 2026
"""


class MetricNames:
    """
    Prometheus metric name constants.
    
    Naming convention: codex_hunters_<domain>_<metric>_<unit>
    
    Usage in LIVELLO 2:
        from prometheus_client import Counter
        from core.governance.codex_hunters.monitoring import MetricNames
        
        discoveries_total = Counter(
            MetricNames.DISCOVERIES_TOTAL,
            MetricNames.DISCOVERIES_TOTAL_HELP,
            ["source"]
        )
    """
    
    # Counters
    DISCOVERIES_TOTAL = "codex_hunters_discoveries_total"
    DISCOVERIES_TOTAL_HELP = "Total number of entity discoveries"
    
    RESTORATIONS_TOTAL = "codex_hunters_restorations_total"
    RESTORATIONS_TOTAL_HELP = "Total number of entity restorations"
    
    BINDINGS_TOTAL = "codex_hunters_bindings_total"
    BINDINGS_TOTAL_HELP = "Total number of entity bindings"
    
    EXPEDITIONS_TOTAL = "codex_hunters_expeditions_total"
    EXPEDITIONS_TOTAL_HELP = "Total number of expeditions"
    
    ERRORS_TOTAL = "codex_hunters_errors_total"
    ERRORS_TOTAL_HELP = "Total number of errors"
    
    # Gauges
    ACTIVE_EXPEDITIONS = "codex_hunters_active_expeditions"
    ACTIVE_EXPEDITIONS_HELP = "Number of currently running expeditions"
    
    PENDING_ENTITIES = "codex_hunters_pending_entities"
    PENDING_ENTITIES_HELP = "Number of entities pending processing"
    
    QUALITY_SCORE = "codex_hunters_quality_score"
    QUALITY_SCORE_HELP = "Average quality score of restored entities"
    
    # Histograms
    DISCOVERY_DURATION_SECONDS = "codex_hunters_discovery_duration_seconds"
    DISCOVERY_DURATION_HELP = "Time spent on discovery operations"
    DISCOVERY_DURATION_BUCKETS = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
    
    RESTORATION_DURATION_SECONDS = "codex_hunters_restoration_duration_seconds"
    RESTORATION_DURATION_HELP = "Time spent on restoration operations"
    RESTORATION_DURATION_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
    
    BINDING_DURATION_SECONDS = "codex_hunters_binding_duration_seconds"
    BINDING_DURATION_HELP = "Time spent on binding operations"
    BINDING_DURATION_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
    
    EXPEDITION_DURATION_SECONDS = "codex_hunters_expedition_duration_seconds"
    EXPEDITION_DURATION_HELP = "Total expedition duration"
    EXPEDITION_DURATION_BUCKETS = [1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
    
    # Standard label names
    LABEL_SOURCE = "source"
    LABEL_STATUS = "status"
    LABEL_EXPEDITION_TYPE = "expedition_type"
    LABEL_ERROR_TYPE = "error_type"


class HealthCheckNames:
    """Health check component names."""
    
    POSTGRES = "postgres"
    QDRANT = "qdrant"
    REDIS = "redis"
    CONSUMERS = "consumers"
    EXPEDITIONS = "expeditions"
