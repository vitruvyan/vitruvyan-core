"""Embedding API — Prometheus Metrics."""

from prometheus_client import Counter, Histogram, Gauge

embedding_requests_total = Counter(
    'embedding_requests_total',
    'Total embedding requests',
    ['endpoint', 'status']
)

embedding_duration_seconds = Histogram(
    'embedding_duration_seconds',
    'Embedding generation latency',
    ['endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

model_loaded = Gauge(
    'embedding_model_loaded',
    'Whether the embedding model is loaded (1=yes, 0=no)'
)
