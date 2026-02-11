# services/api_mcp/config.py
"""Centralized configuration for MCP Server."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ServiceConfig:
    """MCP service configuration."""
    port: int = 8020
    log_level: str = "INFO"  # Changed from DEBUG (production default)


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
class PostgresConfig:
    """PostgreSQL configuration (centralized, NO hardcoded credentials)."""
    host: str = "omni_postgres"
    port: int = 5432
    database: str = "vitruvyan"
    user: str = "vitruvyan"
    # CRITICAL: Password MUST come from environment, NEVER hardcoded
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))


@dataclass(frozen=True)
class ValidationConfig:
    """
    Orthodoxy Wardens validation thresholds (config-driven, domain-agnostic).
    
    All thresholds now configurable via environment variables (no hardcoded magic numbers).
    """
    # Factor score validation (z-score thresholds)
    z_score_threshold: float = 3.0  # ±3σ = 99.7% confidence interval (configurable)
    composite_threshold: float = 5.0  # Composite score extreme threshold
    
    # Summary length validation (generic, not VEE-specific)
    min_summary_words: int = 100
    max_summary_words: int = 200
    
    # Factor keys (deployment-specific taxonomy, finance is ONE example)
    # Production: Load from ENV as JSON array or deployment config
    default_factor_keys: List[str] = field(default_factory=lambda: [
        "factor_1",  # Example: momentum (finance), relevance (semantic), quality (content)
        "factor_2",  # Example: trend (finance), coherence (text), risk (portfolio)
        "factor_3",  # Example: volatility (finance), diversity (data), stability (system)
        "factor_4",  # Example: sentiment (finance/text), confidence (ML), impact (causal)
        "factor_5",  # Example: fundamentals (finance), context (semantic), metadata (generic)
    ])


@dataclass(frozen=True)
class MCPConfig:
    """Master configuration."""
    service: ServiceConfig
    api: APIEndpoints
    redis: RedisConfig
    postgres: PostgresConfig
    validation: ValidationConfig


_config: MCPConfig = None


def get_config() -> MCPConfig:
    """Get or create configuration from environment."""
    global _config
    if _config is None:
        _config = MCPConfig(
            service=ServiceConfig(
                port=int(os.getenv("PORT", "8020")),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
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
            postgres=PostgresConfig(
                host=os.getenv("POSTGRES_HOST", "omni_postgres"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "vitruvyan"),
                user=os.getenv("POSTGRES_USER", "vitruvyan"),
                # Password MUST be in environment (security requirement)
            ),
            validation=ValidationConfig(
                z_score_threshold=float(os.getenv("MCP_Z_THRESHOLD", "3.0")),
                composite_threshold=float(os.getenv("MCP_COMPOSITE_THRESHOLD", "5.0")),
                min_summary_words=int(os.getenv("MCP_MIN_SUMMARY_WORDS", "100")),
                max_summary_words=int(os.getenv("MCP_MAX_SUMMARY_WORDS", "200")),
                # Factor keys from ENV or default (deployment-specific taxonomy)
                default_factor_keys=[
                    k.strip() 
                    for k in os.getenv("MCP_FACTOR_KEYS", "factor_1,factor_2,factor_3,factor_4,factor_5").split(",")
                ],
            ),
        )
    return _config
