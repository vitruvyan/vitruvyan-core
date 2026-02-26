"""DSE consumers — pure process functions (zero I/O)."""
from .sampling import (
    latin_hypercube_sampling,
    cartesian_product_sampling,
    sobol_sequence_sampling,
    count_dimensions,
)
from .pareto import compute_pareto_frontier, dominates
from .engine import run_dse

__all__ = [
    "latin_hypercube_sampling",
    "cartesian_product_sampling",
    "sobol_sequence_sampling",
    "count_dimensions",
    "compute_pareto_frontier",
    "dominates",
    "run_dse",
]
