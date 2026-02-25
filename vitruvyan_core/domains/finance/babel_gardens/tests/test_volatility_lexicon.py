"""Tests for volatility perception signal extraction."""

import pytest

from core.cognitive.babel_gardens.domain import SignalSchema
from domains.finance.babel_gardens.volatility_lexicon import (
    VOLATILITY_LEXICON,
    extract_volatility_perception,
)

SCHEMA = SignalSchema(
    name="volatility_perception",
    value_range=(0.0, 1.0),
    aggregation_method="mean",
    fusion_weight=0.5,
    extraction_method="heuristic:lexicon",
)


def test_high_volatility_text():
    result = extract_volatility_perception("Market crash and panic selling", SCHEMA)
    assert result.signal_name == "volatility_perception"
    assert result.value > 0.8
    assert result.confidence > 0.3


def test_no_volatility_text():
    result = extract_volatility_perception("The weather is sunny today", SCHEMA)
    assert result.value == 0.0
    assert result.confidence < 0.2


def test_moderate_volatility():
    result = extract_volatility_perception("Some market volatility expected", SCHEMA)
    assert 0.3 < result.value < 1.0


def test_italian_volatility():
    result = extract_volatility_perception("Crollo in borsa e panico tra gli investitori", SCHEMA)
    assert result.value > 0.8


def test_value_in_range():
    result = extract_volatility_perception("flash crash meltdown", SCHEMA)
    assert 0.0 <= result.value <= 1.0


def test_extraction_trace():
    result = extract_volatility_perception("Market volatility rising", SCHEMA)
    assert "method" in result.extraction_trace
    assert result.extraction_trace["method"] == "heuristic:lexicon"
    assert "timestamp" in result.extraction_trace


def test_wrong_schema_name():
    wrong_schema = SignalSchema(
        name="wrong_name",
        value_range=(0.0, 1.0),
        aggregation_method="mean",
    )
    with pytest.raises(ValueError):
        extract_volatility_perception("test", wrong_schema)


def test_lexicon_not_empty():
    assert len(VOLATILITY_LEXICON) > 0
