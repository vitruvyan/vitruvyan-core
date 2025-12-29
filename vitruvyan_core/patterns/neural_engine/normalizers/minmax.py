"""
Min-Max normalization strategy.

Scales raw values to [0, 1] range.
"""

from typing import Optional
import pandas as pd

from vitruvyan_core.core.cognitive.neural_engine.contracts import NormalizerStrategy


class MinMaxNormalizer(NormalizerStrategy):
    """
    Min-Max normalization: (x - min) / (max - min)
    
    Scales values to [0, 1] range.
    """
    
    @property
    def name(self) -> str:
        return "minmax"
    
    def normalize(
        self,
        raw_values: pd.Series,
        higher_is_better: bool = True,
        stratification_groups: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Normalize using min-max scaling.
        
        Args:
            raw_values: Series of raw values
            higher_is_better: Whether higher values are better
            stratification_groups: Optional groups for stratified normalization
        
        Returns:
            Series of values scaled to [0, 1]
        """
        if raw_values.empty:
            return pd.Series(dtype=float)
        
        # Handle stratified normalization
        if stratification_groups is not None:
            return self._normalize_stratified(raw_values, stratification_groups, higher_is_better)
        
        # Global normalization
        min_val = raw_values.min()
        max_val = raw_values.max()
        
        # Handle no variance
        if min_val == max_val:
            return pd.Series(0.5, index=raw_values.index)
        
        normalized = (raw_values - min_val) / (max_val - min_val)
        
        # Invert if lower is better
        if not higher_is_better:
            normalized = 1.0 - normalized
        
        return normalized
    
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
            higher_is_better: Whether higher values are better
        
        Returns:
            Series of min-max scaled values computed within groups
        """
        result = pd.Series(index=raw_values.index, dtype=float)
        
        for group_name, group_indices in groups.groupby(groups).groups.items():
            group_values = raw_values.loc[group_indices]
            
            min_val = group_values.min()
            max_val = group_values.max()
            
            # Handle no variance within group
            if min_val == max_val:
                result.loc[group_indices] = 0.5
            else:
                normalized = (group_values - min_val) / (max_val - min_val)
                if not higher_is_better:
                    normalized = 1.0 - normalized
                result.loc[group_indices] = normalized
        
        return result
