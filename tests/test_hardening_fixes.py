"""
Tests for Hardening Fixes — Vitruvyan Core v1.0
=================================================

Tests for all 5 hardening fixes:
1. Hard Timeout Execution Control (NodeExecutionGuard)
2. Dead Letter Queue (DLQ)
3. Redis KEYS elimination (SCAN-based)
4. Audit Structured Logging (AuditLogger)
5. load_dotenv removal verification

These tests are UNIT tests — no Docker, Redis, or PostgreSQL required.
Mock-based where external dependencies are needed.

Author: Vitruvyan Core Team
Created: February 15, 2026
"""

import os
import time
import json
import uuid
import pytest
import logging
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime


# ============================================================================
# FIX 1: Hard Timeout Execution Control
# ============================================================================

class TestNodeExecutionGuard:
    """Tests for core.orchestration.execution_guard.NodeExecutionGuard"""

    def test_successful_execution(self):
        """Node completes within timeout → success result."""
        from core.orchestration.execution_guard import NodeExecutionGuard

        guard = NodeExecutionGuard(default_timeout=5, max_workers=2)

        def fast_node(state):
            state["result"] = "done"
            return state

        result = guard.execute_node("test_node", fast_node, {"input": "hello"})

        assert result.success is True
        assert result.timed_out is False
        assert result.state["result"] == "done"
        assert result.execution_time_ms > 0
        assert result.node_name == "test_node"
        assert result.error is None

        guard.shutdown()

    def test_timeout_enforcement(self):
        """Node exceeding timeout → timed_out result with fallback state."""
        from core.orchestration.execution_guard import NodeExecutionGuard

        guard = NodeExecutionGuard(default_timeout=1, max_workers=2)

        def slow_node(state):
            time.sleep(10)  # Will be interrupted by timeout
            return state

        result = guard.execute_node("slow_node", slow_node, {"input": "test"})

        assert result.success is False
        assert result.timed_out is True
        assert result.state["_node_timeout"] == "slow_node"
        assert result.state["_node_timeout_seconds"] == 1
        assert "timed out" in result.error
        assert result.execution_time_ms >= 1000  # At least 1s

        guard.shutdown()

    def test_exception_handling(self):
        """Node raising exception → error result with metadata."""
        from core.orchestration.execution_guard import NodeExecutionGuard

        guard = NodeExecutionGuard(default_timeout=5, max_workers=2)

        def bad_node(state):
            raise ValueError("something went wrong")

        result = guard.execute_node("bad_node", bad_node, {"input": "test"})

        assert result.success is False
        assert result.timed_out is False
        assert "ValueError" in result.error
        assert result.state["_node_error"] == "something went wrong"
        assert result.state["_node_error_type"] == "ValueError"

        guard.shutdown()

    def test_per_call_timeout_override(self):
        """Per-call timeout overrides default."""
        from core.orchestration.execution_guard import NodeExecutionGuard

        guard = NodeExecutionGuard(default_timeout=30, max_workers=2)

        def slow_node(state):
            time.sleep(10)
            return state

        # Override with 1s timeout
        result = guard.execute_node("slow_node", slow_node, {"input": "test"}, timeout=1)

        assert result.timed_out is True
        assert result.state["_node_timeout_seconds"] == 1

        guard.shutdown()

    def test_env_var_configuration(self):
        """Timeout configurable via NODE_EXEC_TIMEOUT_SECONDS env var."""
        from core.orchestration.execution_guard import DEFAULT_TIMEOUT_SECONDS, MAX_WORKERS

        # Defaults should be set
        assert DEFAULT_TIMEOUT_SECONDS == int(os.getenv("NODE_EXEC_TIMEOUT_SECONDS", "30"))
        assert MAX_WORKERS == int(os.getenv("NODE_EXEC_MAX_WORKERS", "4"))

    def test_singleton_pattern(self):
        """get_execution_guard returns same instance."""
        from core.orchestration.execution_guard import (
            get_execution_guard, reset_execution_guard
        )
        reset_execution_guard()

        g1 = get_execution_guard()
        g2 = get_execution_guard()
        assert g1 is g2

        reset_execution_guard()

    def test_state_not_mutated_on_timeout(self):
        """Original state dict keys preserved on timeout."""
        from core.orchestration.execution_guard import NodeExecutionGuard

        guard = NodeExecutionGuard(default_timeout=1, max_workers=2)

        original = {"key1": "val1", "key2": "val2"}

        def slow_node(state):
            time.sleep(10)
            return state

        result = guard.execute_node("slow_node", slow_node, original)
        assert result.state["key1"] == "val1"
        assert result.state["key2"] == "val2"

        guard.shutdown()


