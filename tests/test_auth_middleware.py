"""Tests for core.middleware.auth — AuthMiddleware (opt-in Bearer validation)."""

import os
import pytest
from unittest.mock import AsyncMock

from starlette.testclient import TestClient
from fastapi import FastAPI

# Ensure middleware is importable from core
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vitruvyan_core"))

from core.middleware.auth import AuthMiddleware


def _make_app(enabled: bool = False, **kwargs) -> FastAPI:
    """Create a minimal FastAPI app with AuthMiddleware."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, enabled=enabled, **kwargs)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/data")
    def data():
        return {"data": [1, 2, 3]}

    return app


class TestAuthMiddlewareDisabled:
    """When disabled (default), middleware is transparent no-op."""

    def test_no_auth_needed_when_disabled(self):
        app = _make_app(enabled=False)
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        assert resp.json()["data"] == [1, 2, 3]

    def test_health_accessible_when_disabled(self):
        app = _make_app(enabled=False)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_default_is_disabled(self):
        """Without env var, middleware should default to disabled."""
        app = FastAPI()
        app.add_middleware(AuthMiddleware)  # no enabled= param

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200


class TestAuthMiddlewareEnabled:
    """When enabled, middleware enforces Bearer token."""

    def test_missing_header_returns_401(self):
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 401
        assert "Authorization" in resp.json()["detail"]

    def test_invalid_scheme_returns_401(self):
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/api/data", headers={"Authorization": "Basic abc123"})
        assert resp.status_code == 401

    def test_valid_bearer_passes(self):
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/api/data", headers={"Authorization": "Bearer my-token"})
        assert resp.status_code == 200
        assert resp.json()["data"] == [1, 2, 3]

    def test_public_paths_skip_auth(self):
        """Health endpoint should be accessible without auth."""
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_docs_path_skips_auth(self):
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/docs")
        assert resp.status_code == 200  # FastAPI's Swagger UI

    def test_options_preflight_skips_auth(self):
        """CORS preflight (OPTIONS) should pass without auth."""
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.options("/api/data")
        assert resp.status_code != 401

    def test_custom_validator_rejects_bad_token(self):
        async def strict_validator(token: str) -> bool:
            return token == "secret-key-42"

        app = _make_app(enabled=True, token_validator=strict_validator)
        client = TestClient(app)

        # Wrong token
        resp = client.get("/api/data", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401

        # Correct token
        resp = client.get("/api/data", headers={"Authorization": "Bearer secret-key-42"})
        assert resp.status_code == 200

    def test_custom_public_paths(self):
        app = _make_app(enabled=True, public_paths=["/custom-public"])
        client = TestClient(app)

        # Custom public path should pass
        # (will 404 since no route, but NOT 401)
        resp = client.get("/custom-public")
        assert resp.status_code != 401

        # Default /health should be blocked (custom paths override defaults)
        resp = client.get("/health")
        assert resp.status_code == 401

    def test_empty_token_rejected(self):
        app = _make_app(enabled=True)
        client = TestClient(app)
        resp = client.get("/api/data", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401


class TestAuthMiddlewareEnvVar:
    """Test env var driven behavior."""

    def test_env_var_enables_middleware(self, monkeypatch):
        monkeypatch.setenv("VITRUVYAN_AUTH_ENABLED", "true")
        app = FastAPI()
        app.add_middleware(AuthMiddleware)

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app)
        # Without Bearer, should get 401
        resp = client.get("/test")
        assert resp.status_code == 401

    def test_env_var_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("VITRUVYAN_AUTH_ENABLED", raising=False)
        app = FastAPI()
        app.add_middleware(AuthMiddleware)

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
