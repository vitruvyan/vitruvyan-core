"""
Composite Scorer
================

Domain-agnostic weighted composite score calculator.

Computes weighted average of z-scores using profile-based weights
from IScoringStrategy implementations.

Author: vitruvyan-core
Date: February 8, 2026
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

try:
    from contracts import IScoringStrategy
except ModuleNotFoundError:
    from vitruvyan_core.contracts import IScoringStrategy

logger = logging.getLogger(__name__)


class CompositeScorer:
    """
    Domain-agnostic composite score calculator.
    
    Algorithm:
        composite_score = Σ(z_score_i × weight_i) / Σ(weight_i)
    
    Where:
        - z_score_i: Z-score for feature i
        - weight_i: Weight for feature i from profile
        - Normalization handles missing z-scores dynamically
    
    Example:
        Profile weights: {momentum: 0.4, trend: 0.3, volatility: 0.3}
        
        Entity A (all z-scores present):
            composite = (1.5×0.4 + 0.8×0.3 + -0.5×0.3) / 1.0 = 0.69
        
        Entity B (volatility missing):
            composite = (1.5×0.4 + 0.8×0.3) / 0.7 = 1.20
    """
    
    def __init__(self, scoring_strategy: IScoringStrategy):
        """
        Initialize Composite Scorer.
        
        Args:
            scoring_strategy: Implementation of IScoringStrategy
                            (provides profile weights and composite logic)
        """
        self.scoring_strategy = scoring_strategy
    
    def compute_composite_scores(
        self,
        df: pd.DataFrame,
        profile: str,
        feature_z_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Computes composite scores using profile weights (vectorized).
        
        Args:
            df: DataFrame with z-score columns
            profile: Profile name (e.g., "aggressive", "balanced", "conservative")
            feature_z_mapping: Maps feature name -> z-score column name
                              Example: {"momentum": "momentum_z", "trend": "trend_z"}
        
        Returns:
            DataFrame with additional columns:
              - composite_score: Weighted z-score average
              - weights_used: Dict of normalized weights used per entity
        
        Raises:
            InvalidProfileError: If profile doesn't exist
        """
        if not self.scoring_strategy.validate_profile(profile):
            raise ValueError(f"Invalid profile: '{profile}'")
        
        out = df.copy()
        
        # Get profile weights
        profile_weights = self.scoring_strategy.get_profile_weights(profile)
        
        # Build aligned arrays for vectorized computation
        feature_names = []
        z_cols = []
        weights = []
        
        for feature_name, weight in profile_weights.items():
            z_col = feature_z_mapping.get(feature_name)
            if z_col and z_col in out.columns:
                feature_names.append(feature_name)
                z_cols.append(z_col)
                weights.append(weight)
        
        if not z_cols:
            out["composite_score"] = np.nan
            out["weights_used"] = [{}] * len(out)
            return out
        
        if len(out) == 0:
            out["composite_score"] = pd.Series(dtype=float)
            out["weights_used"] = pd.Series(dtype=object)
            return out
        
        # Vectorized: extract z-score matrix and compute weighted sum
        z_matrix = out[z_cols].values.astype(float)            # shape: (n_entities, n_features)
        weights_arr = np.array(weights)                        # shape: (n_features,)
        available_mask = ~np.isnan(z_matrix)                   # True where z-score exists
        
        # Per-entity active weights (zero where z-score is NaN)
        active_weights = available_mask * weights_arr          # broadcast: (n, f) * (f,)
        weight_sums = active_weights.sum(axis=1)               # shape: (n,)
        
        # Weighted z-scores (NaN treated as 0 for summation)
        z_filled = np.where(available_mask, z_matrix, 0.0)
        weighted_z_sums = (z_filled * active_weights).sum(axis=1)
        
        # Composite score with normalization (NaN where no features available)
        with np.errstate(divide='ignore', invalid='ignore'):
            composite_scores = np.where(
                weight_sums > 0,
                weighted_z_sums / weight_sums,
                np.nan
            )
        
        out["composite_score"] = composite_scores
        
        # Build per-entity normalized weights (readable audit trail)
        weights_used_list = []
        for i in range(len(out)):
            ws = weight_sums[i]
            if ws > 0:
                entity_weights = {
                    feature_names[j]: round(float(active_weights[i, j] / ws), 3)
                    for j in range(len(feature_names))
                    if available_mask[i, j]
                }
            else:
                entity_weights = {}
            weights_used_list.append(entity_weights)
        
        out["weights_used"] = weights_used_list
        
        logger.info(f"Composite scores computed for profile '{profile}': "
                   f"{out['composite_score'].notna().sum()}/{len(out)} entities scored")
        
        return out
    
    def apply_risk_adjustment(
        self,
        df: pd.DataFrame,
        risk_tolerance: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        Applies risk adjustment using scoring strategy.
        
        Args:
            df: DataFrame with composite_score column
            risk_tolerance: Risk tolerance level (e.g., "low", "medium", "high")
            **kwargs: Additional parameters passed to strategy.apply_risk_adjustment()
        
        Returns:
            DataFrame with adjusted composite_score
        """
        return self.scoring_strategy.apply_risk_adjustment(
            df, 
            risk_tolerance=risk_tolerance,
            **kwargs
        )


class CompositeScorerError(Exception):
    """Base exception for composite scoring errors"""
    pass
