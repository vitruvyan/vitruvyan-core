"""Babel Gardens API — Sacred Order #2 (PERCEPTION / Linguistic Layer) — Port 8009."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import get_config
from .modules.embedding_engine import EmbeddingEngineModule
from .modules.sentiment_fusion import SentimentFusionModule
from .modules.profile_processor import ProfileProcessorModule
from .modules.cognitive_bridge import CognitiveBridgeModule
from .shared.model_manager import model_manager
from .shared.vector_cache import vector_cache

logger = logging.getLogger(__name__)


class BabelGardensService:
    """Unified service facade."""
    def __init__(self):
        self.semantic_grove = EmbeddingEngineModule()
        self.emotional_meadow = SentimentFusionModule()
        self.profile_processor = ProfileProcessorModule()
        self.cognitive_bridge = CognitiveBridgeModule()

service: BabelGardensService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    config = get_config()
    logger.info(f"✅ Babel Gardens starting on port {config.service.port}")
    service = BabelGardensService()
    await model_manager.initialize()
    yield
    logger.info("🛑 Babel Gardens shutting down")
    await model_manager.cleanup()


app = FastAPI(
    title="Babel Gardens API",
    description="Multilingual Semantic Processing",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    from .adapters import get_persistence, get_bus_adapter
    return {
        "status": "healthy", "service": "babel_gardens", "version": "2.0.0",
        "components": {
            "models": model_manager.is_healthy(), "cache": vector_cache.is_healthy(),
            "postgres": get_persistence().check_database_health(),
            "redis": get_bus_adapter().check_health(),
        },
    }


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    return {"service": "Babel Gardens", "version": "2.0.0", "sacred_order": "#2", "docs": "/docs"}


# Include legacy routes for backward compatibility
try:
    from ._legacy.main_legacy import app as legacy_app
    for route in legacy_app.routes:
        if hasattr(route, "path") and route.path not in ["/", "/health", "/metrics", "/docs", "/openapi.json"]:
            app.routes.append(route)
except ImportError:
    logger.warning("Legacy routes not available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8009)), log_level="info")