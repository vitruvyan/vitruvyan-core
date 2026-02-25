"""Pattern Weavers API — Sacred Order #5 (REASON / Semantic Layer) — Port 8011."""

import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from core.middleware.auth import AuthMiddleware

from .config import get_config

# Ensure core agents initialized at import-time see coherent DB defaults.
_bootstrap_cfg = get_config()
os.environ.setdefault("POSTGRES_HOST", _bootstrap_cfg.postgres.host)
os.environ.setdefault("POSTGRES_PORT", str(_bootstrap_cfg.postgres.port))
os.environ.setdefault("POSTGRES_DB", _bootstrap_cfg.postgres.database)
os.environ.setdefault("POSTGRES_USER", _bootstrap_cfg.postgres.user)
os.environ.setdefault("POSTGRES_PASSWORD", _bootstrap_cfg.postgres.password)
if _bootstrap_cfg.taxonomy_path:
    os.environ.setdefault("PATTERN_TAXONOMY_PATH", _bootstrap_cfg.taxonomy_path)

from .adapters.finance_adapter import is_finance_enabled
from .api import router

logger = logging.getLogger(__name__)

# Prometheus metrics
QUERIES = Counter("weaver_queries_total", "Total queries", ["status"])
LATENCY = Histogram(
    "weaver_query_duration_seconds",
    "Query latency",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    config = get_config()
    from core.cognitive.pattern_weavers.domain import (
        PatternConfig,
        set_config as set_domain_config,
    )

    domain_config = PatternConfig.from_env()
    set_domain_config(domain_config)

    logger.info(f"✅ Pattern Weavers starting on port {config.service.port}")
    logger.info(
        "✅ Pattern domain: %s | taxonomy categories: %d",
        config.service.pattern_domain,
        len(domain_config.taxonomy.categories),
    )
    yield
    logger.info("🛑 Pattern Weavers shutting down")


app = FastAPI(
    title="Pattern Weavers API",
    description="Semantic Contextualization — Domain-Agnostic",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().service.cors_allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
if is_finance_enabled():
    from .api.routes_finance import router as finance_router

    app.include_router(finance_router)


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
        "pattern_domain": get_config().service.pattern_domain,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    cfg = get_config()
    uvicorn.run(
        app,
        host=cfg.service.host,
        port=cfg.service.port,
        log_level=cfg.service.log_level.lower(),
    )
