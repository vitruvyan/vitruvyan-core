"""
Neural Engine Core - Domain-agnostic computational substrate.

This is a SUBSTRATE, not a framework. It provides:
- Abstract contracts for evaluation logic
- Orchestration of computation → normalization → aggregation
- Data structures for inputs and outputs

It does NOT provide:
- Domain knowledge
- Pre-built factors or profiles
- Preferred patterns or utilities
- Opinions on how to evaluate

Your vertical defines "what matters" and "how to measure it".
The core only structures the evaluation flow.

MINIMAL CORE EXPORTS:
- Contracts: AbstractFactor, NormalizerStrategy, AggregationProfile
- Context & Results: EvaluationContext, EvaluationResult, EntityEvaluation, FactorContribution
- Orchestrator: EvaluationOrchestrator
- Reference: ZScoreNormalizer (example implementation only)

OPTIONAL PATTERNS (vitruvyan_core.patterns.neural_engine):
- Registries (FactorRegistry, ProfileRegistry, NormalizerRegistry)
- Additional normalizers (MinMaxNormalizer, RankNormalizer)
- Math utilities (winsorize, time_decay, safe_divide)
"""

import warnings

from vitruvyan_core.core.cognitive.neural_engine.contracts import (
    AbstractFactor,
    NormalizerStrategy,
    AggregationProfile
)
from vitruvyan_core.core.cognitive.neural_engine.context import EvaluationContext
from vitruvyan_core.core.cognitive.neural_engine.result import (
    EvaluationResult,
    EntityEvaluation,
    FactorContribution
)
from vitruvyan_core.core.cognitive.neural_engine.orchestrator import EvaluationOrchestrator
from vitruvyan_core.core.cognitive.neural_engine.normalizers import ZScoreNormalizer


# ============================================================================
# COMPATIBILITY LAYER - DEPRECATED
# These imports work but are not part of core identity
# ============================================================================

def _deprecated_import(name: str, new_location: str):
    """Issue deprecation warning for moved components."""
    warnings.warn(
        f"{name} has been moved to {new_location} as an optional pattern. "
        f"It is not part of the core substrate. "
        f"Import from '{new_location}' or implement your own pattern.",
        DeprecationWarning,
        stacklevel=3
    )


def __getattr__(attr_name: str):
    """
    Lazy import for backward compatibility.
    Issues deprecation warning for non-core components.
    """
    # Registry pattern (optional, not core)
    if attr_name == "FactorRegistry":
        _deprecated_import("FactorRegistry", "vitruvyan_core.patterns.neural_engine")
        from vitruvyan_core.patterns.neural_engine import FactorRegistry
        return FactorRegistry
    
    if attr_name == "ProfileRegistry":
        _deprecated_import("ProfileRegistry", "vitruvyan_core.patterns.neural_engine")
        from vitruvyan_core.patterns.neural_engine import ProfileRegistry
        return ProfileRegistry
    
    if attr_name == "NormalizerRegistry":
        _deprecated_import("NormalizerRegistry", "vitruvyan_core.patterns.neural_engine")
        from vitruvyan_core.patterns.neural_engine import NormalizerRegistry
        return NormalizerRegistry
    
    # Additional normalizers (optional, not core)
    if attr_name == "MinMaxNormalizer":
        _deprecated_import("MinMaxNormalizer", "vitruvyan_core.patterns.neural_engine")
        from vitruvyan_core.patterns.neural_engine import MinMaxNormalizer
        return MinMaxNormalizer
    
    if attr_name == "RankNormalizer":
        _deprecated_import("RankNormalizer", "vitruvyan_core.patterns.neural_engine")
        from vitruvyan_core.patterns.neural_engine import RankNormalizer
        return RankNormalizer
    
    raise AttributeError(f"module '{__name__}' has no attribute '{attr_name}'")


# Core substrate exports only
__all__ = [
    # Contracts
    "AbstractFactor",
    "NormalizerStrategy",
    "AggregationProfile",
    # Context & Results
    "EvaluationContext",
    "EvaluationResult",
    "EntityEvaluation",
    "FactorContribution",
    # Orchestrator
    "EvaluationOrchestrator",
    # Reference normalizer
    "ZScoreNormalizer",
]
