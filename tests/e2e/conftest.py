"""
E2E Test Fixtures — Vitruvyan Core
===================================
Shared fixtures for end-to-end tests that require running Docker services.

Prerequisites:
    cd infrastructure/docker && docker compose up -d

All fixtures auto-skip if services are unreachable.
"""
import os
import sys
import time
import uuid

import pytest

# ── PYTHONPATH (mirrors Docker PYTHONPATH=/app/vitruvyan_core) ──
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VC_PATH = os.path.join(ROOT, "vitruvyan_core")
if VC_PATH not in sys.path:
    sys.path.insert(0, VC_PATH)

# ---------------------------------------------------------------------------
# Service base URLs (external ports)
# ---------------------------------------------------------------------------
GRAPH_URL = os.getenv("GRAPH_URL", "http://localhost:9004")
NEURAL_URL = os.getenv("NEURAL_URL", "http://localhost:9003")
BABEL_URL = os.getenv("BABEL_URL", "http://localhost:9009")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://localhost:9010")
PATTERN_WEAVERS_URL = os.getenv("PATTERN_WEAVERS_URL", "http://localhost:9017")
ORTHODOXY_URL = os.getenv("ORTHODOXY_URL", "http://localhost:9006")
VAULT_URL = os.getenv("VAULT_URL", "http://localhost:9007")
CODEX_URL = os.getenv("CODEX_URL", "http://localhost:9008")
MEMORY_URL = os.getenv("MEMORY_URL", "http://localhost:9016")
CONCLAVE_URL = os.getenv("CONCLAVE_URL", "http://localhost:9012")

# Infrastructure
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "9432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "vitruvyan_core")
POSTGRES_USER = os.getenv("POSTGRES_USER", "vitruvyan_core_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "9379"))

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "9333"))


# ---------------------------------------------------------------------------
# Helper: test if a service is reachable
# ---------------------------------------------------------------------------
def _service_reachable(url: str, timeout: float = 3.0) -> bool:
    """Check if a service health endpoint is reachable."""
    import httpx
    try:
        r = httpx.get(f"{url}/health", timeout=timeout)
        return r.status_code in (200, 503)  # 503 = degraded but alive
    except Exception:
        return False


def _infra_reachable(kind: str) -> bool:
    """Check if infrastructure (postgres/redis/qdrant) is reachable."""
    if kind == "postgres":
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=POSTGRES_HOST, port=POSTGRES_PORT,
                dbname=POSTGRES_DB, user=POSTGRES_USER,
                password=POSTGRES_PASSWORD, connect_timeout=3,
            )
            conn.close()
            return True
        except Exception:
            return False
    elif kind == "redis":
        try:
            import redis as _redis
            r = _redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=3)
            r.ping()
            r.close()
            return True
        except Exception:
            return False
    elif kind == "qdrant":
        try:
            import httpx
            r = httpx.get(f"http://{QDRANT_HOST}:{QDRANT_PORT}/healthz", timeout=3)
            return r.status_code == 200
        except Exception:
            return False
    return False


# ---------------------------------------------------------------------------
# Unique test run ID (isolate test data)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def e2e_run_id():
    """Unique identifier for this test run, used to isolate test data."""
    return f"e2e_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# HTTP client fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def http_client():
    """Shared httpx client with reasonable timeouts."""
    import httpx
    client = httpx.Client(timeout=30.0)
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Service availability fixtures (skip if unreachable)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def graph_api(http_client):
    if not _service_reachable(GRAPH_URL):
        pytest.skip("Graph API not reachable")
    return GRAPH_URL


@pytest.fixture(scope="session")
def neural_api(http_client):
    if not _service_reachable(NEURAL_URL):
        pytest.skip("Neural Engine API not reachable")
    return NEURAL_URL


@pytest.fixture(scope="session")
def embedding_api(http_client):
    if not _service_reachable(EMBEDDING_URL):
        pytest.skip("Embedding API not reachable")
    return EMBEDDING_URL


@pytest.fixture(scope="session")
def babel_api(http_client):
    if not _service_reachable(BABEL_URL):
        pytest.skip("Babel Gardens API not reachable")
    return BABEL_URL


@pytest.fixture(scope="session")
def pattern_weavers_api(http_client):
    if not _service_reachable(PATTERN_WEAVERS_URL):
        pytest.skip("Pattern Weavers API not reachable")
    return PATTERN_WEAVERS_URL


@pytest.fixture(scope="session")
def orthodoxy_api(http_client):
    if not _service_reachable(ORTHODOXY_URL):
        pytest.skip("Orthodoxy Wardens API not reachable")
    return ORTHODOXY_URL


@pytest.fixture(scope="session")
def vault_api(http_client):
    if not _service_reachable(VAULT_URL):
        pytest.skip("Vault Keepers API not reachable")
    return VAULT_URL


# ---------------------------------------------------------------------------
# Infrastructure fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def pg_conn():
    """Direct PostgreSQL connection for verification queries."""
    if not _infra_reachable("postgres"):
        pytest.skip("PostgreSQL not reachable")
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def redis_client():
    """Direct Redis client for stream verification."""
    if not _infra_reachable("redis"):
        pytest.skip("Redis not reachable")
    import redis as _redis
    client = _redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield client
    client.close()


@pytest.fixture(scope="session")
def qdrant_http():
    """Qdrant base URL for REST API calls."""
    if not _infra_reachable("qdrant"):
        pytest.skip("Qdrant not reachable")
    return f"http://{QDRANT_HOST}:{QDRANT_PORT}"


# ---------------------------------------------------------------------------
# Graph helper
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def graph_run(http_client, graph_api):
    """Helper to call the graph /run endpoint and return parsed JSON response."""
    def _run(input_text: str, user_id: str = "e2e_test_user") -> dict:
        import json
        r = http_client.post(
            f"{graph_api}/run",
            json={"input_text": input_text, "user_id": user_id},
            timeout=60.0,
        )
        assert r.status_code == 200, f"Graph /run returned {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Parse the nested JSON string in "json" field
        if isinstance(data.get("json"), str):
            data["parsed"] = json.loads(data["json"])
        else:
            data["parsed"] = data.get("json", {})
        return data
    return _run
