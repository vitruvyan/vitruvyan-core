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
        Computes composite scores using profile weights.
        
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
        
        # Compute composite score per row
        def compute_row_score(row: pd.Series) -> tuple[float, Dict[str, float]]:
            """Returns (composite_score, normalized_weights_used)"""
            score_parts = []
            
            for feature_name, weight in profile_weights.items():
                z_col = feature_z_mapping.get(feature_name)
                
                if z_col and z_col in row.index:
                    z_value = row[z_col]
                    
                    if pd.notnull(z_value):
                        score_parts.append((feature_name, z_value, weight))
            
            if not score_parts:
                return (np.nan, {})
            
            # Compute weighted sum with normalization
            total_weight = sum(w for _, _, w in score_parts)
            
            if total_weight <= 0:
                return (np.nan, {})
            
            composite = sum(z * (w / total_weight) for _, z, w in score_parts)
            normalized_weights = {name: round(w / total_weight, 3) for name, _, w in score_parts}
            
            return (composite, normalized_weights)
        
        # Apply to all rows
        results = [compute_row_score(row) for _, row in out.iterrows()]
        
        out["composite_score"] = [score for score, _ in results]
        out["weights_used"] = [weights for _, weights in results]
        
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
