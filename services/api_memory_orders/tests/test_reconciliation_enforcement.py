"""Tests for Memory Orders reconciliation enforcement modes."""

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
        self.emits: list[tuple[str, dict]] = []

    def emit(self, channel, payload, emitter=None, correlation_id=None):
        self.emits.append((channel, payload))
        return "evt-1"


class _FakePersistence:
    def __init__(self):
        self.cached_result = None
        self.cache_calls = 0
        self.release_calls = 0
        self.lock_acquired = True

    def fetch_pg_reconciliation_snapshot(self, table: str, limit: int):
        return (
            {"id": "A", "version": 2, "updated_at": "2026-02-16T10:00:00Z", "metadata": {"text": "alpha"}},
            {"id": "B", "version": 1, "updated_at": "2026-02-16T10:00:00Z", "metadata": {"text": "beta"}},
        )

    def fetch_qdrant_reconciliation_snapshot(self, collection: str, limit: int):
        return (
            {"id": "A", "version": 1, "updated_at": "2026-02-15T10:00:00Z", "metadata": {}},
            {"id": "C", "version": 1, "updated_at": "2026-02-16T10:00:00Z", "metadata": {}},
        )

    def execute_reconciliation_operations(self, operations, collection: str, mode: str):
        return {
            "attempted": len(operations),
            "applied": len(operations),
            "skipped": 0,
            "failed": 0,
            "mode": mode,
            "dead_lettered": 0,
        }

    def get_cached_idempotency_result(self, idempotency_key: str):
        return self.cached_result

    def cache_idempotency_result(self, idempotency_key: str, result: dict, ttl_s: int):
        self.cache_calls += 1
        self.cached_result = result

    def acquire_reconciliation_lock(self, lock_key: str, ttl_s: int):
        return self.lock_acquired, "token-1"

    def release_reconciliation_lock(self, lock_key: str, token: str):
        self.release_calls += 1

    def increment_metric(self, metric_name: str, value: float = 1.0):
        return None


def test_reconciliation_dry_run_never_executes(monkeypatch):
    fake_bus = _FakeBus()
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.StreamBus", lambda: fake_bus)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.MemoryPersistence", lambda: _FakePersistence())
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.settings.MEMORY_RECONCILIATION_MODE", "dry_run")

    adapter = MemoryBusAdapter()
    result = asyncio.run(adapter.handle_reconciliation(execute=True, allow_mass_delete=True))

    assert result["status"] == "ok"
    assert result["operations_count"] > 0
    assert result["execution"]["mode"] == "dry_run"
    assert result["execution"]["applied"] == 0


def test_reconciliation_assisted_executes_when_requested(monkeypatch):
    fake_bus = _FakeBus()
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.StreamBus", lambda: fake_bus)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.MemoryPersistence", lambda: _FakePersistence())
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.settings.MEMORY_RECONCILIATION_MODE", "assisted")

    adapter = MemoryBusAdapter()
    result = asyncio.run(adapter.handle_reconciliation(execute=True, allow_mass_delete=True))

    assert result["status"] == "ok"
    assert result["execution"]["mode"] == "assisted"
    assert result["execution"]["attempted"] == result["operations_count"]


def test_reconciliation_idempotency_returns_cached(monkeypatch):
    fake_bus = _FakeBus()
    fake_persistence = _FakePersistence()
    fake_persistence.cached_result = {
        "status": "ok",
        "severity": "healthy",
        "drift_types": [],
        "operations_count": 0,
        "requires_execution": False,
        "execution": None,
        "recommendation": "cached",
        "correlation_id": "cached-correlation",
        "idempotent_replay": False,
    }
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.StreamBus", lambda: fake_bus)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.MemoryPersistence", lambda: fake_persistence)

    adapter = MemoryBusAdapter()
    result = asyncio.run(adapter.handle_reconciliation(idempotency_key="demo-key"))

    assert result["idempotent_replay"] is True
    assert fake_persistence.release_calls == 0


def test_reconciliation_policy_blocks_mass_delete(monkeypatch):
    fake_bus = _FakeBus()
    fake_persistence = _FakePersistence()
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.StreamBus", lambda: fake_bus)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.MemoryPersistence", lambda: fake_persistence)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.settings.MEMORY_RECONCILIATION_MODE", "assisted")
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.settings.MEMORY_RECONCILIATION_MAX_DELETE_RATIO", 0.1)

    adapter = MemoryBusAdapter()
    result = asyncio.run(adapter.handle_reconciliation(execute=True, allow_mass_delete=False))

    assert result["status"] == "blocked"
    assert result["execution"]["attempted"] == result["operations_count"]
    assert result["execution"]["applied"] == 0


def test_reconciliation_lock_conflict_raises(monkeypatch):
    fake_bus = _FakeBus()
    fake_persistence = _FakePersistence()
    fake_persistence.lock_acquired = False
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.StreamBus", lambda: fake_bus)
    monkeypatch.setattr("api_memory_orders.adapters.bus_adapter.MemoryPersistence", lambda: fake_persistence)

    adapter = MemoryBusAdapter()

    try:
        asyncio.run(adapter.handle_reconciliation())
        assert False, "Expected RuntimeError for lock conflict"
    except RuntimeError as exc:
        assert "already running" in str(exc)
