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
    
    # CORS origins (Vercel UI + production)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",            # Local dev (port 3000)
        "http://localhost:3001",            # Local dev (port 3001)
        "https://*.vercel.app",             # Vercel deployments
        "https://vitruvyan-ui.vercel.app",  # Production Vercel
        "https://dev.vitruvyan.com",        # Production UI (Nginx SSL)
        "http://161.97.140.157:3000",       # VPS UI (if needed)
        "http://161.97.140.157:3001",       # VPS UI port 3001
    ]
    
    # PostgreSQL (for semantic clusters + entity search)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "core_postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "vitruvyan_core")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "vitruvyan")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "your_password")
    
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


settings = Settings()
