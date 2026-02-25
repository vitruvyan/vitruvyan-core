"""Tests for Memory Orders -> Vault Keepers audit event emission."""

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

from api_memory_orders.adapters.bus_adapter import MemoryBusAdapter  # noqa: E402


class _FakeBus:
    def __init__(self):
        self.emits: list[dict] = []

    def emit(self, channel, payload, emitter=None, correlation_id=None):
        self.emits.append(
            {
                "channel": channel,
                "payload": payload,
                "emitter": emitter,
                "correlation_id": correlation_id,
            }
        )
        return "evt-1"


class _FakePersistence:
    def get_postgres_count(self, table, embedded_column):
        return 100

    def get_qdrant_count(self, collection):
        return 96

    def check_postgres_health(self):
        raise NotImplementedError

    def check_qdrant_health(self):
        raise NotImplementedError

    def check_redis_health(self):
        raise NotImplementedError

    def check_embedding_api_health(self):
        raise NotImplementedError

    def check_babel_gardens_health(self):
        raise NotImplementedError

    def fetch_postgres_sync_data(self, table, limit):
        return ()

    def fetch_qdrant_sync_data(self, collection, limit):
        return ()


def test_coherence_pipeline_emits_vault_audit_request(monkeypatch):
    fake_bus = _FakeBus()

    monkeypatch.setattr(
        "api_memory_orders.adapters.bus_adapter.StreamBus",
        lambda: fake_bus,
    )
    monkeypatch.setattr(
        "api_memory_orders.adapters.bus_adapter.MemoryPersistence",
        lambda: _FakePersistence(),
    )

    adapter = MemoryBusAdapter()
    report = asyncio.run(adapter.handle_coherence_check(table="entities", collection="entity_embeddings"))

    assert report.status in {"healthy", "warning", "critical"}

    channels = [item["channel"] for item in fake_bus.emits]
    assert "memory.coherence.checked" in channels
    assert "audit.vault.requested" in channels

    audit_emit = next(item for item in fake_bus.emits if item["channel"] == "audit.vault.requested")
    envelope = audit_emit["payload"]
    payload = envelope["payload"]

    assert envelope["stream"] == "audit.vault.requested"
    assert payload["order"] == "memory_orders"
    assert payload["action"] == "coherence"
    assert payload["correlation_id"]
    assert "summary" in payload
    assert "drift_metrics" in payload
    assert payload["mode"] in {"dry_run", "assisted", "autonomous"}
