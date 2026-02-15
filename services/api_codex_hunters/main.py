#!/usr/bin/env python3
"""
Codex Hunters API Service
=========================
FastAPI service for expedition management and data discovery coordination.
Version: 2.0.0 (February 2026 - SACRED_ORDER_PATTERN)
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.middleware.auth import AuthMiddleware

from .config import get_config
from .api import router
from .monitoring import init_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    config = get_config()
    logger.info(f"🚀 Codex Hunters API starting on {config.service.host}:{config.service.port}")
    init_metrics()
    yield
    # Shutdown
    logger.info("👋 Codex Hunters API shutting down")


app = FastAPI(
    title="Codex Hunters API",
    description="Expedition management and data discovery coordination",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "codex_hunters",
        "version": "2.0.0",
        "motto": "No codex left unfound",
    }


if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "api_codex_hunters.main:app",
        host=config.service.host,
        port=config.service.port,
        reload=config.service.debug,
    )