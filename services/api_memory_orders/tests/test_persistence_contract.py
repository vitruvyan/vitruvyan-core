"""Unit tests for MemoryPersistence PostgresAgent contract handling."""

from __future__ import annotations

import sys
from pathlib import Path


# Allow `import api_memory_orders...` in repo-local pytest runs.
SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_memory_orders.adapters.persistence import MemoryPersistence  # noqa: E402


class _FakeQdrant:
    """Minimal stub used to avoid initializing real QdrantAgent."""


def test_get_postgres_count_uses_dict_scalar_contract(monkeypatch):
    """fetch_one returns dict rows; count extraction must not use tuple indexing."""

    class FakePG:
        def fetch_one(self, _sql):
            return {"count": 7}

    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.PostgresAgent",
        lambda: FakePG(),
    )
    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.QdrantAgent",
        lambda: _FakeQdrant(),
    )

    persistence = MemoryPersistence()

    assert persistence.get_postgres_count("entities") == 7


def test_fetch_postgres_sync_data_uses_fetch_not_fetch_all(monkeypatch):
    """Sync reads must use PostgresAgent.fetch() dict rows contract."""

    class FakePG:
        def fetch(self, sql):
            assert "SELECT id, embedded FROM entities" in sql
            return [
                {"id": "id_1", "embedded": True},
                {"id": "id_2", "embedded": True},
            ]

        def fetch_all(self, _sql):
            raise AssertionError("fetch_all() must not be called")

    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.PostgresAgent",
        lambda: FakePG(),
    )
    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.QdrantAgent",
        lambda: _FakeQdrant(),
    )

    persistence = MemoryPersistence()
    rows = persistence.fetch_postgres_sync_data("entities", limit=100)

    assert rows == (
        {"id": "id_1", "embedded": True},
        {"id": "id_2", "embedded": True},
    )


def test_check_postgres_health_handles_dict_rows(monkeypatch):
    """Health check should support dict scalar extraction for all scalar queries."""

    class FakePG:
        def fetch_one(self, sql):
            if sql == "SELECT 1;":
                return {"?column?": 1}
            if sql == "SELECT COUNT(*) FROM entities;":
                return {"count": 42}
            if sql == "SELECT COUNT(*) FROM entities WHERE embedded = true;":
                return {"count": 40}
            return None

    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.PostgresAgent",
        lambda: FakePG(),
    )
    monkeypatch.setattr(
        "api_memory_orders.adapters.persistence.QdrantAgent",
        lambda: _FakeQdrant(),
    )

    persistence = MemoryPersistence()
    health = persistence.check_postgres_health()

    assert health.status == "healthy"
    assert dict(health.metrics) == {"entities_total": 42, "entities_embedded": 40}
