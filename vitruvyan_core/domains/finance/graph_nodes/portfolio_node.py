"""
Finance Domain — Portfolio Node
=================================

LLM-powered portfolio analysis and rebalancing recommendations.
Fetches user portfolio, detects concentration risk, generates reasoning.

Pipeline position: decide → portfolio → output_normalizer
Triggered when: intent="portfolio_review"

State inputs:
    - user_id: str      — User identifier
    - language: str     — Response language (default "en")
    - input_text: str   — Original user query
    - intent: str       — "portfolio_review"

State outputs:
    - response: dict    — {narrative, conversation_type, portfolio, concentration,
                           action, issues, total_value, diversification_score}
    - route: str        — "portfolio_complete"

External calls:
    - PostgresAgent (user_portfolio table)
    - LLMAgent (reasoning generation)

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Thresholds
CONCENTRATION_RISK_THRESHOLD = 0.40   # 40% in single ticker = high risk
MIN_DIVERSIFICATION = 3               # Minimum holdings for diversification
HIGH_ALLOCATION = 0.30                # 30%+ = notable


def portfolio_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze user portfolio with LLM reasoning for rebalancing.

    Flow:
        1. Fetch holdings from PostgreSQL (user_portfolio)
        2. Compute concentration and risk metrics
        3. Detect issues (concentration, diversification)
        4. Generate LLM reasoning via LLMAgent
        5. Return structured response
    """
    user_id = state.get("user_id")
    lang = state.get("language", "en")

    logger.info(f"[portfolio_node] user={user_id}, lang={lang}")

    # --- Step 1: Fetch portfolio ---
    try:
        from core.agents.postgres_agent import PostgresAgent
        pg = PostgresAgent()

        rows = pg.fetch(
            """
            SELECT ticker, quantity, entry_price, current_value, last_updated
            FROM user_portfolio
            WHERE user_id = %s
            ORDER BY current_value DESC
            """,
            (user_id,),
        )

        if not rows:
            logger.warning(f"[portfolio_node] No portfolio for user={user_id}")
            return _empty_response(state, lang)

        portfolio = [dict(r) if hasattr(r, "keys") else _row_to_dict(r) for r in rows]
        logger.info(f"[portfolio_node] Fetched {len(portfolio)} holdings")

    except Exception as e:
        logger.error(f"[portfolio_node] DB error: {e}")
        return _error_response(state, str(e))

    # --- Step 2: Concentration analysis ---
    total_value = sum(float(h.get("current_value", 0)) for h in portfolio)
    if total_value == 0:
        return _empty_response(state, lang)

    concentration: Dict[str, float] = {}
    for h in portfolio:
        tk = h.get("ticker", "?")
        val = float(h.get("current_value", 0))
        concentration[tk] = round((val / total_value) * 100, 2)

    max_tk = max(concentration, key=concentration.get)
    max_pct = concentration[max_tk]

    # --- Step 3: Detect issues ---
    issues: List[str] = []
    action = "hold"

    if max_pct > CONCENTRATION_RISK_THRESHOLD * 100:
        issues.append(f"High concentration in {max_tk} ({max_pct}%)")
        action = f"reduce_{max_tk}"

    if len(portfolio) < MIN_DIVERSIFICATION:
        issues.append(f"Low diversification (only {len(portfolio)} holdings)")
        if action == "hold":
            action = "diversify"

    notable = {
        k: v for k, v in concentration.items()
        if v > HIGH_ALLOCATION * 100 and v <= CONCENTRATION_RISK_THRESHOLD * 100
    }
    if notable and action == "hold":
        parts = [f"{k} ({v}%)" for k, v in notable.items()]
        issues.append(f"Notable allocations: {', '.join(parts)}")
        action = "monitor"

    if not issues:
        issues.append("Portfolio well-balanced")
        action = "hold"

    # --- Step 4: LLM reasoning ---
    narrative = _generate_reasoning(
        portfolio, concentration, action, issues, max_tk, max_pct, lang
    )

    # --- Step 5: Build response ---
    portfolio_data = {
        "holdings": [
            {
                "ticker": h.get("ticker"),
                "value": float(h.get("current_value", 0)),
                "weight": concentration.get(h.get("ticker"), 0),
                "quantity": h.get("quantity", 0),
            }
            for h in portfolio
        ],
        "total_value": total_value,
        "concentration": concentration,
    }

    state["response"] = {
        "narrative": narrative,
        "conversation_type": "portfolio_analysis",
        "portfolio": portfolio_data,
        "concentration": concentration,
        "action": action,
        "issues": issues,
        "total_value": total_value,
        "diversification_score": len(portfolio),
        "timestamp": datetime.utcnow().isoformat(),
    }
    state["route"] = "portfolio_complete"

    logger.info(f"[portfolio_node] Done: action={action}, issues={len(issues)}")
    return state


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------


