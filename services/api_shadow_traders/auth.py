"""Compatibility auth decorators for Shadow Traders endpoints.

The original service used decorators from ``core.auth``. Mercator currently
provides middleware-level auth; this module preserves endpoint decorators and
ensures ``request.state.user_id`` is populated when possible.
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request

try:
    import jwt  # type: ignore
except Exception:  # pragma: no cover - optional dependency safety
    jwt = None  # type: ignore


def _strict_mode() -> bool:
    return str(os.getenv("SHADOW_AUTH_STRICT", "false")).lower() in {"1", "true", "yes", "on"}


def _find_request(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Optional[Request]:
    req = kwargs.get("request")
    if isinstance(req, Request):
        return req
    for value in args:
        if isinstance(value, Request):
            return value
    return None


def _extract_user_id_from_bearer(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    if not token:
        return None
    if jwt is None:
        return None
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("preferred_username") or payload.get("sub")
    except Exception:
        return None


def _extract_user_id_from_payload(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Optional[str]:
    # Prefer explicit "trade_req" kwargs if present.
    payload = kwargs.get("trade_req")
    if payload is not None and hasattr(payload, "user_id"):
        return str(getattr(payload, "user_id"))

    # Fallback: inspect positional payloads.
    for value in args:
        if hasattr(value, "user_id"):
            try:
                return str(getattr(value, "user_id"))
            except Exception:
                continue
    return None


def _resolve_user_id(request: Request, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Optional[str]:
    # Explicit headers for local/dev invocations.
    header_user = request.headers.get("X-User-ID") or request.headers.get("X-Authenticated-User")
    if header_user:
        return header_user

    token_user = _extract_user_id_from_bearer(request)
    if token_user:
        return token_user

    payload_user = _extract_user_id_from_payload(args, kwargs)
    if payload_user:
        return payload_user

    return None


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        request = _find_request(args, kwargs)
        if request is None:
            if _strict_mode():
                raise HTTPException(status_code=401, detail="Authentication required")
            return await func(*args, **kwargs)

        user_id = _resolve_user_id(request, args, kwargs)
        if user_id:
            request.state.user_id = user_id
            return await func(*args, **kwargs)

        if _strict_mode():
            raise HTTPException(status_code=401, detail="Missing authenticated user context")

        request.state.user_id = "anonymous"
        return await func(*args, **kwargs)

    return wrapper


def optional_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        request = _find_request(args, kwargs)
        if request is not None:
            user_id = _resolve_user_id(request, args, kwargs)
            if user_id:
                request.state.user_id = user_id
        return await func(*args, **kwargs)

    return wrapper

