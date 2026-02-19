"""Persistence adapter for Edge Oculus Prime service.

Single service-side I/O point for PostgreSQL reads used by HTTP endpoints.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from .runtime import build_postgres_agent
from ..config import OculusPrimeSettings


class OculusPrimePersistence:
    """Service-side persistence adapter for Oculus Prime read models."""

    def __init__(self, settings: OculusPrimeSettings):
        self.settings = settings

    @contextmanager
    def _postgres(self) -> Iterator[Any]:
        pg = build_postgres_agent(self.settings)
        try:
            yield pg
        finally:
            pg.close()

    @staticmethod
    def _iso(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _extract_count(row: dict[str, Any] | None) -> int:
        if not row:
            return 0
        value = row.get("count")
        if value is None and row:
            value = next(iter(row.values()))
        return int(value or 0)

    def health(self) -> dict[str, Any]:
        with self._postgres() as pg:
            ping = pg.fetch_scalar("SELECT 1;")
            if ping != 1:
                raise RuntimeError("PostgreSQL ping failed")
        return {
            "status": "healthy",
            "service": self.settings.service_name,
            "version": self.settings.service_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "postgresql": "connected",
        }

    def fetch_evidence_chunks(self, evidence_id: str) -> list[dict[str, Any]]:
        with self._postgres() as pg:
            rows = pg.fetch(
                """
                SELECT
                    evidence_id,
                    chunk_id,
                    schema_version,
                    created_utc,
                    source_ref,
                    normalized_text,
                    technical_metadata,
                    integrity,
                    sampling_policy_ref,
                    tags
                FROM evidence_packs
                WHERE evidence_id = %s
                ORDER BY chunk_id
                """,
                (evidence_id,),
            )

        chunks: list[dict[str, Any]] = []
        for row in rows:
            chunks.append(
                {
                    "evidence_id": row.get("evidence_id"),
                    "chunk_id": row.get("chunk_id"),
                    "schema_version": row.get("schema_version"),
                    "created_utc": self._iso(row.get("created_utc")),
                    "source_ref": row.get("source_ref"),
                    "normalized_text": row.get("normalized_text"),
                    "technical_metadata": row.get("technical_metadata"),
                    "integrity": row.get("integrity"),
                    "sampling_policy_ref": row.get("sampling_policy_ref"),
                    "tags": row.get("tags"),
                }
            )
        return chunks

    def fetch_pipeline_status(self, hours: int = 24, limit: int = 10) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        with self._postgres() as pg:
            evidence_count = self._extract_count(
                pg.fetch_one(
                    """
                    SELECT COUNT(*) AS count
                    FROM evidence_packs
                    WHERE created_utc >= %s
                    """,
                    (cutoff,),
                )
            )
            emitted_events = self._extract_count(
                pg.fetch_one(
                    """
                    SELECT COUNT(*) AS count
                    FROM intake_event_log
                    WHERE emitted_utc >= %s
                    """,
                    (cutoff,),
                )
            )
            failed_events = self._extract_count(
                pg.fetch_one(
                    """
                    SELECT COUNT(*) AS count
                    FROM intake_event_failures
                    WHERE failed_utc >= %s
                    """,
                    (cutoff,),
                )
            )

            rows = pg.fetch(
                """
                SELECT
                    evidence_id,
                    created_utc,
                    technical_metadata,
                    integrity
                FROM evidence_packs
                WHERE created_utc >= %s
                ORDER BY created_utc DESC
                LIMIT %s
                """,
                (cutoff, limit),
            )

        fragments: list[dict[str, Any]] = []
        for row in rows:
            metadata = row.get("technical_metadata") or {}
            integrity = row.get("integrity") or {}
            fragments.append(
                {
                    "fragment_id": row.get("evidence_id"),
                    "fragment_type": metadata.get("fragment_type", "unknown"),
                    "file_name": metadata.get("file_name", "unknown"),
                    "created_at": self._iso(row.get("created_utc")),
                    "hash": (
                        integrity.get("evidence_hash")
                        or integrity.get("hash")
                        or integrity.get("hash_value")
                    ),
                    "processing_status": "complete",
                    "metadata": metadata,
                }
            )

        return {
            "status": "success",
            "events_count": emitted_events,
            "failed_events_count": failed_events,
            "fragments_count": len(fragments),
            "recent_fragments": fragments,
            "embeddings_count": 0,
            "vault_entries": evidence_count,
            "time_window_hours": hours,
            "risk_score": 73,
            "anomalies_detected": 12,
            "confidence": 0.85,
        }

    def fetch_oculus_prime_events(self, hours: int = 24) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events: list[dict[str, Any]] = []

        with self._postgres() as pg:
            ingested_rows = pg.fetch(
                """
                SELECT
                    created_utc,
                    evidence_id,
                    source_ref->>'source_type' AS source_type,
                    technical_metadata
                FROM evidence_packs
                WHERE created_utc >= %s
                ORDER BY created_utc DESC
                """,
                (cutoff,),
            )

            emitted_rows = pg.fetch(
                """
                SELECT
                    emitted_utc,
                    event_id,
                    evidence_id,
                    chunk_id,
                    metadata
                FROM intake_event_log
                WHERE emitted_utc >= %s
                ORDER BY emitted_utc DESC
                LIMIT 200
                """,
                (cutoff,),
            )

            failure_rows = pg.fetch(
                """
                SELECT
                    failed_utc,
                    evidence_id,
                    chunk_id,
                    error_message,
                    retry_count
                FROM intake_event_failures
                WHERE failed_utc >= %s
                ORDER BY failed_utc DESC
                LIMIT 200
                """,
                (cutoff,),
            )

        for row in ingested_rows:
            metadata = row.get("technical_metadata") or {}
            source_type = row.get("source_type") or "unknown"
            events.append(
                {
                    "timestamp": self._iso(row.get("created_utc")),
                    "type": "upload",
                    "message": f"Evidence ingested ({source_type})",
                    "severity": "low",
                    "metadata": {
                        "evidence_id": row.get("evidence_id"),
                        "source_type": source_type,
                        "file_name": metadata.get("file_name", "unknown"),
                        "fragment_type": metadata.get("fragment_type", "unknown"),
                    },
                }
            )

        for row in emitted_rows:
            metadata = row.get("metadata") or {}
            emitted_channels = metadata.get("emitted_channels") or []
            primary_channel = emitted_channels[0] if emitted_channels else "oculus_prime.evidence.created"
            message = f"{primary_channel} emitted"
            if len(emitted_channels) > 1:
                message = f"{primary_channel} emitted (aliases: {', '.join(emitted_channels[1:])})"
            events.append(
                {
                    "timestamp": self._iso(row.get("emitted_utc")),
                    "type": "stream_emit",
                    "message": message,
                    "severity": "low",
                    "metadata": {
                        "event_id": row.get("event_id"),
                        "evidence_id": row.get("evidence_id"),
                        "chunk_id": row.get("chunk_id"),
                        "emitted_channels": emitted_channels,
                        "migration_mode": metadata.get("migration_mode"),
                    },
                }
            )

        for row in failure_rows:
            events.append(
                {
                    "timestamp": self._iso(row.get("failed_utc")),
                    "type": "stream_emit_failed",
                    "message": row.get("error_message", "Unknown emission failure"),
                    "severity": "high",
                    "metadata": {
                        "evidence_id": row.get("evidence_id"),
                        "chunk_id": row.get("chunk_id"),
                        "retry_count": row.get("retry_count", 0),
                    },
                }
            )

        events.sort(key=lambda item: item["timestamp"] or "", reverse=True)
        return {
            "status": "success",
            "events": events,
            "total": len(events),
            "time_window_hours": hours,
        }

    def fetch_intake_events(self, hours: int = 24) -> dict[str, Any]:
        # Legacy method name retained for compatibility.
        return self.fetch_oculus_prime_events(hours=hours)


# Legacy alias kept to avoid breaking existing imports.
IntakePersistence = OculusPrimePersistence
