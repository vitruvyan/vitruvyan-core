"""
Vitruvyan Core — Node Execution Guard (Hard Timeout)
=====================================================

Provides hard execution timeout for graph node/plugin execution.
Uses concurrent.futures.ThreadPoolExecutor to enforce real interruption
of hanging or infinite-loop nodes.

This is NOT a soft elapsed-time check. The ThreadPoolExecutor.submit()
with .result(timeout=N) raises TimeoutError after N seconds regardless
of what the node is doing.

Configuration:
    NODE_EXEC_TIMEOUT_SECONDS: Default timeout per node (env var, default: 30)
    NODE_EXEC_MAX_WORKERS: Max concurrent node executions (env var, default: 4)

Author: Vitruvyan Core Team
Created: February 15, 2026
Status: LEVEL 1 — Pure Python, no I/O dependencies
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (env-driven, no load_dotenv)
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("NODE_EXEC_TIMEOUT_SECONDS", "30"))
MAX_WORKERS = int(os.getenv("NODE_EXEC_MAX_WORKERS", "4"))


@dataclass(frozen=True)
class ExecutionResult:
    """Result of a guarded node execution."""
    success: bool
    state: Dict[str, Any]
    execution_time_ms: float
    timed_out: bool = False
    error: Optional[str] = None
    node_name: str = ""


class NodeExecutionGuard:
    """
    Hard timeout enforcement for graph node execution.

    Wraps node handler calls in a ThreadPoolExecutor with a configurable
    timeout. If a node exceeds the timeout, the future is cancelled and
    a fallback state is returned.

    Thread Safety:
        The guard uses a shared ThreadPoolExecutor. Each call to
        execute_node() submits a task and blocks the caller until
        the task completes or the timeout expires.

    Usage:
        guard = NodeExecutionGuard()
        result = guard.execute_node("my_node", handler_fn, state)
        if result.timed_out:
            logger.warning("Node timed out")
        final_state = result.state
    """

    def __init__(
        self,
        default_timeout: int = None,
        max_workers: int = None,
    ):
        self._timeout = default_timeout or DEFAULT_TIMEOUT_SECONDS
        self._max_workers = max_workers or MAX_WORKERS
        self._executor = ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="node_exec"
        )
        logger.info(
            "NodeExecutionGuard initialized (timeout=%ds, workers=%d)",
            self._timeout, self._max_workers
        )

    def execute_node(
        self,
        node_name: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        state: Dict[str, Any],
        timeout: int = None,
    ) -> ExecutionResult:
        """
        Execute a node handler with hard timeout enforcement.

        Args:
            node_name: Human-readable node identifier (for logging/audit)
            handler: The node function (state → state)
            state: Current graph state dict
            timeout: Per-call timeout override (seconds). Falls back to default.

        Returns:
            ExecutionResult with success/timeout/error status and final state.
        """
        effective_timeout = timeout or self._timeout
        start_time = time.monotonic()

        future = self._executor.submit(handler, state)

        try:
            result_state = future.result(timeout=effective_timeout)
            elapsed_ms = (time.monotonic() - start_time) * 1000

            return ExecutionResult(
                success=True,
                state=result_state if isinstance(result_state, dict) else state,
                execution_time_ms=round(elapsed_ms, 2),
                timed_out=False,
                node_name=node_name,
            )

        except FuturesTimeoutError:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            future.cancel()  # Best-effort cancellation

            logger.error(
                "TIMEOUT: Node '%s' exceeded %ds limit (elapsed: %.0fms)",
                node_name, effective_timeout, elapsed_ms
            )

            # Return state unchanged with error metadata
            fallback_state = dict(state)
            fallback_state["_node_timeout"] = node_name
            fallback_state["_node_timeout_seconds"] = effective_timeout

            return ExecutionResult(
                success=False,
                state=fallback_state,
                execution_time_ms=round(elapsed_ms, 2),
                timed_out=True,
                error=f"Node '{node_name}' timed out after {effective_timeout}s",
                node_name=node_name,
            )

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000

            logger.error(
                "ERROR: Node '%s' raised %s: %s (elapsed: %.0fms)",
                node_name, type(e).__name__, str(e), elapsed_ms
            )

            # Return state unchanged with error metadata
            fallback_state = dict(state)
            fallback_state["_node_error"] = str(e)
            fallback_state["_node_error_type"] = type(e).__name__

            return ExecutionResult(
                success=False,
                state=fallback_state,
                execution_time_ms=round(elapsed_ms, 2),
                timed_out=False,
                error=f"{type(e).__name__}: {e}",
                node_name=node_name,
            )

    def shutdown(self, wait: bool = False):
        """Shutdown the thread pool executor."""
        self._executor.shutdown(wait=wait)
        logger.info("NodeExecutionGuard shutdown (wait=%s)", wait)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_guard: Optional[NodeExecutionGuard] = None


def get_execution_guard() -> NodeExecutionGuard:
    """Get or create the global NodeExecutionGuard instance."""
    global _guard
    if _guard is None:
        _guard = NodeExecutionGuard()
    return _guard


def reset_execution_guard() -> None:
    """Reset the global guard (for testing)."""
    global _guard
    if _guard is not None:
        _guard.shutdown(wait=False)
    _guard = None
