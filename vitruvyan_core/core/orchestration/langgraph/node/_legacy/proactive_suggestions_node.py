"""
Proactive Suggestions Node - Phase 2.1
Anticipate user needs and provide intelligent suggestions based on analysis context.

Suggestion Types:
1. Correlation Alerts: When analyzing single entity_id, suggest correlated assets
2. Earnings Safety: Warn about upcoming earnings for short-term horizons
3. Smart Money Flow: Highlight institutional buying/selling patterns
4. Sector Rotation: Suggest related sectors based on market conditions
5. Risk Hedge: Recommend hedging strategies for volatile positions
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def generate_correlation_alert(entity_ids: List[str], state: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate correlation alert when user analyzes a single entity_id.
    Suggest highly correlated assets for diversification or concentration.
    """
    if len(entity_ids) != 1:
        return None
    
    entity_id = entity_ids[0]
    
    # Common correlation patterns (simplified - in production, query from correlation matrix)
    correlations = {
        "EXAMPLE_ENTITY_1": ["EXAMPLE_ENTITY_4", "EXAMPLE_ENTITY_5", "META"],
        "EXAMPLE_ENTITY_3": ["RIVN", "LCID", "NIO"],
        "JPM": ["BAC", "WFC", "C"],
        "XOM": ["CVX", "COP", "SLB"],
        "EXAMPLE_ENTITY_2": ["AMD", "INTC", "AVGO"],
        "SPY": ["VOO", "IVV", "QQQ"],
    }
    
    related = correlations.get(entity_id.upper())
    if not related:
        return None
    
    return {
        "type": "correlation_alert",
        "title": "💡 Asset correlati",
        "message": f"Stai analizzando {entity_id}. Potresti considerare anche: {', '.join(related[:2])} per diversificazione o concentrazione settoriale.",
        "priority": "medium"
    }


def generate_earnings_warning(entity_ids: List[str], horizon: str, state: Dict[str, Any]) -> Dict[str, str]:
    """
    Warn about upcoming earnings when user has short-term horizon (<30 days).
    Earnings create volatility that can disrupt short-term technical analysis.
    """
    if not horizon or horizon == "unspecified":
        return None
    
    # Check if horizon is short-term based on classification
    horizon_category = state.get("horizon", "")
    is_short_term = horizon_category == "short"
    
    # Also check horizon_text for explicit short terms
    horizon_text = state.get("horizon_text", horizon).lower()
    short_term_keywords = ["giorn", "sett", "day", "week", "short", "breve"]
    if any(kw in horizon_text for kw in short_term_keywords):
        is_short_term = True
    
    if not is_short_term:
        return None
    
    # Simplified earnings calendar (in production, query from earnings API)
    upcoming_earnings = ["EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_3", "EXAMPLE_ENTITY_2", "EXAMPLE_ENTITY_4", "EXAMPLE_ENTITY_5"]
    
    at_risk_entities = [t for t in entity_ids if t.upper() in upcoming_earnings]
    
    if not at_risk_entities:
        return None
    
    return {
        "type": "earnings_warning",
        "title": "⚠️ Attenzione earnings",
        "message": f"Con orizzonte breve ({horizon_text}), attenzione: {', '.join(at_risk_entities)} ha earnings imminenti. La volatilità potrebbe aumentare.",
        "priority": "high"
    }


def generate_smart_money_insight(entity_ids: List[str], state: Dict[str, Any]) -> Dict[str, str]:
    """
    Highlight institutional buying/selling patterns (smart money flow).
    Based on recent 13F filings or unusual institutional volume.
    """
    # Check if we have raw_output with ranking data
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    entities = ranking.get("entities", [])
    
    if not entities:
        return None
    
    # Look for sentiment or momentum indicators (proxy for smart money)
    top_stock = entities[0] if entities else None
    if not top_stock:
        return None
    
    entity_id = top_stock.get("entity_id")
    factors = top_stock.get("factors", {})
    sentiment_z = factors.get("sentiment_z") or 0
    momentum_z = factors.get("momentum_z") or 0
    
    # Strong positive momentum + sentiment = potential smart money accumulation
    if momentum_z > 1.0 and sentiment_z > 0.5:
        return {
            "type": "smart_money_flow",
            "title": "🎯 Smart money in azione",
            "message": f"{entity_id} mostra forte momentum ({momentum_z:.1f}) e sentiment positivo. Possibile accumulo istituzionale in corso.",
            "priority": "medium"
        }
    
    # Strong negative momentum + negative sentiment = potential distribution
    if momentum_z < -1.0 and sentiment_z < -0.5:
        return {
            "type": "smart_money_flow",
            "title": "⚠️ Distribuzione istituzionale",
            "message": f"{entity_id} mostra momentum debole ({momentum_z:.1f}) e sentiment negativo. Possibile distribuzione da parte degli istituzionali.",
            "priority": "high"
        }
    
    return None


