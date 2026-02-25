"""Babel Gardens API — Sacred Order #2 (PERCEPTION / Linguistic Layer) — Port 8009."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from core.middleware.auth import AuthMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import get_config

# Ensure core agents initialized at import-time see coherent DB defaults.
_bootstrap_cfg = get_config()
os.environ.setdefault("POSTGRES_HOST", _bootstrap_cfg.postgres.host)
os.environ.setdefault("POSTGRES_PORT", str(_bootstrap_cfg.postgres.port))
os.environ.setdefault("POSTGRES_DB", _bootstrap_cfg.postgres.database)
os.environ.setdefault("POSTGRES_USER", _bootstrap_cfg.postgres.user)
os.environ.setdefault("POSTGRES_PASSWORD", _bootstrap_cfg.postgres.password)

from .modules.embedding_engine import EmbeddingEngineModule
from .modules.profile_processor import ProfileProcessorModule
from .modules.cognitive_bridge import CognitiveBridgeModule
from .modules.emotion_detector import EmotionDetectorModule
from .modules.sentiment_fusion import SentimentFusionModule
from .shared.model_manager import model_manager
from .shared.vector_cache import vector_cache
from .api.routes_embeddings import router as embedding_router
from .api.routes_admin import router as admin_router
from .api.routes_emotion import router as emotion_router
from .api.routes_sentiment import router as sentiment_router
from .adapters.finance_adapter import is_finance_enabled

# Comprehension Engine v3 (feature-flagged)
_COMPREHENSION_V3 = os.getenv("BABEL_COMPREHENSION_V3", "0") == "1"

logger = logging.getLogger(__name__)


class BabelGardensService:
    """Unified service facade."""
    def __init__(self):
        self.semantic_grove = EmbeddingEngineModule()
        self.profile_processor = ProfileProcessorModule()
        self.cognitive_bridge = CognitiveBridgeModule()
        self.emotion_detector = EmotionDetectorModule()
        self.sentiment_fusion = SentimentFusionModule()
        # Comprehension Engine v3 (created only when feature-flagged)
        self.comprehension_adapter = None
        self.signal_fusion_adapter = None

service: BabelGardensService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    config = get_config()
    logger.info(f"✅ Babel Gardens starting on port {config.service.port}")
    service = BabelGardensService()
    await model_manager.initialize()

    # Comprehension Engine v3 bootstrap (feature-flagged)
    if _COMPREHENSION_V3:
        from .adapters.comprehension_adapter import ComprehensionAdapter
        from .adapters.signal_fusion_adapter import SignalFusionAdapter
        from core.cognitive.babel_gardens.governance.signal_registry import (
            get_comprehension_registry,
            get_signal_contributor_registry,
        )

        service.comprehension_adapter = ComprehensionAdapter()
        service.signal_fusion_adapter = SignalFusionAdapter()

        # Register finance plugins when BABEL_DOMAIN=finance
        if is_finance_enabled():
            from domains.finance.babel_gardens.finance_comprehension_plugin import (
                FinanceComprehensionPlugin,
            )
            registry = get_comprehension_registry()
            registry.register(FinanceComprehensionPlugin())
            registry.set_default_domain("finance")

            from .plugins.finbert_contributor import FinBERTContributor
            contributor = FinBERTContributor()
            if contributor.is_available():
                get_signal_contributor_registry().register(contributor)
                logger.info("FinBERTContributor registered (transformers available)")
            else:
                logger.info("FinBERTContributor skipped (transformers not installed)")

        logger.info("Comprehension Engine v3 initialized")

    yield
    logger.info("🛑 Babel Gardens shutting down")
    await model_manager.cleanup()


app = FastAPI(
    title="Babel Gardens API",
    description="Multilingual Semantic Processing",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware,
                   allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
                   allow_credentials=True,
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


# ── Route layer (thin HTTP adapters → modules) ──
app.include_router(embedding_router)
app.include_router(admin_router)
app.include_router(emotion_router)
app.include_router(sentiment_router)

if is_finance_enabled():
    from .api.routes_finance import router as finance_router

    app.include_router(finance_router)

if _COMPREHENSION_V3:
    from .api.routes_comprehension import router as comprehension_router

    app.include_router(comprehension_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8009)), log_level="info")
