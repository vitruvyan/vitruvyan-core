"""Embedding API — Health Check."""

import logging
from datetime import datetime
from ..services import get_embedding_service
from ..config import get_config

logger = logging.getLogger(__name__)


async def health_check() -> dict:
    """Return component-level health status."""
    config = get_config()
    service = get_embedding_service()
    components = service.health_check()
    all_healthy = all(v == "healthy" for v in components.values())
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "service": "vitruvyan_embedding_api",
        "version": "1.0.0",
        "model": config.model.name,
    }
