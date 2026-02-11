"""MCP Server — Model Context Protocol Bridge to Sacred Orders — Port 8020."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from api import router

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    logger.info("=" * 60)
    logger.info("🏛️ Vitruvyan MCP Server starting")
    logger.info(f"   LangGraph: {config.api.langgraph}")
    logger.info(f"   Pattern Weavers: {config.api.pattern_weavers}")
    logger.info(f"   Redis: {config.redis.host}:{config.redis.port}")
    logger.info(f"   Port: {config.service.port}")
    logger.info("=" * 60)
    yield
    logger.info("🛑 MCP Server shutting down")


app = FastAPI(
    title="Vitruvyan MCP Server",
    description="Model Context Protocol Bridge to Sacred Orders",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(app, host="0.0.0.0", port=config.service.port, log_level="info")
