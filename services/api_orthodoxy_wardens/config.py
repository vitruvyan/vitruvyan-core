"""
⚖️ Orthodoxy Wardens — Service Configuration

Single source of truth for all environment variables.
No os.getenv() scattered across files.
"""

import os


def _default_postgres_host() -> str:
    """Resolve PostgreSQL host for docker and local shells."""
    explicit = os.getenv("POSTGRES_HOST") or os.getenv("PG_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_postgres"
    return "localhost"


def _default_postgres_port() -> int:
    """Resolve PostgreSQL port for docker network vs local mapped port."""
    explicit = os.getenv("POSTGRES_PORT") or os.getenv("PG_PORT")
    if explicit:
        return int(explicit)
    if os.path.exists("/.dockerenv"):
        return 5432
    return 2432


def _default_qdrant_host() -> str:
    """Resolve Qdrant host for docker and local shells."""
    explicit = os.getenv("QDRANT_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_qdrant"
    return "localhost"


def _default_redis_host() -> str:
    """Resolve Redis host for docker and local shells."""
    explicit = os.getenv("REDIS_HOST")
    if explicit:
        return explicit
    if os.path.exists("/.dockerenv"):
        return "mercator_redis"
    return "localhost"


class Settings:
    """Centralized configuration for api_orthodoxy_wardens service."""

    # Service identity
    SERVICE_NAME = "api_orthodoxy_wardens"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8006"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ORTHODOXY_DOMAIN = os.getenv("ORTHODOXY_DOMAIN", "generic").lower()
    ORTHODOXY_RULESET_VERSION = os.getenv("ORTHODOXY_RULESET_VERSION", "")

    # Redis / Cognitive Bus
    REDIS_URL = os.getenv(
        "REDIS_URL", f"redis://{_default_redis_host()}:6379/0"
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
    PG_HOST = _default_postgres_host()
    PG_PORT = _default_postgres_port()
    PG_DB = os.getenv("PG_DB", os.getenv("POSTGRES_DB", "mercator"))
    PG_USER = os.getenv("PG_USER", os.getenv("POSTGRES_USER", "mercator_user"))

    # Qdrant
    QDRANT_HOST = _default_qdrant_host()
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


settings = Settings()

if settings.ORTHODOXY_DOMAIN not in {"generic", "finance"}:
    settings.ORTHODOXY_DOMAIN = "generic"
