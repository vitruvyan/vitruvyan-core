"""Tests for finance memory_orders configuration helpers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
CORE_DIR = ROOT_DIR / "vitruvyan_core"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from domains.finance.memory_orders.finance_config import (
    FinanceMemoryConfig,
    get_finance_default_sources,
    get_finance_source_candidates,
    get_finance_thresholds,
)


def test_default_sources_match_primary_config():
    cfg = FinanceMemoryConfig()
    defaults = get_finance_default_sources()

    assert defaults["table"] == cfg.primary_table
    assert defaults["collection"] == cfg.primary_collection


def test_source_candidates_include_vitruvyan_fallback():
    candidates = get_finance_source_candidates()

    assert candidates["tables"] == ("entities", "phrases")
    assert candidates["collections"] == ("entities_embeddings", "phrases_embeddings")


def test_source_candidates_keep_override_first():
    candidates = get_finance_source_candidates(
        table_override="custom_entities",
        collection_override="custom_vectors",
    )

    assert candidates["tables"][0] == "custom_entities"
    assert candidates["collections"][0] == "custom_vectors"
    assert "entities" in candidates["tables"]
    assert "phrases_embeddings" in candidates["collections"]


def test_finance_thresholds_are_ordered():
    healthy, warning = get_finance_thresholds()

    assert healthy == FinanceMemoryConfig().healthy_drift_threshold
    assert warning == FinanceMemoryConfig().warning_drift_threshold
    assert healthy < warning
