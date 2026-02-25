# api_neural_engine/main.py
"""Neural Engine API — Domain-agnostic ranking service :8003"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vitruvyan_core.core.middleware.auth import AuthMiddleware

from .api.routes import router
from .config import PORT, LOG_LEVEL, CORS_ORIGINS
from .modules.engine_orchestrator import EngineOrchestrator
from .monitoring.metrics import (
    http_requests_total, http_request_duration_seconds, service_is_healthy,
)

logging.basicConfig(level=getattr(logging, str(LOG_LEVEL).upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engine orchestrator on startup, shutdown on exit."""
    logger.info("Neural Engine API starting...")
    try:
        app.state.orchestrator = EngineOrchestrator()
        await app.state.orchestrator.initialize()
        service_is_healthy.set(1)
        logger.info("Neural Engine API ready on port %d", PORT)
    except Exception as e:
        logger.error("Failed to initialize orchestrator: %s", e)
        service_is_healthy.set(0)
        raise
    yield
    logger.info("Neural Engine API shutting down...")
    await app.state.orchestrator.shutdown()
    service_is_healthy.set(0)


app = FastAPI(
    title="Vitruvyan Neural Engine API",
    description="Domain-agnostic quantitative ranking service",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def track_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    http_requests_total.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).observe(duration)
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    return response


app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Vitruvyan Neural Engine API",
        "version": "2.0.0",
        "architecture": "domain-agnostic",
        "port": PORT,
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
