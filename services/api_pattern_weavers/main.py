"""Pattern Weavers API — Sacred Order #5 (REASON / Semantic Layer) — Port 8017."""

import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from .api import router
from .config import get_config

logger = logging.getLogger(__name__)

# Prometheus metrics
QUERIES = Counter("weaver_queries_total", "Total queries", ["status"])
LATENCY = Histogram("weaver_query_duration_seconds", "Query latency",
                    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    config = get_config()
    logger.info(f"✅ Pattern Weavers starting on port {config.service.port}")
    yield
    logger.info("🛑 Pattern Weavers shutting down")


app = FastAPI(
    title="Pattern Weavers API",
    description="Semantic Contextualization — Domain-Agnostic",
    version="2.0.0",
    lifespan=lifespan,
)

# Include routes from api/routes.py
app.include_router(router)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """API info."""
    return {
        "service": "Pattern Weavers API",
        "version": "2.0.0",
        "sacred_order": "#5 (REASON)",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8017))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
