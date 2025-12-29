"""
vitruvyan_os.services.core.api_graph
=====================================

FastAPI service exposing LangGraph conversational orchestration.

Port: 8004
Sacred Order: Orchestration (Order II)

Endpoints:
----------
- POST /run: Execute LangGraph workflow (single invocation)
- GET /health: Health check
- GET /metrics: Prometheus metrics

Metrics:
--------
- graph_requests_total (Counter)
- graph_failures_total (Counter)
- graph_request_duration_seconds (Histogram)
- graph_execution_duration_seconds (Histogram)
- vsgs_grounding_requests (Counter) - VSGS semantic grounding
- vsgs_grounding_hits (Counter) - VSGS cache hits

Dependencies:
-------------
- vitruvyan_os.core.orchestration.langgraph: Graph execution engine

Version: 1.0.5
"""

__version__ = '1.0.5'
__port__ = 8004
__sacred_order__ = 'Orchestration (Order II)'
