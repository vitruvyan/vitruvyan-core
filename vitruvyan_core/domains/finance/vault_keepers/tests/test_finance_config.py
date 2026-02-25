"""Tests for finance vault keepers configuration helpers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
CORE_DIR = ROOT_DIR / "vitruvyan_core"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from domains.finance.vault_keepers.finance_config import (  # noqa: E402
    FinanceVaultConfig,
    get_finance_backup_defaults,
    get_finance_retention_days,
    normalize_finance_archive_content_type,
    normalize_finance_source_order,
)


def test_backup_defaults():
    defaults = get_finance_backup_defaults()
    assert defaults["mode"] == FinanceVaultConfig().default_backup_mode
    assert defaults["include_vectors"] is FinanceVaultConfig().default_include_vectors


def test_archive_type_normalization_from_channel():
    normalized = normalize_finance_archive_content_type(
        content_type="orthodoxy.audit.completed",
        channel="orthodoxy.audit.completed",
    )
    assert normalized == "audit_result"


def test_archive_type_normalization_from_heuristics():
    assert normalize_finance_archive_content_type("babel.sentiment.completed") == "eval_result"
    assert normalize_finance_archive_content_type("snapshot") == "system_state"
    assert normalize_finance_archive_content_type("whatever") == "audit_result"


def test_source_order_normalization():
    assert normalize_finance_source_order("Memory") == "memory_orders"
    assert normalize_finance_source_order("Babel") == "babel_gardens"


def test_retention_days():
    assert get_finance_retention_days(signal=False) == FinanceVaultConfig().archive_retention_days
    assert get_finance_retention_days(signal=True) == FinanceVaultConfig().signal_retention_days
