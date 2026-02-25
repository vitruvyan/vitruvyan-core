"""Tests for finance orthodoxy configuration."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
CORE_DIR = ROOT_DIR / "vitruvyan_core"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from domains.finance.orthodoxy_wardens.compliance_config import (  # noqa: E402
    FinanceOrthodoxyConfig,
    get_finance_event_defaults,
    get_finance_ruleset_version,
)


def test_finance_ruleset_version():
    assert get_finance_ruleset_version() == FinanceOrthodoxyConfig().ruleset_version


def test_finance_event_defaults():
    defaults = get_finance_event_defaults()

    assert defaults["trigger_type"] == FinanceOrthodoxyConfig().default_trigger_type
    assert defaults["scope"] == FinanceOrthodoxyConfig().default_scope
    assert defaults["source"] == FinanceOrthodoxyConfig().default_source


def test_finance_strict_mode_defaults():
    cfg = FinanceOrthodoxyConfig()

    assert cfg.strict_mode is True
    assert cfg.confidence_floor >= 0.7
