"""
Contracts Module
================

Defines abstract interfaces (contracts) for domain-specific implementations.
These contracts enable the Generic Aggregation Engine to work with any domain.

Contracts:
- IDataProvider: Data access layer (universe, features, metadata)
- IScoringStrategy: Scoring logic layer (profiles, weights, risk adjustment)

Author: vitruvyan-core
Date: February 8, 2026
"""

from .data_provider import (
    IDataProvider,
    DataProviderError,
    EntityNotFoundError,
    FeatureNotAvailableError
)

from .scoring_strategy import (
    IScoringStrategy,
    ScoringStrategyError,
    InvalidProfileError,
    InvalidWeightsError
)

__all__ = [
    # Data Provider
    "IDataProvider",
    "DataProviderError",
    "EntityNotFoundError",
    "FeatureNotAvailableError",
    
    # Scoring Strategy
    "IScoringStrategy",
    "ScoringStrategyError",
    "InvalidProfileError",
    "InvalidWeightsError",
]
