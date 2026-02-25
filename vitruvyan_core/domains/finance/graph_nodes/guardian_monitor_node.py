"""
Finance Domain — Guardian Monitor Node
========================================

Portfolio health monitoring and risk detection.
Detects concentration risk, performance degradation, sector imbalance.
On critical severity, triggers embedded autopilot evaluation.

Pipeline position: decide → guardian_monitor → output_normalizer
Triggered when: intent="portfolio_monitor"

State inputs:
    - user_id: str      — User identifier
    - language: str     — Response language
    - input_text: str   — Original user query

State outputs:
    - guardian_insights: list    — List of insight dicts
    - max_severity: str         — "low"|"medium"|"high"|"critical"
    - guardian_summary: str     — Concise text summary
    - issues_detected: bool    — Whether any issues found
    - autopilot_actions: list  — (critical only) Proposed actions
    - route: str               — "guardian_complete"

External calls:
    - PostgresAgent (shadow_portfolio_snapshots, user_portfolio)

Author: Vitruvyan Finance Vertical
Created: February 24, 2026
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Severity thresholds
CONCENTRATION_CRITICAL = 0.70   # 70%+ in single ticker = critical
CONCENTRATION_HIGH = 0.50       # 50%+ = high
CONCENTRATION_MEDIUM = 0.40     # 40%+ = medium


def guardian_monitor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor portfolio health and detect risk issues.

    Generates insights with severity levels:
        low     — Informational
        medium  — Minor concern
        high    — Significant risk
        critical — Requires immediate action (triggers autopilot)
    """
    user_id = state.get("user_id")
    logger.info(f"[guardian_monitor] Starting for user={user_id}")

    if not user_id:
        logger.error("[guardian_monitor] Missing user_id")
        return _build_result(state, [], "low", "Missing user ID")

    # --- Fetch portfolio data ---
    holdings = _fetch_portfolio(user_id)
    if not holdings:
        return _build_result(
            state, [], "low", "No portfolio data found. Create a portfolio first."
        )

    # --- Analyze portfolio ---
    insights = _analyze_portfolio(holdings, user_id)
    if not insights:
        return _build_result(
            state, [], "low", "Portfolio health check complete. No issues."
        )

    # Determine max severity
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    max_severity = max(
        (i["severity"] for i in insights),
        key=lambda s: severity_order.get(s, 0),
    )

    # Build summary
    parts = [f"{i['title']} ({i['severity']})" for i in insights[:3]]
    summary = ". ".join(parts)

    logger.info(
        f"[guardian_monitor] {len(insights)} insights, "
        f"max_severity={max_severity}"
    )

    result = _build_result(state, insights, max_severity, summary)

    # Critical severity → embedded autopilot evaluation
    if max_severity == "critical":
        autopilot_actions = _autopilot_evaluate(insights, user_id)
        result["autopilot_actions"] = autopilot_actions
        logger.info(
            f"[guardian_monitor] Critical: {len(autopilot_actions)} "
            f"autopilot actions proposed"
        )

    return result


# -----------------------------------------------------------------
# Portfolio analysis
# -----------------------------------------------------------------


def _fetch_portfolio(user_id: str) -> List[Dict[str, Any]]:
    """Fetch portfolio from PostgreSQL."""
    try:
        from core.agents.postgres_agent import PostgresAgent

        pg = PostgresAgent()
        rows = pg.fetch(
            """
            SELECT ticker, quantity, current_value
            FROM user_portfolio
            WHERE user_id = %s
            ORDER BY current_value DESC
            """,
            (user_id,),
        )
        if not rows:
            return []

        result = []
        for r in rows:
            if isinstance(r, dict):
                result.append(r)
            elif isinstance(r, (list, tuple)):
                result.append({
                    "ticker": r[0],
                    "quantity": r[1],
                    "current_value": float(r[2]) if r[2] else 0,
                })
        return result

    except Exception as e:
        logger.error(f"[guardian_monitor] DB error: {e}")
        return []