def _row_to_dict(row) -> dict:
    """Convert a tuple row to dict with expected keys."""
    keys = ["ticker", "quantity", "entry_price", "current_value", "last_updated"]
    if isinstance(row, (list, tuple)):
        return {k: row[i] if i < len(row) else None for i, k in enumerate(keys)}
    return {}


def _generate_reasoning(
    portfolio: list,
    concentration: Dict[str, float],
    action: str,
    issues: List[str],
    max_tk: str,
    max_pct: float,
    lang: str,
) -> str:
    """Generate reasoning via LLMAgent, with template fallback."""
    try:
        from core.agents.llm_agent import get_llm_agent

        llm = get_llm_agent()
        prompt = (
            f"You are a portfolio analyst. Analyze this portfolio:\n"
            f"- Holdings: {len(portfolio)} stocks\n"
            f"- Highest concentration: {max_tk} at {max_pct}%\n"
            f"- Issues: {', '.join(issues)}\n"
            f"- Recommended action: {action}\n\n"
            f"Provide a concise analysis and recommendation in "
            f"{'Italian' if lang == 'it' else 'Spanish' if lang == 'es' else 'English'}. "
            f"Keep it under 150 words."
        )
        result = llm.complete(prompt)
        if result and len(result) > 20:
            return result
    except Exception as e:
        logger.warning(f"[portfolio_node] LLM fallback: {e}")

    return _template_reasoning(action, max_tk, max_pct, issues, lang)


def _template_reasoning(
    action: str, ticker: str, pct: float, issues: List[str], lang: str
) -> str:
    """Template-based reasoning fallback."""
    if lang == "it":
        if action.startswith("reduce_"):
            return (
                f"Il tuo portfolio ha il {pct}% in {ticker}. "
                f"Se scende del 10%, perdi il {pct * 0.1:.1f}% del capitale. "
                f"Considera di ridurre l'esposizione al 30-40%."
            )
        if action == "diversify":
            return "Il portfolio ha pochi titoli. Aggiungi 2-3 titoli in settori diversi."
        return "Il portfolio appare ben bilanciato."

    # English (default)
    if action.startswith("reduce_"):
        return (
            f"Your portfolio is {pct}% in {ticker}. "
            f"A 10% drop means {pct * 0.1:.1f}% total loss. "
            f"Consider reducing to 30-40%."
        )
    if action == "diversify":
        return "Your portfolio has few holdings. Add 2-3 stocks in different sectors."
    return "Your portfolio looks well-balanced."


def _empty_response(state: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """Response when no portfolio found."""
    msg = {
        "it": "Non ho trovato nessun portfolio associato al tuo account.",
        "es": "No encontré ninguna cartera asociada a tu cuenta.",
    }
    state["response"] = {
        "narrative": msg.get(lang, "No portfolio found for your account."),
        "conversation_type": "portfolio_analysis",
        "portfolio": [],
        "concentration": {},
        "action": "start_tracking",
        "issues": ["No portfolio found"],
    }
    state["route"] = "portfolio_complete"
    return state


def _error_response(state: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Response on database error."""
    state["response"] = {
        "narrative": f"Error analyzing portfolio: {error}",
        "conversation_type": "error",
        "error": error,
    }
    state["route"] = "error"
    return state
