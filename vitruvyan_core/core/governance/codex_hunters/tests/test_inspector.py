"""
Unit tests for InspectorConsumer.

Pure domain tests — no Docker, no Redis, no PostgreSQL, no Qdrant.
"""

import pytest

from vitruvyan_core.core.governance.codex_hunters.consumers.inspector import (
    InspectorConsumer,
    DEFAULT_THRESHOLDS,
)
from vitruvyan_core.core.governance.codex_hunters.domain.entities import (
    ConsistencyStatus,
)


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def inspector():
    return InspectorConsumer()


def _make_input(*collections):
    """Convenience: wrap collection dicts in the expected envelope."""
    return {"collections": list(collections)}


def _coll(name, a, b, *, a_ids=None, b_ids=None):
    d = {"collection_name": name, "source_a_count": a, "source_b_count": b}
    if a_ids is not None:
        d["source_a_ids"] = a_ids
    if b_ids is not None:
        d["source_b_ids"] = b_ids
    return d


# ── Validation ───────────────────────────────────────────────────────────

class TestValidation:
    def test_missing_collections_key(self, inspector):
        result = inspector.process({})
        assert not result.success
        assert any("collections" in e for e in result.errors)

    def test_collections_not_list(self, inspector):
        result = inspector.process({"collections": "bad"})
        assert not result.success

    def test_empty_collections(self, inspector):
        result = inspector.process({"collections": []})
        assert not result.success

    def test_missing_collection_name(self, inspector):
        result = inspector.process(_make_input({"source_a_count": 1, "source_b_count": 1}))
        assert not result.success
        assert any("collection_name" in e for e in result.errors)


# ── Scoring ──────────────────────────────────────────────────────────────

class TestScoring:
    def test_perfect_consistency(self, inspector):
        result = inspector.process(_make_input(_coll("x", 100, 100)))
        assert result.success
        report = result.data["report"]
        assert report.overall_score == 1.0
        assert report.overall_status == ConsistencyStatus.EXCELLENT

    def test_both_zero_is_empty(self, inspector):
        result = inspector.process(_make_input(_coll("x", 0, 0)))
        assert result.success
        report = result.data["report"]
        assert report.overall_score == 1.0
        assert report.overall_status == ConsistencyStatus.EMPTY

    def test_ratio_score(self, inspector):
        result = inspector.process(_make_input(_coll("x", 80, 100)))
        assert result.success
        report = result.data["report"]
        assert abs(report.overall_score - 0.80) < 1e-6

    def test_critical_score(self, inspector):
        result = inspector.process(_make_input(_coll("x", 40, 100)))
        assert result.success
        report = result.data["report"]
        assert report.overall_score < DEFAULT_THRESHOLDS["critical"]
        assert report.needs_healing is True

    def test_weighted_average(self, inspector):
        """Larger collections weigh more in overall score."""
        result = inspector.process(
            _make_input(
                _coll("big", 1000, 1000),   # score 1.0, weight 1000
                _coll("small", 10, 5),       # score 0.5, weight 10
            )
        )
        assert result.success
        report = result.data["report"]
        # Weighted: (1.0*1000 + 0.5*10) / (1000+10) ≈ 0.995
        assert report.overall_score > 0.99


# ── Orphan Detection ─────────────────────────────────────────────────────

class TestOrphans:
    def test_orphans_detected(self, inspector):
        result = inspector.process(
            _make_input(
                _coll(
                    "x", 3, 3,
                    a_ids=["a", "b", "c"],
                    b_ids=["b", "c", "d"],
                )
            )
        )
        assert result.success
        cc = result.data["report"].collections[0]
        assert "a" in cc.orphans_a      # in A but not B
        assert "d" in cc.orphans_b      # in B but not A
        assert "b" not in cc.orphans_a  # shared

    def test_no_orphans_when_no_ids(self, inspector):
        result = inspector.process(_make_input(_coll("x", 100, 95)))
        assert result.success
        cc = result.data["report"].collections[0]
        assert cc.orphans_a == []
        assert cc.orphans_b == []


# ── Recommendations ──────────────────────────────────────────────────────

class TestRecommendations:
    def test_excellent_recommendation(self, inspector):
        result = inspector.process(_make_input(_coll("x", 100, 100)))
        recs = result.data["report"].recommendations
        assert any("excellent" in r.lower() for r in recs)

    def test_critical_recommendation(self, inspector):
        result = inspector.process(_make_input(_coll("x", 30, 100)))
        recs = result.data["report"].recommendations
        assert any("critical" in r.lower() for r in recs)
        assert result.data["report"].needs_healing is True


# ── Custom Thresholds ────────────────────────────────────────────────────

class TestCustomThresholds:
    def test_strict_thresholds(self):
        strict = InspectorConsumer(thresholds={"excellent": 0.99, "good": 0.95, "poor": 0.90, "critical": 0.80})
        result = strict.process(_make_input(_coll("x", 95, 100)))
        report = result.data["report"]
        # 0.95 → with strict thresholds this is "good" not "excellent"
        assert report.overall_status == ConsistencyStatus.GOOD

    def test_custom_healing_threshold(self):
        lax = InspectorConsumer(healing_threshold=0.30)
        result = lax.process(_make_input(_coll("x", 40, 100)))
        report = result.data["report"]
        # score = 0.40, healing_threshold = 0.30 → no healing needed
        assert report.needs_healing is False


# ── Statistics ───────────────────────────────────────────────────────────

class TestStats:
    def test_stats_accumulate(self, inspector):
        inspector.process(_make_input(_coll("x", 100, 100)))
        inspector.process(_make_input(_coll("y", 50, 100)))
        stats = inspector.get_inspection_stats()
        assert stats["total_inspections"] == 2
        assert stats["process_count"] == 2
        assert stats["error_count"] == 0
        assert 0.0 < stats["average_consistency"] <= 1.0


# ── Serialization ────────────────────────────────────────────────────────

class TestSerialization:
    def test_report_dict(self, inspector):
        result = inspector.process(_make_input(_coll("x", 100, 95)))
        d = result.data["report_dict"]
        assert isinstance(d, dict)
        assert "overall_score" in d
        assert "collections" in d
        assert isinstance(d["collections"], list)
        assert d["collections"][0]["collection_name"] == "x"
