"""
Pattern library for Neural Engine Core.

These are OPTIONAL utilities and implementations. They are not part of the
core substrate identity. Use them if they fit your needs, or implement your
own patterns.

The core substrate provides:
- Contracts (AbstractFactor, NormalizerStrategy, AggregationProfile)
- Orchestration (EvaluationOrchestrator)
- Data structures (EvaluationContext, EvaluationResult)

Everything else is your responsibility or an optional pattern.
"""

# Optional patterns - use if helpful, ignore if not
from vitruvyan_core.patterns.neural_engine.registry import (
    FactorRegistry,
    ProfileRegistry,
    NormalizerRegistry
)
from vitruvyan_core.patterns.neural_engine.normalizers import (
    MinMaxNormalizer,
    RankNormalizer
)
from vitruvyan_core.patterns.neural_engine.math_utils import (
    winsorize,
    time_decay,
    safe_divide
)

__all__ = [
    # Registry pattern (optional organization mechanism)
    "FactorRegistry",
    "ProfileRegistry",
    "NormalizerRegistry",
    # Additional normalizers (optional implementations)
    "MinMaxNormalizer",
    "RankNormalizer",
    # Math utilities (optional helpers)
    "winsorize",
    "time_decay",
    "safe_divide",
]
