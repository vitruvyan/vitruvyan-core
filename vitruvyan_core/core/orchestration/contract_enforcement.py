"""
Vitruvyan Core — Contract Enforcement Decorator
=================================================

Cross-cutting enforcement for LangGraph node contracts.
Applied in build_graph() — individual nodes are unaware of wrapping.

LIVELLO 1 compliance:
  - Pure Python, zero I/O, zero external dependencies
  - Metric names are string constants ONLY (no prometheus_client)
  - Prometheus instantiation happens in LIVELLO 2 (service layer)

Environment:
  CONTRACT_ENFORCE_MODE (read ONCE at import-time):
    - "warn"   (default): log WARNING + increment violation counter
    - "strict": raise ContractViolationError (staging/test)
    - "off":    return original function unwrapped — zero overhead

Author: Vitruvyan Core Team
Created: February 28, 2026
Status: LIVELLO 1 — FOUNDATIONAL
"""

import functools
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── Configuration (read ONCE at import-time) ────────────────────────────────
_MODE = os.getenv("CONTRACT_ENFORCE_MODE", "warn")

# ─── Metric name constants (LIVELLO 1: strings only, no prometheus_client) ───
METRIC_CONTRACT_VIOLATIONS = "vitruvyan_contract_violations_total"
METRIC_CONTRACT_CHECKS = "vitruvyan_contract_checks_total"


# ─── Violation tracking (in-memory, no I/O) ──────────────────────────────────
_violation_count: int = 0


def get_violation_count() -> int:
    """Return total violation count since process start (test helper)."""
    return _violation_count


def reset_violation_count() -> None:
    """Reset violation counter (test helper only)."""
    global _violation_count
    _violation_count = 0


# ─── Exception ────────────────────────────────────────────────────────────────

class ContractViolationError(Exception):
    """
    Raised when CONTRACT_ENFORCE_MODE=strict and a node violates its contract.

    Attributes:
        node_name: Name of the violating node
        phase: "pre" (missing required input) or "post" (missing produced output)
        missing_fields: Fields that were expected but absent
        type_errors: Fields with wrong types (if validate_types was used)
    """

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
        parts = []
        if self.missing_fields:
            parts.append(f"missing={self.missing_fields}")
        if self.type_errors:
            parts.append(f"type_errors={self.type_errors}")
        detail = ", ".join(parts)
        super().__init__(
            f"[CONTRACT] {node_name} {phase} violation: {detail}"
        )


# ─── Node Contract Dataclass ─────────────────────────────────────────────────

@dataclass(frozen=True)
class NodeContractSpec:
    """
    Declarative contract for a single LangGraph node.

    Used by the NODE_CONTRACTS registry (node_contracts_registry.py).
    """
    requires: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)
    validate_types: Dict[str, type] = field(default_factory=dict)


# ─── Decorator ────────────────────────────────────────────────────────────────

def enforced(
    requires: Optional[List[str]] = None,
    produces: Optional[List[str]] = None,
    validate_types: Optional[Dict[str, type]] = None,
    node_name: Optional[str] = None,
) -> Callable:
    """
    Contract enforcement decorator for LangGraph nodes.

    Applied in build_graph() via _wrap(), NOT in individual node files.

    Args:
        requires: State fields the node expects as input (must exist and not be None)
        produces: State fields the node must include in its return dict
        validate_types: Optional type checks {field_name: expected_type}
        node_name: Node identifier for logging (auto-detected from function name if omitted)

    Returns:
        Decorator that wraps the node function with pre/post checks.
        In "off" mode, returns the original function unwrapped.
    """
    _requires = requires or []
    _produces = produces or []
    _types = validate_types or {}

    def decorator(fn: Callable) -> Callable:
        # off mode: zero overhead — return original function
        if _MODE == "off":
            return fn

        name = node_name or fn.__name__

        @functools.wraps(fn)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            global _violation_count

            # ── PRE-CHECK: required fields exist in state ──
            missing_pre = [
                f for f in _requires
                if f not in state or state[f] is None
            ]
            if missing_pre:
                _violation_count += 1
                msg = (
                    f"[CONTRACT-PRE] {name}: missing required fields "
                    f"{missing_pre} in state (available: "
                    f"{sorted(k for k in state.keys() if not k.startswith('_'))})"
                )
                if _MODE == "strict":
                    raise ContractViolationError(name, "pre", missing_fields=missing_pre)
                logger.warning(msg)

            # ── PRE type checks ──
            pre_type_errors = {}
            for field_name, expected_type in _types.items():
                if field_name in _requires and field_name in state:
                    val = state[field_name]
                    if val is not None and not isinstance(val, expected_type):
                        pre_type_errors[field_name] = (
                            f"expected {expected_type.__name__}, "
                            f"got {type(val).__name__}"
                        )
            if pre_type_errors:
                _violation_count += 1
                msg = f"[CONTRACT-PRE] {name}: type errors {pre_type_errors}"
                if _MODE == "strict":
                    raise ContractViolationError(
                        name, "pre", type_errors=pre_type_errors
                    )
                logger.warning(msg)

            # ── Execute node ──
            result = fn(state)

            # ── POST-CHECK: produced fields exist in result ──
            if result is not None and isinstance(result, dict):
                missing_post = [
                    f for f in _produces
                    if f not in result or result[f] is None
                ]
                if missing_post:
                    _violation_count += 1
                    msg = (
                        f"[CONTRACT-POST] {name}: missing produced fields "
                        f"{missing_post} in output (available: "
                        f"{sorted(k for k in result.keys() if not k.startswith('_'))})"
                    )
                    if _MODE == "strict":
                        raise ContractViolationError(
                            name, "post", missing_fields=missing_post
                        )
                    logger.warning(msg)

                # ── POST type checks ──
                post_type_errors = {}
                for field_name, expected_type in _types.items():
                    if field_name in _produces and field_name in result:
                        val = result[field_name]
                        if val is not None and not isinstance(val, expected_type):
                            post_type_errors[field_name] = (
                                f"expected {expected_type.__name__}, "
                                f"got {type(val).__name__}"
                            )
                if post_type_errors:
                    _violation_count += 1
                    msg = (
                        f"[CONTRACT-POST] {name}: type errors "
                        f"{post_type_errors}"
                    )
                    if _MODE == "strict":
                        raise ContractViolationError(
                            name, "post", type_errors=post_type_errors
                        )
                    logger.warning(msg)

            return result

        # Attach contract metadata for introspection
        wrapper._contract = NodeContractSpec(
            requires=list(_requires),
            produces=list(_produces),
            validate_types=dict(_types),
        )
        return wrapper

    return decorator
