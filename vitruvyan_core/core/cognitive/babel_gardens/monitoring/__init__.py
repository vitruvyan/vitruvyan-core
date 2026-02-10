"""
Babel Gardens - Monitoring Definitions
======================================

Metric names and health check constants.
NO prometheus_client imports - just name constants.
"""


class MetricNames:
    """Prometheus metric name constants."""
    
    # Embedding metrics
    EMBEDDING_REQUESTS = "babel_embedding_requests_total"
    EMBEDDING_LATENCY = "babel_embedding_duration_seconds"
    EMBEDDING_CACHE_HITS = "babel_embedding_cache_hits_total"
    EMBEDDING_CACHE_MISSES = "babel_embedding_cache_misses_total"
    
    # Sentiment metrics
    SENTIMENT_REQUESTS = "babel_sentiment_requests_total"
    SENTIMENT_LATENCY = "babel_sentiment_duration_seconds"
    
    # Emotion metrics
    EMOTION_REQUESTS = "babel_emotion_requests_total"
    EMOTION_LATENCY = "babel_emotion_duration_seconds"
    
    # Synthesis metrics
    SYNTHESIS_REQUESTS = "babel_synthesis_requests_total"
    SYNTHESIS_LATENCY = "babel_synthesis_duration_seconds"
    
    # Topic metrics
    TOPIC_REQUESTS = "babel_topic_requests_total"
    TOPIC_LATENCY = "babel_topic_duration_seconds"
    
    # Error metrics
    ERRORS = "babel_errors_total"


class HealthCheckNames:
    """Health check component names."""
    
    EMBEDDING_MODEL = "embedding_model"
    SENTIMENT_MODEL = "sentiment_model"
    EMOTION_MODEL = "emotion_model"
    CACHE = "vector_cache"
    DATABASE = "postgres"
    VECTOR_STORE = "qdrant"
    REDIS = "redis"


class Labels:
    """Common label names for metrics."""
    
    LANGUAGE = "language"
    MODEL_TYPE = "model_type"
    STATUS = "status"
    ENDPOINT = "endpoint"
    METHOD = "method"
    ERROR_TYPE = "error_type"


__all__ = ["MetricNames", "HealthCheckNames", "Labels"]
