"""
Proactive Suggestions Node — Finance Domain
=============================================

Generates proactive suggestions after analysis is complete:
  1. Correlation alerts (analyzing AAPL? consider MSFT, GOOGL)
  2. Earnings warnings (short horizon + upcoming earnings)
  3. Smart money flow (institutional accumulation / distribution)
  4. Risk hedge suggestions (high volatility detected)

Pipeline position (Phase 2 wiring — not yet wired):
  advisor → proactive_suggestions → END

Pure Python — no I/O, no infrastructure dependencies.
Reads only from state (raw_output, tickers, horizon).

Author: Ported from vitruvyan upstream (Phase 2.1, Oct 2025)
Adapted: February 24, 2026 (mercator domain pattern)
Status: CREATED (wiring deferred to Phase 2 — can/advisor restructure)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Correlation map (stub — should come from Pattern Weavers in production)
# ---------------------------------------------------------------------------
SECTOR_CORRELATIONS: Dict[str, List[str]] = {
    "AAPL": ["MSFT", "GOOGL", "META"],
    "TSLA": ["RIVN", "LCID", "NIO"],
    "JPM": ["BAC", "WFC", "C"],
    "XOM": ["CVX", "COP", "SLB"],
    "NVDA": ["AMD", "INTC", "AVGO"],
    "SPY": ["VOO", "IVV", "QQQ"],
    "AMZN": ["SHOP", "WMT", "BABA"],
    "MSFT": ["AAPL", "GOOGL", "CRM"],
    "META": ["SNAP", "PINS", "GOOGL"],
    "NFLX": ["DIS", "ROKU", "PARA"],
}


def _correlation_alert(tickers: List[str], state: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Suggest correlated assets when analysing a single ticker."""
    if len(tickers) != 1:
        return None
    related = SECTOR_CORRELATIONS.get(tickers[0].upper())
    if not related:
        return None
    return {
        "type": "correlation_alert",
        "title": "💡 Correlated assets",
        "message": (
            f"Analysing {tickers[0]}. Consider also: "
            f"{', '.join(related[:2])} for diversification."
        ),
        "priority": "medium",
    }


def _earnings_warning(
    tickers: List[str], horizon: str, state: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """Warn about upcoming earnings on short-term horizons."""
    if not horizon or horizon == "unspecified":
        return None

    horizon_text = state.get("horizon_text", horizon).lower()
    short_keywords = ["giorn", "sett", "day", "week", "short", "breve"]
    is_short = state.get("horizon") == "short" or any(
        kw in horizon_text for kw in short_keywords
    )
    if not is_short:
        return None

    # Stub: hardcoded earnings calendar (replace with live data in production)
    upcoming_earnings = {"AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "META", "AMZN"}
    at_risk = [t for t in tickers if t.upper() in upcoming_earnings]
    if not at_risk:
        return None

    return {
        "type": "earnings_warning",
        "title": "⚠️ Earnings alert",
        "message": (
            f"Short horizon ({horizon_text}) + upcoming earnings for "
            f"{', '.join(at_risk)}. Volatility may spike."
        ),
        "priority": "high",
    }


def _smart_money_insight(
    tickers: List[str], state: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """Detect institutional accumulation / distribution patterns."""
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", [])
    if not stocks:
        return None

    top = stocks[0]
    ticker = top.get("ticker")
    factors = top.get("factors", {})
    momentum_z = factors.get("momentum_z") or 0
    sentiment_z = factors.get("sentiment_z") or 0

    if momentum_z > 1.0 and sentiment_z > 0.5:
        return {
            "type": "smart_money_flow",
            "title": "🎯 Smart money signal",
            "message": (
                f"{ticker}: strong momentum ({momentum_z:.1f}) + positive sentiment. "
                f"Possible institutional accumulation."
            ),
            "priority": "medium",
        }
    if momentum_z < -1.0 and sentiment_z < -0.5:
        return {
            "type": "smart_money_flow",
            "title": "⚠️ Institutional distribution",
            "message": (
                f"{ticker}: weak momentum ({momentum_z:.1f}) + negative sentiment. "
                f"Possible institutional distribution."
            ),
            "priority": "high",
        }
    return None


def _risk_hedge_suggestion(
    tickers: List[str], state: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """Suggest hedging for volatile positions."""
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", [])
    if not stocks:
        return None

    high_vol = [
        s.get("ticker")
        for s in stocks[:3]
        if abs(s.get("factors", {}).get("vola_z") or 0) > 1.5
    ]
    if not high_vol:
        return None

    return {
        "type": "risk_hedge",
        "title": "🛡️ Consider hedging",
        "message": (
            f"High-volatility assets detected: {', '.join(high_vol)}. "
            f"Consider protective puts, stop-loss, or sector diversification."
        ),
        "priority": "medium",
    }


# ---------------------------------------------------------------------------
# Main node
# ---------------------------------------------------------------------------

def proactive_suggestions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate proactive suggestions based on analysis context.

    Runs all suggestion generators and appends results to state.
    Pure function — reads from state, returns enriched state.
    """
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    if not ranking or not ranking.get("stocks"):
        return state

    tickers = state.get("tickers", [])
    horizon = state.get("horizon", "unspecified")

    generators = [
        (_correlation_alert, (tickers, state)),
        (_earnings_warning, (tickers, horizon, state)),
        (_smart_money_insight, (tickers, state)),
        (_risk_hedge_suggestion, (tickers, state)),
    ]

    suggestions: List[Dict[str, str]] = []
    for gen_fn, args in generators:
        try:
            result = gen_fn(*args)
            if result:
                suggestions.append(result)
        except Exception as exc:
            logger.warning(f"[proactive_suggestions] {gen_fn.__name__}: {exc}")

    if not suggestions:
        return state

    state["proactive_suggestions"] = suggestions

    # Enrich response if already built
    response = state.get("response")
    if isinstance(response, dict):
        text = _format_suggestions(suggestions)
        response["proactive_suggestions"] = suggestions
        response["proactive_suggestions_text"] = text

    return state


def _format_suggestions(suggestions: List[Dict[str, str]]) -> str:
    """Format suggestions into user-friendly text."""
    priority_order = {"high": 0, "medium": 1, "low": 2}
    ordered = sorted(
        suggestions, key=lambda s: priority_order.get(s.get("priority", "low"), 2)
    )
    lines = [
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 PROACTIVE SUGGESTIONS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]
    for s in ordered:
        lines.append(s.get("title", ""))
        lines.append(s.get("message", "") + "\n")
    return "\n".join(lines)
