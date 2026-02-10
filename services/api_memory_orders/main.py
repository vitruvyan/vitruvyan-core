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
from fastapi import FastAPI

# Add paths for imports
sys.path.insert(0, '/app')

from api_memory_orders.api import router, set_bus_adapter
from api_memory_orders.config import settings
from api_memory_orders.adapters import MemoryBusAdapter
from api_memory_orders.monitoring import metrics_endpoint

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("MemoryOrders")

# Create FastAPI app
app = FastAPI(
    title="Memory Orders",
    version="2.0.0",
    description="Dual-Memory Coherence System (LIVELLO 1 + LIVELLO 2)"
)

# Include router
app.include_router(router)

# Global bus adapter
bus_adapter = None


@app.on_event("startup")
async def startup():
    """Initialize bus adapter on startup."""
    global bus_adapter
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.SERVICE_NAME}")
    logger.info(f"PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info("=" * 60)
    
    try:
        # Initialize bus adapter
        bus_adapter = MemoryBusAdapter()
        set_bus_adapter(bus_adapter)
        logger.info("✅ Bus adapter initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    logger.info("🚀 Memory Orders ready")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down Memory Orders")


# Prometheus metrics endpoint
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
