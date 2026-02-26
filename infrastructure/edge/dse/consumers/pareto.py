"""
Pareto Frontier Algorithms — Non-Dominated Point Detection
===========================================================

PURE FUNCTIONS for multi-objective optimization.
Zero I/O. Zero state. O(n²) dominance comparison.

Concepts:
- Dominance: Point A dominates B if A is better-or-equal in ALL
  objectives and strictly better in AT LEAST ONE.
- Pareto Frontier: the set of all non-dominated points.
- Pareto Rank: 0 = frontier, 1 = first dominated layer, ...

Ported from aegis/services/core/api_aegis_dse/dse_engine/pareto.py
Refactored: Feb 26, 2026 — vitruvyan-core SACRED_ORDER_PATTERN conformance

IMPORT RULE (LIVELLO 1): relative imports only.
"""

import logging
from typing import Any, Dict, List

from ..domain.schemas import OptimizationDirection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core: Pareto Frontier
# ---------------------------------------------------------------------------

def compute_pareto_frontier(
    design_points: List[Dict[str, Any]],
    kpi_names: List[str],
    directions: Dict[str, OptimizationDirection],
) -> List[Dict[str, Any]]:
    """
    Compute the Pareto frontier from normalized design points.

    Args:
        design_points: Each dict must contain "kpis_normalized" (all ∈ [0,1]).
        kpi_names: KPI identifiers to consider.
        directions: {kpi_name: MAXIMIZE | MINIMIZE}

    Returns:
        Subset of input that forms the Pareto frontier.

    Example:
        Point A: {compliance: 0.9, cost: 0.8}  # high compliance, low raw cost → normalized high
        Point B: {compliance: 0.7, cost: 0.5}
        → A dominates B → frontier = [A]
    """
    if not design_points:
        return []

    logger.debug(
        "Pareto: evaluating %d points across %d KPIs",
        len(design_points), len(kpi_names),
    )

    pareto: List[Dict[str, Any]] = []
    for i, point_a in enumerate(design_points):
        dominated = any(
            dominates(point_b, point_a, kpi_names, directions)
            for j, point_b in enumerate(design_points)
            if i != j
        )
        if not dominated:
            pareto.append(point_a)

    logger.info(
        "Pareto: %d/%d points on frontier",
        len(pareto), len(design_points),
    )
    return pareto


# ---------------------------------------------------------------------------
# Helper: Dominance check
# ---------------------------------------------------------------------------

def dominates(
    point_a: Dict[str, Any],
    point_b: Dict[str, Any],
    kpi_names: List[str],
    directions: Dict[str, OptimizationDirection],
) -> bool:
    """
    Return True if point_a dominates point_b.

    Dominance conditions (all in normalized [0,1] space):
    1. For every KPI: value_a >= value_b  (both maximize and minimize,
       because minimize KPIs are inverted during normalization so higher = better).
    2. For at least one KPI: value_a > value_b (strictly better).
    """
    kpis_a = point_a.get("kpis_normalized", {})
    kpis_b = point_b.get("kpis_normalized", {})

    all_gte = True
    any_gt = False

    for kpi in kpi_names:
        va = kpis_a.get(kpi, 0.0)
        vb = kpis_b.get(kpi, 0.0)

        if va < vb:
            all_gte = False
            break
        if va > vb:
            any_gt = True

    return all_gte and any_gt


# ---------------------------------------------------------------------------
# Extended: Pareto Rank
# ---------------------------------------------------------------------------

def compute_pareto_rank(
    design_points: List[Dict[str, Any]],
    kpi_names: List[str],
    directions: Dict[str, OptimizationDirection],
) -> List[Dict[str, Any]]:
    """
    Assign a Pareto rank to each design point.

    Rank 0 = Pareto frontier.
    Rank 1 = frontier after removing rank-0 points.
    ... and so on (iterated Pareto peeling).

    Mutates a copy — original dicts are not modified.
    """
    remaining = list(design_points)
    ranked: List[Dict[str, Any]] = []
    current_rank = 0

    while remaining:
        frontier = compute_pareto_frontier(remaining, kpi_names, directions)
        frontier_ids = {id(p) for p in frontier}

        for point in remaining:
            if id(point) in frontier_ids:
                ranked.append({**point, "pareto_rank": current_rank})

        remaining = [p for p in remaining if id(p) not in frontier_ids]
        current_rank += 1

    logger.info("Pareto ranks assigned: max_rank=%d", current_rank - 1)
    return ranked
