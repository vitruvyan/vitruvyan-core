"""
🌐 Vitruvyan API Configuration - Centralized Endpoint Management
================================================================
Sacred Order: Infrastructure (Foundation Layer)

ALL API endpoints consolidated under api.vitruvyan.com for production.
Supports 3 environments: production (HTTPS), docker (internal), local (localhost).

Architecture:
- Production: https://api.vitruvyan.com/{service}
- Docker: http://vitruvyan_api_{service}:{port}
- Local: http://localhost:{port}

Usage:
    from config.api_config import get_api_url, APIService
    
    # Production (default)
    url = get_api_url(APIService.LANGGRAPH)  # https://api.vitruvyan.com/langgraph
    
    # Docker internal
    url = get_api_url(APIService.NEURAL, env="docker")  # http://vitruvyan_api_neural:8003
    
    # Local development
    url = get_api_url(APIService.BABEL, env="local")  # http://localhost:8009

Created: Nov 19, 2025
Status: ACTIVE (API Consolidation Refactor)
"""

import os
from enum import Enum
from typing import Optional


class APIService(Enum):
    """
    Vitruvyan microservices registry.
    Each service has: name, port, production path.
    """
    # Core Services
    LANGGRAPH = ("langgraph", 8004, "/langgraph")
    NEURAL = ("neural", 8003, "/neural")
    BABEL = ("babel_gardens", 8009, "/babel")
    EMBEDDING = ("embedding", 8010, "/embedding")
    
    # Agent Services
    WEAVERS = ("pattern_weavers", 8011, "/weavers")  # FIX (Feb 11): Service name pattern_weavers, port 8011
    AUDIT = ("audit", 8006, "/audit")
    
    # Support Services
    GEMMA = ("gemma", 8007, "/gemma")
    CODEX = ("codex", 8008, "/codex")
    QDRANT = ("qdrant", 6333, "/qdrant")
    DOCS = ("docs", 8013, "/docs")  # Vitruvyan Docs Synapse
    DSE = ("api_edge_dse", 8021, "/dse")  # Design Space Exploration (edge)
    
    def __init__(self, service_name: str, port: int, prod_path: str):
        self.service_name = service_name
        self.port = port
        self.prod_path = prod_path


