"""
Vitruvyan OCULUS PRIME — Event Bus Emission Contract (Streams-Native)

This module emits evidence-created events to Redis Streams via StreamBus
and writes append-only audit logs in PostgreSQL.

Versioned naming migration (v1 -> v2):
- v1 legacy channel: `intake.evidence.created`
- v2 canonical channel: `oculus_prime.evidence.created`
- rollout mode controlled by `OCULUS_PRIME_EVENT_MIGRATION_MODE`
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

logger = logging.getLogger(__name__)


@dataclass
class EvidenceCreatedEvent:
    """Immutable payload for evidence-created events."""

    event_id: str
    event_version: str = "1.0.0"
    schema_ref: str = "vitruvyan://intake/events/evidence_created/v1.0"
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
    Streams-native event emitter for Oculus Prime layer.

    Responsibilities:
    - Generate deterministic idempotency key
    - Emit to StreamBus (Redis Streams)
    - Persist event/failure audit logs in PostgreSQL
    """

    LEGACY_CHANNEL = "intake.evidence.created"
    LEGACY_EVENT_VERSION = "1.0.0"
    LEGACY_SCHEMA_REF = "vitruvyan://intake/events/evidence_created/v1.0"

    CANONICAL_CHANNEL = "oculus_prime.evidence.created"
    CANONICAL_EVENT_VERSION = "2.0.0"
    CANONICAL_SCHEMA_REF = "vitruvyan://oculus_prime/events/evidence_created/v2.0"

    MIGRATION_MODES = {"dual_write", "v1_only", "v2_only"}

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
        migration_mode: Optional[str] = None,
    ):
        self.stream_bus = stream_bus
        self.postgres_agent = postgres_agent
        self.migration_mode = self._resolve_migration_mode(migration_mode)
        self.channel = self._primary_channel()

        if self.stream_bus is None:
            try:
                self.stream_bus = StreamBus()
            except Exception:
                # Keep emitter usable even when bus is unavailable.
                self.stream_bus = None

    @classmethod
    def _resolve_migration_mode(cls, migration_mode: Optional[str]) -> str:
        configured = (
            migration_mode
            or os.getenv("OCULUS_PRIME_EVENT_MIGRATION_MODE")
            or os.getenv("INTAKE_EVENT_MIGRATION_MODE")
            or "dual_write"
        )
        normalized = str(configured).strip().lower()
        if normalized not in cls.MIGRATION_MODES:
            logger.warning(
                "Invalid OCULUS_PRIME_EVENT_MIGRATION_MODE='%s'; fallback to dual_write",
                configured,
            )
            return "dual_write"
        return normalized

    def _primary_channel(self) -> str:
        if self.migration_mode == "v1_only":
            return self.LEGACY_CHANNEL
        return self.CANONICAL_CHANNEL

    def _target_specs(self) -> list[tuple[str, str, str, str]]:
        if self.migration_mode == "v1_only":
            return [
                (
                    self.LEGACY_CHANNEL,
                    self.LEGACY_EVENT_VERSION,
                    self.LEGACY_SCHEMA_REF,
                    "intake_event_emitter",
                )
            ]
        if self.migration_mode == "v2_only":
            return [
                (
                    self.CANONICAL_CHANNEL,
                    self.CANONICAL_EVENT_VERSION,
                    self.CANONICAL_SCHEMA_REF,
                    "oculus_prime_event_emitter",
                )
            ]
        return [
            (
                self.CANONICAL_CHANNEL,
                self.CANONICAL_EVENT_VERSION,
                self.CANONICAL_SCHEMA_REF,
                "oculus_prime_event_emitter",
            ),
            (
                self.LEGACY_CHANNEL,
                self.LEGACY_EVENT_VERSION,
                self.LEGACY_SCHEMA_REF,
                "intake_event_emitter",
            ),
        ]

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

    def _build_event(
        self,
        event_id: str,
        event_version: str,
        schema_ref: str,
        evidence_id: str,
        chunk_id: str,
        source_type: str,
        source_uri: str,
        evidence_pack_ref: str,
        source_hash: str,
        intake_agent_id: str,
        intake_agent_version: str,
        byte_size: Optional[int],
        language_detected: Optional[str],
        sampling_policy_ref: Optional[str],
        correlation_id: Optional[str],
    ) -> EvidenceCreatedEvent:
        return EvidenceCreatedEvent(
            event_id=event_id,
            event_version=event_version,
            schema_ref=schema_ref,
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
        event_id = f"EVT-{str(uuid.uuid4()).upper()}"

        specs = self._target_specs()
        primary_event = self._build_event(
            event_id=event_id,
            event_version=specs[0][1],
            schema_ref=specs[0][2],
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            source_type=source_type,
            source_uri=source_uri,
            evidence_pack_ref=evidence_pack_ref,
            source_hash=source_hash,
            intake_agent_id=intake_agent_id,
            intake_agent_version=intake_agent_version,
            byte_size=byte_size,
            language_detected=language_detected,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id,
        )

        if not self.stream_bus:
            self._log_emission_failure(primary_event, "StreamBus unavailable")
            return primary_event

        emitted_channels: list[str] = []
        emit_errors: list[dict[str, str]] = []

        for channel, event_version, schema_ref, emitter_id in specs:
            event = self._build_event(
                event_id=event_id,
                event_version=event_version,
                schema_ref=schema_ref,
                evidence_id=evidence_id,
                chunk_id=chunk_id,
                source_type=source_type,
                source_uri=source_uri,
                evidence_pack_ref=evidence_pack_ref,
                source_hash=source_hash,
                intake_agent_id=intake_agent_id,
                intake_agent_version=intake_agent_version,
                byte_size=byte_size,
                language_detected=language_detected,
                sampling_policy_ref=sampling_policy_ref,
                correlation_id=correlation_id,
            )

            try:
                self.stream_bus.emit(
                    channel,
                    event.to_dict(),
                    emitter=emitter_id,
                    correlation_id=correlation_id,
                )
                emitted_channels.append(channel)
            except Exception as exc:
                error_message = f"[{channel}] {exc}"
                emit_errors.append({"channel": channel, "error": error_message})
                self._log_emission_failure(event, error_message)

        if not emitted_channels:
            self._log_emission_failure(primary_event, "All stream emissions failed")
            return primary_event

        metadata = dict(primary_event.metadata or {})
        metadata["migration_mode"] = self.migration_mode
        metadata["requested_channels"] = [spec[0] for spec in specs]
        metadata["emitted_channels"] = emitted_channels
        if emit_errors:
            metadata["emission_errors"] = emit_errors
        primary_event.metadata = metadata

        self._log_event_emission(primary_event)
        return primary_event

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


# Canonical class name with legacy alias.
OculusPrimeEventEmitter = IntakeEventEmitter
