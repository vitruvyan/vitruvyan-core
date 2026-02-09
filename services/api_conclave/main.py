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
import sys

from fastapi import FastAPI

sys.path.append("/app")

from api_conclave.api.routes import router, set_bus_adapter
from api_conclave.config import settings
from api_conclave.adapters.bus_adapter import ConclaveBusAdapter

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("Conclave")

# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="🕯 Synaptic Conclave - Epistemic Observatory",
    description="HTTP-to-Streams bridge (Streams-native since Jan 24, 2026)",
    version=settings.SERVICE_VERSION,
)
app.include_router(router)

bus_adapter: ConclaveBusAdapter | None = None


# ── Startup ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global bus_adapter
    logger.info("Initializing Synaptic Conclave (observatory mode)")
    bus_adapter = ConclaveBusAdapter()
    set_bus_adapter(bus_adapter)
    logger.info("Conclave ready (bus_adapter=%s)", bus_adapter.is_connected)


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Conclave on %s:%s", settings.SERVICE_HOST, settings.SERVICE_PORT)
    uvicorn.run("main:app", host=settings.SERVICE_HOST, port=settings.SERVICE_PORT, log_level="info")
