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

Design rationale:
    Phase 3 enforcement is *observability-first*: violations are logged so
    that the contract registry can be populated incrementally without
    breaking the graph at startup.  Hard enforcement (raise on violation)
    is a future Phase 4 flag.

Author: Vitruvyan Core Team
Created: March 2026
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)


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
            # ── Pre-condition check ──────────────────────────────────────────
            missing_in = _requires - set(state.keys())
            if missing_in:
                logger.warning(
                    "[contract] node=%s REQUIRES missing keys: %s",
                    node_name,
                    sorted(missing_in),
                )

            # ── Execute node ─────────────────────────────────────────────────
            result = fn(state)

            # ── Post-condition check ─────────────────────────────────────────
            if result is not None:
                missing_out = _produces - set(result.keys())
                if missing_out:
                    logger.warning(
                        "[contract] node=%s PRODUCES missing keys: %s",
                        node_name,
                        sorted(missing_out),
                    )

            return result

        return wrapper

    return decorator
