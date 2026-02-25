from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


SERVICES_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))

from api_codex_hunters.adapters.bus_adapter import BusAdapter
from api_codex_hunters.adapters.persistence import PersistenceAdapter


def test_get_default_source_prefers_db_default_flag() -> None:
    adapter = PersistenceAdapter.__new__(PersistenceAdapter)
    adapter._config = SimpleNamespace(
        source_registry=SimpleNamespace(default_source_key=None)
    )
    adapter.list_source_registry = lambda: [
        {"source_key": "yfinance", "is_default": False},
        {"source_key": "primary", "is_default": True},
    ]

    assert adapter.get_default_source_key() == "primary"


def test_get_default_source_prefers_explicit_preferred() -> None:
    adapter = PersistenceAdapter.__new__(PersistenceAdapter)
    adapter._config = SimpleNamespace(
        source_registry=SimpleNamespace(default_source_key=None)
    )
    adapter.list_source_registry = lambda: [
        {"source_key": "primary", "is_default": True},
        {"source_key": "reddit", "is_default": False},
    ]

    assert adapter.get_default_source_key(preferred="reddit") == "reddit"


def test_bus_adapter_resolves_default_and_rejects_unknown_source() -> None:
    adapter = BusAdapter.__new__(BusAdapter)
    adapter._known_sources = {"primary": {}, "reddit": {}}
    adapter._default_source = "primary"
    adapter._persistence = SimpleNamespace(get_default_source_key=lambda: "primary")
    adapter._refresh_sources_from_registry = lambda force=False: None

    assert adapter.resolve_source(None) == "primary"
    assert adapter.resolve_source("reddit") == "reddit"
    with pytest.raises(ValueError):
        adapter.resolve_source("unknown")
