"""Centralized configuration for MCP Enterprise Server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EnterpriseServiceConfig:
    """MCP Enterprise service configuration."""

    port: int = 8021
    log_level: str = "INFO"
    core_mcp_url: str = "http://localhost:8020"
    langgraph_url: str = "http://localhost:9004"
    neural_engine_url: str = "http://localhost:8003"
    pattern_weavers_url: str = "http://localhost:8017"
    postgres_host: str = "localhost"
    postgres_port: int = 9432
    postgres_db: str = "vitruvyan_core"
    postgres_user: str = "vitruvyan_core_user"
    redis_host: str = "localhost"
    redis_port: int = 6379


_config: EnterpriseServiceConfig | None = None


def get_config() -> EnterpriseServiceConfig:
    """Get or create configuration from environment."""
    global _config
    if _config is None:
        _config = EnterpriseServiceConfig(
            port=int(os.getenv("PORT", "8021")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            core_mcp_url=os.getenv("MCP_CORE_URL", "http://localhost:8020"),
            langgraph_url=os.getenv("LANGGRAPH_URL", "http://localhost:9004"),
            neural_engine_url=os.getenv("NEURAL_ENGINE_API", "http://localhost:8003"),
            pattern_weavers_url=os.getenv("PATTERN_WEAVERS_API", "http://localhost:8017"),
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "9432")),
            postgres_db=os.getenv("POSTGRES_DB", "vitruvyan_core"),
            postgres_user=os.getenv("POSTGRES_USER", "vitruvyan_core_user"),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
        )
    return _config
