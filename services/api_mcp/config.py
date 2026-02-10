# services/api_mcp/config.py
"""Centralized configuration for MCP Server."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceConfig:
    """MCP service configuration."""
    port: int = 8020
    log_level: str = "DEBUG"


@dataclass(frozen=True)
class APIEndpoints:
    """External API endpoints."""
    neural_engine: str = "http://omni_neural_engine:8003"
    langgraph: str = "http://omni_api_graph:8004"
    pattern_weavers: str = "http://omni_pattern_weavers:8017"


@dataclass(frozen=True)
class RedisConfig:
    """Redis Cognitive Bus configuration."""
    host: str = "omni_redis"
    port: int = 6379


@dataclass(frozen=True)
class MCPConfig:
    """Master configuration."""
    service: ServiceConfig
    api: APIEndpoints
    redis: RedisConfig


_config: MCPConfig = None


def get_config() -> MCPConfig:
    """Get or create configuration from environment."""
    global _config
    if _config is None:
        _config = MCPConfig(
            service=ServiceConfig(
                port=int(os.getenv("PORT", "8020")),
                log_level=os.getenv("LOG_LEVEL", "DEBUG"),
            ),
            api=APIEndpoints(
                neural_engine=os.getenv("NEURAL_ENGINE_API", "http://omni_neural_engine:8003"),
                langgraph=os.getenv("LANGGRAPH_URL", "http://omni_api_graph:8004"),
                pattern_weavers=os.getenv("PATTERN_WEAVERS_API", "http://omni_pattern_weavers:8017"),
            ),
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "omni_redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            ),
        )
    return _config
