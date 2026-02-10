"""
Pattern Weavers Monitoring
==========================

Health checks and Prometheus metrics.
"""

import logging
from typing import Dict

from ..adapters import get_bus_adapter, get_embedding_adapter, get_persistence

logger = logging.getLogger(__name__)


async def check_all_health() -> Dict[str, bool]:
    """
    Check health of all dependencies.
    
    Returns:
        Dict with component health status
    """
    persistence = get_persistence()
    bus = get_bus_adapter()
    embedding = get_embedding_adapter()
    
    return {
        "qdrant": persistence.check_qdrant_health(),
        "postgres": persistence.check_database_health(),
        "redis": bus.check_health(),
        "embedding_service": embedding.check_health(),
    }


def get_overall_status(health: Dict[str, bool]) -> str:
    """
    Determine overall service status from component health.
    
    Args:
        health: Component health dict
        
    Returns:
        "healthy", "degraded", or "unhealthy"
    """
    healthy_count = sum(health.values())
    total = len(health)
    
    if healthy_count == total:
        return "healthy"
    elif healthy_count >= total // 2:
        return "degraded"
    else:
        return "unhealthy"
