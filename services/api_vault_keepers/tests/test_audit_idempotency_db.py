"""Integration test for DB-level audit idempotency in Vault Keepers."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


pytestmark = pytest.mark.integration


@dataclass
class _AuditRecordStub:
    record_id: str
    timestamp: str
    operation: str
    performed_by: str
    resource_type: str
    resource_id: str
    action: str
    status: str
    correlation_id: str
    metadata: tuple[tuple[str, str], ...]


class _FakeQdrant:
    """Avoid real Qdrant dependency for this DB-focused test."""


def test_store_audit_record_is_idempotent_by_correlation_id(monkeypatch):
    # Use docker-mapped PostgreSQL from local host.
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "9432")
    monkeypatch.setenv("POSTGRES_DB", "vitruvyan_core")
    monkeypatch.setenv("POSTGRES_USER", "vitruvyan_core_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "@Caravaggio971_core")

    from api_vault_keepers.adapters import persistence as persistence_module

    monkeypatch.setattr(persistence_module, "QdrantAgent", lambda: _FakeQdrant())

    try:
        adapter = persistence_module.PersistenceAdapter()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL not reachable for integration test: {exc}")

    correlation_id = f"idempotency_test_{uuid4().hex[:12]}"
    metric_before = persistence_module.VAULT_AUDIT_DUPLICATE_ATTEMPTS_TOTAL._value.get()

    adapter.pg_agent.execute(
        "DELETE FROM vault_audit_log WHERE correlation_id = %s",
        (correlation_id,),
    )

    record_one = _AuditRecordStub(
        record_id=f"audit_{uuid4().hex[:10]}",
        timestamp=datetime.utcnow().isoformat(),
        operation="coherence_check",
        performed_by="memory_orders.api",
        resource_type="memory_orders",
        resource_id=correlation_id,
        action="coherence",
        status="completed",
        correlation_id=correlation_id,
        metadata=(("probe", "one"),),
    )
    record_two = _AuditRecordStub(
        record_id=f"audit_{uuid4().hex[:10]}",
        timestamp=datetime.utcnow().isoformat(),
        operation="coherence_check",
        performed_by="memory_orders.api",
        resource_type="memory_orders",
        resource_id=correlation_id,
        action="coherence",
        status="completed",
        correlation_id=correlation_id,
        metadata=(("probe", "two"),),
    )

    first = adapter.store_audit_record(record_one)
    second = adapter.store_audit_record(record_two)

    count = adapter.pg_agent.fetch_scalar(
        "SELECT COUNT(*) FROM vault_audit_log WHERE correlation_id = %s",
        (correlation_id,),
    )
    metric_after = persistence_module.VAULT_AUDIT_DUPLICATE_ATTEMPTS_TOTAL._value.get()

    assert first["status"] == "stored"
    assert second["status"] == "duplicate_ignored"
    assert int(count) == 1
    assert metric_after == metric_before + 1

    adapter.pg_agent.execute(
        "DELETE FROM vault_audit_log WHERE correlation_id = %s",
        (correlation_id,),
    )
