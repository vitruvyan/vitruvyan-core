"""
Vault Keepers — Sacred Order API (LIVELLO 2)
FastAPI bootstrap. Logic delegated to adapters/bus_adapter.py.
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

sys.path.append("/app")

from api_vault_keepers.api.routes import router, set_bus_adapter
from api_vault_keepers.config import settings
from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("VaultKeepers")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Vault Keepers awakening...")
    logger.info("Port: %s | Redis: %s:%s", settings.SERVICE_PORT, settings.REDIS_HOST, settings.REDIS_PORT)
    logger.info("PostgreSQL: %s:%s/%s", settings.POSTGRES_HOST, settings.POSTGRES_PORT, settings.POSTGRES_DB)
    logger.info("Qdrant: %s:%s", settings.QDRANT_HOST, settings.QDRANT_PORT)
    bus_adapter = VaultBusAdapter()
    set_bus_adapter(bus_adapter)
    logger.info("Sacred Channels: %s", ", ".join(settings.SACRED_CHANNELS))
    logger.info("Vault Keepers ready")
    yield
    logger.info("Vault Keepers entering dormancy...")


app = FastAPI(
    title="Vitruvyan Vault Keepers",
    description="Sacred Memory Custodians",
    version=settings.SERVICE_VERSION,
    docs_url="/vault/docs",
    redoc_url="/vault/redoc",
    lifespan=lifespan,
)
app.include_router(router)
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def root_health():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "vault_status": "blessed",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.SERVICE_HOST, port=settings.SERVICE_PORT, log_level="info")
