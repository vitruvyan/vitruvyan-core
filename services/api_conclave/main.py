"""
Synaptic Conclave — Sacred Order API (LIVELLO 2 Entry Point)

Thin FastAPI shell.  All logic delegated to:
  - api/routes.py            HTTP endpoints
  - adapters/bus_adapter.py  StreamBus bridge (LIVELLO 1)
  - adapters/persistence.py  Database I/O (stub)
  - monitoring/metrics.py    Prometheus metrics
  - config.py                Centralized env vars

Follows SERVICE_PATTERN.md.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.auth import AuthMiddleware

sys.path.append("/app")

from api_conclave.api.routes import router, set_bus_adapter, set_persistence
from api_conclave.config import settings
from api_conclave.adapters.bus_adapter import ConclaveBusAdapter
from api_conclave.adapters.persistence import PersistenceAdapter

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("Conclave")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Synaptic Conclave (observatory mode)")
    bus_adapter = ConclaveBusAdapter()
    set_bus_adapter(bus_adapter)
    persistence = PersistenceAdapter()
    set_persistence(persistence)

    # Emit awakening event
    if bus_adapter.is_connected:
        try:
            bus_adapter.emit(
                channel="conclave.awakened",
                data={
                    "type": "awakened",
                    "conclave_version": settings.SERVICE_VERSION,
                    "startup_time": datetime.utcnow().isoformat() + "Z",
                    "components": ["bus_adapter", "routes", "metrics", "listener"],
                },
                emitter="conclave.startup",
            )
        except Exception as exc:
            logger.warning("Awakening event emission failed: %s", exc)

    logger.info("Conclave ready (bus_adapter=%s)", bus_adapter.is_connected)
    yield


app = FastAPI(
    title="Synaptic Conclave - Epistemic Observatory",
    description="HTTP-to-Streams bridge (Streams-native since Jan 24, 2026)",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)
app.include_router(router)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Conclave on %s:%s", settings.SERVICE_HOST, settings.SERVICE_PORT)
    uvicorn.run("main:app", host=settings.SERVICE_HOST, port=settings.SERVICE_PORT, log_level="info")
