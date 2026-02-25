"""Tests for finance sentiment configuration."""

import pytest

from domains.finance.babel_gardens.sentiment_config import (
    FinanceSentimentConfig,
    get_finance_fusion_weights,
    get_finance_model_boost,
)


def test_default_weights_sum_to_one():
    config = FinanceSentimentConfig()
    total = sum(config.fusion_weights.values())
    assert abs(total - 1.0) < 0.001


def test_get_finance_fusion_weights():
    weights = get_finance_fusion_weights()
    assert "llm" in weights
    assert "finbert" in weights
    assert "multilingual" in weights
    assert abs(sum(weights.values()) - 1.0) < 0.001


def test_model_boost_non_english():
    weights = get_finance_model_boost(language="it", is_financial=False)
    default = get_finance_fusion_weights()
    assert weights["multilingual"] > default["multilingual"]


def test_model_boost_financial_content():
    weights = get_finance_model_boost(language="en", is_financial=True)
    default = get_finance_fusion_weights()
    assert weights["finbert"] > default["finbert"]


def test_model_boost_both():
    weights = get_finance_model_boost(language="it", is_financial=True)
    assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)


def test_model_boost_english_non_financial():
    weights = get_finance_model_boost(language="en", is_financial=False)
    default = get_finance_fusion_weights()
    assert weights == default
