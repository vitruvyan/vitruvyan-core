"""
Mercator Financial Factors

Concrete implementations of AbstractFactor for financial analysis.
Each factor computes a quantitative signal for investment decision-making.

Factors implemented:
- PriceMomentumFactor: Price-based momentum signals
- EarningsQualityFactor: Quality of earnings and cash flow
- ValuationFactor: Relative valuation metrics
- GrowthFactor: Growth potential indicators
- VolatilityFactor: Risk/volatility measures
- LiquidityFactor: Trading liquidity assessment

Author: Vitruvyan Development Team
Created: December 30, 2025
"""

import pandas as pd
import numpy as np
from typing import Any
from vitruvyan_core.core.cognitive.neural_engine import AbstractFactor


class PriceMomentumFactor(AbstractFactor):
    """
    Price Momentum Factor

    Measures price-based momentum signals including:
    - Short-term price momentum (1-3 months)
    - Medium-term trend (3-12 months)
    - Acceleration/deceleration patterns

    Higher values indicate stronger upward momentum.
    """

    @property
    def name(self) -> str:
        return "price_momentum"

    @property
    def higher_is_better(self) -> bool:
        return True

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute price momentum score

        Required columns in entities DataFrame:
        - current_price: Current stock price
        - price_1m: Price 1 month ago
        - price_3m: Price 3 months ago
        - price_12m: Price 12 months ago
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                current = entity.get('current_price', 0)
                p1m = entity.get('price_1m', current)
                p3m = entity.get('price_3m', current)
                p12m = entity.get('price_12m', current)

                if current <= 0 or p1m <= 0 or p3m <= 0 or p12m <= 0:
                    scores.append(0.0)
                    continue

                # Short-term momentum (1-month return)
                mom_1m = (current / p1m) - 1

                # Medium-term momentum (3-month return)
                mom_3m = (current / p3m) - 1

                # Long-term trend (12-month return)
                mom_12m = (current / p12m) - 1

                # Weighted momentum score
                # Recent performance gets higher weight
                momentum_score = (
                    0.5 * mom_1m +      # 50% weight on recent month
                    0.3 * mom_3m +      # 30% weight on quarter
                    0.2 * mom_12m      # 20% weight on year
                )

                scores.append(float(momentum_score))

            except (KeyError, ZeroDivisionError, TypeError):
                scores.append(0.0)

        return pd.Series(scores, index=entities.index)


class EarningsQualityFactor(AbstractFactor):
    """
    Earnings Quality Factor

    Assesses the quality and sustainability of earnings including:
    - Cash flow coverage of earnings
    - Accruals quality
    - Earnings persistence
    - Accounting conservatism

    Higher values indicate higher quality earnings.
    """

    @property
    def name(self) -> str:
        return "earnings_quality"

    @property
    def higher_is_better(self) -> bool:
        return True

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute earnings quality score

        Required columns:
        - net_income: Net income
        - cash_from_operations: Operating cash flow
        - total_assets: Total assets
        - earnings_volatility: Standard deviation of earnings over time
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                net_income = entity.get('net_income', 0)
                cfo = entity.get('cash_from_operations', 0)
                total_assets = entity.get('total_assets', 1)  # Avoid division by zero
                earnings_vol = entity.get('earnings_volatility', 0.5)

                if total_assets <= 0:
                    scores.append(0.0)
                    continue

                # Cash flow to earnings ratio (quality indicator)
                if net_income != 0:
                    cash_coverage = cfo / abs(net_income)
                else:
                    cash_coverage = 1.0 if cfo > 0 else -1.0

                # Earnings persistence (inverse of volatility, normalized)
                persistence = 1.0 / (1.0 + earnings_vol)

                # Return on assets (profitability control)
                roa = net_income / total_assets

                # Combined quality score
                quality_score = (
                    0.4 * min(max(cash_coverage, -2), 2) +  # Cap at reasonable range
                    0.4 * persistence +
                    0.2 * min(max(roa, -0.5), 0.5)  # Cap ROA
                )

                scores.append(float(quality_score))

            except (KeyError, TypeError):
                scores.append(0.0)

        return pd.Series(scores, index=entities.index)


