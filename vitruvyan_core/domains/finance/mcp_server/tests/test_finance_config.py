from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_MODULE_PATH = Path(__file__).resolve().parents[1] / "finance_config.py"
_SPEC = importlib.util.spec_from_file_location("finance_mcp_config_test_module", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

build_finance_phrase_samples = _MODULE.build_finance_phrase_samples
get_finance_signal_source_candidates = _MODULE.get_finance_signal_source_candidates
normalize_finance_args = _MODULE.normalize_finance_args
resolve_finance_tool_name = _MODULE.resolve_finance_tool_name


def test_resolve_finance_tool_aliases():
    assert resolve_finance_tool_name("screen_tickers") == "screen_entities"
    assert resolve_finance_tool_name("compare_tickers") == "compare_entities"
    assert resolve_finance_tool_name("query_sentiment") == "query_signals"
    assert resolve_finance_tool_name("unknown_tool") == "unknown_tool"


def test_normalize_screen_tickers_to_entities():
    args = normalize_finance_args(
        "screen_tickers",
        {"tickers": ["AAPL", "NVDA"], "profile": "balanced_mid", "horizon": "short"},
    )
    assert args["entity_ids"] == ["AAPL", "NVDA"]
    assert args["profile"] == "balanced"
    assert "horizon" not in args


def test_normalize_query_sentiment_to_query_signals():
    args = normalize_finance_args(
        "query_sentiment",
        {"ticker": "TSLA", "days": 90, "include_phrases": True},
    )
    assert args["entity_id"] == "TSLA"
    assert args["time_window"] == 30
    assert args["include_context"] is True


def test_signal_source_candidates_include_primary_and_legacy():
    candidates = get_finance_signal_source_candidates()
    assert candidates["tables"][0] == "sentiment_scores"
    assert "entity_signals" in candidates["tables"]
    assert candidates["entity_columns"][0] == "ticker"
    assert "entity_id" in candidates["entity_columns"]


def test_phrase_samples_limit():
    samples = build_finance_phrase_samples("AAPL", limit=2)
    assert len(samples) == 2
    assert "AAPL" in samples[0]
