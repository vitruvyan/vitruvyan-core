"""
Vault Keepers — Sacred Order API (LIVELLO 2 Entry Point)

Thin FastAPI shell. All logic delegated to:
  - api/routes.py            HTTP endpoints
  - adapters/bus_adapter.py  Domain pipeline bridge
  - adapters/persistence.py  Database I/O
  - config.py                Centralized env vars

Sacred memory custodians for the Synaptic Conclave.
Divine guardians of Vitruvyan's knowledge preservation and integrity.

Sacred Order: Truth (Memory & Archival)
Layer: Service (LIVELLO 2)

Author: Vitruvyan Development Team
Refactored: Feb 9, 2026 — SERVICE_PATTERN alignment
"""
import logging
import sys

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

sys.path.append("/app")

from api_vault_keepers.api.routes import router, set_bus_adapter
from api_vault_keepers.config import settings
from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("VaultKeepers")

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="🏰 Vitruvyan Vault Keepers",
    description="Sacred Memory Custodians — SERVICE_PATTERN refactored Feb 2026",
    version=settings.SERVICE_VERSION,
    docs_url="/vault/docs",
    redoc_url="/vault/redoc",
)
app.include_router(router)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Global adapter instance
bus_adapter: VaultBusAdapter | None = None


# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global bus_adapter
    logger.info("🏰 Vault Keepers awakening...")
    logger.info(f"   Service: {settings.SERVICE_NAME}")
    logger.info(f"   Port: {settings.SERVICE_PORT}")
    logger.info(f"   Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"   PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    logger.info(f"   Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    
    # Initialize bus adapter (connects to StreamBus + PostgreSQL + Qdrant)
    bus_adapter = VaultBusAdapter()
    set_bus_adapter(bus_adapter)
    
    logger.info("🕯️  Synaptic Conclave integration activated")
    logger.info(f"   📻 Sacred Channels: {len(settings.SACRED_CHANNELS)}")
    for channel in settings.SACRED_CHANNELS:
        logger.info(f"      • {channel}")
    
    logger.info("✅ Vault Keepers ready — Sacred memory custodians on divine duty")


# ── Shutdown ─────────────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown():
    logger.info("🏰 Vault Keepers entering dormancy...")


# ── Root Health ──────────────────────────────────────────────────────────────
@app.get("/health")
async def root_health():
    """Quick health check at root level"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "vault_status": "blessed",
    }


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Vault Keepers on {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        log_level="info",
    )
