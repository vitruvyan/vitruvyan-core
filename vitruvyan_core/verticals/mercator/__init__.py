"""
Mercator Vertical: Financial Analysis & Portfolio Management

Mercator is Vitruvyan Core's finance vertical, providing comprehensive
quantitative analysis for investment decision-making.

Key Capabilities:
- Multi-factor quantitative evaluation
- Risk-adjusted portfolio optimization
- Attribution analysis and performance decomposition
- Explainable investment recommendations
- Real-time market signal processing

Architecture:
- Domain factors: Price momentum, earnings quality, valuation metrics, etc.
- Aggregation profiles: Growth, value, balanced, defensive strategies
- Risk assessment: Market, volatility, liquidity, correlation risks
- Explainability: Investment thesis generation and narrative reports

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

from .mercator_vertical import MercatorVertical
from .factors import (
    PriceMomentumFactor,
    EarningsQualityFactor,
    ValuationFactor,
    GrowthFactor,
    VolatilityFactor,
    LiquidityFactor
)
from .providers import (
    MercatorAggregationProvider,
    MercatorRiskProvider,
    MercatorExplainabilityProvider
)

__all__ = [
    'MercatorVertical',
    'PriceMomentumFactor',
    'EarningsQualityFactor',
    'ValuationFactor',
    'GrowthFactor',
    'VolatilityFactor',
    'LiquidityFactor',
    'MercatorAggregationProvider',
    'MercatorRiskProvider',
    'MercatorExplainabilityProvider'
]