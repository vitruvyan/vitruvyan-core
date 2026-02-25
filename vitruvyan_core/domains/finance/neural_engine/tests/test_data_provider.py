from typing import Any, Dict, List, Optional, Tuple

from vitruvyan_core.domains.finance.neural_engine.data_provider import TickerDataProvider


class FakePostgresAgent:
    def fetch(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        _ = params
        q = " ".join(sql.split()).lower()

        if "from tickers" in q and "and ticker = any" not in q:
            return [
                {
                    "ticker": "AAPL",
                    "company_name": "Apple Inc.",
                    "instrument_type": "stock",
                    "sector": "Technology",
                    "fund_category": None,
                    "country": "US",
                    "active": True,
                },
                {
                    "ticker": "QQQ",
                    "company_name": "Invesco QQQ",
                    "instrument_type": "etf",
                    "sector": None,
                    "fund_category": "Large Growth",
                    "country": "US",
                    "active": True,
                },
            ]

        if "from tickers" in q and "and ticker = any" in q:
            return [{"ticker": "AAPL"}]

        if "from momentum_logs" in q:
            return [{"ticker": "AAPL", "rsi": 60.0, "momentum_at": "2026-02-20T12:00:00"}]

        if "from trend_logs" in q:
            return [
                {
                    "ticker": "AAPL",
                    "sma_short": 110.0,
                    "sma_medium": 100.0,
                    "trend_at": "2026-02-20T12:00:00",
                }
            ]

        if "from volatility_logs" in q:
            return [{"ticker": "AAPL", "atr": 5.0, "volatility_at": "2026-02-20T12:00:00"}]

        if "from sentiment_scores" in q:
            return [
                {
                    "ticker": "AAPL",
                    "sentiment": 0.45,
                    "sentiment_tag": "positive",
                    "sentiment_at": "2026-02-20T12:00:00",
                }
            ]

        if "from fundamentals" in q:
            return [
                {
                    "ticker": "AAPL",
                    "revenue_growth_yoy": 0.12,
                    "eps_growth_yoy": 0.10,
                    "net_margin": 0.25,
                    "debt_to_equity": 2.0,
                    "free_cash_flow": 150000000.0,
                    "dividend_yield": 0.006,
                }
            ]

        if "from factor_scores" in q:
            return [
                {
                    "ticker": "AAPL",
                    "value": 0.1,
                    "growth": 0.2,
                    "size": 0.3,
                    "quality": 0.4,
                    "academic_momentum": 0.5,
                }
            ]

        if "from vare_risk_analysis" in q:
            return [
                {
                    "ticker": "AAPL",
                    "vare_risk_score": 35.0,
                    "vare_risk_category": "MEDIUM",
                    "vare_confidence": 0.9,
                    "vare_market_risk": 20.0,
                    "vare_volatility_risk": 40.0,
                    "vare_liquidity_risk": 25.0,
                    "vare_correlation_risk": 30.0,
                }
            ]

        return []

    def fetch_one(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
        _ = sql, params
        return {
            "inflation_rate": 2.8,
            "interest_rate": 4.5,
            "market_volatility": 18.0,
        }


def test_get_universe_applies_filters():
    provider = TickerDataProvider(pg_agent=FakePostgresAgent())
    universe = provider.get_universe({"tickers": ["aapl"], "sector": "Technology"})

    assert len(universe) == 1
    assert universe.iloc[0]["entity_id"] == "AAPL"
    assert universe.iloc[0]["stratification_field"] == "Technology"


def test_get_features_merges_layers_and_computes_transforms():
    provider = TickerDataProvider(pg_agent=FakePostgresAgent())
    features = provider.get_features(["AAPL"])
    row = features.iloc[0]

    # Trend strength: (110 - 100) / 100 * 100 = 10
    assert round(float(row["trend"]), 4) == 10.0
    # Debt inversion for "lower debt is better"
    assert round(float(row["debt_to_equity_inv"]), 4) == -2.0
    # Macro overlay is added for every entity row
    assert round(float(row["interest_rate"]), 4) == 4.5
    # VARE fields present for risk adjustment
    assert round(float(row["vare_risk_score"]), 4) == 35.0

