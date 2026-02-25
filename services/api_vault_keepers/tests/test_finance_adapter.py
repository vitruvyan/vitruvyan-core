"""Tests for finance adapter in Vault Keepers service."""

from __future__ import annotations

import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_vault_keepers.adapters.finance_adapter import (  # noqa: E402
    get_finance_adapter,
    is_finance_enabled,
)
from api_vault_keepers.config import settings  # noqa: E402


def test_is_finance_enabled_switch(monkeypatch):
    monkeypatch.setattr(settings, "VAULT_DOMAIN", "generic")
    assert is_finance_enabled() is False

    monkeypatch.setattr(settings, "VAULT_DOMAIN", "finance")
    assert is_finance_enabled() is True


def test_get_finance_adapter_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "VAULT_DOMAIN", "generic")
    monkeypatch.setattr("api_vault_keepers.adapters.finance_adapter._finance_adapter", None)
    assert get_finance_adapter() is None


def test_archive_normalization(monkeypatch):
    monkeypatch.setattr(settings, "VAULT_DOMAIN", "finance")
    monkeypatch.setattr("api_vault_keepers.adapters.finance_adapter._finance_adapter", None)

    adapter = get_finance_adapter()
    assert adapter is not None

    resolved = adapter.resolve_archive_request(
        content_type="orthodoxy.audit.completed",
        source_order="Orthodoxy",
        channel="orthodoxy.audit.completed",
    )
    assert resolved["content_type"] == "audit_result"
    assert resolved["source_order"] == "orthodoxy_wardens"


def test_backup_defaults(monkeypatch):
    monkeypatch.setattr(settings, "VAULT_DOMAIN", "finance")
    monkeypatch.setattr("api_vault_keepers.adapters.finance_adapter._finance_adapter", None)

    adapter = get_finance_adapter()
    assert adapter is not None

    resolved = adapter.resolve_backup_params(mode=None, include_vectors=None)
    assert resolved["mode"] in {"full", "incremental"}
    assert isinstance(resolved["include_vectors"], bool)
