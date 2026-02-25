"""MCP Server — Model Context Protocol Bridge to Sacred Orders — Port 8020."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.auth import AuthMiddleware

from config import get_config
from api import router
from adapters.finance_adapter import get_finance_adapter, is_finance_enabled

_bootstrap_config = get_config()
logging.basicConfig(
    level=getattr(logging, _bootstrap_config.service.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    logger.info("=" * 60)
    logger.info("🏛️ Mercator MCP Server starting")
    logger.info(f"   Domain: {config.service.domain}")
    logger.info(f"   LangGraph: {config.api.langgraph}")
    logger.info(f"   Pattern Weavers: {config.api.pattern_weavers}")
    logger.info(f"   Redis: {config.redis.host}:{config.redis.port}")
    logger.info(f"   PostgreSQL: {config.postgres.host}:{config.postgres.port}/{config.postgres.database}")
    logger.info(f"   Port: {config.service.port}")
    if is_finance_enabled():
        finance_adapter = get_finance_adapter()
        if finance_adapter is not None:
            logger.info("   Finance aliases: %s", sorted(finance_adapter.config.tool_aliases.keys()))
    logger.info("=" * 60)
    yield
    logger.info("🛑 MCP Server shutting down")


app = FastAPI(
    title="Mercator MCP Server",
    description="Model Context Protocol Bridge to Sacred Orders",
    version="1.0.0",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=_ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
if is_finance_enabled():
    from api.routes_finance import router as finance_router

    app.include_router(finance_router)


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(app, host="0.0.0.0", port=config.service.port, log_level="info")
