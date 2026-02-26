"""
DSE Sampling Strategy Selector — Pure Decision Logic
======================================================

Determines the optimal sampling strategy based on:
1. Number of dimensions detected in the Pattern context.
2. ML-historical best performer (via injected DB query result).
3. Heuristic fallback (dimension count thresholds).

PATTERN (LIVELLO 1): stateless classifier.
- Input: context dict + optional historical record.
- Output: strategy name + reason string + confidence float.

No I/O. No DB access. Dependencies injected as plain dicts.

Last updated: Feb 26, 2026
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from ..consumers.sampling import count_dimensions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy identifiers (canonical names)
# ---------------------------------------------------------------------------

STRATEGY_LHS = "lhs"
STRATEGY_CARTESIAN = "cartesian"
STRATEGY_SOBOL = "sobol"

# Thresholds
_SMALL_SPACE_THRESHOLD = 5    # dimensions < 5  → cartesian
_MEDIUM_SPACE_THRESHOLD = 15  # 5 ≤ dims ≤ 15  → lhs


class SamplingStrategySelector:
    """
    Pure strategy selector.

    Inputs are provided as plain Python values — no infrastructure.

    Usage:
        selector = SamplingStrategySelector()
        strategy, reason, conf = selector.decide(context)
    """

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def decide(
        self,
        pattern_context: Dict[str, Any],
        ml_record: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, float]:
        """
        Decide sampling strategy.

        Args:
            pattern_context: Pattern Weavers output — {dim_name: [values], ...}
            ml_record: Optional historical DB result with keys:
                - "sampling_plan": str (e.g. "MC_uniform_v1")
                - "avg_score": float
                - "sample_count": int
                Injected by LIVELLO 2 adapter; never fetched here.

        Returns:
            (strategy, reason, confidence)
        """
        # 1. ML-historical path
        if ml_record:
            return self._from_ml_record(ml_record, pattern_context)

        # 2. Heuristic fallback
        num_dims = count_dimensions(pattern_context)
        return self._heuristic(num_dims)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _from_ml_record(
        self,
        record: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Tuple[str, str, float]:
        """Map a historical best-strategy DB record to canonical names."""
        plan: str = record.get("sampling_plan", "")
        avg_score: float = float(record.get("avg_score", 0.0))
        sample_count: int = int(record.get("sample_count", 0))
        confidence = min(sample_count / 1000.0, 1.0)

        if "Sobol" in plan:
            strategy = STRATEGY_SOBOL
        elif "LHS" in plan or "MC" in plan or "uniform" in plan:
            strategy = STRATEGY_LHS
        else:
            strategy = STRATEGY_CARTESIAN

        logger.info(
            "Strategy (ML): %s from plan=%s score=%.3f n=%d conf=%.2f",
            strategy, plan, avg_score, sample_count, confidence,
        )
        # Low-confidence ML → blend with heuristic hint
        if confidence < 0.3:
            h_strategy, h_reason, _ = self._heuristic(count_dimensions(context))
            if h_strategy != strategy:
                logger.info(
                    "Strategy: low-confidence ML (%s) overridden by heuristic (%s)",
                    strategy, h_strategy,
                )
                return h_strategy, f"heuristic_override_low_conf_{plan}", 0.5

        return strategy, f"ml_historical_best_{plan}", confidence

    def _heuristic(self, num_dims: int) -> Tuple[str, str, float]:
        """Deterministic dimension-count heuristic."""
        if num_dims == 0:
            return STRATEGY_CARTESIAN, "heuristic_empty_context", 0.5
        if num_dims < _SMALL_SPACE_THRESHOLD:
            return STRATEGY_CARTESIAN, "heuristic_small_space", 0.7
        if num_dims <= _MEDIUM_SPACE_THRESHOLD:
            return STRATEGY_LHS, "heuristic_medium_space", 0.8
        return STRATEGY_LHS, "heuristic_large_space", 0.8
