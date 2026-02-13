"""
Graph Orchestrator Prometheus Metrics & Health Monitoring

All Prometheus metrics definitions and middleware.
Separates monitoring concerns from business logic.

Layer: LIVELLO 2 (Service)
"""

import time
import logging
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logger = logging.getLogger(__name__)


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Request counters
graph_requests_total = Counter(
    'graph_requests_total',
    'Total number of requests to Graph API',
    ['route', 'method', 'status']
)

graph_failures_total = Counter(
    'graph_failures_total',
    'Total number of failed requests to Graph API',
    ['route', 'error_type']
)

# Latency histograms
graph_request_duration_seconds = Histogram(
    'graph_request_duration_seconds',
    'Request duration in seconds',
    ['route', 'method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

graph_execution_duration_seconds = Histogram(
    'graph_execution_duration_seconds',
    'Graph execution duration in seconds',
    ['graph_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0]
)

# Gauge for inflight requests
api_requests_inflight = Gauge(
    'api_requests_inflight',
    'Number of requests currently being processed'
)

# DEPRECATED (Feb 2026): CrewAI removed
# crew_agent_latency_seconds = Histogram(
#     'crew_agent_latency_seconds',
#     'CrewAI agent execution latency',
#     ['agent_type'],
#     buckets=[1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 60.0, 120.0]
# )

# Graph node execution metrics
graph_node_executions_total = Counter(
    'graph_node_executions_total',
    'Total number of graph node executions',
    ['node_name', 'status']
)


# ============================================================================
# PROMETHEUS MIDDLEWARE
# ============================================================================

async def prometheus_middleware(request: Request, call_next):
    """
    Middleware to collect Prometheus metrics for all requests.
    
    Tracks:
    - Request count by route/method/status
    - Request duration
    - Inflight requests gauge
    - Error rates (4xx/5xx)
    """
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)
    
    # Track inflight requests
    api_requests_inflight.inc()
    
    # Start timer
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        route = request.url.path
        method = request.method
        status = response.status_code
        
        graph_requests_total.labels(route=route, method=method, status=status).inc()
        graph_request_duration_seconds.labels(route=route, method=method).observe(duration)
        
        # Track failures (4xx and 5xx)
        if status >= 400:
            error_type = "client_error" if status < 500 else "server_error"
            graph_failures_total.labels(route=route, error_type=error_type).inc()
        
        return response
        
    except Exception as e:
        # Record exception
        duration = time.time() - start_time
        route = request.url.path
        method = request.method
        
        graph_failures_total.labels(route=route, error_type="exception").inc()
        graph_requests_total.labels(route=route, method=method, status=500).inc()
        graph_request_duration_seconds.labels(route=route, method=method).observe(duration)
        
        logger.error(f"Exception in {route}: {e}", exc_info=True)
        raise
        
    finally:
        # Decrement inflight counter
        api_requests_inflight.dec()


# ============================================================================
# PROMETHEUS ENDPOINT
# ============================================================================

async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    Exposes all collected metrics in Prometheus format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
