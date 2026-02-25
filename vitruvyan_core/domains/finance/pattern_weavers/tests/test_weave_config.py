"""Tests for finance weave configuration."""

import pytest

from domains.finance.pattern_weavers.weave_config import (
    FinanceWeaveConfig,
    get_category_boost,
    get_finance_threshold,
)


def test_default_thresholds():
    cfg = FinanceWeaveConfig()
    assert cfg.base_similarity_threshold < cfg.finance_similarity_threshold


def test_finance_threshold_switch():
    assert get_finance_threshold(True) == FinanceWeaveConfig().finance_similarity_threshold
    assert get_finance_threshold(False) == FinanceWeaveConfig().base_similarity_threshold


def test_boost_only_when_financial():
    boosted = get_category_boost("sectors", True)
    neutral = get_category_boost("sectors", False)
    assert boosted > 1.0
    assert neutral == 1.0


def test_unknown_category_boost():
    assert get_category_boost("unknown", True) == pytest.approx(1.0)
