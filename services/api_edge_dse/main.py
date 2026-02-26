"""
DSE Edge Service — FastAPI bootstrap
Design Space Exploration engine for vitruvyan-core edge deployments.
Version: 1.0.0
"""

import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .adapters.bus_adapter import DSEBusAdapter
from .adapters.persistence import DSEPersistenceAdapter
from .api.routes import router, set_adapter
from .config import config
from .streams_listener import DSEStreamsListener

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DSE Edge Service",
    description="Design Space Exploration — edge compute for vitruvyan-core",
    version=config.SERVICE_VERSION,
)

# Prometheus metrics sub-app
app.mount("/metrics", make_asgi_app())

# HTTP routes
app.include_router(router)

# Global references (set on startup)
_listener: DSEStreamsListener = None  # type: ignore[assignment]
_listener_task: asyncio.Task = None   # type: ignore[assignment]


@app.on_event("startup")
async def startup() -> None:
    global _listener, _listener_task

    persistence = DSEPersistenceAdapter()
    persistence.ensure_schema()

    adapter = DSEBusAdapter(persistence=persistence)
    set_adapter(adapter)

    _listener = DSEStreamsListener(adapter=adapter, bus=adapter.bus)
    _listener_task = asyncio.create_task(_listener.run())

    logger.info("DSE Edge Service started on port %d", config.API_PORT)


@app.on_event("shutdown")
async def shutdown() -> None:
    if _listener_task:
        _listener_task.cancel()
        try:
            await _listener_task
        except asyncio.CancelledError:
            pass
    logger.info("DSE Edge Service stopped")


if __name__ == "__main__":
    uvicorn.run(
        "services.api_edge_dse.main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
    )
