"""MCP Server — Prometheus Metrics."""

from prometheus_client import Counter, Histogram

mcp_requests_total = Counter(
    'vitruvyan_mcp_requests_total',
    'Total MCP tool requests',
    ['tool', 'status']
)

mcp_execution_duration = Histogram(
    'vitruvyan_mcp_execution_duration_seconds',
    'MCP execution duration',
    ['tool']
)
