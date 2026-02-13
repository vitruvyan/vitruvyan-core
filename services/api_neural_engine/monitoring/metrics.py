"""Neural Engine — Prometheus Metrics"""
from prometheus_client import Counter, Histogram, Gauge

# HTTP request metrics
http_requests_total = Counter(
    'neural_engine_http_requests_total',
    'Total HTTP requests to Neural Engine',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'neural_engine_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Engine processing metrics
screening_requests_total = Counter(
    'neural_engine_screening_requests_total',
    'Total screening requests processed',
    ['profile', 'stratification_mode']
)

screening_duration_seconds = Histogram(
    'neural_engine_screening_duration_seconds',
    'Screening processing time in seconds',
    ['profile'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

entities_processed_total = Counter(
    'neural_engine_entities_processed_total',
    'Total entities processed',
    ['operation']
)

data_provider_calls_total = Counter(
    'neural_engine_data_provider_calls_total',
    'Total data provider calls',
    ['method', 'status']
)

cache_hits_total = Counter(
    'neural_engine_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'neural_engine_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

service_is_healthy = Gauge(
    'neural_engine_service_healthy',
    'Service health status (1=healthy, 0=unhealthy)'
)