class APIEnvironment:
    """
    Environment detection and URL building.
    """
    
    # Base URLs per environment
    PRODUCTION_BASE = "https://api.vitruvyan.com"
    DOCKER_PREFIX = "http://vitruvyan_api_"
    LOCAL_BASE = "http://localhost"
    
    @staticmethod
    def detect() -> str:
        """
        Auto-detect environment from VITRUVYAN_ENV variable.
        
        Returns:
            "production" | "docker" | "local"
        """
        env = os.getenv("VITRUVYAN_ENV", "docker").lower()
        
        if env in ["production", "prod"]:
            return "production"
        elif env in ["docker", "container"]:
            return "docker"
        elif env in ["local", "dev", "development"]:
            return "local"
        else:
            # Default: docker (most common in deployment)
            return "docker"
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment."""
        return APIEnvironment.detect() == "production"
    
    @staticmethod
    def is_docker() -> bool:
        """Check if running in Docker environment."""
        return APIEnvironment.detect() == "docker"
    
    @staticmethod
    def is_local() -> bool:
        """Check if running in local development."""
        return APIEnvironment.detect() == "local"


def get_api_url(
    service: APIService,
    env: Optional[str] = None,
    endpoint: str = ""
) -> str:
    """
    Get complete API URL for a service.
    
    Args:
        service: APIService enum (LANGGRAPH, NEURAL, etc.)
        env: Environment override ("production", "docker", "local")
             If None, auto-detects from VITRUVYAN_ENV
        endpoint: Optional endpoint path to append (e.g., "/run", "/health")
    
    Returns:
        Complete URL string
    
    Examples:
        >>> get_api_url(APIService.LANGGRAPH)
        'http://vitruvyan_api_langgraph:8004'
        
        >>> get_api_url(APIService.NEURAL, env="production", endpoint="/screen")
        'https://api.vitruvyan.com/neural/screen'
        
        >>> get_api_url(APIService.BABEL, env="local")
        'http://localhost:8009'
    """
    # Determine environment
    if env is None:
        env = APIEnvironment.detect()
    
    # Build base URL
    if env == "production":
        base_url = f"{APIEnvironment.PRODUCTION_BASE}{service.prod_path}"
    elif env == "docker":
        # Docker internal: Use service names from docker-compose.yml (no vitruvyan_ prefix)
        base_url = f"http://{service.service_name}:{service.port}"
    elif env == "local":
        base_url = f"{APIEnvironment.LOCAL_BASE}:{service.port}"
    else:
        raise ValueError(f"Invalid environment: {env}")
    
    # Append endpoint if provided
    if endpoint:
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        base_url = f"{base_url}{endpoint}"
    
    return base_url


def get_env_override(service: APIService) -> Optional[str]:
    """
    Check if service URL is overridden in environment variables.
    
    Args:
        service: APIService enum
    
    Returns:
        Override URL if exists, None otherwise
    
    Environment variable format: {SERVICE}_API_URL
    Examples:
        - LANGGRAPH_API_URL=http://custom-host:8004
        - NEURAL_API_URL=https://custom-neural.com
    """
    env_var = f"{service.service_name.upper()}_API_URL"
    return os.getenv(env_var)


def get_api_url_with_fallback(
    service: APIService,
    endpoint: str = "",
    fallback_env: str = "docker"
) -> str:
    """
    Get API URL with environment variable override support.
    
    Priority:
    1. Environment variable override (e.g., LANGGRAPH_API_URL)
    2. Auto-detected environment URL
    3. Fallback environment URL
    
    Args:
        service: APIService enum
        endpoint: Optional endpoint path
        fallback_env: Fallback environment if detection fails
    
    Returns:
        Complete URL string with highest priority
    
    Example:
        # With LANGGRAPH_API_URL=http://custom:9000 in .env
        >>> get_api_url_with_fallback(APIService.LANGGRAPH, "/run")
        'http://custom:9000/run'
        
        # Without override, uses auto-detection
        >>> get_api_url_with_fallback(APIService.NEURAL)
        'http://vitruvyan_api_neural:8003'
    """
    # Check environment variable override first
    override = get_env_override(service)
    if override:
        if endpoint:
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
            return f"{override}{endpoint}"
        return override
    
    # Use auto-detected environment
    try:
        return get_api_url(service, env=None, endpoint=endpoint)
    except Exception:
        # Fallback to specified environment
        return get_api_url(service, env=fallback_env, endpoint=endpoint)


# Convenience functions for common services
def get_langgraph_url(endpoint: str = "") -> str:
    """Get LangGraph API URL."""
    return get_api_url_with_fallback(APIService.LANGGRAPH, endpoint)


def get_neural_url(endpoint: str = "") -> str:
    """Get Neural Engine API URL."""
    return get_api_url_with_fallback(APIService.NEURAL, endpoint)


def get_babel_url(endpoint: str = "") -> str:
    """Get Babel Gardens API URL."""
    return get_api_url_with_fallback(APIService.BABEL, endpoint)


def get_embedding_url(endpoint: str = "") -> str:
    """Get Embedding API URL."""
    return get_api_url_with_fallback(APIService.EMBEDDING, endpoint)


def get_weavers_url(endpoint: str = "") -> str:
    """Get Pattern Weavers API URL."""
    return get_api_url_with_fallback(APIService.WEAVERS, endpoint)


def get_audit_url(endpoint: str = "") -> str:
    """Get Audit Engine API URL."""
    return get_api_url_with_fallback(APIService.AUDIT, endpoint)


def get_gemma_url(endpoint: str = "") -> str:
    """Get Gemma API URL."""
    return get_api_url_with_fallback(APIService.GEMMA, endpoint)


def get_codex_url(endpoint: str = "") -> str:
    """Get Codex Hunters API URL."""
    return get_api_url_with_fallback(APIService.CODEX, endpoint)


def get_docs_url(endpoint: str = "") -> str:
    """Get Vitruvyan Docs Synapse API URL."""
    return get_api_url_with_fallback(APIService.DOCS, endpoint)


def get_dse_url(endpoint: str = "") -> str:
    """Get Design Space Exploration API URL."""
    return get_api_url_with_fallback(APIService.DSE, endpoint)


# ─────────────────────────────────────────────────────────────
# Tenancy Configuration (domain-agnostic)
# ─────────────────────────────────────────────────────────────

# Operational mode: "bootstrap" (audit-only) or "enforced" (hard 403)
TENANCY_MODE: str = os.getenv("TENANCY_MODE", "bootstrap")

# Internal/system tenant ID (shared corpora, normative, etc.)
TENANCY_INTERNAL_TENANT_ID: str = os.getenv("TENANCY_INTERNAL_TENANT_ID", "999")

# Superadmin roles that bypass tenant scope (comma-separated)
TENANCY_SUPERADMIN_ROLES: list = os.getenv(
    "TENANCY_SUPERADMIN_ROLES", "super_admin,realm-admin"
).split(",")


# Export all
__all__ = [
    "APIService",
    "APIEnvironment",
    "get_api_url",
    "get_api_url_with_fallback",
    "get_langgraph_url",
    "get_neural_url",
    "get_babel_url",
    "get_embedding_url",
    "get_weavers_url",
    "get_audit_url",
    "get_gemma_url",
    "get_codex_url",
    "get_docs_url",
    "get_dse_url",
    # Tenancy
    "TENANCY_MODE",
    "TENANCY_INTERNAL_TENANT_ID",
    "TENANCY_SUPERADMIN_ROLES",
]


if __name__ == "__main__":
    # Self-test
    print("🧪 API Config Self-Test")
    print("=" * 60)
    
    # Test all environments
    for env in ["production", "docker", "local"]:
        print(f"\n{env.upper()} Environment:")
        print(f"  LangGraph: {get_api_url(APIService.LANGGRAPH, env=env, endpoint='/run')}")
        print(f"  Neural:    {get_api_url(APIService.NEURAL, env=env, endpoint='/screen')}")
        print(f"  Babel:     {get_api_url(APIService.BABEL, env=env)}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed")
