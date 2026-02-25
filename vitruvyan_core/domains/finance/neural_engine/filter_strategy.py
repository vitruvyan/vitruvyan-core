"""
Financial Filter Strategy
=========================

Finance implementation of IFilterStrategy.
Ports legacy Neural Engine filters from monolith engine_core.py
into contract-based orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from vitruvyan_core.contracts import IFilterStrategy
from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class FinancialFilterStrategy(IFilterStrategy):
    """Finance-specific screening and guardrail filters."""

    def __init__(self, pg_agent: Optional[PostgresAgent] = None):
        self._pg = pg_agent or PostgresAgent()

    def apply_filters(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any],
        context: Dict[str, Any] | None = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        out = df.copy()
        diagnostics: Dict[str, Any] = {
            "applied": [],
            "removed": {},
            "initial_count": len(out),
        }

        if out.empty:
            diagnostics["final_count"] = 0
            return out, diagnostics

        # Function P: smart money flow
        if filters.get("smart_money_flow"):
            out = self.get_dark_pool_z(out)
            before = len(out)
            out = self.apply_smart_money_filter(
                out,
                threshold=float(filters.get("smart_money_threshold", 1.5)),
            )
            diagnostics["applied"].append("smart_money_flow")
            diagnostics["removed"]["smart_money_flow"] = before - len(out)

        # Function H: divergence
        if filters.get("divergence_detection"):
            out = self.get_divergence_score(out)
            before = len(out)
            out = out[
                out["divergence_type"].notna() & out["divergence_score"].notna()
            ].copy()
            diagnostics["applied"].append("divergence_detection")
            diagnostics["removed"]["divergence_detection"] = before - len(out)

        # Function I: multi-timeframe consensus
        if filters.get("multi_timeframe_filter"):
            out = self.get_multi_timeframe_consensus(out)
            before = len(out)
            out = out[
                out["mtf_consensus"].notna() & (out["mtf_consensus"] > 0.3)
            ].copy()
            diagnostics["applied"].append("multi_timeframe_filter")
            diagnostics["removed"]["multi_timeframe_filter"] = before - len(out)

        # Function F: momentum breakout
        if filters.get("momentum_breakout"):
            before = len(out)
            out = out[out.get("momentum_z", pd.Series(index=out.index)).fillna(-999) > 2.0].copy()
            diagnostics["applied"].append("momentum_breakout")
            diagnostics["removed"]["momentum_breakout"] = before - len(out)

        # Function G: value screening
        if filters.get("value_screening"):
            before = len(out)
            out = out[
                (out.get("value_z", out.get("value", pd.Series(index=out.index))).fillna(-999) > 0.0)
                & (out.get("quality_z", out.get("quality", pd.Series(index=out.index))).fillna(-999) > -0.5)
            ].copy()
            diagnostics["applied"].append("value_screening")
            diagnostics["removed"]["value_screening"] = before - len(out)

        # Earnings safety
        earnings_days = filters.get("earnings_safety_days")
        if earnings_days is not None:
            out = self.get_days_to_earnings(out)
            before = len(out)
            out = self.apply_earnings_safety_filter(out, int(earnings_days))
            diagnostics["applied"].append("earnings_safety")
            diagnostics["removed"]["earnings_safety"] = before - len(out)

        # Function J: portfolio diversification
        portfolio_tickers = filters.get("portfolio_diversification") or []
        if portfolio_tickers:
            before = len(out)
            out = self.apply_portfolio_diversification(
                out,
                portfolio_tickers=[str(x).upper() for x in portfolio_tickers],
                correlation_threshold=float(filters.get("correlation_threshold", 0.3)),
            )
            diagnostics["applied"].append("portfolio_diversification")
            diagnostics["removed"]["portfolio_diversification"] = before - len(out)

        # Function K: macro sensitivity
        macro_factor = filters.get("macro_factor")
        if macro_factor:
            before = len(out)
            out = self.apply_macro_sensitivity_filter(out, macro_factor=str(macro_factor))
            diagnostics["applied"].append("macro_sensitivity")
            diagnostics["removed"]["macro_sensitivity"] = before - len(out)

        diagnostics["final_count"] = len(out)
        return out, diagnostics

    def apply_guardrails_and_topk(
        self,
        df: pd.DataFrame,
        top_k: int = 10,
        bypass_sector_cap: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        work = df.copy()
        type_col = "instrument_type" if "instrument_type" in work.columns else "type"
        group_col = "stratification_field" if "stratification_field" in work.columns else "sector"

        stocks = work[work[type_col].eq("stock")].sort_values("composite_score", ascending=False)
        etf = work[work[type_col].eq("etf")].sort_values("composite_score", ascending=False)
        fund = work[work[type_col].eq("fund")].sort_values("composite_score", ascending=False)

        def cap_by(gdf: pd.DataFrame, cap: int, flexible: bool = False) -> pd.DataFrame:
            if gdf.empty:
                return gdf
            rows: List[dict] = []
            counts: Dict[str, int] = {}
            for _, row in gdf.iterrows():
                key = str(row.get(group_col) or "unknown")
                if not flexible and counts.get(key, 0) >= cap:
                    continue
                rows.append(row.to_dict())
                counts[key] = counts.get(key, 0) + 1
                if len(rows) >= top_k:
                    break
            if flexible and len(rows) < top_k:
                used = {r.get("entity_id") for r in rows}
                for _, row in gdf.iterrows():
                    if row.get("entity_id") in used:
                        continue
                    rows.append(row.to_dict())
                    if len(rows) >= top_k:
                        break
            return pd.DataFrame(rows)

        if bypass_sector_cap:
            stocks_top = stocks.head(top_k)
        else:
            stocks_top = cap_by(stocks, cap=2, flexible=False)
        etf_top = cap_by(etf, cap=2, flexible=True)
        fund_top = cap_by(fund, cap=2, flexible=True)

        return stocks_top, etf_top, fund_top

    def get_dark_pool_z(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if out.empty:
            return out
        rows = self._pg.fetch(
            """
            WITH recent_dark_pool AS (
                SELECT ticker, AVG(dark_pool_ratio) AS avg_dark_pool_ratio_5d
                FROM dark_pool_volume
                WHERE date >= CURRENT_DATE - INTERVAL '5 days'
                GROUP BY ticker
            ),
            historical_dark_pool AS (
                SELECT ticker,
                       AVG(dark_pool_ratio) AS avg_dark_pool_ratio_90d,
                       STDDEV(dark_pool_ratio) AS std_dark_pool_ratio_90d
                FROM dark_pool_volume
                WHERE date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY ticker
            )
            SELECT r.ticker,
                   r.avg_dark_pool_ratio_5d AS dark_pool_ratio,
                   CASE WHEN h.std_dark_pool_ratio_90d > 0
                        THEN (r.avg_dark_pool_ratio_5d - h.avg_dark_pool_ratio_90d) / h.std_dark_pool_ratio_90d
                        ELSE NULL END AS dark_pool_z
            FROM recent_dark_pool r
            LEFT JOIN historical_dark_pool h ON r.ticker = h.ticker
            """
        )
        if not rows:
            out["dark_pool_ratio"] = np.nan
            out["dark_pool_z"] = np.nan
            return out
        dp = pd.DataFrame(rows)
        dp["entity_id"] = dp["ticker"].astype(str).str.upper()
        return out.merge(dp[["entity_id", "dark_pool_ratio", "dark_pool_z"]], on="entity_id", how="left")

    def apply_smart_money_filter(self, df: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
        out = df.copy()
        if "dark_pool_z" not in out.columns:
            return out
        return out[out["dark_pool_z"].notna() & (out["dark_pool_z"] > threshold)].copy()

    def get_days_to_earnings(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if out.empty:
            return out
        rows = self._pg.fetch(
            """
            SELECT ticker,
                   MIN(earnings_date) AS next_earnings_date,
                   MIN(earnings_date) - CURRENT_DATE AS days_to_earnings
            FROM earnings_calendar
            WHERE earnings_date >= CURRENT_DATE
            GROUP BY ticker
            """
        )
        if not rows:
            out["next_earnings_date"] = pd.NaT
            out["days_to_earnings"] = np.nan
            return out
        edf = pd.DataFrame(rows)
        edf["entity_id"] = edf["ticker"].astype(str).str.upper()
        return out.merge(
            edf[["entity_id", "next_earnings_date", "days_to_earnings"]],
            on="entity_id",
            how="left",
        )

    def apply_earnings_safety_filter(self, df: pd.DataFrame, days_buffer: int = 7) -> pd.DataFrame:
        out = df.copy()
        if "days_to_earnings" not in out.columns:
            return out
        return out[(out["days_to_earnings"].isna()) | (out["days_to_earnings"] > days_buffer)].copy()

    def get_divergence_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if out.empty:
            return out

        price_rows = self._pg.fetch(
            """
            WITH ranked_prices AS (
                SELECT ticker, dt, close,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY dt DESC) AS rn
                FROM ohlcv_daily
                WHERE close IS NOT NULL
            )
            SELECT ticker,
                   MAX(CASE WHEN rn = 1 THEN close END) AS close_latest,
                   MAX(CASE WHEN rn = 7 THEN close END) AS close_7d_ago
            FROM ranked_prices
            WHERE rn IN (1, 7)
            GROUP BY ticker
            HAVING MAX(CASE WHEN rn = 1 THEN close END) IS NOT NULL
               AND MAX(CASE WHEN rn = 7 THEN close END) IS NOT NULL
            """
        )
        rsi_rows = self._pg.fetch(
            """
            WITH ranked_rsi AS (
                SELECT ticker, timestamp, rsi,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp DESC) AS rn
                FROM momentum_logs
                WHERE rsi IS NOT NULL
            )
            SELECT ticker,
                   MAX(CASE WHEN rn = 1 THEN rsi END) AS rsi_latest,
                   MAX(CASE WHEN rn = 7 THEN rsi END) AS rsi_7d_ago
            FROM ranked_rsi
            WHERE rn IN (1, 7)
            GROUP BY ticker
            HAVING MAX(CASE WHEN rn = 1 THEN rsi END) IS NOT NULL
               AND MAX(CASE WHEN rn = 7 THEN rsi END) IS NOT NULL
            """
        )

        if not price_rows or not rsi_rows:
            out["price_trend_7d"] = np.nan
            out["rsi_trend_7d"] = np.nan
            out["divergence_score"] = np.nan
            out["divergence_type"] = None
            return out

        price_df = pd.DataFrame(price_rows)
        rsi_df = pd.DataFrame(rsi_rows)
        price_df["entity_id"] = price_df["ticker"].astype(str).str.upper()
        rsi_df["entity_id"] = rsi_df["ticker"].astype(str).str.upper()

        close_latest = pd.to_numeric(price_df["close_latest"], errors="coerce")
        close_7d_ago = pd.to_numeric(price_df["close_7d_ago"], errors="coerce")
        price_df["price_trend_7d"] = ((close_latest - close_7d_ago) / close_7d_ago) * 100.0

        rsi_latest = pd.to_numeric(rsi_df["rsi_latest"], errors="coerce")
        rsi_7d_ago = pd.to_numeric(rsi_df["rsi_7d_ago"], errors="coerce")
        rsi_df["rsi_trend_7d"] = ((rsi_latest - rsi_7d_ago) / rsi_7d_ago) * 100.0

        out = out.merge(price_df[["entity_id", "price_trend_7d"]], on="entity_id", how="left")
        out = out.merge(rsi_df[["entity_id", "rsi_trend_7d"]], on="entity_id", how="left")
        out["divergence_score"] = (out["price_trend_7d"] - out["rsi_trend_7d"]).abs()

        def classify(row: pd.Series) -> Optional[str]:
            p = row.get("price_trend_7d")
            r = row.get("rsi_trend_7d")
            if pd.isna(p) or pd.isna(r):
                return None
            if p < -1 and r > 1:
                return "bullish"
            if p > 1 and r < -1:
                return "bearish"
            return None

        out["divergence_type"] = out.apply(classify, axis=1)
        return out

    def get_multi_timeframe_consensus(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if out.empty:
            return out
        rows = self._pg.fetch(
            """
            SELECT DISTINCT ON (ticker)
                ticker,
                short_trend,
                medium_trend,
                long_trend
            FROM trend_logs
            WHERE short_trend IS NOT NULL
              AND medium_trend IS NOT NULL
              AND long_trend IS NOT NULL
            ORDER BY ticker, timestamp DESC
            """
        )
        if not rows:
            out["mtf_consensus"] = np.nan
            out["mtf_short_score"] = np.nan
            out["mtf_medium_score"] = np.nan
            out["mtf_long_score"] = np.nan
            out["mtf_alignment"] = None
            return out

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

        return out.merge(
            mtf[
                [
                    "entity_id",
                    "mtf_consensus",
                    "mtf_short_score",
                    "mtf_medium_score",
                    "mtf_long_score",
                    "mtf_alignment",
                ]
            ],
            on="entity_id",
            how="left",
        )

    def apply_portfolio_diversification(
        self,
        df: pd.DataFrame,
        portfolio_tickers: List[str],
        correlation_threshold: float = 0.3,
    ) -> pd.DataFrame:
        out = df.copy()
        if out.empty or not portfolio_tickers:
            out["avg_correlation"] = np.nan
            return out

        all_tickers = list(set(out["entity_id"].astype(str).str.upper().tolist() + portfolio_tickers))

        rows = self._pg.fetch(
            """
            WITH daily_returns AS (
                SELECT ticker,
                       dt,
                       (close - LAG(close) OVER (PARTITION BY ticker ORDER BY dt)) /
                       LAG(close) OVER (PARTITION BY ticker ORDER BY dt) AS return
                FROM ohlcv_daily
                WHERE ticker = ANY(%s)
                  AND dt >= CURRENT_DATE - INTERVAL '90 days'
                  AND close IS NOT NULL
            )
            SELECT ticker, dt, return
            FROM daily_returns
            WHERE return IS NOT NULL
            ORDER BY ticker, dt
            """,
            (all_tickers,),
        )

        if not rows:
            out["avg_correlation"] = np.nan
            return out

        rdf = pd.DataFrame(rows)
        pivot = rdf.pivot(index="dt", columns="ticker", values="return")
        corr = pivot.corr()

        correlations: List[Optional[float]] = []
        for ticker in out["entity_id"].astype(str).str.upper().tolist():
            if ticker not in corr.columns:
                correlations.append(np.nan)
                continue
            vals: List[float] = []
            for p in portfolio_tickers:
                if p in corr.columns and p != ticker:
                    v = corr.loc[ticker, p]
                    if pd.notna(v):
                        vals.append(float(v))
            correlations.append(float(np.mean(vals)) if vals else np.nan)

        out["avg_correlation"] = correlations
        return out[out["avg_correlation"].isna() | (out["avg_correlation"] < correlation_threshold)].copy()

    def apply_macro_sensitivity_filter(
        self,
        df: pd.DataFrame,
        macro_factor: str,
        rate_threshold: float = 4.0,
        volatility_threshold: float = 20.0,
    ) -> pd.DataFrame:
        out = df.copy()
        if out.empty:
            return out

        macro_factor = str(macro_factor).lower().strip()

        # Ensure macro columns are present; if not, skip.
        for col in ("inflation_rate", "interest_rate", "market_volatility"):
            if col not in out.columns:
                return out

        category_col = "stratification_field" if "stratification_field" in out.columns else "sector"
        categories = out[category_col].fillna("").astype(str)

        current_rates = pd.to_numeric(out["interest_rate"], errors="coerce").dropna()
        current_vix = pd.to_numeric(out["market_volatility"], errors="coerce").dropna()

        rates = float(current_rates.iloc[0]) if not current_rates.empty else None
        vix = float(current_vix.iloc[0]) if not current_vix.empty else None

        if macro_factor == "inflation":
            target = {"energy", "materials", "real estate", "consumer staples"}
            return out[categories.str.lower().isin(target)].copy()

        if macro_factor == "rates":
            if rates is None:
                return out
            if rates < rate_threshold:
                target = {"technology", "consumer discretionary", "communication services", "real estate"}
            else:
                target = {"financials", "energy"}
            return out[categories.str.lower().isin(target)].copy()

        if macro_factor == "volatility":
            if vix is None or vix <= volatility_threshold:
                return out
            target = {"utilities", "consumer staples", "healthcare"}
            return out[categories.str.lower().isin(target)].copy()

        if macro_factor == "dollar":
            # Placeholder: no DXY series in current contract payload.
            return out

        return out

