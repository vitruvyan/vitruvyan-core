"""
DSE Compute Engine — Core Algorithm
=====================================

PURE FUNCTION: run_dse(design_points, policy_set, normalization_profile, run_context)

Pipeline:
  1. Validate inputs
  2. Simulate KPIs (placeholder — production: call Neural Engine API)
  3. Normalize KPIs to [0,1]
  4. Compute Pareto frontier
  5. Compute dottrinale ranking (doctrine-weighted scoring)
  6. Compute audit hash
  7. Return RunArtifact

INVARIANTS:
  - Deterministic: same inputs + seed → same RunArtifact.
  - Stateless: no DB, no events, no external state access.
  - Side-effect free: only CPU computation.

Ported from aegis/services/core/api_aegis_dse/dse_engine/core.py
Refactored: Feb 26, 2026 — vitruvyan-core SACRED_ORDER_PATTERN conformance

IMPORT RULE (LIVELLO 1): relative imports only.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Any, Dict, List

from ..domain.schemas import (
    DesignPoint,
    NormalizationProfile,
    OptimizationDirection,
    PolicySet,
    RunArtifact,
    RunContext,
    compute_input_hash,
)
from .pareto import compute_pareto_frontier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_dse(
    design_points: List[DesignPoint],
    policy_set: PolicySet,
    normalization_profile: NormalizationProfile,
    run_context: RunContext,
    seed: int = 42,
) -> RunArtifact:
    """
    Execute Design Space Exploration.

    Args:
        design_points: Knob-parametrized configurations.
        policy_set: Doctrine weights and optimization objective.
        normalization_profile: KPI min/max/direction configs.
        run_context: Audit metadata (user_id, trace_id, use_case).
        seed: Reproducibility seed.

    Returns:
        RunArtifact with pareto_frontier, ranking_dottrinale, audit hash.

    Raises:
        ValueError: if design_points empty or kpi_configs empty.
    """
    np.random.seed(seed)

    logger.info(
        "run_dse: %d design_points, policy=%s, seed=%d",
        len(design_points), policy_set.policy_name, seed,
    )

    # Step 1 — Validate
    if not design_points:
        raise ValueError("design_points cannot be empty")
    if not normalization_profile.kpi_configs:
        raise ValueError("normalization_profile.kpi_configs cannot be empty")

    # Step 2 — Simulate KPIs  (placeholder; production: call Neural Engine)
    enriched = [_simulate_kpis(dp, normalization_profile) for dp in design_points]

    # Step 3 — Normalize KPIs to [0,1]
    normalized = [_normalize_kpis(row, normalization_profile) for row in enriched]

    # Step 4 — Pareto frontier
    kpi_names = [k.kpi_name for k in normalization_profile.kpi_configs]
    directions: Dict[str, OptimizationDirection] = {
        k.kpi_name: k.direction for k in normalization_profile.kpi_configs
    }
    pareto_frontier = compute_pareto_frontier(normalized, kpi_names, directions)

    # Step 5 — Dottrinale ranking
    ranking = _compute_dottrinale_ranking(
        normalized, pareto_frontier, policy_set, normalization_profile
    )

    # Step 6 — Audit hash
    input_hash = compute_input_hash(design_points, policy_set, normalization_profile)

    # Step 7 — Build artifact
    artifact = RunArtifact(
        run_context=run_context,
        policy_set=policy_set,
        normalization_profile=normalization_profile,
        pareto_frontier=pareto_frontier,
        ranking_dottrinale=ranking,
        input_hash=input_hash,
        seed=seed,
        schema_version="1.0.0",
        asof=datetime.utcnow(),
        total_design_points=len(design_points),
        pareto_count=len(pareto_frontier),
    )

    logger.info(
        "run_dse complete: pareto=%d/%d, hash=%s…",
        artifact.pareto_count, artifact.total_design_points,
        artifact.input_hash[:12],
    )
    return artifact


# ---------------------------------------------------------------------------
# Internal helpers (private — not exported)
# ---------------------------------------------------------------------------

def _simulate_kpis(
    design_point: DesignPoint,
    profile: NormalizationProfile,
) -> Dict[str, Any]:
    """
    Simulate raw KPI values from knob parameters.

    PLACEHOLDER: production integrations should call the Neural Engine API
    or an explainability provider and replace this function.

    Current heuristic: deterministic score derived from knob hash
    so that the same DesignPoint always yields the same simulated KPIs.
    """
    knob_sum = sum(
        float(v) if isinstance(v, (int, float)) else len(str(v))
        for v in design_point.knobs.values()
    )
    rng = np.random.default_rng(seed=int(abs(knob_sum * 1000)) % (2**31))

    kpis: Dict[str, float] = {}
    for kpi_cfg in profile.kpi_configs:
        raw = rng.uniform(kpi_cfg.min_value, kpi_cfg.max_value)
        kpis[kpi_cfg.kpi_name] = float(raw)

    dp_dict = {
        "design_id": design_point.design_id,
        "knobs": dict(design_point.knobs),
        "tags": dict(design_point.tags),
        "constraints": dict(design_point.constraints),
        "kpis": kpis,
    }
    return dp_dict


def _normalize_kpis(
    dp_dict: Dict[str, Any],
    profile: NormalizationProfile,
) -> Dict[str, Any]:
    """
    Normalize raw KPI values to [0,1].

    For MAXIMIZE: normalized = (raw − min) / (max − min)
    For MINIMIZE: normalized = 1 − (raw − min) / (max − min)
      so that higher normalized always means "better" (allows uniform Pareto logic).
    """
    raw_kpis: Dict[str, float] = dp_dict.get("kpis", {})
    normalized: Dict[str, float] = {}

    for kpi_cfg in profile.kpi_configs:
        raw = raw_kpis.get(kpi_cfg.kpi_name, kpi_cfg.min_value)
        span = kpi_cfg.max_value - kpi_cfg.min_value
        if span == 0:
            norm = 0.0
        else:
            norm = (raw - kpi_cfg.min_value) / span
            norm = max(0.0, min(1.0, norm))

        if kpi_cfg.direction == OptimizationDirection.MINIMIZE:
            norm = 1.0 - norm  # invert so that higher = better

        normalized[kpi_cfg.kpi_name] = norm

    return {**dp_dict, "kpis_normalized": normalized}


def _compute_dottrinale_ranking(
    design_points: List[Dict[str, Any]],
    pareto_frontier: List[Dict[str, Any]],
    policy_set: PolicySet,
    profile: NormalizationProfile,
) -> List[Dict[str, Any]]:
    """
    Rank all design points by doctrine-weighted composite score.

    Score = Σ (doctrine_weight_i × kpi_normalized_i)

    Pareto-optimal points receive a +0.1 bonus (tie-breaker).
    """
    pareto_ids = {p["design_id"] for p in pareto_frontier}
    kpi_names = [k.kpi_name for k in profile.kpi_configs]
    weights = policy_set.doctrine_weights

    scored: List[Dict[str, Any]] = []
    for dp in design_points:
        kpis_n = dp.get("kpis_normalized", {})
        score = sum(
            weights.get(kpi, 1.0 / len(kpi_names)) * kpis_n.get(kpi, 0.0)
            for kpi in kpi_names
        )
        is_pareto = dp["design_id"] in pareto_ids
        if is_pareto:
            score += 0.1
        scored.append({**dp, "dottrinale_score": round(score, 6), "is_pareto": is_pareto})

    scored.sort(key=lambda x: x["dottrinale_score"], reverse=True)
    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank

    return scored
