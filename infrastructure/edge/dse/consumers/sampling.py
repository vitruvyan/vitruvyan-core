"""
DSE Sampling Strategies — Pure Mathematical Functions
======================================================

PURE FUNCTIONS for design space sampling.
Zero I/O. Zero state. Fully testable. Deterministic (seed-based).

Strategies:
- Latin Hypercube Sampling (LHS): uniform coverage for high-dim spaces.
- Cartesian Product: exhaustive enumeration for small spaces.
- Sobol Sequence: quasi-random low-discrepancy (Phase 2+).

Ported from aegis/vitruvyan_core/aegis/dse/sampling.py
Refactored: Feb 26, 2026 — vitruvyan-core SACRED_ORDER_PATTERN conformance

IMPORT RULE (LIVELLO 1): relative imports only.
"""

import itertools
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.stats import qmc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def count_dimensions(context: Dict[str, List[Any]]) -> int:
    """Return total product-space size from a context dict of lists."""
    if not context:
        return 0
    total = 1
    for v in context.values():
        if isinstance(v, list) and v:
            total *= len(v)
    return total


# ---------------------------------------------------------------------------
# Strategy: Latin Hypercube Sampling (LHS)
# ---------------------------------------------------------------------------

def latin_hypercube_sampling(
    dimensions: Dict[str, List[Any]],
    num_samples: int,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Latin Hypercube Sampling — uniform coverage of continuous/discrete spaces.

    Algorithm:
    1. Divide each dimension into `num_samples` equal strata.
    2. Draw one sample per stratum (uniform within).
    3. Shuffle strata across dimensions (avoid diagonal clustering).
    4. Map continuous [0,1] samples to discrete dimension values.

    Args:
        dimensions: {"sector": ["Banking", "Tech"], "region": ["EU", "US"]}
        num_samples: Design points to generate (recommended: 50).
        seed: Reproducibility seed (default: 42).

    Returns:
        List[Dict]: e.g. [{"sector": "Banking", "region": "EU"}, ...]

    Coverage advantage:
        Cartesian 2×2 = 4 corner points.
        LHS 50 samples = uniform interior + boundary coverage (~95%).
    """
    if not dimensions:
        logger.warning("LHS: empty dimensions — returning []")
        return []
    if num_samples <= 0:
        logger.warning("LHS: num_samples <= 0 — returning []")
        return []

    dim_names = list(dimensions.keys())
    dim_values = [dimensions[name] for name in dim_names]
    dim_sizes = [len(v) for v in dim_values]
    num_dims = len(dim_names)

    logger.info("LHS: dims=%d samples=%d seed=%d", num_dims, num_samples, seed)

    sampler = qmc.LatinHypercube(d=num_dims, seed=seed)
    lhs_samples = sampler.random(n=num_samples)

    design_points: List[Dict[str, Any]] = []
    for sample in lhs_samples:
        point: Dict[str, Any] = {}
        for idx, name in enumerate(dim_names):
            raw = sample[idx]
            discrete = int(raw * dim_sizes[idx])
            discrete = min(discrete, dim_sizes[idx] - 1)
            point[name] = dim_values[idx][discrete]
        design_points.append(point)

    unique = len({tuple(sorted(p.items())) for p in design_points})
    logger.info("LHS: generated %d points (%d unique)", len(design_points), unique)
    return design_points


# ---------------------------------------------------------------------------
# Strategy: Cartesian Product
# ---------------------------------------------------------------------------

def cartesian_product_sampling(
    dimensions: Dict[str, List[Any]],
) -> List[Dict[str, Any]]:
    """
    Exhaustive Cartesian product of all dimension values.

    Best for small spaces (< 20 total combinations) or baseline testing.
    Grows exponentially — use LHS for 4+ dimensions.

    Args:
        dimensions: {"x": [0, 1], "y": [0, 1]}

    Returns:
        All combinations: [{"x": 0, "y": 0}, {"x": 0, "y": 1}, ...]
    """
    if not dimensions:
        logger.warning("Cartesian: empty dimensions — returning []")
        return []

    dim_names = list(dimensions.keys())
    dim_values = [dimensions[name] for name in dim_names]

    design_points = [
        dict(zip(dim_names, combo))
        for combo in itertools.product(*dim_values)
    ]

    logger.info(
        "Cartesian: %d points from %d dimensions",
        len(design_points), len(dim_names),
    )
    return design_points


# ---------------------------------------------------------------------------
# Strategy: Sobol Sequence (Phase 2+)
# ---------------------------------------------------------------------------

def sobol_sequence_sampling(
    dimensions: Dict[str, List[Any]],
    num_samples: int,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Sobol quasi-random low-discrepancy sequence sampling.

    Phase 2+ feature — superior uniformity for high-dimensional spaces.
    Requires scipy >= 1.7.

    Args:
        dimensions: {"param": [...], ...}
        num_samples: Number of design points.
        seed: Optional seed (Sobol is deterministic; seed shifts the sequence).

    Returns:
        List[Dict]: Design points.
    """
    if not dimensions:
        logger.warning("Sobol: empty dimensions — returning []")
        return []
    if num_samples <= 0:
        logger.warning("Sobol: num_samples <= 0 — returning []")
        return []

    dim_names = list(dimensions.keys())
    dim_values = [dimensions[name] for name in dim_names]
    dim_sizes = [len(v) for v in dim_values]
    num_dims = len(dim_names)

    # Sobol requires power-of-2 sample count (pad up)
    import math
    n_pow2 = 2 ** math.ceil(math.log2(max(num_samples, 1)))

    logger.info(
        "Sobol: dims=%d requested=%d padded_to=%d",
        num_dims, num_samples, n_pow2,
    )

    sampler = qmc.Sobol(d=num_dims, scramble=True, seed=seed)
    sobol_samples = sampler.random(n=n_pow2)[:num_samples]

    design_points: List[Dict[str, Any]] = []
    for sample in sobol_samples:
        point: Dict[str, Any] = {}
        for idx, name in enumerate(dim_names):
            raw = sample[idx]
            discrete = min(int(raw * dim_sizes[idx]), dim_sizes[idx] - 1)
            point[name] = dim_values[idx][discrete]
        design_points.append(point)

    logger.info("Sobol: generated %d points", len(design_points))
    return design_points
