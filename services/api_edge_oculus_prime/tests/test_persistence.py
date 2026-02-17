"""Unit tests for Edge Oculus Prime persistence adapter."""

from __future__ import annotations

import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_edge_oculus_prime.adapters.persistence import IntakePersistence  # noqa: E402
from api_edge_oculus_prime.config import IntakeSettings  # noqa: E402


def _settings() -> IntakeSettings:
    return IntakeSettings(
        service_name="aegis_oculus_prime_api",
        service_version="1.0.0",
        host="0.0.0.0",
        port=8050,
        log_level="INFO",
        uploads_dir="/tmp/uploads",
        frontend_url="http://localhost:3000",
        cors_origins=["http://localhost:3000"],
        cors_origin_regex=r"https://.*\.vercel\.app",
        redis_host="localhost",
        redis_port=6379,
        postgres_host="localhost",
        postgres_port="5432",
        postgres_db="vitruvyan_core",
        postgres_user="vitruvyan",
        postgres_password="secret",
        document_formats=(".txt", ".pdf"),
        image_formats=(".png", ".jpg"),
        audio_formats=(".wav",),
        video_formats=(".mp4",),
        cad_formats=(".dxf",),
        geo_formats=(".geojson",),
    )


def test_health_uses_postgres_ping_and_closes_connection(monkeypatch):
    class FakePG:
        def __init__(self):
            self.closed = False

        def fetch_scalar(self, sql, params=None):
            assert sql.strip() == "SELECT 1;"
            assert params is None
            return 1

        def close(self):
            self.closed = True

    fake_pg = FakePG()
    monkeypatch.setattr(
        "api_edge_oculus_prime.adapters.persistence.build_postgres_agent",
        lambda _settings: fake_pg,
    )

    persistence = IntakePersistence(settings=_settings())
    payload = persistence.health()

    assert payload["status"] == "healthy"
    assert payload["service"] == "aegis_oculus_prime_api"
    assert fake_pg.closed is True


def test_fetch_pipeline_status_is_intake_only_without_downstream_queries(monkeypatch):
    class FakePG:
        def __init__(self):
            self.closed = False
            self.sql: list[str] = []

        def fetch_one(self, sql, params=None):
            self.sql.append(sql)
            if "FROM evidence_packs" in sql:
                return {"count": 4}
            if "FROM intake_event_log" in sql:
                return {"count": 3}
            if "FROM intake_event_failures" in sql:
                return {"count": 1}
            return {"count": 0}

        def fetch(self, sql, params=None):
            self.sql.append(sql)
            if "FROM evidence_packs" in sql:
                return [
                    {
                        "evidence_id": "EVD-1",
                        "created_utc": None,
                        "technical_metadata": {"file_name": "sample.txt", "fragment_type": "document"},
                        "integrity": {"evidence_hash": "sha256:abc"},
                    }
                ]
            return []

        def close(self):
            self.closed = True

    fake_pg = FakePG()
    monkeypatch.setattr(
        "api_edge_oculus_prime.adapters.persistence.build_postgres_agent",
        lambda _settings: fake_pg,
    )

    persistence = IntakePersistence(settings=_settings())
    payload = persistence.fetch_pipeline_status(hours=24, limit=10)

    assert payload["status"] == "success"
    assert payload["events_count"] == 3
    assert payload["failed_events_count"] == 1
    assert payload["vault_entries"] == 4
    assert payload["fragments_count"] == 1
    assert all("cognitive_entities" not in query for query in fake_pg.sql)
    assert fake_pg.closed is True


def test_fetch_intake_events_aggregates_ingest_emit_and_failures(monkeypatch):
    class FakePG:
        def __init__(self):
            self.sql: list[str] = []

        def fetch(self, sql, params=None):
            self.sql.append(sql)
            if "FROM evidence_packs" in sql:
                return [
                    {
                        "created_utc": "2026-02-16T20:00:00+00:00",
                        "evidence_id": "EVD-UPL",
                        "source_type": "document",
                        "technical_metadata": {"file_name": "a.txt", "fragment_type": "document"},
                    }
                ]
            if "FROM intake_event_log" in sql:
                return [
                    {
                        "emitted_utc": "2026-02-16T20:00:10+00:00",
                        "event_id": "EVT-1",
                        "evidence_id": "EVD-UPL",
                        "chunk_id": "CHK-0",
                    }
                ]
            if "FROM intake_event_failures" in sql:
                return [
                    {
                        "failed_utc": "2026-02-16T20:00:20+00:00",
                        "evidence_id": "EVD-UPL",
                        "chunk_id": "CHK-0",
                        "error_message": "StreamBus unavailable",
                        "retry_count": 1,
                    }
                ]
            return []

        def close(self):
            return None

    monkeypatch.setattr(
        "api_edge_oculus_prime.adapters.persistence.build_postgres_agent",
        lambda _settings: FakePG(),
    )

    persistence = IntakePersistence(settings=_settings())
    payload = persistence.fetch_intake_events(hours=24)

    assert payload["status"] == "success"
    assert payload["total"] == 3
    assert {event["type"] for event in payload["events"]} == {
        "upload",
        "stream_emit",
        "stream_emit_failed",
    }
