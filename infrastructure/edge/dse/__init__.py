"""
DSE — Design Space Exploration Engine
======================================

LIVELLO 1: Pure Domain Layer (Zero I/O)
Sacred Order: REASON (Computation — deterministic, explainable outputs)

Responsibilities:
- Sample multi-dimensional parameter spaces (LHS, Cartesian, Sobol)
- Compute Pareto frontiers (non-dominated multi-objective optimization)
- Score and rank design points via dottrinale doctrine weights
- Select optimal sampling strategy (heuristic + ML-historical)

Import pattern (relative only):
    from .consumers.sampling import latin_hypercube_sampling
    from .consumers.pareto import compute_pareto_frontier
    from .consumers.engine import run_dse
    from .domain.schemas import DesignPoint, RunArtifact
"""

__all__ = [
    "domain",
    "consumers",
    "governance",
    "events",
    "monitoring",
]
