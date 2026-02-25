"""
Finance Domain — Comparison Node
==================================

Pure-Python multi-ticker comparative analysis.
Computes factor differences, winner-by-factor, ranking order.
No I/O — operates entirely on in-memory Neural Engine results.

Pipeline position: decide → comparison → output_normalizer
Triggered when: intent="comparison" OR 2+ tickers with any screening intent

State inputs:
    - raw_output: dict  — Neural Engine response with ranking.stocks
    - tickers: list     — Ticker symbols being compared
    - intent: str       — User intent

State outputs:
    - comparison_state: dict  — Structured comparison data
    - comparison_mode: bool   — Flag for compose to generate comparison narrative
    - route: str              — "comparison_valid" | "compose" (error)

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Factor keys from Neural Engine output
FACTOR_KEYS = [
    "momentum_z",
    "trend_z",
    "sentiment_z",
    "vola_z",
    "composite_score",
]


def comparison_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate structured comparison state from Neural Engine output.

    Requires raw_output.ranking.stocks with 2+ tickers.
    Computes per-factor deltas, winner-by-factor, and ranking order.
    """
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", [])

    if not stocks or len(stocks) < 2:
        logger.warning(
            f"[comparison_node] Insufficient stocks for comparison: {len(stocks)}"
        )
        state["comparison_mode"] = False
        state["error"] = "Comparison requires at least 2 tickers"
        state["route"] = "compose"
        return state

    logger.info(f"[comparison_node] Comparing {len(stocks)} stocks")

    # --- Extract factor values ---
    tickers = [s.get("ticker") for s in stocks]
    factor_data: Dict[str, Dict[str, float]] = {}

    for key in FACTOR_KEYS:
        factor_data[key] = {}
        for stock in stocks:
            ticker = stock.get("ticker")
            value = stock.get(key)
            factor_data[key][ticker] = float(value) if value is not None else 0.0

    # --- Compute differences / deltas ---
    differences: Dict[str, Dict[str, Any]] = {}

    for key, ticker_values in factor_data.items():
        diff: Dict[str, Any] = dict(ticker_values)  # copy base values

        if len(ticker_values) == 2:
            # Two-ticker: simple delta
            t1, t2 = list(ticker_values.keys())
            v1, v2 = ticker_values[t1], ticker_values[t2]
            delta = abs(v1 - v2)
            denom = max(abs(v1), abs(v2), 0.01)
            diff["delta"] = round(delta, 3)
            diff["delta_pct"] = round((delta / denom) * 100, 2)
        else:
            # Multi-ticker: range
            vals = list(ticker_values.values())
            range_val = max(vals) - min(vals)
            avg_val = sum(vals) / len(vals)
            denom = max(abs(avg_val), 0.01)
            diff["range"] = round(range_val, 3)
            diff["range_pct"] = round((range_val / denom) * 100, 2)

        differences[key] = diff

    # --- Winner by factor ---
    winner_by_factor = {
        key: max(tv, key=tv.get) for key, tv in factor_data.items()
    }

    # --- Ranking by composite_score ---
    sorted_stocks = sorted(
        stocks, key=lambda s: s.get("composite_score", 0), reverse=True
    )
    ranking_order = [s.get("ticker") for s in sorted_stocks]

    # --- Global dispersion ---
    composites = [s.get("composite_score", 0) for s in stocks]
    global_range = max(composites) - min(composites) if composites else 0
    avg_composite = sum(composites) / len(composites) if composites else 0
    global_range_pct = (global_range / max(abs(avg_composite), 0.01)) * 100

    # --- Factor deltas (simplified for frontend) ---
    factor_deltas = {}
    for key, diff in differences.items():
        factor_deltas[key] = diff.get("delta", diff.get("range", 0.0))

    # --- Build comparison state ---
    overall_winner = ranking_order[0] if ranking_order else tickers[0]
    overall_loser = ranking_order[-1] if ranking_order else tickers[-1]

    state["comparison_state"] = {
        "tickers": tickers,
        "winner": overall_winner,
        "loser": overall_loser,
        "differences": differences,
        "winner_by_factor": winner_by_factor,
        "ranking_order": ranking_order,
        "factor_deltas": factor_deltas,
        "range": round(global_range, 3),
        "range_pct": round(global_range_pct, 2),
        "num_tickers": len(tickers),
        "timestamp": datetime.utcnow().isoformat(),
    }
    state["comparison_mode"] = True
    state["route"] = "comparison_valid"

    logger.info(
        f"[comparison_node] Done: winner={overall_winner}, "
        f"ranking={ranking_order}"
    )
    return state
