"""Tests for finance adapter in Memory Orders service."""

from __future__ import annotations

import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_memory_orders.adapters.finance_adapter import (  # noqa: E402
    FinanceAdapter,
    get_finance_adapter,
    is_finance_enabled,
)
from api_memory_orders.config import settings  # noqa: E402


class _FakePG:
    def __init__(self, existing_tables):
        self._existing_tables = set(existing_tables)

    def fetch_one(self, _sql, params=None):
        table_name = params[0] if params else ""
        return {"exists": table_name in self._existing_tables}


class _FakeCollection:
    def __init__(self, name: str):
        self.name = name


class _FakeCollectionsResponse:
    def __init__(self, names):
        self.collections = [_FakeCollection(name) for name in names]


class _FakeQdrantClient:
    def __init__(self, existing_collections):
        self._existing_collections = tuple(existing_collections)

    def get_collections(self):
        return _FakeCollectionsResponse(self._existing_collections)


class _FakePersistence:
    def __init__(self, existing_tables, existing_collections):
        self.pg = _FakePG(existing_tables)
        self.qdrant = type("Qdrant", (), {"client": _FakeQdrantClient(existing_collections)})()


def test_is_finance_enabled_switch(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_DOMAIN", "generic")
    assert is_finance_enabled() is False

    monkeypatch.setattr(settings, "MEMORY_DOMAIN", "finance")
    assert is_finance_enabled() is True


def test_get_finance_adapter_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "MEMORY_DOMAIN", "generic")
    monkeypatch.setattr("api_memory_orders.adapters.finance_adapter._finance_adapter", None)

    assert get_finance_adapter() is None


def test_resolve_sources_prefers_mercator_defaults():
    persistence = _FakePersistence(
        existing_tables=("entities",),
        existing_collections=("entity_embeddings",),
    )
    adapter = FinanceAdapter()

    resolved = adapter.resolve_sources(persistence)

    assert resolved["table"] == "entities"
    assert resolved["collection"] == "entity_embeddings"
    assert resolved["resolved_table_from_db"] is True
    assert resolved["resolved_collection_from_qdrant"] is True


def test_resolve_sources_falls_back_to_vitruvyan_sources():
    persistence = _FakePersistence(
        existing_tables=("phrases",),
        existing_collections=("phrases_embeddings",),
    )
    adapter = FinanceAdapter()

    resolved = adapter.resolve_sources(persistence)

    assert resolved["table"] == "phrases"
    assert resolved["collection"] == "phrases_embeddings"
    assert resolved["resolved_table_from_db"] is True
    assert resolved["resolved_collection_from_qdrant"] is True


def test_resolve_sources_without_probe_uses_override_head():
    persistence = _FakePersistence(existing_tables=(), existing_collections=())
    adapter = FinanceAdapter()

    resolved = adapter.resolve_sources(
        persistence=persistence,
        table="manual_table",
        collection="manual_collection",
        probe_backends=False,
    )

    assert resolved["table"] == "manual_table"
    assert resolved["collection"] == "manual_collection"
    assert resolved["resolved_table_from_db"] is False
    assert resolved["resolved_collection_from_qdrant"] is False
