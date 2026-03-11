"""
Vitruvyan Core — Node Contract Enforcement
==========================================
Provides the @enforced decorator for LangGraph nodes.

Usage (from graph_flow.py)::

    from core.orchestration.contract_enforcement import enforced

    @enforced(requires=["input_text"], produces=["route"], node_name="decide")
    def route_node(state):
        ...

The decorator:
1. Warns (does NOT raise) when a required key is absent from state.
2. Warns when a declared produced key is absent from the returned state.
3. Is a no-op when both sets are empty — wrapping cost is zero.
4. Never swallows exceptions from the wrapped node.

Enforcement modes (CONTRACT_ENFORCE_MODE env var):
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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ── Module-level state ─────────────────────────────────────────────

_violation_count: int = 0
def _get_enforce_mode() -> str:
    return os.getenv("CONTRACT_ENFORCE_MODE",
                    os.getenv("ENFORCE_CONTRACTS", "warn")).lower()


def get_violation_count() -> int:
    return _violation_count


def reset_violation_count() -> None:
    global _violation_count
    _violation_count = 0


# ── NodeContractSpec ───────────────────────────────────────────────

@dataclass(frozen=True)
class NodeContractSpec:
    """Frozen descriptor attached to wrapped nodes for introspection."""
    requires: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)
    validate_types: Dict[str, type] = field(default_factory=dict)


# ── ContractViolationError ─────────────────────────────────────────

class ContractViolationError(RuntimeError):
    """Raised in strict mode when a node contract is violated."""

    def __init__(
        self,
        node_name: str,
        phase: str,
        missing_fields: Optional[List[str]] = None,
        type_errors: Optional[Dict[str, str]] = None,
    ):
        self.node_name = node_name
        self.phase = phase
        self.missing_fields = missing_fields or []
        self.type_errors = type_errors or {}
        parts = [f"[contract] node={node_name} phase={phase}"]
        if self.missing_fields:
            label = "REQUIRES" if phase == "pre" else "PRODUCES"
            parts.append(f"{label} missing keys: {self.missing_fields}")
        if self.type_errors:
            parts.append(f"type_errors={self.type_errors}")
        super().__init__(" ".join(parts))


# ── Decorator ──────────────────────────────────────────────────────

def enforced(
    requires: Optional[list] = None,
    produces: Optional[list] = None,
    node_name: str = "",
    validate_types: Optional[Dict[str, type]] = None,
) -> Callable:
    """
    Decorator factory that validates LangGraph node state contracts.

    Args:
        requires: State keys the node expects to be present on entry.
        produces: State keys the node promises to set on exit.
        node_name: Human-readable name for log messages.
        validate_types: Optional mapping of field names to expected types.

    Returns:
        Decorator that wraps a ``state -> state`` node function.
    """
    _requires: List[str] = list(requires or [])
    _produces: List[str] = list(produces or [])
    _types: Dict[str, type] = dict(validate_types or {})
    _spec = NodeContractSpec(requires=_requires, produces=_produces, validate_types=_types)

    def decorator(fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Callable:

        mode = _get_enforce_mode()
        if mode == "off":
            return fn

        @functools.wraps(fn)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            global _violation_count
            _name = node_name or fn.__name__
            _mode = _get_enforce_mode()

            # ── Pre-condition check ──────────────────────────────
            missing_in = [k for k in _requires if k not in state or state[k] is None]
            if missing_in:
                _violation_count += 1
                if _mode == "strict":
                    raise ContractViolationError(_name, "pre", missing_fields=missing_in)
                logger.warning("[contract] node=%s REQUIRES missing keys: %s", _name, missing_in)

            # ── Type validation (pre) ────────────────────────────
            type_errs: Dict[str, str] = {}
            for field_name, expected_type in _types.items():
                if field_name in state and state[field_name] is not None:
                    if not isinstance(state[field_name], expected_type):
                        type_errs[field_name] = (
                            f"expected {expected_type.__name__}, "
                            f"got {type(state[field_name]).__name__}"
                        )
            if type_errs:
                _violation_count += 1
                if _mode == "strict":
                    raise ContractViolationError(_name, "pre", type_errors=type_errs)
                logger.warning("[contract] node=%s type mismatch: %s", _name, type_errs)

            # ── Execute node ─────────────────────────────────────
            result = fn(state)

            # ── Post-condition check ─────────────────────────────
            if result is not None:
                missing_out = [k for k in _produces if k not in result]
                if missing_out:
                    _violation_count += 1
                    if _mode == "strict":
                        raise ContractViolationError(_name, "post", missing_fields=missing_out)
                    logger.warning("[contract] node=%s PRODUCES missing keys: %s", _name, missing_out)

            return result

        wrapper._contract = _spec
        return wrapper

    return decorator
