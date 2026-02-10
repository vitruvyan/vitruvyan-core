"""
Graph Orchestrator API service.
Orchestrates LangGraph execution via HTTP (request-response pattern).
"""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import router, set_adapters
from .adapters.graph_adapter import GraphOrchestrationAdapter
from .adapters.persistence import GraphPersistence
from .monitoring.health import prometheus_middleware, metrics_endpoint

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="LangGraph orchestrator with audit monitoring (Orchestrator pattern: request-response HTTP)",
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

# Prometheus middleware
app.middleware("http")(prometheus_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(router)
app.get("/metrics")(metrics_endpoint)

# ─────────────────────────────────────────────────────────────────────────────
# Startup & Shutdown
# ─────────────────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Initialize adapters and audit monitoring on startup"""
    logger.info(f"🚀 Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info(f"   Audit monitoring: {'enabled' if settings.AUDIT_ENABLED else 'disabled'}")
    logger.info(f"   Service: {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")

    # Initialize adapters
    graph_adapter = GraphOrchestrationAdapter()
    persistence = GraphPersistence()
    set_adapters(graph_adapter, persistence)

    logger.info("✅ Adapters initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown audit monitoring"""
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}")