def generate_risk_hedge_suggestion(entity_ids: List[str], state: Dict[str, Any]) -> Dict[str, str]:
    """
    Suggest hedging strategies for volatile or risky positions.
    Based on volatility z-score and market conditions.
    """
    raw_output = state.get("raw_output", {})
    ranking = raw_output.get("ranking", {})
    entities = ranking.get("entities", [])
    
    if not entities:
        return None
    
    # Check for high volatility entities
    high_vol_stocks = []
    for entity in entities[:3]:  # Check top 3
        entity_id = entity.get("entity_id")
        factors = entity.get("factors", {})
        vola_z = factors.get("vola_z")
        
        # Skip if vola_z is None
        if vola_z is not None and abs(vola_z) > 1.5:  # High volatility (>1.5 std dev)
            high_vol_stocks.append(entity_id)
    
    if not high_vol_stocks:
        return None
    
    return {
        "type": "risk_hedge",
        "title": "🛡️ Considera una copertura",
        "message": f"Asset volatili rilevati: {', '.join(high_vol_stocks)}. Considera strategie di hedging (put protettive, stop loss, diversificazione settoriale).",
        "priority": "medium"
    }


def proactive_suggestions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main node that generates proactive suggestions based on analysis context.
    Generates suggestions when we have valid analysis results.
    
    Returns state with added 'proactive_suggestions' list.
    """
    # Check if we have valid neural engine results
    result = state.get("result", {})
    route = result.get("route", state.get("route", ""))
    
    # Only generate suggestions for successful neural engine runs
    if route != "ne_valid":
        logger.debug(f"[proactive_suggestions] Skipping - route is '{route}', not 'ne_valid'")
        return state
    
    # Extract context
    entity_ids = state.get("entity_ids", [])
    horizon = state.get("horizon", "unspecified")
    intent = state.get("intent", "")
    
    logger.info(f"[proactive_suggestions] Generating suggestions for entity_ids={entity_ids}, horizon={horizon}, intent={intent}")
    
    suggestions = []
    
    # Generate different types of suggestions with proper argument passing
    try:
        suggestion = generate_correlation_alert(entity_ids, state)
        if suggestion:
            suggestions.append(suggestion)
            logger.info(f"[proactive_suggestions] Added suggestion: {suggestion['type']}")
    except Exception as e:
        logger.warning(f"[proactive_suggestions] Error in generate_correlation_alert: {e}")
    
    try:
        suggestion = generate_earnings_warning(entity_ids, horizon, state)
        if suggestion:
            suggestions.append(suggestion)
            logger.info(f"[proactive_suggestions] Added suggestion: {suggestion['type']}")
    except Exception as e:
        logger.warning(f"[proactive_suggestions] Error in generate_earnings_warning: {e}")
    
    try:
        suggestion = generate_smart_money_insight(entity_ids, state)
        if suggestion:
            suggestions.append(suggestion)
            logger.info(f"[proactive_suggestions] Added suggestion: {suggestion['type']}")
    except Exception as e:
        logger.warning(f"[proactive_suggestions] Error in generate_smart_money_insight: {e}")
    
    try:
        suggestion = generate_risk_hedge_suggestion(entity_ids, state)
        if suggestion:
            suggestions.append(suggestion)
            logger.info(f"[proactive_suggestions] Added suggestion: {suggestion['type']}")
    except Exception as e:
        logger.warning(f"[proactive_suggestions] Error in generate_risk_hedge_suggestion: {e}")
    
    # Add suggestions to state
    if suggestions:
        state["proactive_suggestions"] = suggestions
        logger.info(f"[proactive_suggestions] Generated {len(suggestions)} suggestions")
        
        # 💡 INJECT suggestions into existing response dict (compose_node already ran)
        response = state.get("response")
        if isinstance(response, dict):
            suggestions_text = format_suggestions_for_response(suggestions)
            response["proactive_suggestions"] = suggestions
            response["proactive_suggestions_text"] = suggestions_text
            
            # Also append to raw_output.notes if action=answer
            if response.get("action") == "answer" and "explainability" in response:
                explainability = response["explainability"]
                if isinstance(explainability, dict) and "detailed" in explainability:
                    detailed = explainability["detailed"]
                    if isinstance(detailed, dict) and "notes" in detailed:
                        notes = detailed["notes"]
                        if isinstance(notes, dict):
                            notes["proactive_suggestions"] = suggestions_text
            
            logger.info("[proactive_suggestions] Injected suggestions into response dict")
    else:
        logger.debug("[proactive_suggestions] No suggestions generated for current context")
    
    return state


def format_suggestions_for_response(suggestions: List[Dict[str, str]]) -> str:
    """
    Format proactive suggestions into user-friendly text.
    Used by compose_node to append suggestions to final response.
    """
    if not suggestions:
        return ""
    
    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_suggestions = sorted(suggestions, key=lambda s: priority_order.get(s.get("priority", "low"), 2))
    
    lines = ["\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    lines.append("📊 SUGGERIMENTI PROATTIVI")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for suggestion in sorted_suggestions:
        title = suggestion.get("title", "")
        message = suggestion.get("message", "")
        lines.append(f"{title}")
        lines.append(f"{message}\n")
    
    return "\n".join(lines)