class ValuationFactor(AbstractFactor):
    """
    Valuation Factor

    Measures relative valuation attractiveness:
    - Price-to-earnings ratio
    - Price-to-book ratio
    - Enterprise value multiples
    - Dividend yield

    Lower values indicate more attractive valuations (higher_is_better=False).
    """

    @property
    def name(self) -> str:
        return "valuation"

    @property
    def higher_is_better(self) -> bool:
        return False  # Lower valuations are better

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute valuation attractiveness score

        Required columns:
        - market_cap: Market capitalization
        - net_income: Net income (for P/E)
        - book_value: Book value of equity (for P/B)
        - enterprise_value: EV (market cap + debt - cash)
        - ebitda: EBITDA
        - dividend_yield: Current dividend yield
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                market_cap = entity.get('market_cap', 0)
                net_income = entity.get('net_income', 0)
                book_value = entity.get('book_value', 0)
                ev = entity.get('enterprise_value', market_cap)
                ebitda = entity.get('ebitda', 0)
                div_yield = entity.get('dividend_yield', 0)

                valuation_scores = []

                # P/E ratio (lower is better, but avoid negative earnings)
                if net_income > 0 and market_cap > 0:
                    pe_ratio = market_cap / net_income
                    # Normalize: cap at reasonable range and invert (lower PE = higher score)
                    pe_score = 1.0 / (1.0 + min(pe_ratio / 50, 5))  # Max PE of 250 gets score ~0.17
                    valuation_scores.append(pe_score)

                # P/B ratio
                if book_value > 0 and market_cap > 0:
                    pb_ratio = market_cap / book_value
                    pb_score = 1.0 / (1.0 + min(pb_ratio / 10, 5))  # Max P/B of 50 gets score ~0.17
                    valuation_scores.append(pb_score)

                # EV/EBITDA
                if ebitda > 0 and ev > 0:
                    ev_ebitda = ev / ebitda
                    ev_score = 1.0 / (1.0 + min(ev_ebitda / 50, 5))  # Max EV/EBITDA of 250
                    valuation_scores.append(ev_score)

                # Dividend yield (higher yield = better, but cap at reasonable levels)
                if div_yield > 0:
                    yield_score = min(div_yield / 0.1, 1.0)  # Cap at 10% yield
                    valuation_scores.append(yield_score)

                # Average of available valuation metrics
                if valuation_scores:
                    avg_score = np.mean(valuation_scores)
                else:
                    avg_score = 0.0

                scores.append(float(avg_score))

            except (KeyError, TypeError, ZeroDivisionError):
                scores.append(0.0)

        return pd.Series(scores, index=entities.index)


class GrowthFactor(AbstractFactor):
    """
    Growth Factor

    Measures growth potential and momentum:
    - Revenue growth rates
    - Earnings growth rates
    - Analyst growth estimates
    - Market expectations

    Higher values indicate stronger growth prospects.
    """

    @property
    def name(self) -> str:
        return "growth"

    @property
    def higher_is_better(self) -> bool:
        return True

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute growth potential score

        Required columns:
        - revenue_growth_1y: 1-year revenue growth
        - revenue_growth_3y: 3-year revenue growth
        - eps_growth_1y: 1-year EPS growth
        - eps_growth_3y: 3-year EPS growth
        - analyst_growth_est: Analyst growth estimates
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                rev_g_1y = entity.get('revenue_growth_1y', 0)
                rev_g_3y = entity.get('revenue_growth_3y', 0)
                eps_g_1y = entity.get('eps_growth_1y', 0)
                eps_g_3y = entity.get('eps_growth_3y', 0)
                analyst_est = entity.get('analyst_growth_est', 0)

                growth_scores = []

                # Revenue growth (weighted average)
                if rev_g_1y != 0 or rev_g_3y != 0:
                    rev_growth = (0.6 * rev_g_1y + 0.4 * rev_g_3y) / 100  # Convert to decimal
                    growth_scores.append(min(max(rev_growth, -0.5), 0.5))  # Cap at +/-50%

                # Earnings growth
                if eps_g_1y != 0 or eps_g_3y != 0:
                    eps_growth = (0.6 * eps_g_1y + 0.4 * eps_g_3y) / 100
                    growth_scores.append(min(max(eps_growth, -0.5), 0.5))

                # Analyst estimates
                if analyst_est != 0:
                    analyst_growth = analyst_est / 100
                    growth_scores.append(min(max(analyst_growth, -0.5), 0.5))

                # Average growth score
                if growth_scores:
                    avg_growth = np.mean(growth_scores)
                else:
                    avg_growth = 0.0

                scores.append(float(avg_growth))

            except (KeyError, TypeError):
                scores.append(0.0)

        return pd.Series(scores, index=entities.index)


