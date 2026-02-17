"""
AEGIS INTAKE — Event Bus Emission Contract (Streams-Native)

This module emits intake.evidence.created events to Redis Streams via StreamBus
and writes append-only audit logs in PostgreSQL.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus


@dataclass
class EvidenceCreatedEvent:
    """Immutable payload for intake.evidence.created."""

    event_id: str
    event_version: str = "1.0.0"
    schema_ref: str = "aegis://intake/events/evidence_created/v1.0"
    timestamp_utc: Optional[str] = None
    evidence_id: Optional[str] = None
    chunk_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.timestamp_utc is None:
            self.timestamp_utc = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class IntakeEventEmitter:
    """
    Streams-native event emitter for Intake Layer.

    Responsibilities:
    - Generate deterministic idempotency key
    - Emit to StreamBus (Redis Streams)
    - Persist event/failure audit logs in PostgreSQL
    """

    _CANONICAL_SOURCE_TYPES = {"document", "image", "audio", "video", "stream", "sensor"}
    _SOURCE_TYPE_MAP = {
        "geo_file": "document",
        "cad_file": "document",
        "map_screenshot": "image",
        "satellite_image": "image",
        "terrain_map": "image",
    }

    def __init__(
        self,
        stream_bus: Optional[StreamBus] = None,
        postgres_agent: Any = None,
    ):
        self.stream_bus = stream_bus
        self.postgres_agent = postgres_agent
        self.channel = "intake.evidence.created"

        if self.stream_bus is None:
            try:
                self.stream_bus = StreamBus()
            except Exception:
                # Keep emitter usable even when bus is unavailable.
                self.stream_bus = None

    @staticmethod
    def generate_idempotency_key(evidence_id: str, chunk_id: str, source_hash: str) -> str:
        composite = f"{evidence_id}{chunk_id}{source_hash}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def _normalize_source_type(self, source_type: str) -> str:
        normalized = self._SOURCE_TYPE_MAP.get(source_type, source_type)
        if normalized not in self._CANONICAL_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type: {source_type}. "
                f"Canonical: {sorted(self._CANONICAL_SOURCE_TYPES)}"
            )
        return normalized

    def emit_evidence_created(
        self,
        evidence_id: str,
        chunk_id: str,
        source_type: str,
        source_uri: str,
        evidence_pack_ref: str,
        source_hash: str,
        intake_agent_id: str,
        intake_agent_version: str,
        byte_size: Optional[int] = None,
        language_detected: Optional[str] = None,
        sampling_policy_ref: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EvidenceCreatedEvent:
        source_type = self._normalize_source_type(source_type)

        event = EvidenceCreatedEvent(
            event_id=f"EVT-{str(uuid.uuid4()).upper()}",
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            idempotency_key=self.generate_idempotency_key(evidence_id, chunk_id, source_hash),
            payload={
                "source_type": source_type,
                "source_uri": source_uri,
                "evidence_pack_ref": evidence_pack_ref,
                "source_hash": source_hash,
                "byte_size": byte_size,
                "language_detected": language_detected,
                "sampling_policy_ref": sampling_policy_ref,
            },
            metadata={
                "intake_agent_id": intake_agent_id,
                "intake_agent_version": intake_agent_version,
                "correlation_id": correlation_id,
                "retry_count": 0,
            },
        )

        try:
            if self.stream_bus:
                self.stream_bus.emit(
                    self.channel,
                    event.to_dict(),
                    emitter="intake_event_emitter",
                    correlation_id=correlation_id,
                )
            else:
                self._log_emission_failure(event, "StreamBus unavailable")
                return event
        except Exception as exc:
            self._log_emission_failure(event, str(exc))
            # Do not raise: evidence pack is already persisted append-only.
            return event

        self._log_event_emission(event)
        return event

    def emit_evidence_created_from_pack(self, evidence_pack: Dict[str, Any]) -> EvidenceCreatedEvent:
        """Compatibility helper for agents that emit directly from evidence pack dict."""
        source_ref = evidence_pack.get("source_ref", {})
        technical_metadata = evidence_pack.get("technical_metadata", {})
        integrity = evidence_pack.get("integrity", {})

        source_hash = source_ref.get("source_hash")
        if not source_hash:
            source_hash = (
                integrity.get("evidence_hash")
                or integrity.get("hash")
                or integrity.get("hash_value")
                or ""
            )

        return self.emit_evidence_created(
            evidence_id=evidence_pack.get("evidence_id", ""),
            chunk_id=evidence_pack.get("chunk_id", "CHK-0"),
            source_type=source_ref.get("source_type", "document"),
            source_uri=source_ref.get("source_uri", ""),
            evidence_pack_ref=f"postgres://evidence_packs/{evidence_pack.get('evidence_id', '')}",
            source_hash=source_hash,
            intake_agent_id=technical_metadata.get("agent_id", evidence_pack.get("agent_id", "intake-agent")),
            intake_agent_version=technical_metadata.get(
                "agent_version", evidence_pack.get("agent_version", "1.0.0")
            ),
            byte_size=source_ref.get("byte_size") or technical_metadata.get("file_size_bytes"),
            language_detected=technical_metadata.get("language_detected"),
            sampling_policy_ref=evidence_pack.get("sampling_policy_ref"),
            correlation_id=technical_metadata.get("correlation_id"),
        )

    def _log_event_emission(self, event: EvidenceCreatedEvent) -> None:
        if not self.postgres_agent:
            return
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intake_event_log (
                        event_id, event_version, schema_ref,
                        evidence_id, chunk_id, idempotency_key,
                        payload, metadata, emitted_utc
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    """,
                    (
                        event.event_id,
                        event.event_version,
                        event.schema_ref,
                        event.evidence_id,
                        event.chunk_id,
                        event.idempotency_key,
                        json.dumps(event.payload or {}),
                        json.dumps(event.metadata or {}),
                        event.timestamp_utc,
                    ),
                )
            self.postgres_agent.connection.commit()
        except Exception:
            self.postgres_agent.connection.rollback()

    def _log_emission_failure(self, event: EvidenceCreatedEvent, error: str) -> None:
        if not self.postgres_agent:
            return
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intake_event_failures (
                        evidence_id, chunk_id, error_message, error_traceback,
                        retry_count, payload, failed_utc
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    (
                        event.evidence_id,
                        event.chunk_id,
                        error,
                        None,
                        int((event.metadata or {}).get("retry_count", 0)),
                        json.dumps(event.to_dict()),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            self.postgres_agent.connection.commit()
        except Exception:
            self.postgres_agent.connection.rollback()
