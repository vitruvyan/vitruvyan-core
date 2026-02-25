"""
Ticker Data Provider
====================

Finance implementation of IDataProvider for Neural Engine.
Reads universe and features from PostgreSQL tables populated by finance stack.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from vitruvyan_core.contracts import IDataProvider
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class TickerDataProvider(IDataProvider):
    """
    PostgreSQL-backed finance data provider.

    Source tables (legacy-compatible):
    - tickers
    - momentum_logs
    - trend_logs
    - volatility_logs
    - sentiment_scores
    - fundamentals
    - factor_scores
    - vare_risk_analysis
    - macro_outlook
    """

    def __init__(self, pg_agent: Optional[PostgresAgent] = None):
        self._pg = pg_agent or PostgresAgent()

        self._available_features: List[str] = [
            "momentum",
            "trend",
            "volatility",
            "sentiment",
            "value",
            "growth",
            "size",
            "quality",
            "academic_momentum",
            "revenue_growth_yoy",
            "eps_growth_yoy",
            "net_margin",
            "debt_to_equity_inv",
            "free_cash_flow",
            "dividend_yield",
            "inflation_rate",
            "interest_rate",
            "market_volatility",
            "dark_pool_ratio",
            "dark_pool_z",
            "price_trend_7d",
            "rsi_trend_7d",
            "divergence_score",
            "mtf_consensus",
            "mtf_short_score",
            "mtf_medium_score",
            "mtf_long_score",
            "days_to_earnings",
        ]

        self._metadata_columns: List[str] = [
            "entity_name",
            "stratification_field",
            "instrument_type",
            "sector",
            "fund_category",
            "country",
            "active",
            "sentiment_tag",
            "sentiment_at",
            "timestamp",
            "divergence_type",
            "mtf_alignment",
            "next_earnings_date",
            "vare_risk_score",
            "vare_risk_category",
            "vare_confidence",
            "vare_market_risk",
            "vare_volatility_risk",
            "vare_liquidity_risk",
            "vare_correlation_risk",
        ]

    def get_universe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Return finance universe from `tickers`.

        Output columns include:
        - entity_id
        - stratification_field (sector/fund_category)
        - metadata columns used by service responses
        """
        rows = self._pg.fetch(
            """
            SELECT
                ticker,
                company_name,
                type::text AS instrument_type,
                sector,
                fund_category,
                country,
                active
            FROM tickers
            WHERE active = TRUE
            """
        )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "entity_name",
                    "stratification_field",
                    "instrument_type",
                    "sector",
                    "fund_category",
                    "country",
                    "active",
                ]
            )

        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        df["entity_name"] = df["company_name"].fillna(df["entity_id"])
        df["instrument_type"] = df["instrument_type"].astype(str).str.lower()
        df["stratification_field"] = np.where(
            df["instrument_type"] == "stock",
            df["sector"],
            df["fund_category"],
        )
        df["stratification_field"] = df["stratification_field"].fillna("Unknown")

        filtered = self._apply_universe_filters(df, filters or {})
        return filtered[
            [
                "entity_id",
                "entity_name",
                "stratification_field",
                "instrument_type",
                "sector",
                "fund_category",
                "country",
                "active",
            ]
        ].reset_index(drop=True)

    def get_features(
        self,
        entity_ids: List[str],
        feature_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Return feature matrix for specified tickers.
        """
        normalized_ids = self._normalize_entity_ids(entity_ids)
        if not normalized_ids:
            cols = ["entity_id"] + (feature_names or self._available_features)
            return pd.DataFrame(columns=cols)

        out = pd.DataFrame({"entity_id": normalized_ids})

        # Technical layers
        mom_df = self._fetch_momentum(normalized_ids)
        tr_df = self._fetch_trend(normalized_ids)
        vol_df = self._fetch_volatility(normalized_ids)
        sent_df = self._fetch_sentiment(normalized_ids)

        # Fundamental + factor layers
        fnd_df = self._fetch_fundamentals(normalized_ids)
        fac_df = self._fetch_factor_scores(normalized_ids)
        dp_df = self._fetch_dark_pool(normalized_ids)
        div_df = self._fetch_divergence(normalized_ids)
        mtf_df = self._fetch_multi_timeframe(normalized_ids)
        earn_df = self._fetch_earnings(normalized_ids)

        # Risk (VARE) + macro overlays
        vare_df = self._fetch_vare_scores(normalized_ids)
        macro_payload = self._fetch_latest_macro()

        for df in [mom_df, tr_df, vol_df, sent_df, fnd_df, fac_df, dp_df, div_df, mtf_df, earn_df, vare_df]:
            if not df.empty:
                out = out.merge(df, on="entity_id", how="left")

        if macro_payload:
            out["inflation_rate"] = macro_payload.get("inflation_rate")
            out["interest_rate"] = macro_payload.get("interest_rate")
            out["market_volatility"] = macro_payload.get("market_volatility")
        else:
            out["inflation_rate"] = np.nan
            out["interest_rate"] = np.nan
            out["market_volatility"] = np.nan

        # Unified timestamp for optional time-decay in core engine.
        ts_candidates = [c for c in ["momentum_at", "trend_at", "volatility_at", "sentiment_at"] if c in out.columns]
        if ts_candidates:
            out["timestamp"] = out[ts_candidates].max(axis=1)
        else:
            out["timestamp"] = pd.NaT

        # Cast numeric feature/risk columns.
        numeric_cols = set(self._available_features) | {
            "vare_risk_score",
            "vare_confidence",
            "vare_market_risk",
            "vare_volatility_risk",
            "vare_liquidity_risk",
            "vare_correlation_risk",
        }
        for col in numeric_cols:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")

        if feature_names:
            selected = ["entity_id"]
            for feature in feature_names:
                if feature not in out.columns:
                    out[feature] = np.nan
                selected.append(feature)
            return out[selected]

        return out

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "domain": "finance",
            "entity_type": "financial_instrument",
            "stratification_field": "stratification_field",
            "available_features": list(self._available_features),
            "metadata_columns": list(self._metadata_columns),
            "feature_descriptions": {
                "momentum": "Latest RSI from momentum_logs",
                "trend": "Trend strength from SMA short/medium (%)",
                "volatility": "ATR-based volatility from volatility_logs",
                "sentiment": "Combined sentiment score from sentiment_scores",
                "value": "Factor score value",
                "growth": "Factor score growth",
                "size": "Factor score size",
                "quality": "Factor score quality",
                "academic_momentum": "Academic momentum factor score",
                "revenue_growth_yoy": "Fundamentals revenue growth YoY",
                "eps_growth_yoy": "Fundamentals EPS growth YoY",
                "net_margin": "Fundamentals net margin",
                "debt_to_equity_inv": "Inverted debt-to-equity (higher=better)",
                "free_cash_flow": "Fundamentals free cash flow",
                "dividend_yield": "Fundamentals dividend yield",
                "inflation_rate": "Latest macro outlook inflation rate",
                "interest_rate": "Latest macro outlook interest rate",
                "market_volatility": "Latest macro outlook volatility indicator",
                "dark_pool_ratio": "5-day dark pool ratio average",
                "dark_pool_z": "Dark pool ratio z-score vs 90-day history",
                "price_trend_7d": "7-day close price trend (%)",
                "rsi_trend_7d": "7-day RSI trend (%)",
                "divergence_score": "Abs(price trend - RSI trend)",
                "mtf_consensus": "Weighted consensus across short/medium/long trend",
                "mtf_short_score": "Short timeframe trend score",
                "mtf_medium_score": "Medium timeframe trend score",
                "mtf_long_score": "Long timeframe trend score",
                "days_to_earnings": "Days until next earnings event",
            },
        }

    def validate_entity_ids(self, entity_ids: List[str]) -> Dict[str, bool]:
        normalized = self._normalize_entity_ids(entity_ids)
        if not normalized:
            return {}

        rows = self._pg.fetch(
            """
            SELECT ticker
            FROM tickers
            WHERE active = TRUE
              AND ticker = ANY(%s)
            """,
            (normalized,),
        )
        valid = {str(r["ticker"]).upper() for r in rows}
        return {eid: eid in valid for eid in normalized}

    def _fetch_momentum(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                rsi,
                timestamp AS momentum_at
            FROM momentum_logs
            WHERE ticker = ANY(%s)
              AND rsi IS NOT NULL
            ORDER BY ticker, timestamp DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "momentum", "momentum_at"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        df.rename(columns={"rsi": "momentum"}, inplace=True)
        return df[["entity_id", "momentum", "momentum_at"]]

    def _fetch_trend(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                sma_short,
                sma_medium,
                timestamp AS trend_at
            FROM trend_logs
            WHERE ticker = ANY(%s)
              AND sma_short IS NOT NULL
              AND sma_medium IS NOT NULL
            ORDER BY ticker, timestamp DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "trend", "trend_at"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        sma_medium = pd.to_numeric(df["sma_medium"], errors="coerce")
        sma_short = pd.to_numeric(df["sma_short"], errors="coerce")
        with np.errstate(divide="ignore", invalid="ignore"):
            df["trend"] = np.where(
                sma_medium != 0,
                ((sma_short - sma_medium) / sma_medium) * 100.0,
                np.nan,
            )
        return df[["entity_id", "trend", "trend_at"]]

    def _fetch_volatility(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                atr,
                timestamp AS volatility_at
            FROM volatility_logs
            WHERE ticker = ANY(%s)
              AND atr IS NOT NULL
            ORDER BY ticker, timestamp DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "volatility", "volatility_at"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        df.rename(columns={"atr": "volatility"}, inplace=True)
        return df[["entity_id", "volatility", "volatility_at"]]

    def _fetch_sentiment(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                combined_score AS sentiment,
                sentiment_tag,
                created_at AS sentiment_at
            FROM sentiment_scores
            WHERE ticker = ANY(%s)
              AND combined_score IS NOT NULL
            ORDER BY ticker, created_at DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "sentiment", "sentiment_tag", "sentiment_at"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        return df[["entity_id", "sentiment", "sentiment_tag", "sentiment_at"]]

    def _fetch_fundamentals(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                revenue_growth_yoy,
                eps_growth_yoy,
                net_margin,
                debt_to_equity,
                free_cash_flow,
                dividend_yield
            FROM fundamentals
            WHERE ticker = ANY(%s)
            ORDER BY ticker, date DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "revenue_growth_yoy",
                    "eps_growth_yoy",
                    "net_margin",
                    "debt_to_equity_inv",
                    "free_cash_flow",
                    "dividend_yield",
                ]
            )
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        debt = pd.to_numeric(df["debt_to_equity"], errors="coerce")
        df["debt_to_equity_inv"] = -debt
        return df[
            [
                "entity_id",
                "revenue_growth_yoy",
                "eps_growth_yoy",
                "net_margin",
                "debt_to_equity_inv",
                "free_cash_flow",
                "dividend_yield",
            ]
        ]

    def _fetch_factor_scores(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                value,
                growth,
                size,
                quality,
                momentum AS academic_momentum
            FROM factor_scores
            WHERE ticker = ANY(%s)
            ORDER BY ticker, date DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "value", "growth", "size", "quality", "academic_momentum"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        return df[["entity_id", "value", "growth", "size", "quality", "academic_momentum"]]

    def _fetch_latest_macro(self) -> Optional[Dict[str, Any]]:
        row = self._pg.fetch_one(
            """
            SELECT inflation_rate, interest_rate, market_volatility
            FROM macro_outlook
            ORDER BY date DESC
            LIMIT 1
            """
        )
        return row or None

    def _fetch_dark_pool(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            WITH recent_dark_pool AS (
                SELECT ticker, AVG(dark_pool_ratio) AS avg_dark_pool_ratio_5d
                FROM dark_pool_volume
                WHERE ticker = ANY(%s)
                  AND date >= CURRENT_DATE - INTERVAL '5 days'
                GROUP BY ticker
            ),
            historical_dark_pool AS (
                SELECT ticker,
                       AVG(dark_pool_ratio) AS avg_dark_pool_ratio_90d,
                       STDDEV(dark_pool_ratio) AS std_dark_pool_ratio_90d
                FROM dark_pool_volume
                WHERE ticker = ANY(%s)
                  AND date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY ticker
            )
            SELECT r.ticker,
                   r.avg_dark_pool_ratio_5d AS dark_pool_ratio,
                   CASE WHEN h.std_dark_pool_ratio_90d > 0
                        THEN (r.avg_dark_pool_ratio_5d - h.avg_dark_pool_ratio_90d) / h.std_dark_pool_ratio_90d
                        ELSE NULL END AS dark_pool_z
            FROM recent_dark_pool r
            LEFT JOIN historical_dark_pool h ON r.ticker = h.ticker
            """,
            (list(entity_ids), list(entity_ids)),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "dark_pool_ratio", "dark_pool_z"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        return df[["entity_id", "dark_pool_ratio", "dark_pool_z"]]

    def _fetch_divergence(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        price_rows = self._pg.fetch(
            """
            WITH ranked_prices AS (
                SELECT ticker, dt, close,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY dt DESC) AS rn
                FROM ohlcv_daily
                WHERE ticker = ANY(%s)
                  AND close IS NOT NULL
            )
            SELECT ticker,
                   MAX(CASE WHEN rn = 1 THEN close END) AS close_latest,
                   MAX(CASE WHEN rn = 7 THEN close END) AS close_7d_ago
            FROM ranked_prices
            WHERE rn IN (1, 7)
            GROUP BY ticker
            """,
            (list(entity_ids),),
        )
        rsi_rows = self._pg.fetch(
            """
            WITH ranked_rsi AS (
                SELECT ticker, timestamp, rsi,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp DESC) AS rn
                FROM momentum_logs
                WHERE ticker = ANY(%s)
                  AND rsi IS NOT NULL
            )
            SELECT ticker,
                   MAX(CASE WHEN rn = 1 THEN rsi END) AS rsi_latest,
                   MAX(CASE WHEN rn = 7 THEN rsi END) AS rsi_7d_ago
            FROM ranked_rsi
            WHERE rn IN (1, 7)
            GROUP BY ticker
            """,
            (list(entity_ids),),
        )
        if not price_rows or not rsi_rows:
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "price_trend_7d",
                    "rsi_trend_7d",
                    "divergence_score",
                    "divergence_type",
                ]
            )

        price_df = pd.DataFrame(price_rows)
        rsi_df = pd.DataFrame(rsi_rows)
        price_df["entity_id"] = price_df["ticker"].astype(str).str.upper()
        rsi_df["entity_id"] = rsi_df["ticker"].astype(str).str.upper()
        close_latest = pd.to_numeric(price_df["close_latest"], errors="coerce")
        close_7d_ago = pd.to_numeric(price_df["close_7d_ago"], errors="coerce")
        rsi_latest = pd.to_numeric(rsi_df["rsi_latest"], errors="coerce")
        rsi_7d_ago = pd.to_numeric(rsi_df["rsi_7d_ago"], errors="coerce")
        price_df["price_trend_7d"] = ((close_latest - close_7d_ago) / close_7d_ago) * 100.0
        rsi_df["rsi_trend_7d"] = ((rsi_latest - rsi_7d_ago) / rsi_7d_ago) * 100.0
        out = price_df[["entity_id", "price_trend_7d"]].merge(
            rsi_df[["entity_id", "rsi_trend_7d"]],
            on="entity_id",
            how="outer",
        )
        out["divergence_score"] = (out["price_trend_7d"] - out["rsi_trend_7d"]).abs()

        def _div_type(row: pd.Series) -> Optional[str]:
            p = row.get("price_trend_7d")
            r = row.get("rsi_trend_7d")
            if pd.isna(p) or pd.isna(r):
                return None
            if p < -1 and r > 1:
                return "bullish"
            if p > 1 and r < -1:
                return "bearish"
            return None

        out["divergence_type"] = out.apply(_div_type, axis=1)
        return out

    def _fetch_multi_timeframe(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                short_trend,
                medium_trend,
                long_trend
            FROM trend_logs
            WHERE ticker = ANY(%s)
              AND short_trend IS NOT NULL
              AND medium_trend IS NOT NULL
              AND long_trend IS NOT NULL
            ORDER BY ticker, timestamp DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "mtf_consensus",
                    "mtf_short_score",
                    "mtf_medium_score",
                    "mtf_long_score",
                    "mtf_alignment",
                ]
            )
        mtf = pd.DataFrame(rows)
        mtf["entity_id"] = mtf["ticker"].astype(str).str.upper()

        def score(v: Any) -> float:
            if pd.isna(v):
                return 0.0
            s = str(v).lower()
            if s in {"bullish", "uptrend", "strong_uptrend"}:
                return 1.0
            if s in {"bearish", "downtrend", "strong_downtrend"}:
                return -1.0
            return 0.0

        mtf["mtf_short_score"] = mtf["short_trend"].map(score)
        mtf["mtf_medium_score"] = mtf["medium_trend"].map(score)
        mtf["mtf_long_score"] = mtf["long_trend"].map(score)
        mtf["mtf_consensus"] = (
            mtf["mtf_short_score"] * 0.5
            + mtf["mtf_medium_score"] * 0.3
            + mtf["mtf_long_score"] * 0.2
        )

        def classify(v: Any) -> Optional[str]:
            if pd.isna(v):
                return None
            if v > 0.3:
                return "bullish"
            if v < -0.3:
                return "bearish"
            return "mixed"

        mtf["mtf_alignment"] = mtf["mtf_consensus"].map(classify)
        return mtf[
            [
                "entity_id",
                "mtf_consensus",
                "mtf_short_score",
                "mtf_medium_score",
                "mtf_long_score",
                "mtf_alignment",
            ]
        ]

    def _fetch_earnings(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT ticker,
                   MIN(earnings_date) AS next_earnings_date,
                   MIN(earnings_date) - CURRENT_DATE AS days_to_earnings
            FROM earnings_calendar
            WHERE ticker = ANY(%s)
              AND earnings_date >= CURRENT_DATE
            GROUP BY ticker
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(columns=["entity_id", "next_earnings_date", "days_to_earnings"])
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        return df[["entity_id", "next_earnings_date", "days_to_earnings"]]

    def _fetch_vare_scores(self, entity_ids: Sequence[str]) -> pd.DataFrame:
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                overall_risk AS vare_risk_score,
                risk_category AS vare_risk_category,
                confidence AS vare_confidence,
                market_risk AS vare_market_risk,
                volatility_risk AS vare_volatility_risk,
                liquidity_risk AS vare_liquidity_risk,
                correlation_risk AS vare_correlation_risk
            FROM vare_risk_analysis
            WHERE ticker = ANY(%s)
            ORDER BY ticker, created_at DESC
            """,
            (list(entity_ids),),
        )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "entity_id",
                    "vare_risk_score",
                    "vare_risk_category",
                    "vare_confidence",
                    "vare_market_risk",
                    "vare_volatility_risk",
                    "vare_liquidity_risk",
                    "vare_correlation_risk",
                ]
            )
        df = pd.DataFrame(rows)
        df["entity_id"] = df["ticker"].astype(str).str.upper()
        return df[
            [
                "entity_id",
                "vare_risk_score",
                "vare_risk_category",
                "vare_confidence",
                "vare_market_risk",
                "vare_volatility_risk",
                "vare_liquidity_risk",
                "vare_correlation_risk",
            ]
        ]

    def _apply_universe_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        out = df.copy()

        ticker_filter = self._normalize_entity_ids(
            self._ensure_list(filters.get("tickers"))
            + self._ensure_list(filters.get("entity_ids"))
            + self._ensure_list(filters.get("universe"))
        )
        if ticker_filter:
            out = out[out["entity_id"].isin(ticker_filter)]

        sector = filters.get("sector")
        if sector:
            sector_l = str(sector).strip().lower()
            out = out[
                out["sector"].fillna("").str.lower().eq(sector_l)
                | out["stratification_field"].fillna("").str.lower().eq(sector_l)
            ]

        instrument_type = filters.get("type")
        if instrument_type:
            t_l = str(instrument_type).strip().lower()
            out = out[out["instrument_type"].fillna("").str.lower().eq(t_l)]

        country = filters.get("country")
        if country:
            c_l = str(country).strip().lower()
            out = out[out["country"].fillna("").str.lower().eq(c_l)]

        return out

    @staticmethod
    def _normalize_entity_ids(entity_ids: Iterable[Any]) -> List[str]:
        out: List[str] = []
        for item in entity_ids:
            if item is None:
                continue
            value = str(item).strip().upper()
            if value:
                out.append(value)
        return out

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]
