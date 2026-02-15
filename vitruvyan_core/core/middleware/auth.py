"""
Vitruvyan Auth Middleware — opt-in Bearer token validation.

Behaviour
---------
- **Disabled by default**: ``VITRUVYAN_AUTH_ENABLED`` defaults to ``"false"``.
  When disabled the middleware is a transparent no-op (zero overhead).
- When enabled (``VITRUVYAN_AUTH_ENABLED=true``), every request must carry a
  valid ``Authorization: Bearer <token>`` header.  Validation is pluggable:
  the default validator simply checks token presence (non-empty).
  Subclass ``AuthMiddleware`` or pass a custom ``token_validator`` callable for
  Keycloak / OIDC / JWT verification.

Environment variables
---------------------
VITRUVYAN_AUTH_ENABLED   "true" / "1" to activate  (default: "false")
AUTH_PUBLIC_PATHS        Comma-separated prefixes that skip auth
                         (default: "/health,/docs,/openapi.json,/redoc,/metrics")

Usage (FastAPI)
---------------
    from core.middleware.auth import AuthMiddleware

    app = FastAPI()
    app.add_middleware(AuthMiddleware)          # disabled unless env var set
    # or force-enable in tests:
    app.add_middleware(AuthMiddleware, enabled=True, token_validator=my_fn)
"""

from __future__ import annotations

import logging
import os
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_DEFAULT_PUBLIC = "/health,/docs,/openapi.json,/redoc,/metrics"


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "yes")


class AuthMiddleware(BaseHTTPMiddleware):
    """Opt-in auth middleware for Vitruvyan services.

    Parameters
    ----------
    app : ASGIApp
        The ASGI application (injected by FastAPI).
    enabled : bool | None
        Override the env-var flag. ``None`` → read ``VITRUVYAN_AUTH_ENABLED``.
    token_validator : callable | None
        ``async def(token: str) -> bool`` — return True if token is valid.
        Defaults to a presence check (any non-empty token passes).
    public_paths : list[str] | None
        URL prefixes that skip authentication.  ``None`` → read
        ``AUTH_PUBLIC_PATHS`` env var (comma-separated).
    """

    def __init__(
        self,
        app,
        enabled: Optional[bool] = None,
        token_validator: Optional[Callable] = None,
        public_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.enabled = enabled if enabled is not None else _env_bool("VITRUVYAN_AUTH_ENABLED")
        self.token_validator = token_validator or self._default_validator
        self.public_paths = (
            public_paths
            if public_paths is not None
            else os.getenv("AUTH_PUBLIC_PATHS", _DEFAULT_PUBLIC).split(",")
        )

        if self.enabled:
            logger.info("AuthMiddleware ENABLED — public paths: %s", self.public_paths)
        else:
            logger.debug("AuthMiddleware DISABLED (set VITRUVYAN_AUTH_ENABLED=true to activate)")

    # ------------------------------------------------------------------
    # Request handling
    # ------------------------------------------------------------------
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Allow CORS preflight through without auth
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow public paths through without auth
        path = request.url.path
        if any(path.startswith(p.strip()) for p in self.public_paths):
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]  # strip "Bearer "
        try:
            valid = await self.token_validator(token)
        except Exception:
            logger.exception("Token validation error")
            valid = False

        if not valid:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)

    # ------------------------------------------------------------------
    # Default validator (presence check only)
    # ------------------------------------------------------------------
    @staticmethod
    async def _default_validator(token: str) -> bool:
        """Accept any non-empty token.  Replace with OIDC/JWT verification."""
        return bool(token and token.strip())
