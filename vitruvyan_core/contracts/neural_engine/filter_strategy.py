"""
Filter Strategy Contract (Interface)
===================================

Defines optional domain-specific filtering hooks applied around Neural Engine
ranking (e.g., momentum breakout, earnings safety, portfolio diversification).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

import pandas as pd


class IFilterStrategy(ABC):
    """Abstract interface for domain-specific screening filters."""

    @abstractmethod
    def apply_filters(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any],
        context: Dict[str, Any] | None = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply domain filters to a scored dataframe.

        Args:
            df: DataFrame containing features/composite scores.
            filters: Requested filter flags/parameters.
            context: Optional execution context.

        Returns:
            (filtered_dataframe, diagnostics)
        """


class FilterStrategyError(Exception):
    """Base exception for filter strategy errors."""

