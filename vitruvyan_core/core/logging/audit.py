"""
Vitruvyan Core — Structured Audit Logger
==========================================

Provides structured, machine-parseable audit logging with mandatory fields
for compliance, forensics, and observability.

Every audit event contains:
    - timestamp (ISO 8601)
    - event_id (unique per event)
    - correlation_id (chain tracking)
    - node_id (which node/component)
    - plugin_id (which plugin, if applicable)
    - execution_time_ms (duration)
    - status (success | error | timeout | skipped)
    - error_code (optional, when status != success)

Persistence:
    - Redis Stream (default): vitruvyan:audit (configurable)
    - PostgreSQL (optional): enabled via AUDIT_POSTGRES_ENABLED=true
    - Python logger (always): JSON-formatted structured log line

Configuration:
    AUDIT_ENABLED: Enable/disable audit logging (default: true)
    AUDIT_STREAM: Redis stream name (default: vitruvyan:audit)
    AUDIT_STREAM_MAX_LEN: Max audit stream length (default: 200000)
    AUDIT_POSTGRES_ENABLED: Also persist to PostgreSQL (default: false)
    AUDIT_LOG_LEVEL: Python log level for audit events (default: INFO)

Author: Vitruvyan Core Team
Created: February 15, 2026
Status: Core infrastructure — zero domain logic
"""

import os
import json
import logging
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field

logger = logging.getLogger("vitruvyan.audit")

# ---------------------------------------------------------------------------
# Configuration (env-driven, no load_dotenv)
# ---------------------------------------------------------------------------
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() in ("true", "1", "yes")
AUDIT_STREAM = os.getenv("AUDIT_STREAM", "vitruvyan:audit")
AUDIT_STREAM_MAX_LEN = int(os.getenv("AUDIT_STREAM_MAX_LEN", "200000"))
AUDIT_POSTGRES_ENABLED = os.getenv("AUDIT_POSTGRES_ENABLED", "false").lower() in ("true", "1", "yes")
AUDIT_LOG_LEVEL = getattr(logging, os.getenv("AUDIT_LOG_LEVEL", "INFO").upper(), logging.INFO)


@dataclass
class AuditEvent:
    """
    Structured audit event with all mandatory fields.

    This is the canonical audit record shape used across the system.
    """
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    event_id: str = ""
    correlation_id: str = ""
    node_id: str = ""
    plugin_id: str = ""
    execution_time_ms: float = 0.0
    status: str = "success"  # success | error | timeout | skipped
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None error_code."""
        d = asdict(self)
        if d["error_code"] is None:
            del d["error_code"]
        return d

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def to_redis_fields(self) -> Dict[str, str]:
        """Convert to Redis Streams field-value pairs."""
        d = self.to_dict()
        # Flatten metadata into JSON string
        d["metadata"] = json.dumps(d.get("metadata", {}))
        return {k: str(v) for k, v in d.items()}


class AuditLogger:
    """
    Structured audit logger with multi-backend persistence.

    Backends:
    1. Python logger (always) — structured JSON log lines
    2. Redis Stream (default) — vitruvyan:audit
    3. PostgreSQL (optional) — audit_events table

    Usage:
        audit = get_audit_logger()
        audit.log(
            event_id="evt_123",
            correlation_id="trace_abc",
            node_id="intent_detection",
            status="success",
            execution_time_ms=42.5,
        )
    """

    def __init__(self, redis_client=None, postgres_agent=None):
        self._redis = redis_client
        self._postgres = postgres_agent
        self._enabled = AUDIT_ENABLED
        self._stream = AUDIT_STREAM
        self._max_len = AUDIT_STREAM_MAX_LEN

    def set_redis_client(self, client) -> None:
        """Set Redis client for stream persistence (lazy init)."""
        self._redis = client

    def set_postgres_agent(self, agent) -> None:
        """Set PostgresAgent for DB persistence (optional)."""
        self._postgres = agent

    def log(
        self,
        event_id: str = "",
        correlation_id: str = "",
        node_id: str = "",
        plugin_id: str = "",
        execution_time_ms: float = 0.0,
        status: str = "success",
        error_code: str = None,
        **metadata,
    ) -> Optional[AuditEvent]:
        """
        Record structured audit event.

        Args:
            event_id: Unique event identifier
            correlation_id: Trace/correlation chain ID
            node_id: Node or component identifier
            plugin_id: Plugin identifier (if applicable)
            execution_time_ms: Execution duration in milliseconds
            status: Event status (success|error|timeout|skipped)
            error_code: Error code string (when status != success)
            **metadata: Additional key-value pairs for context

        Returns:
            AuditEvent if logged, None if disabled
        """
        if not self._enabled:
            return None

        event = AuditEvent(
            event_id=event_id or str(uuid.uuid4())[:12],
            correlation_id=correlation_id,
            node_id=node_id,
            plugin_id=plugin_id,
            execution_time_ms=round(execution_time_ms, 2),
            status=status,
            error_code=error_code,
            metadata=metadata,
        )

        # Backend 1: Python logger (always)
        logger.log(AUDIT_LOG_LEVEL, event.to_json())

        # Backend 2: Redis Stream (if available)
        if self._redis is not None:
            try:
                self._redis.xadd(
                    self._stream,
                    event.to_redis_fields(),
                    maxlen=self._max_len,
                    approximate=True,
                )
            except Exception as e:
                logger.warning("Audit Redis write failed: %s", e)

        # Backend 3: PostgreSQL (if enabled and available)
        if AUDIT_POSTGRES_ENABLED and self._postgres is not None:
            try:
                self._postgres.execute(
                    """INSERT INTO audit_events 
                       (event_id, correlation_id, node_id, plugin_id,
                        execution_time_ms, status, error_code, metadata, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                    (
                        event.event_id,
                        event.correlation_id,
                        event.node_id,
                        event.plugin_id,
                        event.execution_time_ms,
                        event.status,
                        event.error_code,
                        json.dumps(event.metadata),
                    ),
                )
            except Exception as e:
                logger.warning("Audit Postgres write failed: %s", e)

        return event


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def reset_audit_logger() -> None:
    """Reset the global audit logger (for testing)."""
    global _audit_logger
    _audit_logger = None
