"""
Unit Tests — DSE Pareto Frontier
Pure pytest, no Docker, no external services.
"""

import pytest
from infrastructure.edge.dse.consumers.pareto import (
    compute_pareto_frontier,
    dominates,
    compute_pareto_rank,
)
from infrastructure.edge.dse.domain.schemas import OptimizationDirection

MAX = OptimizationDirection.MAXIMIZE
MIN = OptimizationDirection.MINIMIZE


def _point(design_id: int, **kpis) -> dict:
    return {"design_id": design_id, "kpis_normalized": kpis}


class TestDominates:
    KPI_NAMES = ["compliance", "cost"]
    DIRS = {"compliance": MAX, "cost": MAX}  # both inverted → higher = better

    def test_a_dominates_b_strictly_better_in_all(self):
        a = _point(1, compliance=0.9, cost=0.8)
        b = _point(2, compliance=0.7, cost=0.5)
        assert dominates(a, b, self.KPI_NAMES, self.DIRS) is True

    def test_b_does_not_dominate_a(self):
        a = _point(1, compliance=0.9, cost=0.8)
        b = _point(2, compliance=0.7, cost=0.5)
        assert dominates(b, a, self.KPI_NAMES, self.DIRS) is False

    def test_equal_no_dominance(self):
        a = _point(1, compliance=0.7, cost=0.7)
        b = _point(2, compliance=0.7, cost=0.7)
        assert dominates(a, b, self.KPI_NAMES, self.DIRS) is False

    def test_tradeoff_no_dominance(self):
        """A better in compliance, B better in cost — neither dominates."""
        a = _point(1, compliance=0.9, cost=0.3)
        b = _point(2, compliance=0.3, cost=0.9)
        assert dominates(a, b, self.KPI_NAMES, self.DIRS) is False
        assert dominates(b, a, self.KPI_NAMES, self.DIRS) is False


class TestComputeParetoFrontier:
    KPI_NAMES = ["q", "p"]
    DIRS = {"q": MAX, "p": MAX}

    def test_single_point_is_pareto(self):
        pts = [_point(1, q=0.5, p=0.5)]
        frontier = compute_pareto_frontier(pts, self.KPI_NAMES, self.DIRS)
        assert len(frontier) == 1

    def test_dominated_point_excluded(self):
        pts = [
            _point(1, q=0.9, p=0.9),  # dominates all below
            _point(2, q=0.5, p=0.5),
            _point(3, q=0.3, p=0.3),
        ]
        frontier = compute_pareto_frontier(pts, self.KPI_NAMES, self.DIRS)
        assert len(frontier) == 1
        assert frontier[0]["design_id"] == 1

    def test_tradeoff_both_on_frontier(self):
        """Classic tradeoff: neither dominates the other."""
        pts = [
            _point(1, q=0.9, p=0.2),
            _point(2, q=0.2, p=0.9),
        ]
        frontier = compute_pareto_frontier(pts, self.KPI_NAMES, self.DIRS)
        assert len(frontier) == 2

    def test_empty_returns_empty(self):
        assert compute_pareto_frontier([], self.KPI_NAMES, self.DIRS) == []

    def test_all_equal_all_on_frontier(self):
        pts = [_point(i, q=0.5, p=0.5) for i in range(5)]
        frontier = compute_pareto_frontier(pts, self.KPI_NAMES, self.DIRS)
        assert len(frontier) == 5


class TestParetoRank:
    KPI_NAMES = ["s"]
    DIRS = {"s": MAX}

    def test_rank_order(self):
        pts = [
            _point(1, s=0.9),
            _point(2, s=0.6),
            _point(3, s=0.3),
        ]
        ranked = compute_pareto_rank(pts, self.KPI_NAMES, self.DIRS)
        by_id = {r["design_id"]: r["pareto_rank"] for r in ranked}
        assert by_id[1] == 0
        assert by_id[2] == 1
        assert by_id[3] == 2
