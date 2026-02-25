"""
Finance Domain — Allocation Node
==================================

Portfolio allocation optimization with multiple strategies.
Computes allocation weights and optionally persists to PostgreSQL.

Pipeline position: decide → allocation → output_normalizer
Triggered when: intent="allocate"

State inputs:
    - tickers: list       — Ticker symbols for allocation
    - amount: float       — Investment amount (default $10,000)
    - options: dict       — {strategy: str} (equal_weight, risk_parity, etc.)
    - weaver_context: dict — Semantic context from Pattern Weavers
    - numerical_panel: list — Neural Engine z-scores (if available)
    - user_id: str        — User identifier
    - input_text: str     — Original user query

State outputs:
    - allocation_data: dict — {weights, mode, rationale, amount, currency, ...}

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Supported allocation strategies
STRATEGIES = {
    "equal_weight",
    "risk_parity",
    "max_sharpe",
    "sector_focused",
    "risk_adjusted",
}


def allocation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute portfolio allocation weights for given tickers.

    Strategies:
        equal_weight   — Uniform distribution across tickers
        risk_parity    — Weight inversely proportional to volatility z-score
        max_sharpe     — Weight proportional to composite_score
        sector_focused — Boost sector leaders (from weaver_context)
        risk_adjusted  — Blend momentum and inverse-volatility
    """
    tickers = state.get("tickers", [])
    amount = state.get("amount", 10000.0)
    options = state.get("options", {})
    strategy = options.get("strategy", "equal_weight")
    user_id = state.get("user_id", "unknown")

    logger.info(
        f"[allocation_node] tickers={len(tickers)}, amount=${amount}, "
        f"strategy={strategy}, user={user_id}"
    )

    if not tickers:
        logger.warning("[allocation_node] No tickers provided")
        state["allocation_data"] = {
            "error": "No tickers provided",
            "weights": {},
            "mode": "error",
            "rationale": "Cannot allocate without tickers",
            "amount": amount,
            "currency": "USD",
        }
        return state

    if strategy not in STRATEGIES:
        logger.info(
            f"[allocation_node] Unknown strategy '{strategy}', "
            f"falling back to equal_weight"
        )
        strategy = "equal_weight"

    start = time.time()

    try:
        weights = _compute_weights(state, tickers, strategy)

        # Scale weights to dollar amounts
        dollar_weights = {
            tk: round(w * amount, 2) for tk, w in weights.items()
        }

        rationale = _build_rationale(strategy, tickers, weights)

        state["allocation_data"] = {
            "weights": weights,
            "dollar_weights": dollar_weights,
            "mode": strategy,
            "rationale": rationale,
            "amount": amount,
            "currency": "USD",
            "tickers": tickers,
        }

        elapsed = time.time() - start
        logger.info(
            f"[allocation_node] Done: strategy={strategy}, "
            f"latency={elapsed:.3f}s"
        )

    except Exception as e:
        logger.error(f"[allocation_node] Error: {e}")
        state["allocation_data"] = {
            "error": str(e),
            "weights": {},
            "mode": "error",
            "rationale": "Allocation optimization failed",
            "amount": amount,
            "currency": "USD",
        }

    return state


# -----------------------------------------------------------------
# Strategy implementations
# -----------------------------------------------------------------


def _compute_weights(
    state: Dict[str, Any], tickers: list, strategy: str
) -> Dict[str, float]:
    """Dispatch to the appropriate strategy and return normalised weights."""
    if strategy == "equal_weight":
        return _equal_weight(tickers)
    elif strategy == "risk_parity":
        return _risk_parity(state, tickers)
    elif strategy == "max_sharpe":
        return _max_sharpe(state, tickers)
    elif strategy in ("sector_focused", "risk_adjusted"):
        return _risk_adjusted(state, tickers)
    else:
        return _equal_weight(tickers)


def _equal_weight(tickers: list) -> Dict[str, float]:
    """Uniform allocation."""
    n = len(tickers)
    w = round(1.0 / n, 6)
    return {tk: w for tk in tickers}


def _risk_parity(state: Dict[str, Any], tickers: list) -> Dict[str, float]:
    """Weight inversely proportional to volatility z-score."""
    raw = state.get("raw_output", {})
    stocks = raw.get("ranking", {}).get("stocks", [])
    vol_map = {s["ticker"]: abs(s.get("vola_z", 1.0)) for s in stocks}

    inv = {}
    for tk in tickers:
        v = vol_map.get(tk, 1.0)
        inv[tk] = 1.0 / max(v, 0.01)

    total = sum(inv.values())
    return {tk: round(v / total, 6) for tk, v in inv.items()}


def _max_sharpe(state: Dict[str, Any], tickers: list) -> Dict[str, float]:
    """Weight proportional to composite_score (proxy for Sharpe)."""
    raw = state.get("raw_output", {})
    stocks = raw.get("ranking", {}).get("stocks", [])
    score_map = {s["ticker"]: max(s.get("composite_score", 0), 0.01) for s in stocks}

    raw_w = {tk: score_map.get(tk, 0.01) for tk in tickers}
    total = sum(raw_w.values())
    return {tk: round(v / total, 6) for tk, v in raw_w.items()}


def _risk_adjusted(state: Dict[str, Any], tickers: list) -> Dict[str, float]:
    """Blend momentum z-score and inverse-volatility."""
    raw = state.get("raw_output", {})
    stocks = raw.get("ranking", {}).get("stocks", [])
    data = {s["ticker"]: s for s in stocks}

    raw_w = {}
    for tk in tickers:
        s = data.get(tk, {})
        mom = max(s.get("momentum_z", 0), 0.01)
        inv_vol = 1.0 / max(abs(s.get("vola_z", 1.0)), 0.01)
        raw_w[tk] = mom * 0.6 + inv_vol * 0.4  # 60% momentum, 40% inv-vol

    total = sum(raw_w.values())
    return {tk: round(v / total, 6) for tk, v in raw_w.items()}


def _build_rationale(
    strategy: str, tickers: list, weights: Dict[str, float]
) -> str:
    """Generate a short rationale string for the allocation."""
    top = max(weights, key=weights.get)
    top_pct = weights[top] * 100

    descs = {
        "equal_weight": f"Equal allocation across {len(tickers)} tickers ({100/len(tickers):.1f}% each).",
        "risk_parity": f"Risk-parity allocation: lowest-volatility ticker {top} gets {top_pct:.1f}%.",
        "max_sharpe": f"Max-Sharpe allocation: highest-score ticker {top} gets {top_pct:.1f}%.",
        "sector_focused": f"Sector-focused allocation: leader {top} gets {top_pct:.1f}%.",
        "risk_adjusted": f"Risk-adjusted blend: {top} gets {top_pct:.1f}% (60% momentum, 40% inv-vol).",
    }
    return descs.get(strategy, f"Allocation strategy: {strategy}")
