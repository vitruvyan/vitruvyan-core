# Context Memory for LLM Enhancement
# core/langgraph/memory/conversation_context.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class ConversationContextManager:
    """
    Manages conversational context for enhanced LLM responses
    """
    
    def __init__(self):
        self.context_window = 5  # Remember last 5 interactions
        
    def build_conversation_context(self, user_id: str, current_state: Dict[str, Any]) -> str:
        """Build conversation context from recent interactions"""
        
        # Get recent conversation history (would integrate with postgres)
        conversation_history = self._get_recent_conversations(user_id)
        
        # Extract key themes and preferences
        context_summary = self._extract_context_themes(conversation_history)
        
        # Build context string for LLM
        return self._format_context_for_llm(context_summary, current_state)
    
    def _get_recent_conversations(self, user_id: str) -> List[Dict]:
        """Get recent conversation history - uses VSGS semantic_grounding_node"""
        # Phase 2 Migration (Nov 2025): Use semantic_grounding_node state["semantic_matches"]
        # conversation_persistence.py moved to legacy/deprecated/
        return []
    
    def _extract_context_themes(self, history: List[Dict]) -> Dict[str, Any]:
        """Extract recurring themes and user preferences"""
        themes = {
            "preferred_tickers": [],
            "risk_tolerance": "unknown",
            "investment_horizon": "unknown", 
            "emotional_state": "neutral",
            "expertise_level": "intermediate",
            "language_preference": "en"
        }
        
        # Analyze conversation patterns
        for conv in history:
            # Extract tickers mentioned
            if "tickers" in conv:
                themes["preferred_tickers"].extend(conv["tickers"])
            
            # Extract risk signals
            input_text = conv.get("input_text", "").lower()
            if any(word in input_text for word in ["safe", "conservative", "low risk"]):
                themes["risk_tolerance"] = "conservative"
            elif any(word in input_text for word in ["aggressive", "growth", "high return"]):
                themes["risk_tolerance"] = "aggressive"
        
        # Deduplicate preferred tickers
        themes["preferred_tickers"] = list(set(themes["preferred_tickers"]))
        
        return themes
    
    def _format_context_for_llm(self, themes: Dict[str, Any], current_state: Dict[str, Any]) -> str:
        """Format context for LLM consumption"""
        
        context_parts = []
        
        # User profile
        if themes["preferred_tickers"]:
            context_parts.append(f"User often discusses: {', '.join(themes['preferred_tickers'][:5])}")
        
        if themes["risk_tolerance"] != "unknown":
            context_parts.append(f"Risk tolerance: {themes['risk_tolerance']}")
        
        if themes["investment_horizon"] != "unknown":
            context_parts.append(f"Investment horizon: {themes['investment_horizon']}")
        
        # Current session context
        current_tickers = current_state.get("tickers", [])
        if current_tickers:
            context_parts.append(f"Current focus: {', '.join(current_tickers)}")
        
        return "CONVERSATION CONTEXT:\n" + "\n".join(f"- {part}" for part in context_parts)


class MarketContextProvider:
    """
    Provides dynamic market context for LLM responses
    """
    
    def get_market_narrative(self, tickers: List[str] = None) -> str:
        """Get current market narrative context"""
        
        # Base market context
        base_context = self._get_base_market_context()
        
        # Ticker-specific context
        ticker_context = ""
        if tickers:
            ticker_context = self._get_ticker_specific_context(tickers)
        
        return f"{base_context}\n{ticker_context}".strip()
    
    def _get_base_market_context(self) -> str:
        """Base market environment context"""
        # This could be enhanced with live market data
        return """
CURRENT MARKET ENVIRONMENT:
- Tech sector leadership continues amid AI revolution
- Interest rate environment remains dynamic
- Geopolitical tensions creating selective volatility
- Energy transition themes driving long-term flows
- Consumer discretionary showing mixed signals
"""
    
    def _get_ticker_specific_context(self, tickers: List[str]) -> str:
        """Get specific context for mentioned tickers"""
        
        # Sector mapping for context
        tech_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
        finance_tickers = ["JPM", "BAC", "WFC", "GS"]
        
        context_parts = []
        
        for ticker in tickers:
            if ticker in tech_tickers:
                context_parts.append(f"{ticker}: Part of AI/tech revolution theme")
            elif ticker in finance_tickers:
                context_parts.append(f"{ticker}: Sensitive to interest rate environment")
            # Add more sector classifications as needed
        
        return "TICKER-SPECIFIC CONTEXT:\n" + "\n".join(f"- {part}" for part in context_parts) if context_parts else ""


# Integration function for enhanced LLM node
def enhance_llm_with_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance LLM state with conversation and market context"""
    
    user_id = state.get("user_id", "demo")
    tickers = state.get("tickers", [])
    
    # Add conversation context
    context_manager = ConversationContextManager()
    conversation_context = context_manager.build_conversation_context(user_id, state)
    
    # Add market context  
    market_provider = MarketContextProvider()
    market_context = market_provider.get_market_narrative(tickers)
    
    # Enhance state
    state["conversation_context"] = conversation_context
    state["market_context"] = market_context
    
    return state