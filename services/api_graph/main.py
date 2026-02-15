"""
Graph Orchestrator API service.
Orchestrates LangGraph execution via HTTP (request-response pattern).
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.auth import AuthMiddleware

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
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.SERVICE_NAME, settings.SERVICE_VERSION)
    logger.info("  Audit: %s | %s:%s", settings.AUDIT_ENABLED, settings.SERVICE_HOST, settings.SERVICE_PORT)
    graph_adapter = GraphOrchestrationAdapter()
    persistence = GraphPersistence()
    set_adapters(graph_adapter, persistence)
    logger.info("Adapters initialized")
    yield
    logger.info("Shutting down %s", settings.SERVICE_NAME)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="LangGraph orchestrator with audit monitoring (Orchestrator pattern: request-response HTTP)",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

# Prometheus middleware
app.middleware("http")(prometheus_middleware)

# Auth middleware (opt-in — disabled unless VITRUVYAN_AUTH_ENABLED=true)
app.add_middleware(AuthMiddleware)

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

