"""FastAPI bootstrap for Edge Oculus Prime API service."""

from __future__ import annotations

import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.oculus_prime_adapter import OculusPrimeAdapter
from .adapters.runtime import build_stream_bus
from .api import router
from .config import settings


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    adapter = OculusPrimeAdapter(settings=settings, stream_bus=build_stream_bus(settings))
    adapter.ensure_uploads_dir()
    # Keep legacy attribute for compatibility with older tests/integrations.
    app.state.oculus_prime_adapter = adapter
    app.state.intake_adapter = adapter
    logger.info(
        "AEGIS OCULUS PRIME API starting (pg=%s:%s db=%s redis=%s:%s)",
        settings.postgres_host,
        settings.postgres_port,
        settings.postgres_db,
        settings.redis_host,
        settings.redis_port,
    )
    yield


app = FastAPI(
    title="AEGIS OCULUS PRIME API",
    description="Evidence Pack ingestion service for Edge interoperability",
    version=settings.service_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
