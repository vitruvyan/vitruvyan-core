"""
Abstract contracts for the Neural Engine Core.

These interfaces define the computational substrate for domain-agnostic
factor evaluation, normalization, and aggregation.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd


class AbstractFactor(ABC):
    """
    Abstract base class for all scoring factors.
    
    Factors compute raw values for entities. They receive data from the caller
    (no database access) and return a pandas Series indexed by entity_id.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this factor."""
        ...
    
    @property
    def higher_is_better(self) -> bool:
        """
        Whether higher raw values indicate better performance.
        
        Returns:
            True if higher values are better (default), False otherwise
        """
        return True
    
    @property
    def requires_stratification(self) -> bool:
        """
        Whether this factor should be normalized within groups.
        
        Returns:
            True if normalization should be stratified, False for global
        """
        return False
    
    @property
    def stratification_field(self) -> Optional[str]:
        """
        Field name to use for stratification groups.
        
        Returns:
            Column name from entities DataFrame, or None
        """
        return None
    
    @abstractmethod
    def compute(self, entities: pd.DataFrame, context: "EvaluationContext") -> pd.Series:
        """
        Compute raw factor values for entities.
        
        Args:
            entities: DataFrame with at least 'entity_id' column
            context: Evaluation context with metadata and options
        
        Returns:
            Series indexed by entity_id with raw factor values
        """
        ...


class NormalizerStrategy(ABC):
    """
    Abstract base class for normalization strategies.
    
    Normalizers convert raw factor values to comparable scores,
    optionally handling stratification by groups.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this normalizer."""
        ...
    
    @abstractmethod
    def normalize(
        self,
        raw_values: pd.Series,
        higher_is_better: bool = True,
        stratification_groups: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Normalize raw values to comparable scores.
        
        Args:
            raw_values: Series of raw factor values
            higher_is_better: Whether higher values are better
            stratification_groups: Optional series of group labels (same index)
        
        Returns:
            Series of normalized values with same index as raw_values
        """
        ...


class AggregationProfile(ABC):
    """
    Abstract base class for score aggregation profiles.
    
    Profiles define how to combine multiple normalized factor scores
    into a single composite score.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this profile."""
        ...
    
    @abstractmethod
    def get_weights(self, available_factors: List[str]) -> Dict[str, float]:
        """
        Return weights for available factors.
        
        Weights should sum to 1.0. If some factors are missing from
        available_factors, recalibrate remaining weights to sum to 1.0.
        
        Args:
            available_factors: List of factor names that have values
        
        Returns:
            Dictionary mapping factor_name to weight (0.0 to 1.0)
        """
        ...
    
    @abstractmethod
    def aggregate(self, factor_scores: Dict[str, pd.Series]) -> pd.Series:
        """
        Combine normalized factor scores into composite score.
        
        Args:
            factor_scores: Dictionary mapping factor_name to normalized Series
        
        Returns:
            Series of composite scores indexed by entity_id
        """
        ...
