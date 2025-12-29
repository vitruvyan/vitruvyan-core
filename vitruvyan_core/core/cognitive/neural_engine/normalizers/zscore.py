"""
Z-Score normalization strategy.

This is a REFERENCE IMPLEMENTATION demonstrating the NormalizerStrategy contract.
Your domain may require completely different normalization strategies.

Use this as a starting point, not as "the way" to normalize.
"""

from typing import Optional
import pandas as pd
import numpy as np

from vitruvyan_core.core.cognitive.neural_engine.contracts import NormalizerStrategy


class ZScoreNormalizer(NormalizerStrategy):
    """
    Z-score normalization: z = (x - μ) / σ
    
    Supports both global and stratified modes.
    """
    
    @property
    def name(self) -> str:
        return "zscore"
    
    def normalize(
        self,
        raw_values: pd.Series,
        higher_is_better: bool = True,
        stratification_groups: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Normalize using z-score transformation.
        
        Args:
            raw_values: Series of raw values
            higher_is_better: Whether to invert scores (not used in z-score)
            stratification_groups: Optional groups for stratified normalization
        
        Returns:
            Series of z-scores
        """
        if raw_values.empty:
            return pd.Series(dtype=float)
        
        # Handle stratified normalization
        if stratification_groups is not None:
            return self._normalize_stratified(raw_values, stratification_groups, higher_is_better)
        
        # Global normalization
        mean = raw_values.mean()
        std = raw_values.std()
        
        # Handle zero variance
        if std == 0 or pd.isna(std):
            return pd.Series(0.0, index=raw_values.index)
        
        z_scores = (raw_values - mean) / std
        
        # Invert if lower is better
        if not higher_is_better:
            z_scores = -z_scores
        
        return z_scores
    
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
            higher_is_better: Whether to invert scores
        
        Returns:
            Series of z-scores computed within groups
        """
        result = pd.Series(index=raw_values.index, dtype=float)
        
        for group_name, group_indices in groups.groupby(groups).groups.items():
            group_values = raw_values.loc[group_indices]
            
            mean = group_values.mean()
            std = group_values.std()
            
            # Handle zero variance within group
            if std == 0 or pd.isna(std):
                result.loc[group_indices] = 0.0
            else:
                z_scores = (group_values - mean) / std
                if not higher_is_better:
                    z_scores = -z_scores
                result.loc[group_indices] = z_scores
        
        return result
