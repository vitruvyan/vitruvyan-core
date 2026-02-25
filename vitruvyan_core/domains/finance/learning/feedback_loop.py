"""
Finance learning loop event capture.

MVP responsibilities:
1. Persist user activity/feedback events to PostgreSQL
2. Emit canonical learning events to Redis Streams
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from core.agents.postgres_agent import PostgresAgent


logger = logging.getLogger(__name__)


class FeedbackLoopEmitter:
    """Capture finance user feedback events to DB + bus."""

    def __init__(
        self,
        source_service: str,
        stream_channel: str = "learning.feedback.captured",
        enabled: bool = True,
    ):
        self.source_service = source_service
        self.stream_channel = stream_channel
        self.enabled = enabled

    def record_feedback(
        self,
        *,
        user_id: str,
        event_name: str,
        feedback_signal: str,
        payload: Optional[Dict[str, Any]] = None,
        feedback_value: Optional[float] = None,
        correlation_id: Optional[str] = None,
        actor_type: str = "user",
        event_version: str = "v1",
    ) -> Dict[str, Any]:
        """
        Persist a feedback event and emit it on Streams.

        Returns metadata for observability and testing.
        """
        if not self.enabled:
            return {
                "enabled": False,
                "event_uuid": None,
                "persisted": False,
                "stream_event_id": None,
            }

        now = datetime.now(timezone.utc)
        event_uuid = str(uuid4())
        payload = payload or {}

        event = {
            "event_uuid": event_uuid,
            "user_id": user_id,
            "source_service": self.source_service,
            "event_name": event_name,
            "event_version": event_version,
            "actor_type": actor_type,
            "feedback_signal": feedback_signal,
            "feedback_value": feedback_value,
            "correlation_id": correlation_id,
            "payload": payload,
            "timestamp": now.isoformat(),
        }

        persisted = self._persist_event(
            event_uuid=event_uuid,
            user_id=user_id,
            event_name=event_name,
            event_version=event_version,
            actor_type=actor_type,
            feedback_signal=feedback_signal,
            feedback_value=feedback_value,
            correlation_id=correlation_id,
            payload=payload,
            created_at=now,
        )

        stream_event_id = self._emit_stream_event(event, correlation_id=correlation_id)

        return {
            "enabled": True,
            "event_uuid": event_uuid,
            "persisted": persisted,
            "stream_event_id": stream_event_id,
        }

    def _persist_event(
        self,
        *,
        event_uuid: str,
        user_id: str,
        event_name: str,
        event_version: str,
        actor_type: str,
        feedback_signal: str,
        feedback_value: Optional[float],
        correlation_id: Optional[str],
        payload: Dict[str, Any],
        created_at: datetime,
    ) -> bool:
        """Persist event and touch learning profile row."""
        pg = PostgresAgent()
        try:
            inserted = pg.execute(
                """
                INSERT INTO user_feedback_events (
                    event_uuid,
                    user_id,
                    source_service,
                    event_name,
                    event_version,
                    actor_type,
                    feedback_signal,
                    feedback_value,
                    correlation_id,
                    payload,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    event_uuid,
                    user_id,
                    self.source_service,
                    event_name,
                    event_version,
                    actor_type,
                    feedback_signal,
                    feedback_value,
                    correlation_id,
                    json.dumps(payload, default=str),
                    created_at,
                ),
            )

            if not inserted:
                return False

            pg.execute(
                """
                INSERT INTO user_learning_profile (
                    user_id,
                    last_feedback_at,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET last_feedback_at = EXCLUDED.last_feedback_at,
                    updated_at = EXCLUDED.updated_at
                """,
                (user_id, created_at, created_at, created_at),
            )
            return True
        except Exception as exc:
            logger.warning("feedback persist failed: %s", exc)
            return False
        finally:
            pg.close()

    def _emit_stream_event(
        self,
        event: Dict[str, Any],
        *,
        correlation_id: Optional[str],
    ) -> Optional[str]:
        """Emit learning event to Redis Streams."""
        try:
            from core.synaptic_conclave.transport.streams import StreamBus
            bus = StreamBus()
            return bus.emit(
                channel=self.stream_channel,
                payload=event,
                emitter=self.source_service,
                correlation_id=correlation_id,
            )
        except ImportError as exc:
            logger.warning("feedback stream emit skipped (StreamBus unavailable): %s", exc)
            return None
        except Exception as exc:
            logger.warning("feedback stream emit failed: %s", exc)
            return None
