"""
Vitruvyan Core — Node Contract Enforcement
==========================================
Provides the @enforced decorator for LangGraph nodes.

Usage (from graph_flow.py)::

    from core.orchestration.contract_enforcement import enforced

    @enforced(requires={"input_text"}, produces={"route"}, node_name="decide")
    def route_node(state):
        ...

The decorator:
1. Warns (does NOT raise) when a required key is absent from state.
2. Warns when a declared produced key is absent from the returned state.
3. Is a no-op when both sets are empty — wrapping cost is zero.
4. Never swallows exceptions from the wrapped node.

Enforcement modes (ENFORCE_CONTRACTS env var):
    "warn"   — (default) Log violations as warnings, do not raise.
    "strict" — Raise ContractViolationError on any violation.
    "off"    — Disable all contract checks (zero overhead).

Author: Vitruvyan Core Team
Created: March 2026
"""

from __future__ import annotations

import functools
import logging
import os
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)


class ContractViolationError(RuntimeError):
    """Raised in strict mode when a node contract is violated."""


def _get_enforcement_mode() -> str:
    """Read enforcement mode from env var (checked per-call for hot reload)."""
    return os.getenv("ENFORCE_CONTRACTS", "warn").lower()


def enforced(
    requires: Optional[Set[str]] = None,
    produces: Optional[Set[str]] = None,
    node_name: str = "unknown",
) -> Callable:
    """
    Decorator factory that validates LangGraph node state contracts.

    Args:
        requires: State keys the node expects to be present on entry.
        produces: State keys the node promises to set on exit.
        node_name: Human-readable name for log messages.

    Returns:
        Decorator that wraps a ``state -> state`` node function.
    """
    _requires: Set[str] = set(requires or ())
    _produces: Set[str] = set(produces or ())

    def decorator(fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable:
        if not _requires and not _produces:
            # Nothing to check — return original function untouched.
            return fn

        @functools.wraps(fn)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            mode = _get_enforcement_mode()

            if mode == "off":
                return fn(state)

            # ── Pre-condition check ──────────────────────────────────────────
            missing_in = _requires - set(state.keys())
            if missing_in:
                msg = (
                    f"[contract] node={node_name} REQUIRES missing keys: "
                    f"{sorted(missing_in)}"
                )
                if mode == "strict":
                    raise ContractViolationError(msg)
                logger.warning(msg)

            # ── Execute node ─────────────────────────────────────────────────
            result = fn(state)

            # ── Post-condition check ─────────────────────────────────────────
            if result is not None:
                missing_out = _produces - set(result.keys())
                if missing_out:
                    msg = (
                        f"[contract] node={node_name} PRODUCES missing keys: "
                        f"{sorted(missing_out)}"
                    )
                    if mode == "strict":
                        raise ContractViolationError(msg)
                    logger.warning(msg)

            return result

        return wrapper

    return decorator
