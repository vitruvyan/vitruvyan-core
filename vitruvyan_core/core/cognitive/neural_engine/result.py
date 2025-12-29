"""
Result structures for the Neural Engine Core.

Defines the output data structures from factor evaluation.
"""

from dataclasses import dataclass
from typing import List, Optional
from vitruvyan_core.core.cognitive.neural_engine.context import EvaluationContext


@dataclass
class FactorContribution:
    """
    A single factor's contribution to the composite score.
    
    Provides transparency into how each factor influenced the final score.
    """
    
    factor_name: str
    """Name of the factor"""
    
    raw_value: Optional[float]
    """Raw computed value before normalization"""
    
    normalized_value: Optional[float]
    """Normalized value after applying normalization strategy"""
    
    weight: float
    """Weight assigned by aggregation profile (0.0 to 1.0)"""
    
    contribution: float
    """Final contribution to composite score (weight * normalized_value)"""


@dataclass
class EntityEvaluation:
    """
    Complete evaluation for a single entity.
    
    Contains the composite score, rank, and breakdown of factor contributions.
    """
    
    entity_id: str
    """Unique identifier for the entity"""
    
    composite_score: float
    """Final aggregated score"""
    
    rank: Optional[int]
    """Relative rank among evaluated entities (1 = best)"""
    
    factor_contributions: List[FactorContribution]
    """Breakdown of how each factor contributed to composite score"""


@dataclass
class EvaluationResult:
    """
    Complete result from a factor evaluation request.
    
    Contains evaluations for all entities plus metadata about the evaluation.
    """
    
    context: EvaluationContext
    """Original evaluation context"""
    
    evaluations: List[EntityEvaluation]
    """Evaluation for each entity"""
    
    factors_used: List[str]
    """Names of factors that were computed"""
    
    normalizer_used: str
    """Name of the normalization strategy used"""
    
    profile_used: str
    """Name of the aggregation profile used"""
    
    entity_count: int
    """Number of entities evaluated"""
    
    duration_ms: Optional[float] = None
    """Execution time in milliseconds"""
