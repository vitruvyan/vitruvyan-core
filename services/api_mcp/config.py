# services/api_mcp/config.py
"""Centralized configuration for MCP Server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _in_docker() -> bool:
    """Best-effort check for container runtime."""
    return os.path.exists("/.dockerenv")


def _default_postgres_host() -> str:
    explicit = os.getenv("POSTGRES_HOST") or os.getenv("PG_HOST")
    if explicit:
        return explicit
    return "mercator_postgres" if _in_docker() else "localhost"


def _default_postgres_port() -> int:
    explicit = os.getenv("POSTGRES_PORT") or os.getenv("PG_PORT")
    if explicit:
        return int(explicit)
    return 5432 if _in_docker() else 2432


def _default_redis_host() -> str:
    explicit = os.getenv("REDIS_HOST")
    if explicit:
        return explicit
    return "mercator_redis" if _in_docker() else "localhost"


def _default_redis_port() -> int:
    explicit = os.getenv("REDIS_PORT")
    if explicit:
        return int(explicit)
    return 6379 if _in_docker() else 2379


def _default_neural_engine_url() -> str:
    explicit = os.getenv("NEURAL_ENGINE_API")
    if explicit:
        return explicit
    return "http://neural_engine:8003" if _in_docker() else "http://localhost:2003"


def _default_langgraph_url() -> str:
    explicit = os.getenv("LANGGRAPH_URL") or os.getenv("LANGGRAPH_API")
    if explicit:
        return explicit
    return "http://graph:8004" if _in_docker() else "http://localhost:2004"


def _default_pattern_weavers_url() -> str:
    explicit = os.getenv("PATTERN_WEAVERS_API")
    if explicit:
        return explicit
    # Pattern Weavers runs on container port 8011, mapped to localhost:2017.
    return "http://pattern_weavers:8011" if _in_docker() else "http://localhost:2017"


@dataclass(frozen=True)
class ServiceConfig:
    """MCP service configuration."""

    port: int = 8020
    log_level: str = "INFO"
    domain: str = "generic"


@dataclass(frozen=True)
class APIEndpoints:
    """External API endpoints."""

    neural_engine: str = "http://localhost:2003"
    langgraph: str = "http://localhost:2004"
    pattern_weavers: str = "http://localhost:2017"


@dataclass(frozen=True)
class RedisConfig:
    """Redis Cognitive Bus configuration."""

    host: str = "localhost"
    port: int = 2379


@dataclass(frozen=True)
class PostgresConfig:
    """PostgreSQL configuration (centralized, no hardcoded credentials)."""

    host: str = "localhost"
    port: int = 2432
    database: str = "mercator"
    user: str = "mercator_user"
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))


@dataclass(frozen=True)
class ValidationConfig:
    """
    Orthodoxy Wardens validation thresholds (config-driven, domain-agnostic).
    """

    z_score_threshold: float = 3.0
    composite_threshold: float = 5.0
    min_summary_words: int = 100
    max_summary_words: int = 200
    default_factor_keys: List[str] = field(
        default_factory=lambda: [
            "factor_1",
            "factor_2",
            "factor_3",
            "factor_4",
            "factor_5",
        ]
    )


@dataclass(frozen=True)
class FinanceConfig:
    """Finance-specific MCP overrides (active only when MCP_DOMAIN=finance)."""

    signal_table: str = ""
    signal_entity_column: str = ""
    expose_legacy_tools: bool = True


@dataclass(frozen=True)
class MCPConfig:
    """Master configuration."""

    service: ServiceConfig
    api: APIEndpoints
    redis: RedisConfig
    postgres: PostgresConfig
    validation: ValidationConfig
    finance: FinanceConfig


_config: MCPConfig | None = None


def get_config() -> MCPConfig:
    """Get or create configuration from environment."""
    global _config
    if _config is None:
        service_domain = os.getenv("MCP_DOMAIN", "generic").lower()
        if service_domain not in {"generic", "finance"}:
            service_domain = "generic"

        _config = MCPConfig(
            service=ServiceConfig(
                port=int(os.getenv("PORT", "8020")),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                domain=service_domain,
            ),
            api=APIEndpoints(
                neural_engine=_default_neural_engine_url(),
                langgraph=_default_langgraph_url(),
                pattern_weavers=_default_pattern_weavers_url(),
            ),
            redis=RedisConfig(
                host=_default_redis_host(),
                port=_default_redis_port(),
            ),
            postgres=PostgresConfig(
                host=_default_postgres_host(),
                port=_default_postgres_port(),
                database=os.getenv("POSTGRES_DB", "mercator"),
                user=os.getenv("POSTGRES_USER", "mercator_user"),
            ),
            validation=ValidationConfig(
                z_score_threshold=float(os.getenv("MCP_Z_THRESHOLD", "3.0")),
                composite_threshold=float(os.getenv("MCP_COMPOSITE_THRESHOLD", "5.0")),
                min_summary_words=int(os.getenv("MCP_MIN_SUMMARY_WORDS", "100")),
                max_summary_words=int(os.getenv("MCP_MAX_SUMMARY_WORDS", "200")),
                default_factor_keys=[
                    k.strip()
                    for k in os.getenv(
                        "MCP_FACTOR_KEYS",
                        "factor_1,factor_2,factor_3,factor_4,factor_5",
                    ).split(",")
                    if k.strip()
                ],
            ),
            finance=FinanceConfig(
                signal_table=os.getenv("MCP_FINANCE_SIGNAL_TABLE", "").strip(),
                signal_entity_column=os.getenv(
                    "MCP_FINANCE_SIGNAL_ENTITY_COLUMN",
                    "",
                ).strip(),
                expose_legacy_tools=os.getenv(
                    "MCP_FINANCE_EXPOSE_LEGACY_TOOLS",
                    "true",
                ).lower()
                in {"1", "true", "yes", "on"},
            ),
        )

    return _config
