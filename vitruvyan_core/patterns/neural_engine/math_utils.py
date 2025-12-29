"""
Mathematical utilities for the Neural Engine Core.

Provides common mathematical operations for factor computation.
"""

from typing import Optional
import pandas as pd
import numpy as np


def winsorize(
    series: pd.Series,
    lower: float = 0.01,
    upper: float = 0.99
) -> pd.Series:
    """
    Clip outliers to specified percentiles.
    
    Args:
        series: Input series
        lower: Lower percentile (0.0 to 1.0)
        upper: Upper percentile (0.0 to 1.0)
    
    Returns:
        Series with outliers clipped
    """
    if series.empty:
        return series
    
    lower_bound = series.quantile(lower)
    upper_bound = series.quantile(upper)
    
    return series.clip(lower=lower_bound, upper=upper_bound)


def time_decay(
    values: pd.Series,
    timestamps: pd.Series,
    half_life_days: float
) -> pd.Series:
    """
    Apply exponential time decay to values.
    
    Args:
        values: Series of values to decay
        timestamps: Series of timestamps (pandas datetime)
        half_life_days: Half-life in days for exponential decay
    
    Returns:
        Series of decayed values
    """
    if values.empty or timestamps.empty:
        return values
    
    # Calculate days since most recent timestamp
    max_timestamp = timestamps.max()
    days_ago = (max_timestamp - timestamps).dt.total_seconds() / (24 * 3600)
    
    # Exponential decay: value * (0.5 ^ (days_ago / half_life))
    decay_factor = np.power(0.5, days_ago / half_life_days)
    
    return values * decay_factor


def safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
    default: float = 0.0
) -> pd.Series:
    """
    Perform division with fallback for zero/null denominators.
    
    Args:
        numerator: Series of numerators
        denominator: Series of denominators
        default: Value to use when division is undefined
    
    Returns:
        Series of division results with fallback
    """
    result = pd.Series(default, index=numerator.index)
    
    # Only divide where denominator is non-zero and non-null
    valid_mask = (denominator != 0) & denominator.notna()
    result[valid_mask] = numerator[valid_mask] / denominator[valid_mask]
    
    return result
