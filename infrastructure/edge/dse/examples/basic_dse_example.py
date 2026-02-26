"""
Basic DSE Example — Pure Python, No Services Required
=======================================================

Demonstrates the full LIVELLO 1 pipeline:
  1. Build a context (simulating Pattern Weavers output)
  2. Generate design points with LHS sampling
  3. Run the DSE compute engine
  4. Inspect the Pareto frontier and dottrinale ranking

Run:
    python -m infrastructure.edge.dse.examples.basic_dse_example
"""

import sys
import os

# Adjust path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from infrastructure.edge.dse.domain.schemas import (
    DesignPoint,
    KPIConfig,
    NormalizationProfile,
    OptimizationDirection,
    PolicySet,
    RunContext,
)
from infrastructure.edge.dse.consumers.sampling import (
    latin_hypercube_sampling,
    cartesian_product_sampling,
)
from infrastructure.edge.dse.consumers.engine import run_dse
from infrastructure.edge.dse.governance.strategy import SamplingStrategySelector


def main() -> None:
    print("=" * 60)
    print("DSE LIVELLO 1 — Basic Example")
    print("=" * 60)

    # ----------------------------------------------------------------
    # 1. Pattern Weavers context (domain-agnostic example)
    # ----------------------------------------------------------------
    context = {
        "sector":       ["Banking", "Technology", "Healthcare", "Energy"],
        "region":       ["EU", "US", "APAC"],
        "risk_profile": ["conservative", "balanced", "growth"],
        "horizon":      ["short", "medium", "long"],
    }

    # ----------------------------------------------------------------
    # 2. Select sampling strategy (pure heuristic — no DB)
    # ----------------------------------------------------------------
    selector = SamplingStrategySelector()
    strategy, reason, confidence = selector.decide(context)
    print(f"\nStrategy: {strategy!r}  reason={reason}  conf={confidence:.2f}")

    # ----------------------------------------------------------------
    # 3. Generate design points
    # ----------------------------------------------------------------
    if strategy == "lhs":
        raw_points = latin_hypercube_sampling(context, num_samples=50, seed=42)
    else:
        raw_points = cartesian_product_sampling(context)

    print(f"Raw points generated: {len(raw_points)}")

    # Convert to DesignPoint domain objects
    design_points = [
        DesignPoint(
            design_id=i,
            knobs={
                "compliance_threshold": round(0.3 + (i % 7) * 0.1, 2),
                "audit_frequency_days": 30 + (i % 4) * 30,
                "risk_tolerance":       round(0.1 + (i % 5) * 0.15, 2),
            },
            tags={k: str(v) for k, v in raw_points[i].items()},
        )
        for i in range(len(raw_points))
    ]
    print(f"DesignPoints created: {len(design_points)}")

    # ----------------------------------------------------------------
    # 4. Define normalization profile
    # ----------------------------------------------------------------
    profile = NormalizationProfile(
        profile_name="demo_profile",
        kpi_configs=[
            KPIConfig("compliance_score",  0.0, 1.0, OptimizationDirection.MAXIMIZE, weight=0.6),
            KPIConfig("cost_efficiency",   0.0, 1.0, OptimizationDirection.MAXIMIZE, weight=0.2),
            KPIConfig("time_to_deploy",    0.0, 1.0, OptimizationDirection.MINIMIZE, weight=0.2),
        ],
    )

    # ----------------------------------------------------------------
    # 5. Define policy (doctrine weights)
    # ----------------------------------------------------------------
    policy = PolicySet(
        policy_name="demo_policy",
        optimization_objective="maximize_compliance",
        doctrine_weights={
            "compliance_score": 0.6,
            "cost_efficiency":  0.2,
            "time_to_deploy":   0.2,
        },
    )

    # ----------------------------------------------------------------
    # 6. Run DSE compute engine
    # ----------------------------------------------------------------
    run_ctx = RunContext(user_id="demo_user", trace_id="demo-trace-001", use_case="demo")
    artifact = run_dse(design_points, policy, profile, run_ctx, seed=42)

    # ----------------------------------------------------------------
    # 7. Results
    # ----------------------------------------------------------------
    print(f"\n{'─' * 40}")
    print(f"Total design points : {artifact.total_design_points}")
    print(f"Pareto-optimal      : {artifact.pareto_count}")
    print(f"Input hash          : {artifact.input_hash[:16]}...")
    print(f"Seed                : {artifact.seed}")

    top5 = artifact.ranking_dottrinale[:5]
    print(f"\nTop-5 dottrinale ranking:")
    for item in top5:
        pareto_flag = " ✦ PARETO" if item.get("is_pareto") else ""
        print(
            f"  #{item['rank']:2d}  score={item['dottrinale_score']:.4f}"
            f"  id={item['design_id']}{pareto_flag}"
        )

    print(f"\n✅ DSE LIVELLO 1 example complete.")


if __name__ == "__main__":
    main()
