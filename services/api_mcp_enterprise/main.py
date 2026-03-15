"""MCP Enterprise Server — Enterprise MCP Bridge — Port 8021."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from adapters.enterprise_adapter import get_enterprise_adapter

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    adapter = get_enterprise_adapter()
    logger.info("=" * 60)
    logger.info("MCP Enterprise Server starting")
    logger.info("   Domain: enterprise")
    logger.info("   Core MCP: %s", cfg.core_mcp_url)
    logger.info("   Port: %s", cfg.port)
    if adapter:
        logger.info("   Enterprise aliases: %s", sorted(adapter.config.tool_aliases.keys()))
    logger.info("=" * 60)
    yield
    logger.info("MCP Enterprise Server shutting down")


app = FastAPI(
    title="MCP Enterprise Server",
    description="Enterprise-specialized MCP Bridge (ERP tool schemas + arg normalization)",
    version="1.0.0",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import router as core_router  # noqa: E402
from api.routes_enterprise import router as enterprise_router  # noqa: E402

app.include_router(core_router)
app.include_router(enterprise_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=get_config().port, log_level="info")