class VolatilityFactor(AbstractFactor):
    """
    Volatility Factor

    Measures risk through price volatility:
    - Historical volatility
    - Beta relative to market
    - Maximum drawdown
    - Value at risk measures

    Lower values indicate lower risk (higher_is_better=False).
    """

    @property
    def name(self) -> str:
        return "volatility"

    @property
    def higher_is_better(self) -> bool:
        return False  # Lower volatility is better

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute volatility/risk score

        Required columns:
        - historical_volatility: 252-day volatility
        - beta: Market beta
        - max_drawdown: Maximum peak-to-trough decline
        - var_95: 95% Value at Risk
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                hist_vol = entity.get('historical_volatility', 0.3)  # Default 30%
                beta = entity.get('beta', 1.0)
                max_dd = entity.get('max_drawdown', 0.2)  # Default 20%
                var_95 = abs(entity.get('var_95', 0.1))  # Default 10%, take absolute

                # Normalize each risk measure to 0-1 scale
                vol_score = min(hist_vol / 1.0, 1.0)  # Cap at 100% vol
                beta_score = min(abs(beta - 1.0) / 2.0, 1.0)  # Distance from beta=1
                dd_score = min(max_dd / 1.0, 1.0)  # Cap at 100% drawdown
                var_score = min(var_95 / 0.5, 1.0)  # Cap at 50% VaR

                # Average risk score (higher = more risky)
                risk_score = np.mean([vol_score, beta_score, dd_score, var_score])

                scores.append(float(risk_score))

            except (KeyError, TypeError):
                scores.append(0.3)  # Default moderate risk

        return pd.Series(scores, index=entities.index)


class LiquidityFactor(AbstractFactor):
    """
    Liquidity Factor

    Measures trading liquidity and market efficiency:
    - Average daily volume
    - Bid-ask spread
    - Market capitalization
    - Trading frequency

    Higher values indicate better liquidity.
    """

    @property
    def name(self) -> str:
        return "liquidity"

    @property
    def higher_is_better(self) -> bool:
        return True

    def compute(self, entities: pd.DataFrame, context: Any) -> pd.Series:
        """
        Compute liquidity score

        Required columns:
        - avg_daily_volume: Average daily trading volume
        - bid_ask_spread: Average bid-ask spread
        - market_cap: Market capitalization
        - shares_outstanding: Shares outstanding
        """
        scores = []

        for idx, entity in entities.iterrows():
            try:
                avg_volume = entity.get('avg_daily_volume', 0)
                spread = entity.get('bid_ask_spread', 0.01)  # Default 1%
                market_cap = entity.get('market_cap', 0)
                shares_out = entity.get('shares_outstanding', 1)

                liquidity_scores = []

                # Volume score (higher volume = more liquid)
                if market_cap > 0:
                    volume_ratio = avg_volume / market_cap
                    vol_score = min(volume_ratio * 100, 1.0)  # Cap at 1% daily volume/market cap
                    liquidity_scores.append(vol_score)

                # Spread score (tighter spread = more liquid)
                spread_score = 1.0 / (1.0 + spread * 100)  # Invert and normalize
                liquidity_scores.append(spread_score)

                # Market cap score (larger companies tend to be more liquid)
                if market_cap > 0:
                    # Log scale for market cap (billions)
                    mc_score = min(np.log10(market_cap / 1e9 + 1) / 3, 1.0)
                    liquidity_scores.append(mc_score)

                # Average liquidity score
                if liquidity_scores:
                    avg_liquidity = np.mean(liquidity_scores)
                else:
                    avg_liquidity = 0.0

                scores.append(float(avg_liquidity))

            except (KeyError, TypeError):
                scores.append(0.0)

        return pd.Series(scores, index=entities.index)