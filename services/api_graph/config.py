"""
Graph Orchestrator Service Configuration

Centralizes all environment variables and service settings.
NO hardcoded values in main.py or routes.py.

Layer: LIVELLO 2 (Service)
"""

import os
from typing import List


class Settings:
    """Graph Orchestrator service configuration."""
    
    # Service metadata
    SERVICE_NAME: str = "api_graph"
    SERVICE_VERSION: str = "2.0.0"
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8004"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS origins — configure via CORS_ORIGINS env var (comma-separated)
    # Default: local dev only. Set CORS_ORIGINS in .env for production.
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001"
        ).split(",")
        if origin.strip()
    ]
    
    # PostgreSQL (for semantic clusters + entity search)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "core_postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "vitruvyan_core")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "vitruvyan")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    # Redis (if bus integration needed)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "core_redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Audit monitoring
    AUDIT_ENABLED: bool = os.getenv("AUDIT_ENABLED", "false").lower() == "true"
    
    # Graph execution config
    DEFAULT_USER_ID: str = "demo"
    GRAPH_TIMEOUT_SECONDS: int = int(os.getenv("GRAPH_TIMEOUT_SECONDS", "60"))
    
    # Phase 1: Minimal LangGraph wrapper (4 nodes)
    ENABLE_MINIMAL_GRAPH: bool = os.getenv("ENABLE_MINIMAL_GRAPH", "false").lower() == "true"

    # Plasticity: enable/disable the learning loop
    PLASTICITY_ENABLED: bool = os.getenv("PLASTICITY_ENABLED", "true").lower() == "true"
    PLASTICITY_INTERVAL_HOURS: int = int(os.getenv("PLASTICITY_INTERVAL_HOURS", "24"))


settings = Settings()
