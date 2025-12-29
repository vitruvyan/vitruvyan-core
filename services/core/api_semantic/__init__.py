"""
API Semantic — Cognitive Service (Tier 1)
Sacred Order: Perception (Order I)

FastAPI service exposing semantic_engine parsing capabilities via HTTP.
Provides semantic matching and intent extraction for user queries.

Architecture:
- Endpoint: POST /semantic_match
- Metrics: Prometheus instrumentation
- Health: GET /health, GET /metrics

Dependencies:
- Cognitive Tier 1: semantic_engine (parse_user_input)

Performance:
- Average latency: <50ms
- Semantic matching operations tracked
- Operational status gauge for monitoring
"""

__version__ = "1.0.1"
__sacred_order__ = "Perception (Order I)"
