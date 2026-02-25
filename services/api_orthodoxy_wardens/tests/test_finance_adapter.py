"""Tests for finance adapter in Orthodoxy Wardens service."""

from __future__ import annotations

import sys
from pathlib import Path


SERVICES_DIR = Path(__file__).resolve().parents[2]
CORE_DIR = Path(__file__).resolve().parents[3] / "vitruvyan_core"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from api_orthodoxy_wardens.adapters.finance_adapter import (  # noqa: E402
    get_finance_adapter,
    is_finance_enabled,
)
from api_orthodoxy_wardens.config import settings  # noqa: E402


def test_is_finance_enabled_switch(monkeypatch):
    monkeypatch.setattr(settings, "ORTHODOXY_DOMAIN", "generic")
    assert is_finance_enabled() is False

    monkeypatch.setattr(settings, "ORTHODOXY_DOMAIN", "finance")
    assert is_finance_enabled() is True


def test_get_finance_adapter_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ORTHODOXY_DOMAIN", "generic")
    monkeypatch.setattr(
        "api_orthodoxy_wardens.adapters.finance_adapter._finance_adapter",
        None,
    )
    assert get_finance_adapter() is None


def test_finance_ruleset_includes_domain_compliance_rules(monkeypatch):
    monkeypatch.setattr(settings, "ORTHODOXY_DOMAIN", "finance")
    monkeypatch.setattr(
        "api_orthodoxy_wardens.adapters.finance_adapter._finance_adapter",
        None,
    )

    adapter = get_finance_adapter()
    assert adapter is not None

    ruleset = adapter.build_ruleset(force_refresh=True)
    compliance_rules = [rule for rule in ruleset.active_rules if rule.category == "compliance"]

    assert ruleset.rule_count > 21
    assert len(compliance_rules) > 0
    assert any(rule.rule_id.startswith("compliance.") for rule in compliance_rules)


def test_finance_build_event_defaults(monkeypatch):
    monkeypatch.setattr(settings, "ORTHODOXY_DOMAIN", "finance")
    monkeypatch.setattr(
        "api_orthodoxy_wardens.adapters.finance_adapter._finance_adapter",
        None,
    )
    adapter = get_finance_adapter()
    assert adapter is not None

    event = adapter.build_event(text="Portfolio outlook")
    assert event["text"] == "Portfolio outlook"
    assert event["trigger_type"] == "output_validation"
    assert event["scope"] == "single_output"
    assert event["source"] == "orthodoxy.finance"
