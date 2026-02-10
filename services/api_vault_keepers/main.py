"""
Vault Keepers — Sacred Order API (LIVELLO 2)
FastAPI bootstrap. Logic delegated to adapters/bus_adapter.py.
"""
import logging
import sys
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

sys.path.append("/app")

from api_vault_keepers.api.routes import router, set_bus_adapter
from api_vault_keepers.config import settings
from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("VaultKeepers")

app = FastAPI(
    title="🏰 Vitruvyan Vault Keepers",
    description="Sacred Memory Custodians",
    version=settings.SERVICE_VERSION,
    docs_url="/vault/docs",
    redoc_url="/vault/redoc",
)
app.include_router(router)
Instrumentator().instrument(app).expose(app)

bus_adapter: VaultBusAdapter | None = None
@app.on_event("startup")
async def startup():
    global bus_adapter
    logger.info("🏰 Vault Keepers awakening...")
    logger.info(f"Port: {settings.SERVICE_PORT} | Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    logger.info(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    
    bus_adapter = VaultBusAdapter()
    set_bus_adapter(bus_adapter)
    
    logger.info(f"📻 Sacred Channels: {', '.join(settings.SACRED_CHANNELS)}")
    logger.info("✅ Vault Keepers ready")

@app.on_event("shutdown")
async def shutdown():
    logger.info("🏰 Vault Keepers entering dormancy...")

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
