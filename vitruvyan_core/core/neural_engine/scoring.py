"""
Z-Score Calculator
==================

Domain-agnostic z-score computation with stratification support.

Supports 3 stratification modes:
- global: Z-score vs entire universe
- stratified: Z-score vs grouping field (e.g., sector, region, age_group)
- composite: Weighted blend (30% global + 70% stratified)

Author: vitruvyan-core
Date: February 8, 2026
"""

import logging
from typing import Optional, Literal
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

StratificationMode = Literal["global", "stratified", "composite"]


class ZScoreCalculator:
    """
    Domain-agnostic z-score calculator with stratification support.
    
    Algorithm:
        z = (x - μ) / σ
    
    Where:
        - x: raw feature value
        - μ: mean (global or stratified)
        - σ: standard deviation (global or stratified)
    
    Stratification modes:
        - global: μ and σ computed across entire universe
        - stratified: μ and σ computed per group (e.g., per sector)
        - composite: 30% global + 70% stratified (balanced approach)
    """
    
    def __init__(
        self, 
        stratification_mode: StratificationMode = "global",
        stratification_field: Optional[str] = None
    ):
        """
        Initialize Z-Score Calculator.
        
        Args:
            stratification_mode: "global", "stratified", or "composite"
            stratification_field: Column name for stratification (required if mode != "global")
        """
        self.stratification_mode = stratification_mode
        self.stratification_field = stratification_field
        
        if stratification_mode in ["stratified", "composite"] and not stratification_field:
            raise ValueError(f"stratification_field required for mode '{stratification_mode}'")
    
    def compute_z_scores(
        self,
        df: pd.DataFrame,
        feature_columns: list[str],
        output_suffix: str = "_z"
    ) -> pd.DataFrame:
        """
        Computes z-scores for specified feature columns.
        
        Args:
            df: Input DataFrame
            feature_columns: List of column names to compute z-scores for
            output_suffix: Suffix for z-score columns (default: "_z")
        
        Returns:
            DataFrame with additional z-score columns (e.g., "momentum_z", "trend_z")
        
        Example:
            Input:
                | entity_id | sector     | momentum | trend |
                |-----------|------------|----------|-------|
                | AAPL      | Technology | 68.5     | 5.2   |
                | XOM       | Energy     | 45.0     | -2.1  |
            
            Output (global mode):
                | entity_id | sector     | momentum | momentum_z | trend | trend_z |
                |-----------|------------|----------|------------|-------|---------|
                | AAPL      | Technology | 68.5     | 1.23       | 5.2   | 1.45    |
                | XOM       | Energy     | 45.0     | -0.87      | -2.1  | -0.92   |
        """
        out = df.copy()
        
        for col in feature_columns:
            if col not in out.columns:
                logger.warning(f"Column '{col}' not found, skipping z-score calculation")
                continue
            
            z_col = f"{col}{output_suffix}"
            
            if self.stratification_mode == "global":
                out[z_col] = self._compute_global_z(out, col)
            
            elif self.stratification_mode == "stratified":
                out[z_col] = self._compute_stratified_z(out, col)
            
            elif self.stratification_mode == "composite":
                out[z_col] = self._compute_composite_z(out, col)
            
            else:
                raise ValueError(f"Invalid stratification_mode: {self.stratification_mode}")
        
        return out
    
    def _compute_global_z(self, df: pd.DataFrame, col: str) -> pd.Series:
        """Computes z-score vs entire universe."""
        if df[col].notnull().sum() <= 1:
            return pd.Series(np.nan, index=df.index)
        
        mu = df[col].mean()
        sigma = df[col].std(ddof=0)
        
        if sigma == 0 or pd.isna(sigma):
            return pd.Series(0.0, index=df.index)
        
        return (df[col] - mu) / sigma
    
    def _compute_stratified_z(self, df: pd.DataFrame, col: str) -> pd.Series:
        """Computes z-score per stratification group."""
        if self.stratification_field not in df.columns:
            logger.error(f"Stratification field '{self.stratification_field}' not found, falling back to global")
            return self._compute_global_z(df, col)
        
        def group_z(x: pd.Series) -> pd.Series:
            if x.std() > 0:
                return (x - x.mean()) / x.std()
            else:
                return pd.Series(0.0, index=x.index)
        
        return df.groupby(self.stratification_field, group_keys=False)[col].transform(group_z)
    
    def _compute_composite_z(self, df: pd.DataFrame, col: str) -> pd.Series:
        """Computes composite z-score (30% global + 70% stratified)."""
        z_global = self._compute_global_z(df, col)
        z_stratified = self._compute_stratified_z(df, col)
        
        return 0.3 * z_global + 0.7 * z_stratified
    
    def apply_time_decay(
        self,
        df: pd.DataFrame,
        z_score_columns: list[str],
        timestamp_column: str,
        half_life_days: float = 30.0
    ) -> pd.DataFrame:
        """
        Applies exponential time decay to z-scores.
        
        Formula:
            z_decayed = z_original × exp(-days_old / half_life)
        
        Args:
            df: DataFrame with z-score columns
            z_score_columns: List of z-score column names
            timestamp_column: Column with timestamps
            half_life_days: Decay half-life in days (default: 30)
        
        Returns:
            DataFrame with decayed z-scores
        """
        out = df.copy()
        
        if timestamp_column not in out.columns:
            logger.warning(f"Timestamp column '{timestamp_column}' not found, skipping decay")
            return out
        
        now = pd.Timestamp.now(tz='UTC')
        out[timestamp_column] = pd.to_datetime(out[timestamp_column], utc=True)
        out["days_old"] = (now - out[timestamp_column]).dt.total_seconds() / 86400.0
        out["decay_factor"] = np.exp(-out["days_old"] / half_life_days)
        
        for col in z_score_columns:
            if col in out.columns:
                mask = out[col].notna()
                out.loc[mask, col] = out.loc[mask, col] * out.loc[mask, "decay_factor"]
        
        logger.info(f"Time decay applied: mean decay_factor={out['decay_factor'].mean():.3f}")
        out = out.drop(columns=["days_old", "decay_factor"])
        
        return out


class ZScoreError(Exception):
    """Base exception for z-score calculation errors"""
    pass
