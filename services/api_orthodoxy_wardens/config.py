"""
⚖️ Orthodoxy Wardens — Service Configuration

Single source of truth for all environment variables.
No os.getenv() scattered across files.
"""

import os


class Settings:
    """Centralized configuration for api_orthodoxy_wardens service."""

    # Service identity
    SERVICE_NAME = "api_orthodoxy_wardens"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8018"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Redis / Cognitive Bus
    REDIS_URL = os.getenv(
        "REDIS_URL", "redis://vitruvyan_redis_master:6379"
    )
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "orthodoxy_wardens")
    CONSUMER_NAME = os.getenv("CONSUMER_NAME", "warden_1")

    # Sacred Channels (inbound)
    SACRED_CHANNELS = [
        "orthodoxy.audit.requested",
        "orthodoxy.validation.requested",
        "engine.eval.completed",
        "babel.sentiment.completed",
        "memory.write.completed",
        "vee.explanation.completed",
        "langgraph.response.completed",
    ]

    # PostgreSQL
    PG_HOST = os.getenv("PG_HOST", "core_postgres")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "vitruvyan")
    PG_USER = os.getenv("PG_USER", "vitruvyan_user")

    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "vitruvyan_qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


settings = Settings()