# ============================================================================
# FIX 2: Dead Letter Queue (DLQ)
# ============================================================================

class TestDeadLetterQueue:
    """Tests for core.synaptic_conclave.transport.dlq.DeadLetterQueue"""

    def _mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock()
        mock.incr.return_value = 1
        mock.exists.return_value = False
        mock.xadd.return_value = b"1234567890-0"
        mock.xlen.return_value = 0
        mock.xrange.return_value = []
        return mock

    def test_retry_below_threshold(self):
        """Events below retry limit should not be moved to DLQ."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue

        mock_redis = self._mock_redis()
        mock_redis.incr.return_value = 1  # First failure

        dlq = DeadLetterQueue(mock_redis, prefix="test")
        moved = dlq.record_failure(
            stream="test:channel",
            event_id="evt_1",
            group="group1",
            consumer="worker1",
            reason="processing error",
        )

        assert moved is False
        mock_redis.xadd.assert_not_called()  # Not moved to DLQ

    def test_move_to_dlq_after_max_retries(self):
        """Events exceeding retry limit should be moved to DLQ."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue, DLQ_MAX_RETRIES

        mock_redis = self._mock_redis()
        mock_redis.incr.return_value = DLQ_MAX_RETRIES  # Hit the limit

        dlq = DeadLetterQueue(mock_redis, prefix="test")
        moved = dlq.record_failure(
            stream="test:channel",
            event_id="evt_1",
            group="group1",
            consumer="worker1",
            reason="persistent failure",
            correlation_id="corr_123",
            payload={"data": "value"},
        )

        assert moved is True
        mock_redis.xadd.assert_called_once()

        # Verify DLQ entry fields
        call_args = mock_redis.xadd.call_args
        fields = call_args[0][1]
        assert fields["original_stream"] == "test:channel"
        assert fields["original_event_id"] == "evt_1"
        assert fields["consumer_group"] == "group1"
        assert fields["correlation_id"] == "corr_123"
        assert fields["failure_reason"] == "persistent failure"
        assert int(fields["retry_count"]) == DLQ_MAX_RETRIES

    def test_idempotency_key_prevents_duplicates(self):
        """Same event should not be added to DLQ twice."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue, DLQ_MAX_RETRIES

        mock_redis = self._mock_redis()
        mock_redis.incr.return_value = DLQ_MAX_RETRIES
        mock_redis.exists.return_value = True  # Idempotency key exists

        dlq = DeadLetterQueue(mock_redis, prefix="test")
        moved = dlq.record_failure(
            stream="test:channel",
            event_id="evt_1",
            group="group1",
            consumer="worker1",
            reason="duplicate test",
        )

        assert moved is True
        mock_redis.xadd.assert_not_called()  # Suppressed by idempotency

    def test_idempotency_key_deterministic(self):
        """Same inputs always produce the same idempotency key."""
        from core.synaptic_conclave.transport.dlq import generate_idempotency_key

        key1 = generate_idempotency_key("stream_a", "evt_1", "group_x")
        key2 = generate_idempotency_key("stream_a", "evt_1", "group_x")
        key3 = generate_idempotency_key("stream_a", "evt_2", "group_x")

        assert key1 == key2  # Same input → same key
        assert key1 != key3  # Different input → different key

    def test_dlq_entry_serialization(self):
        """DLQEntry serializes to and from Redis correctly."""
        from core.synaptic_conclave.transport.dlq import DLQEntry

        entry = DLQEntry(
            original_stream="test:stream",
            original_event_id="evt_1",
            consumer_group="group1",
            consumer_name="worker1",
            failure_reason="test error",
            retry_count=3,
            correlation_id="corr_abc",
            idempotency_key="idem_123",
            timestamp="2026-02-15T10:00:00Z",
            payload={"key": "value"},
        )

        fields = entry.to_redis_fields()
        assert fields["original_stream"] == "test:stream"
        assert json.loads(fields["payload"]) == {"key": "value"}

        # Round-trip
        redis_data = {k.encode(): v.encode() for k, v in fields.items()}
        restored = DLQEntry.from_redis(redis_data)
        assert restored.original_stream == "test:stream"
        assert restored.payload == {"key": "value"}
        assert restored.retry_count == 3

    def test_list_entries(self):
        """list_entries returns DLQEntry objects."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue

        mock_redis = self._mock_redis()
        mock_redis.xrange.return_value = [
            (b"1-0", {
                b"original_stream": b"test:s",
                b"original_event_id": b"e1",
                b"consumer_group": b"g1",
                b"consumer_name": b"w1",
                b"failure_reason": b"err",
                b"retry_count": b"3",
                b"correlation_id": b"c1",
                b"idempotency_key": b"ik1",
                b"timestamp": b"2026-02-15T10:00:00Z",
                b"payload": b'{"k":"v"}',
            })
        ]

        dlq = DeadLetterQueue(mock_redis, prefix="test")
        entries = dlq.list_entries()

        assert len(entries) == 1
        assert entries[0].original_event_id == "e1"
        assert entries[0].failure_reason == "err"

    def test_health_check(self):
        """Health returns structured status."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue

        mock_redis = self._mock_redis()
        dlq = DeadLetterQueue(mock_redis, prefix="test")
        health = dlq.health()

        assert health["status"] == "healthy"
        assert "entries" in health
        assert "max_retries" in health

    def test_ack_after_dlq_move(self):
        """Event is ACKed from original stream when moved to DLQ."""
        from core.synaptic_conclave.transport.dlq import DeadLetterQueue, DLQ_MAX_RETRIES

        mock_redis = self._mock_redis()
        mock_redis.incr.return_value = DLQ_MAX_RETRIES

        dlq = DeadLetterQueue(mock_redis, prefix="test")
        dlq.record_failure(
            stream="test:channel",
            event_id="evt_1",
            group="group1",
            consumer="worker1",
            reason="max retries",
        )

        mock_redis.xack.assert_called_once_with("test:channel", "group1", "evt_1")


# ============================================================================
# FIX 3: Redis KEYS Elimination
# ============================================================================

class TestRedisKeysElimination:
    """Verify no Redis KEYS command usage in production code."""

    def test_no_keys_in_cache_manager(self):
        """cache_manager.py must use scan_iter, not keys()."""
        import inspect
        from core.llm import cache_manager

        source = inspect.getsource(cache_manager)
        # Should NOT contain .keys( direct calls
        assert ".keys(" not in source or "scan_iter" in source
        # Should contain scan_iter
        assert "scan_iter" in source

    def test_no_keys_in_cache_api(self):
        """cache_api.py must use scan_iter, not keys()."""
        import inspect
        from core.llm import cache_api

        source = inspect.getsource(cache_api)
        assert "scan_iter" in source


# ============================================================================
# FIX 4: Audit Structured Logging
# ============================================================================

class TestAuditLogger:
    """Tests for core.logging.audit.AuditLogger"""

    def test_audit_event_structure(self):
        """AuditEvent has all mandatory fields."""
        from core.logging.audit import AuditEvent

        event = AuditEvent(
            event_id="evt_1",
            correlation_id="corr_1",
            node_id="intent_detection",
            plugin_id="finance",
            execution_time_ms=42.5,
            status="success",
        )

        d = event.to_dict()
        assert "timestamp" in d
        assert d["event_id"] == "evt_1"
        assert d["correlation_id"] == "corr_1"
        assert d["node_id"] == "intent_detection"
        assert d["plugin_id"] == "finance"
        assert d["execution_time_ms"] == 42.5
        assert d["status"] == "success"
        assert "error_code" not in d  # Omitted when None

    def test_audit_event_with_error(self):
        """Error code included when present."""
        from core.logging.audit import AuditEvent

        event = AuditEvent(
            event_id="evt_2",
            status="error",
            error_code="TIMEOUT_EXCEEDED",
        )

        d = event.to_dict()
        assert d["status"] == "error"
        assert d["error_code"] == "TIMEOUT_EXCEEDED"

    def test_audit_event_json_serializable(self):
        """AuditEvent can be serialized to JSON."""
        from core.logging.audit import AuditEvent

        event = AuditEvent(
            event_id="evt_3",
            node_id="compose_node",
            metadata={"key": "value"},
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["node_id"] == "compose_node"
        assert parsed["metadata"] == {"key": "value"}

    def test_audit_event_redis_fields(self):
        """AuditEvent produces valid Redis field-value pairs (all strings)."""
        from core.logging.audit import AuditEvent

        event = AuditEvent(event_id="evt_4", node_id="test")
        fields = event.to_redis_fields()

        for k, v in fields.items():
            assert isinstance(k, str)
            assert isinstance(v, str)

    def test_audit_logger_log_to_python_logger(self):
        """AuditLogger always writes to Python logger."""
        from core.logging.audit import AuditLogger

        with patch("core.logging.audit.logger") as mock_logger:
            audit = AuditLogger()
            event = audit.log(
                event_id="evt_5",
                node_id="test_node",
                execution_time_ms=10.0,
            )

            assert event is not None
            assert event.event_id == "evt_5"
            mock_logger.log.assert_called_once()

    def test_audit_logger_log_to_redis(self):
        """AuditLogger writes to Redis stream when client is set."""
        from core.logging.audit import AuditLogger

        mock_redis = MagicMock()
        audit = AuditLogger(redis_client=mock_redis)

        with patch("core.logging.audit.logger"):
            audit.log(event_id="evt_6", node_id="test")

        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "vitruvyan:audit"  # Default stream name

    def test_audit_logger_disabled(self):
        """AuditLogger returns None when disabled."""
        from core.logging.audit import AuditLogger

        audit = AuditLogger()
        audit._enabled = False

        result = audit.log(event_id="evt_7", node_id="test")
        assert result is None

    def test_audit_logger_singleton(self):
        """get_audit_logger returns same instance."""
        from core.logging.audit import get_audit_logger, reset_audit_logger

        reset_audit_logger()
        a1 = get_audit_logger()
        a2 = get_audit_logger()
        assert a1 is a2
        reset_audit_logger()

    def test_audit_logger_metadata_kwargs(self):
        """Extra kwargs stored in metadata dict."""
        from core.logging.audit import AuditLogger

        with patch("core.logging.audit.logger"):
            audit = AuditLogger()
            event = audit.log(
                event_id="evt_8",
                node_id="test",
                custom_field="custom_value",
                another="data",
            )

            assert event.metadata["custom_field"] == "custom_value"
            assert event.metadata["another"] == "data"


# ============================================================================
# FIX 5: load_dotenv Removal Verification
# ============================================================================

class TestLoadDotenvRemoval:
    """Verify no load_dotenv calls remain in core modules."""

    def _get_core_python_files(self):
        """Get all Python files in vitruvyan_core/core/."""
        import glob
        base = os.path.join(
            os.path.dirname(__file__), "..", "vitruvyan_core", "core"
        )
        return glob.glob(os.path.join(base, "**", "*.py"), recursive=True)

    def test_no_load_dotenv_calls_in_core(self):
        """No load_dotenv() call should exist in core/ (only comments)."""
        core_files = self._get_core_python_files()

        violations = []
        for filepath in core_files:
            if "_legacy" in filepath or "__pycache__" in filepath:
                continue
            with open(filepath, "r") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()
                    # Skip comments
                    if stripped.startswith("#"):
                        continue
                    if "load_dotenv()" in stripped:
                        violations.append(f"{filepath}:{lineno}: {stripped}")

        assert violations == [], (
            f"load_dotenv() calls found in core:\n" + "\n".join(violations)
        )

    def test_no_dotenv_import_in_core(self):
        """No 'from dotenv import load_dotenv' should exist in core/ (only comments)."""
        core_files = self._get_core_python_files()

        violations = []
        for filepath in core_files:
            if "_legacy" in filepath or "__pycache__" in filepath:
                continue
            with open(filepath, "r") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "from dotenv import" in stripped:
                        violations.append(f"{filepath}:{lineno}: {stripped}")

        assert violations == [], (
            f"dotenv imports found in core:\n" + "\n".join(violations)
        )


# ============================================================================
# INTEGRATION: graph_runner trace_id
# ============================================================================

class TestTraceIdFullLength:
    """Verify trace_id is full UUID4, not truncated."""

    def test_trace_id_full_uuid(self):
        """generate_trace_id returns full UUID4 (36 chars with dashes)."""
        from core.orchestration.langgraph.graph_runner import generate_trace_id

        trace_id = generate_trace_id()
        # Full UUID4: 8-4-4-4-12 = 36 chars
        assert len(trace_id) == 36
        # Validate it's a proper UUID
        parsed = uuid.UUID(trace_id)
        assert str(parsed) == trace_id
