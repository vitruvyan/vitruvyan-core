"""
Rank-based normalization strategy.

Converts raw values to percentile ranks.
"""

from typing import Optional
import pandas as pd

from vitruvyan_core.core.cognitive.neural_engine.contracts import NormalizerStrategy


class RankNormalizer(NormalizerStrategy):
    """
    Rank normalization: converts values to percentile ranks.
    
    Output is in [0, 1] range where 1.0 = highest rank.
    """
    
    @property
    def name(self) -> str:
        return "rank"
    
    def normalize(
        self,
        raw_values: pd.Series,
        higher_is_better: bool = True,
        stratification_groups: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Normalize using percentile ranking.
        
        Args:
            raw_values: Series of raw values
            higher_is_better: Whether higher values should rank higher
            stratification_groups: Optional groups for stratified normalization
        
        Returns:
            Series of percentile ranks in [0, 1]
        """
        if raw_values.empty:
            return pd.Series(dtype=float)
        
        # Handle stratified normalization
        if stratification_groups is not None:
            return self._normalize_stratified(raw_values, stratification_groups, higher_is_better)
        
        # Global ranking
        ascending = not higher_is_better
        ranks = raw_values.rank(method='average', ascending=ascending)
        
        # Convert to percentile [0, 1]
        count = len(raw_values)
        percentiles = (ranks - 1) / (count - 1) if count > 1 else pd.Series(0.5, index=raw_values.index)
        
        return percentiles
    
    def _normalize_stratified(
        self,
        raw_values: pd.Series,
        groups: pd.Series,
        higher_is_better: bool
    ) -> pd.Series:
        """
        Normalize within stratification groups.
        
        Args:
            raw_values: Series of raw values
            groups: Series of group labels (same index)
            higher_is_better: Whether higher values should rank higher
        
        Returns:
            Series of percentile ranks computed within groups
        """
        result = pd.Series(index=raw_values.index, dtype=float)
        ascending = not higher_is_better
        
        for group_name, group_indices in groups.groupby(groups).groups.items():
            group_values = raw_values.loc[group_indices]
            
            ranks = group_values.rank(method='average', ascending=ascending)
            count = len(group_values)
            
            # Convert to percentile [0, 1]
            if count > 1:
                percentiles = (ranks - 1) / (count - 1)
            else:
                percentiles = pd.Series(0.5, index=group_values.index)
            
            result.loc[group_indices] = percentiles
        
        return result
