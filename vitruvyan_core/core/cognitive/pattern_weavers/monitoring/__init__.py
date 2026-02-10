"""
Pattern Weavers - Monitoring Constants
======================================

Metric and health check name constants.
Pure Python - no prometheus_client import.

Actual Prometheus metrics are instantiated in LIVELLO 2 (service layer).
"""


class MetricNames:
    """
    Prometheus metric name constants.
    
    Pattern: pattern_weavers_<metric_type>_<unit>
    """
    
    # Counters
    WEAVE_REQUESTS_TOTAL = "pattern_weavers_weave_requests_total"
    CONCEPTS_FOUND_TOTAL = "pattern_weavers_concepts_found_total"
    KEYWORD_MATCHES_TOTAL = "pattern_weavers_keyword_matches_total"
    EMBEDDING_REQUESTS_TOTAL = "pattern_weavers_embedding_requests_total"
    ERRORS_TOTAL = "pattern_weavers_errors_total"
    
    # Histograms
    WEAVE_DURATION_SECONDS = "pattern_weavers_weave_duration_seconds"
    EMBEDDING_DURATION_SECONDS = "pattern_weavers_embedding_duration_seconds"
    SIMILARITY_SEARCH_DURATION_SECONDS = "pattern_weavers_similarity_search_duration_seconds"
    
    # Gauges
    TAXONOMY_SIZE = "pattern_weavers_taxonomy_size"
    EMBEDDING_CACHE_SIZE = "pattern_weavers_embedding_cache_size"
    ACTIVE_REQUESTS = "pattern_weavers_active_requests"


class HealthCheckNames:
    """Health check component names."""
    
    QDRANT = "qdrant"
    POSTGRES = "postgres"
    REDIS = "redis"
    EMBEDDING_API = "embedding_api"
    TAXONOMY = "taxonomy"


class Labels:
    """Standard metric label values."""
    
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_TIMEOUT = "timeout"
    
    MATCH_TYPE_SEMANTIC = "semantic"
    MATCH_TYPE_KEYWORD = "keyword"
    MATCH_TYPE_EXACT = "exact"
