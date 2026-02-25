"""Tests for MemoryStreamsListener auto-reconciliation behavior."""

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

from api_memory_orders.streams_listener import MemoryStreamsListener  # noqa: E402


class _FakeStreamBus:
    def create_consumer_group(self, channel, group):
        return None

    def consume(self, *args, **kwargs):
        return iter(())

    def ack(self, event, group):
        return None


class _FakeReport:
    def __init__(self, status: str, drift_percentage: float = 0.0):
        self.status = status
        self.drift_percentage = drift_percentage


class _FakeAdapter:
    def __init__(self, status: str):
        self._status = status
        self.reconcile_calls: list[dict] = []

    async def handle_coherence_check(self, table, collection, embedded_column="embedded"):
        return _FakeReport(status=self._status, drift_percentage=21.5 if self._status == "critical" else 2.0)

    async def handle_reconciliation(
        self,
        table="entities",
        collection=None,
        limit=1000,
        execute=False,
        idempotency_key=None,
        allow_mass_delete=False,
        correlation_id=None,
    ):
        self.reconcile_calls.append(
            {
                "table": table,
                "collection": collection,
                "limit": limit,
                "execute": execute,
                "idempotency_key": idempotency_key,
                "allow_mass_delete": allow_mass_delete,
            }
        )
        return {
            "status": "ok",
            "severity": "critical",
            "operations_count": 12,
        }


def _build_listener(monkeypatch, status: str) -> tuple[MemoryStreamsListener, _FakeAdapter]:
    fake_adapter = _FakeAdapter(status=status)
    monkeypatch.setattr("api_memory_orders.streams_listener.StreamBus", lambda: _FakeStreamBus())
    monkeypatch.setattr("api_memory_orders.streams_listener.MemoryBusAdapter", lambda: fake_adapter)
    listener = MemoryStreamsListener()
    return listener, fake_adapter


def test_auto_sync_disabled_skips_reconciliation(monkeypatch):
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.ENABLE_AUTO_SYNC", False)
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.MEMORY_RECONCILIATION_MODE", "assisted")

    listener, fake_adapter = _build_listener(monkeypatch, status="critical")
    asyncio.run(listener.handle_coherence_request({"table": "entities", "collection": "entity_embeddings"}))

    assert fake_adapter.reconcile_calls == []


def test_auto_sync_non_critical_skips_reconciliation(monkeypatch):
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.ENABLE_AUTO_SYNC", True)
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.MEMORY_RECONCILIATION_MODE", "assisted")

    listener, fake_adapter = _build_listener(monkeypatch, status="warning")
    asyncio.run(listener.handle_coherence_request({"table": "entities", "collection": "entity_embeddings"}))

    assert fake_adapter.reconcile_calls == []


def test_auto_sync_dry_run_skips_execution(monkeypatch):
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.ENABLE_AUTO_SYNC", True)
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.MEMORY_RECONCILIATION_MODE", "dry_run")

    listener, fake_adapter = _build_listener(monkeypatch, status="critical")
    asyncio.run(listener.handle_coherence_request({"table": "entities", "collection": "entity_embeddings"}))

    assert fake_adapter.reconcile_calls == []


def test_auto_sync_critical_executes_reconciliation(monkeypatch):
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.ENABLE_AUTO_SYNC", True)
    monkeypatch.setattr("api_memory_orders.streams_listener.settings.MEMORY_RECONCILIATION_MODE", "assisted")

    listener, fake_adapter = _build_listener(monkeypatch, status="critical")
    asyncio.run(
        listener.handle_coherence_request(
            {
                "table": "finance_entities",
                "collection": "entity_embeddings",
                "reconcile_limit": "250",
                "allow_mass_delete": True,
                "idempotency_key": "auto-1",
            }
        )
    )

    assert len(fake_adapter.reconcile_calls) == 1
    call = fake_adapter.reconcile_calls[0]
    assert call["table"] == "finance_entities"
    assert call["collection"] == "entity_embeddings"
    assert call["limit"] == 250
    assert call["execute"] is True
    assert call["allow_mass_delete"] is True
    assert call["idempotency_key"] == "auto-1"
