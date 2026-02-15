"""
Memory Orders — API Entry Point (LIVELLO 2)

Thin FastAPI bootstrap. All logic delegated to:
  - api/routes.py            HTTP endpoints
  - adapters/bus_adapter.py  Domain orchestration
  - adapters/persistence.py  I/O operations
  - monitoring/health.py     Metrics

Sacred Order: Memory & Coherence
Layer: Service (LIVELLO 2 — main entry point)
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI

sys.path.insert(0, '/app')

from api_memory_orders.api import router, set_bus_adapter
from api_memory_orders.config import settings
from api_memory_orders.adapters import MemoryBusAdapter
from api_memory_orders.monitoring import metrics_endpoint

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MemoryOrders")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.SERVICE_NAME)
    logger.info("PostgreSQL: %s:%s | Qdrant: %s:%s | Redis: %s:%s",
                settings.POSTGRES_HOST, settings.POSTGRES_PORT,
                settings.QDRANT_HOST, settings.QDRANT_PORT,
                settings.REDIS_HOST, settings.REDIS_PORT)
    bus_adapter = MemoryBusAdapter()
    set_bus_adapter(bus_adapter)
    logger.info("Bus adapter initialized — Memory Orders ready")
    yield
    logger.info("Shutting down Memory Orders")


app = FastAPI(
    title="Memory Orders",
    version="2.0.0",
    description="Dual-Memory Coherence System (LIVELLO 1 + LIVELLO 2)",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    host = "0.0.0.0"
    port = settings.SERVICE_PORT
    
    logger.info(f"Starting uvicorn on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
