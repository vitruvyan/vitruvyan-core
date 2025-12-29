def decide_strategy(parsed_input: dict) -> str:
    """
    Determina quale strategia o agente attivare in base all'intento.
    """
    intent = parsed_input.get("intent", "unknown")

    if intent == "allocate":
        return "allocation_strategy"
    elif intent == "trend":
        return "trend_analysis"
    elif intent == "strategy":
        return "portfolio_builder"
    elif intent == "risk":
        return "risk_assessment"
    elif intent == "sentiment":
        return "sentiment_analysis"
    else:
        return "fallback_strategy"


# Test standalone
if __name__ == "__main__":
    for intent in ["allocate", "trend", "strategy", "risk", "sentiment", "nonsense"]:
        print(f"Intent: {intent} ➡️ Route: {decide_strategy({'intent': intent})}")