"""Integration-style test for document intake write + emit flow."""

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

from infrastructure.edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent  # noqa: E402


class _FakeCursor:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, sql, params=None):
        self._connection.executed_sql.append(sql)
        self._connection.executed_params.append(params)

    def fetchone(self):
        return [101]


class _FakeConnection:
    def __init__(self):
        self.executed_sql: list[str] = []
        self.executed_params: list[tuple | None] = []
        self.committed = False

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        self.committed = True


class _FakePostgres:
    def __init__(self):
        self.connection = _FakeConnection()


class _FakeEmitter:
    def __init__(self):
        self.events: list[dict] = []

    def emit_evidence_created(self, **kwargs):
        self.events.append(kwargs)


def test_document_ingest_persists_evidence_and_emits_event(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text("sensor value: 42\nstatus: nominal\n", encoding="utf-8")

    fake_postgres = _FakePostgres()
    fake_emitter = _FakeEmitter()
    agent = DocumentIntakeAgent(event_emitter=fake_emitter, postgres_agent=fake_postgres)

    evidence_ids = agent.ingest_document(
        source_path=str(source),
        chunking_strategy="none",
        chunk_size=4000,
        sampling_policy_ref="SAMPPOL-DOC-DEFAULT-V1",
        correlation_id="trace-test-1",
    )

    assert len(evidence_ids) == 1
    assert any("INSERT INTO evidence_packs" in sql for sql in fake_postgres.connection.executed_sql)
    assert fake_postgres.connection.committed is True

    assert len(fake_emitter.events) == 1
    emitted = fake_emitter.events[0]
    assert emitted["evidence_id"] == evidence_ids[0]
    assert emitted["chunk_id"] == "CHK-0"
