"""Tests for enterprise vault keepers configuration helpers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
CORE_DIR = ROOT_DIR / "vitruvyan_core"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from domains.enterprise.vault_keepers.enterprise_config import (  # noqa: E402
    EnterpriseVaultConfig,
    get_enterprise_retention_days,
    normalize_enterprise_archive_content_type,
    normalize_enterprise_source_order,
)


def test_config_immutable():
    cfg = EnterpriseVaultConfig()
    assert cfg.domain_name == "enterprise"
    assert cfg.archive_retention_days == 3650  # 10 years fiscal


def test_retention_days_default():
    assert get_enterprise_retention_days(signal=False) == 3650
    assert get_enterprise_retention_days(signal=True) == 1825


def test_retention_days_by_content_type():
    assert get_enterprise_retention_days(content_type="invoice_archive") == 3650
    assert get_enterprise_retention_days(content_type="agent_log") == 365
    assert get_enterprise_retention_days(content_type="partner_archive") == 1825


def test_archive_type_normalization_from_channel():
    normalized = normalize_enterprise_archive_content_type(
        content_type=None,
        channel="enterprise.invoice.archived",
    )
    assert normalized == "invoice_archive"


def test_archive_type_normalization_from_heuristics():
    assert normalize_enterprise_archive_content_type("fattura_2024") == "invoice_archive"
    assert normalize_enterprise_archive_content_type("customer_export") == "partner_archive"
    assert normalize_enterprise_archive_content_type("snapshot") == "system_state"
    assert normalize_enterprise_archive_content_type("compliance_check") == "audit_result"


def test_archive_type_empty():
    assert normalize_enterprise_archive_content_type("") == "generic"
    assert normalize_enterprise_archive_content_type(None) == "generic"


def test_source_order_normalization():
    assert normalize_enterprise_source_order("Memory") == "memory_orders"
    assert normalize_enterprise_source_order("odoo") == "enterprise"
    assert normalize_enterprise_source_order("Babel") == "babel_gardens"
    assert normalize_enterprise_source_order(None) == "enterprise"
