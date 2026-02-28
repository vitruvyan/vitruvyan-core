# vitruvyan_core/domains/finance/compose_formatter.py
"""
Finance Domain — Compose Formatter Hook

Provides domain-specific context formatting for compose_node.py.
This module is loaded dynamically by compose_node via the GRAPH_DOMAIN hook:

    domains.<domain>.compose_formatter.format_domain_context(raw_output, state)

Returns a list of context strings that compose_node appends to the LLM prompt.
This keeps finance-specific rendering (stocks, tickers, z-scores, RSI, trends)
out of the core orchestration layer.

> **Last updated**: Feb 28, 2026 17:00 UTC
"""

from typing import Any, Dict, List, Optional


# Keys that finance domain graph_nodes write to top-level state.
# graph_runner collects these into response["domain_extensions"].
DOMAIN_EXTENSION_KEYS = {
    "numerical_panel",
    "vee_explanations",
    "vare_risk",
    "vwre_attribution",
    "screening_meta",
    "gauge",
    "final_verdict",
    "conversation_type",
}


def format_domain_context(
    raw_output: Dict[str, Any],
    state: Dict[str, Any],
) -> Optional[List[str]]:
    """
    Extract finance-specific context from raw_output for LLM synthesis.

    Called by compose_node when GRAPH_DOMAIN=finance.
    Returns a list of context lines, or None if no finance data is present.
    """
    parts: List[str] = []

    # Auto-detect conversation_type from entity count (finance UX)
    entity_ids = state.get("entity_ids", [])
    if not state.get("conversation_type") and entity_ids:
        if len(entity_ids) == 1:
            state["conversation_type"] = "single_ticker"
        elif len(entity_ids) > 1:
            state["conversation_type"] = "comparison"

    # Extract ranking data (screener results)
    ranking = raw_output.get("ranking", {})
    stocks = ranking.get("stocks", []) if isinstance(ranking, dict) else []
    if stocks:
        for s in stocks[:5]:  # Limit to top 5
            tk = s.get("ticker", "?")
            line_parts = [f"{tk}:"]
            for metric in ("composite_score", "trend_z", "momentum_z", "vola_z"):
                v = s.get(metric)
                if v is not None:
                    line_parts.append(f"{metric}={v}")
            if s.get("short_trend"):
                line_parts.append(
                    f"trend={s['short_trend']}/{s.get('medium_trend', '?')}/{s.get('long_trend', '?')}"
                )
            if s.get("rsi"):
                line_parts.append(f"RSI={s['rsi']}")
            parts.append(" ".join(line_parts))

    # Extract VEE explanations if present
    vee = state.get("vee_explanations")
    if isinstance(vee, dict):
        for ticker, explanation in vee.items():
            if isinstance(explanation, dict) and explanation.get("summary"):
                parts.append(f"{ticker} VEE: {explanation['summary']}")

    # Extract VARE risk if present
    vare = state.get("vare_risk")
    if isinstance(vare, dict):
        for ticker, risk in vare.items():
            if isinstance(risk, dict) and risk.get("risk_level"):
                parts.append(f"{ticker} Risk: {risk['risk_level']}")

    return parts if parts else None
