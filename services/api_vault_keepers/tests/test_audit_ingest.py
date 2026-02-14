"""Unit tests for Vault Keepers audit ingest from Memory Orders events."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_vault_keepers.adapters.bus_adapter import VaultBusAdapter  # noqa: E402
from api_vault_keepers.streams_listener import _handle_event  # noqa: E402


class _FakeChamberlain:
    def __init__(self):
        self.inputs: list[dict] = []

    def process(self, audit_input):
        self.inputs.append(audit_input)
        return audit_input


class _FakePersistence:
    def __init__(self):
        self.records: list[dict] = []

    def store_audit_record(self, audit_record):
        self.records.append(audit_record)
        return {"status": "stored", "record_id": "vault-audit-1"}


class _FakeListenerAdapter:
    def __init__(self):
        self.calls: list[tuple[dict, str | None]] = []

    def ingest_external_audit(self, payload, correlation_id=None):
        self.calls.append((payload, correlation_id))
        return {"status": "stored"}


def test_ingest_external_audit_maps_memory_orders_to_vault_record():
    adapter = object.__new__(VaultBusAdapter)
    adapter.chamberlain = _FakeChamberlain()
    adapter.persistence = _FakePersistence()

    envelope = {
        "stream": "audit.vault.requested",
        "source": "memory_orders.api",
        "timestamp": "2026-02-14T10:00:00Z",
        "correlation_id": "corr-root",
        "payload": {
            "order": "memory_orders",
            "action": "coherence",
            "summary": {"status": "warning"},
            "drift_metrics": {"drift_percentage": 4.0},
            "mode": "dry_run",
            "status": "completed",
            "correlation_id": "corr-123",
        },
    }

    result = adapter.ingest_external_audit(payload=envelope)

    assert result["status"] == "stored"
    assert result["record_id"] == "vault-audit-1"
    assert result["correlation_id"] == "corr-123"
    assert result["resource_type"] == "memory_orders"

    stored_record = adapter.persistence.records[0]
    assert stored_record["resource_type"] == "memory_orders"
    assert stored_record["operation"] == "coherence_check"
    assert stored_record["action"] == "coherence"
    assert stored_record["metadata"]["origin_order"] == "memory_orders"
    assert stored_record["metadata"]["mode"] == "dry_run"


def test_stream_listener_routes_audit_vault_requested_to_ingest():
    adapter = _FakeListenerAdapter()
    payload = {"payload": {"order": "memory_orders", "action": "sync"}}

    asyncio.run(
        _handle_event(
            adapter=adapter,
            channel="audit.vault.requested",
            payload=payload,
            correlation_id="corr-listener",
        )
    )

    assert len(adapter.calls) == 1
    assert adapter.calls[0][0] == payload
    assert adapter.calls[0][1] == "corr-listener"
