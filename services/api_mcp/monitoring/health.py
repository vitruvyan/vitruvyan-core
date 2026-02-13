"""MCP Server — Health Check."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def health_check() -> dict:
    """Return MCP service health status."""
    from middleware import get_stream_bus
    stream_bus = get_stream_bus()
    return {
        "status": "healthy",
        "service": "vitruvyan_mcp_server",
        "bus": "connected" if stream_bus else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }
