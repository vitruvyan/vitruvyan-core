"""
DSE Edge Service — Configuration
==================================

ALL os.getenv() calls are centralized here.
LIVELLO 1 domain code never reads environment variables.

Last updated: Feb 26, 2026
"""

import os


class Config:
    # Service identity
    SERVICE_NAME: str = "api_edge_dse"
    SERVICE_VERSION: str = "1.0.0"
    API_PORT: int = int(os.getenv("DSE_API_PORT", "8021"))

    # DSE compute defaults
    DEFAULT_SEED: int = int(os.getenv("DSE_DEFAULT_SEED", "42"))
    DEFAULT_NUM_SAMPLES: int = int(os.getenv("DSE_DEFAULT_NUM_SAMPLES", "50"))

    # Redis Streams (Synaptic Conclave)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "core_redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # PostgreSQL (PostgresAgent)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "core_postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "vitruvyan")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "vitruvyan")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # Qdrant (QdrantAgent) — Phase 3+
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "core_qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))

    # Stream consumer group
    CONSUMER_GROUP: str = os.getenv("DSE_CONSUMER_GROUP", "dse_edge")
    CONSUMER_ID: str = os.getenv("DSE_CONSUMER_ID", "dse_1")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