def _analyze_portfolio(
    holdings: List[Dict[str, Any]], user_id: str
) -> List[Dict[str, Any]]:
    """Run portfolio health checks and produce insight list."""
    insights: List[Dict[str, Any]] = []
    total_value = sum(float(h.get("current_value", 0)) for h in holdings)
    if total_value <= 0:
        return insights

    # Concentration analysis
    for h in holdings:
        tk = h.get("ticker", "?")
        val = float(h.get("current_value", 0))
        weight = val / total_value

        if weight >= CONCENTRATION_CRITICAL:
            insights.append({
                "type": "concentration_risk",
                "severity": "critical",
                "title": f"Critical concentration: {tk} ({weight*100:.1f}%)",
                "description": (
                    f"{tk} represents {weight*100:.1f}% of portfolio. "
                    f"A 10% drop = {weight*10:.1f}% total loss."
                ),
                "recommendations": [
                    f"Reduce {tk} to below 40%",
                    "Diversify into 2-3 additional sectors",
                ],
                "metrics": {"ticker": tk, "weight": round(weight, 4)},
            })
        elif weight >= CONCENTRATION_HIGH:
            insights.append({
                "type": "concentration_risk",
                "severity": "high",
                "title": f"High concentration: {tk} ({weight*100:.1f}%)",
                "description": f"{tk} is {weight*100:.1f}% of portfolio.",
                "recommendations": [f"Consider reducing {tk} exposure"],
                "metrics": {"ticker": tk, "weight": round(weight, 4)},
            })
        elif weight >= CONCENTRATION_MEDIUM:
            insights.append({
                "type": "concentration_risk",
                "severity": "medium",
                "title": f"Notable allocation: {tk} ({weight*100:.1f}%)",
                "description": f"{tk} is {weight*100:.1f}% of portfolio.",
                "recommendations": ["Monitor position closely"],
                "metrics": {"ticker": tk, "weight": round(weight, 4)},
            })

    # Diversification check
    if len(holdings) < 3:
        insights.append({
            "type": "diversification",
            "severity": "high" if len(holdings) == 1 else "medium",
            "title": f"Low diversification ({len(holdings)} holdings)",
            "description": "Portfolio lacks diversification across sectors.",
            "recommendations": ["Add positions in different sectors"],
            "metrics": {"num_holdings": len(holdings)},
        })

    return insights


# -----------------------------------------------------------------
# Embedded autopilot logic (for critical severity)
# -----------------------------------------------------------------


def _autopilot_evaluate(
    insights: List[Dict[str, Any]], user_id: str
) -> List[Dict[str, Any]]:
    """
    Generate autonomous action proposals for critical insights.

    This is an embedded lightweight autopilot — for full AutopilotAgent
    integration, upgrade to the dedicated autopilot_node.
    """
    actions: List[Dict[str, Any]] = []

    for insight in insights:
        if insight["severity"] != "critical":
            continue

        if insight["type"] == "concentration_risk":
            metrics = insight.get("metrics", {})
            ticker = metrics.get("ticker", "?")
            weight = metrics.get("weight", 0)

            # Propose sell to reduce concentration to 40%
            if weight > 0.40:
                reduce_pct = round((weight - 0.40) * 100, 1)
                actions.append({
                    "action_type": "sell",
                    "ticker": ticker,
                    "percentage": reduce_pct,
                    "rationale": (
                        f"Reduce {ticker} from {weight*100:.1f}% to ~40% "
                        f"(sell ~{reduce_pct}% of portfolio value)"
                    ),
                    "risk_score": 0.5 if reduce_pct < 20 else 0.75,
                    "source": "guardian_autopilot",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    return actions


# -----------------------------------------------------------------
# Response builder
# -----------------------------------------------------------------


def _build_result(
    state: Dict[str, Any],
    insights: List[Dict[str, Any]],
    max_severity: str,
    summary: str,
) -> Dict[str, Any]:
    """Build standardized guardian result."""
    state["guardian_insights"] = insights
    state["max_severity"] = max_severity
    state["guardian_summary"] = summary
    state["issues_detected"] = len(insights) > 0
    state["route"] = "guardian_complete"
    return state
