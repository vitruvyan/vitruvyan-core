"""
Vitruvyan Core — Finance Domain Plugin
=======================================

Reference implementation of GraphPlugin for the Finance vertical.

This plugin integrates the finance domain with the LangGraph orchestration:
- FinanceParser: Extracts budget, horizon, companies from queries
- FinanceIntentRegistry: Intent detection for finance queries
- FinanceRouteRegistry: Routing for finance intents
- State extensions: tickers, budget, horizon, sector filters

This is the REFERENCE IMPLEMENTATION. Other domains (healthcare, logistics)
should follow this pattern.

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: PRODUCTION
"""

import re
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from core.orchestration import (
    GraphPlugin,
    NodeContract,
    Parser,
    BaseParser,
    IntentRegistry,
    IntentDefinition,
    ScreeningFilter,
    RouteRegistry,
    RouteDefinition,
    IntentRouteMapping,
)

from core.agents.postgres_agent import PostgresAgent

# Import compose layer abstractions
from core.orchestration.compose import ResponseFormatter, SlotFiller
from domains.finance.response_formatter import FinanceResponseFormatter
from domains.finance.slot_filler import FinanceSlotFiller

logger = logging.getLogger(__name__)


# ===========================================================================
# FINANCE STATE EXTENSIONS
# ===========================================================================

class FinanceStateExtension(TypedDict, total=False):
    """
    Finance-specific state fields.
    
    These are added to BaseGraphState when the finance domain is active.
    """
    # Ticker/entity fields
    tickers: List[str]           # Validated ticker symbols (AAPL, MSFT, etc.)
    ticker_count: int            # Number of tickers in query
    company_names: List[str]     # Company names (Apple, Microsoft)
    
    # Budget/allocation fields
    budget: Optional[int]        # Investment budget (e.g., 5000)
    currency: str                # Currency (USD, EUR, etc.)
    
    # Horizon/timeframe fields
    horizon: Optional[str]       # short, medium, long
    horizon_months: Optional[int]  # Numeric horizon in months
    
    # Screening filters
    risk_tolerance: Optional[str]  # low, medium, high
    momentum_breakout: bool        # Looking for breakout stocks
    value_screening: bool          # Looking for undervalued stocks
    divergence_detection: bool     # Looking for divergence signals
    sector_filter: Optional[str]   # Sector filter (Technology, Healthcare, etc.)
    
    # Technical analysis results
    raw_output: Dict[str, Any]     # Raw technical data
    technical_signals: List[Dict]  # Computed signals
    
    # Portfolio context
    portfolio_id: Optional[str]    # User's portfolio ID
    portfolio_context: Dict[str, Any]  # Portfolio context


# ===========================================================================
# FINANCE PARSER
# ===========================================================================

class FinanceParser(BaseParser):
    """
    Finance-specific parser for extracting financial concepts from queries.
    
    Extracts:
    - Budget (5000€, $10000, etc.)
    - Horizon (3 months, 2 years, short-term)
    - Company names → ticker symbols
    """
    
    # Common company name → ticker mapping
    COMPANY_MAP = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "tesla": "TSLA",
        "nvidia": "NVDA",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "amd": "AMD",
        "intel": "INTC",
        "ibm": "IBM",
        "oracle": "ORCL",
        "salesforce": "CRM",
        "adobe": "ADBE",
        "paypal": "PYPL",
        "berkshire": "BRK.B",
        "jpmorgan": "JPM",
        "goldman": "GS",
        "visa": "V",
        "mastercard": "MA",
        "cocacola": "KO",
        "coca-cola": "KO",
        "pepsi": "PEP",
        "disney": "DIS",
        "walmart": "WMT",
        "exxon": "XOM",
        "chevron": "CVX",
    }
    
    def __init__(self):
        """Initialize with PostgresAgent for ticker validation."""
        self._pg = None
    
    @property
    def pg(self) -> PostgresAgent:
        """Lazy load PostgresAgent."""
        if self._pg is None:
            try:
                self._pg = PostgresAgent()
            except Exception as e:
                logger.warning(f"PostgresAgent unavailable: {e}")
        return self._pg
    
    def extract_slots(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """
        Extract finance-specific slots from user input.
        
        Returns:
            Dict with budget, horizon, currency, companies
        """
        slots = {}
        
        # Extract budget
        budget = self._extract_budget(text)
        if budget:
            slots["budget"] = budget["amount"]
            slots["currency"] = budget["currency"]
        
        # Extract horizon
        horizon = self._extract_horizon(text)
        if horizon:
            slots["horizon"] = horizon["category"]
            slots["horizon_months"] = horizon["months"]
        
        # Extract companies
        companies = self._extract_companies(text)
        if companies:
            slots["company_names"] = companies
        
        return slots
    
    def validate_entity(self, entity_id: str) -> bool:
        """Validate if a ticker exists in the database."""
        if not self.pg:
            return True  # Skip validation if no DB
        
        try:
            query = "SELECT 1 FROM entity_ids WHERE entity_id = %s LIMIT 1"
            rows = self.pg.fetch_all(query, (entity_id.upper(),))
            return len(rows) > 0
        except Exception:
            return True  # Assume valid if can't check
    
    def get_company_map(self) -> Dict[str, str]:
        """Return company name → ticker mapping."""
        return self.COMPANY_MAP.copy()
    
    def _extract_budget(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract budget amount and currency."""
        if not text:
            return None
        
        # Patterns for budget extraction
        patterns = [
            # "5000 euro", "5000€", "5.000 EUR"
            (r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(€|eur|euro)", "EUR"),
            # "$10000", "10000 USD", "10,000 dollars"
            (r"\$\s*(\d{1,3}(?:,\d{3})*|\d+)", "USD"),
            (r"(\d{1,3}(?:,\d{3})*|\d+)\s*(usd|dollars?)", "USD"),
            # "£5000", "5000 GBP"
            (r"£\s*(\d{1,3}(?:,\d{3})*|\d+)", "GBP"),
            (r"(\d{1,3}(?:,\d{3})*|\d+)\s*(gbp|pounds?)", "GBP"),
        ]
        
        for pattern, currency in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "").replace(".", "")
                try:
                    return {"amount": int(amount_str), "currency": currency}
                except ValueError:
                    continue
        
        # Fallback: any large number might be a budget
        match = re.search(r"\b(\d{3,})\b", text)
        if match:
            amount = int(match.group(1))
            if 100 <= amount <= 10_000_000:  # Reasonable budget range
                return {"amount": amount, "currency": "USD"}
        
        return None
    
    def _extract_horizon(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract investment horizon."""
        if not text:
            return None
        
        txt = text.lower()
        
        # Explicit month patterns
        match = re.search(r"(\d+)\s*(mesi|months?|m)\b", txt)
        if match:
            months = int(match.group(1))
            return {
                "months": months,
                "category": self._months_to_category(months)
            }
        
        # Explicit year patterns
        match = re.search(r"(\d+)\s*(anni|years?|y)\b", txt)
        if match:
            years = int(match.group(1))
            months = years * 12
            return {
                "months": months,
                "category": self._months_to_category(months)
            }
        
        # Keyword-based
        if any(w in txt for w in ["breve", "short", "quick", "rapido"]):
            return {"months": 3, "category": "short"}
        if any(w in txt for w in ["medio", "medium", "moderate"]):
            return {"months": 12, "category": "medium"}
        if any(w in txt for w in ["lungo", "long", "extended"]):
            return {"months": 36, "category": "long"}
        
        return None
    
    def _months_to_category(self, months: int) -> str:
        """Convert months to horizon category."""
        if months <= 6:
            return "short"
        elif months <= 24:
            return "medium"
        else:
            return "long"
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract company names from text."""
        if not text:
            return []
        
        found = []
        txt_lower = text.lower()
        
        for company in self.COMPANY_MAP:
            if company in txt_lower:
                found.append(company)
        
        return found


# ===========================================================================
# FINANCE INTENT REGISTRY
# ===========================================================================

def create_finance_intent_registry() -> IntentRegistry:
    """
    Create intent registry for finance domain.
    
    Returns:
        IntentRegistry with finance-specific intents and filters
    """
    registry = IntentRegistry(domain_name="finance")
    
    # Core analysis intents
    registry.register_intent(IntentDefinition(
        name="trend",
        description="Stock/entity analysis, technical analysis, chart patterns",
        examples=[
            "Analizza AAPL",
            "How is Tesla doing?",
            "Study NVDA technical indicators",
            "Analyze Microsoft stock",
        ],
        synonyms=["analyze", "analizza", "study", "check"],
        requires_entities=True,
    ))
    
    registry.register_intent(IntentDefinition(
        name="risk",
        description="Risk assessment of specific stocks or portfolio",
        examples=[
            "What's the risk of MSFT?",
            "Risk analysis for my portfolio",
            "How risky is TSLA?",
        ],
        synonyms=["rischio"],
        requires_entities=True,
    ))
    
    registry.register_intent(IntentDefinition(
        name="momentum",
        description="Momentum indicators - RSI, MACD, breakout detection",
        examples=[
            "Find stocks with strong momentum",
            "Breakout candidates",
            "Momentum screening",
        ],
        requires_entities=False,
    ))
    
    registry.register_intent(IntentDefinition(
        name="volatility",
        description="Volatility analysis for stocks",
        examples=[
            "How volatile is TSLA?",
            "Volatility comparison AAPL vs MSFT",
        ],
        synonyms=["volatilità"],
        requires_entities=True,
    ))
    
    registry.register_intent(IntentDefinition(
        name="allocate",
        description="Asset allocation with budget",
        examples=[
            "Invest 5000 euro in tech stocks",
            "Buy AAPL with $10000",
            "Allocate 10000 to my portfolio",
        ],
        synonyms=["invest", "investire", "comprare", "buy", "acquista"],
        requires_entities=True,
        requires_amount=True,
    ))
    
    registry.register_intent(IntentDefinition(
        name="portfolio",
        description="Portfolio management and analysis",
        examples=[
            "Analyze my portfolio",
            "Portfolio performance",
            "How is my collection doing?",
        ],
        synonyms=["portafoglio", "collection"],
        requires_entities=False,
    ))
    
    registry.register_intent(IntentDefinition(
        name="sentiment",
        description="Market sentiment analysis",
        examples=[
            "Market sentiment for AAPL",
            "How does the market feel about Tesla?",
            "Sentiment analysis for tech sector",
        ],
        requires_entities=True,
    ))
    
    registry.register_intent(IntentDefinition(
        name="backtest",
        description="Backtesting trading strategies",
        examples=[
            "Backtest momentum strategy",
            "Test this approach on historical data",
        ],
        requires_entities=False,
    ))
    
    registry.register_intent(IntentDefinition(
        name="horizon_advice",
        description="Investment time horizon questions",
        examples=[
            "Should I invest for 5 years?",
            "Short term vs long term strategies",
        ],
        requires_entities=False,
    ))
    
    # Screening filters
    registry.register_filter(ScreeningFilter(
        name="risk_tolerance",
        description="User risk preference",
        value_type="enum",
        enum_values=["low", "medium", "high"],
        keywords=["conservative", "prudent", "stable", "aggressive", "growth", "balanced"],
    ))
    
    registry.register_filter(ScreeningFilter(
        name="momentum_breakout",
        description="Strong momentum/breakout stocks",
        value_type="bool",
        keywords=["breakout", "momentum forte", "explosive", "rottura resistenza", "strong momentum"],
    ))
    
    registry.register_filter(ScreeningFilter(
        name="value_screening",
        description="Undervalued stocks",
        value_type="bool",
        keywords=["sottovalutati", "undervalued", "cheap", "buon prezzo", "bargain", "economici"],
    ))
    
    registry.register_filter(ScreeningFilter(
        name="divergence_detection",
        description="Divergence/contrarian signals",
        value_type="bool",
        keywords=["divergenza", "divergence", "contrarian", "reversal", "inversione"],
    ))
    
    registry.register_filter(ScreeningFilter(
        name="sector",
        description="Sector filter",
        value_type="string",
        keywords=["Technology", "Healthcare", "Energy", "Financial", "Consumer", "Industrial"],
    ))
    
    return registry


# ===========================================================================
# FINANCE ROUTE REGISTRY
# ===========================================================================

def create_finance_route_registry() -> RouteRegistry:
    """
    Create route registry for finance domain.
    
    Returns:
        RouteRegistry with finance-specific routes
    """
    registry = RouteRegistry(domain_name="finance")
    
    # Technical analysis execution
    registry.register_route(RouteDefinition(
        name="dispatcher_exec",
        description="Technical analysis execution",
        requires_entities=True,
    ))
    
    # Empathetic advisor for soft queries
    registry.register_route(RouteDefinition(
        name="llm_soft",
        description="Empathetic advisor for emotional/soft queries",
    ))
    
    # Slot filling for incomplete queries
    registry.register_route(RouteDefinition(
        name="slot_filler",
        description="Slot filling for incomplete queries",
    ))
    
    # Codex Hunters for ticker discovery
    registry.register_route(RouteDefinition(
        name="codex_expedition",
        description="Codex Hunters ticker discovery expedition",
    ))
    
    # Technical intent mappings
    technical_intents = [
        "trend", "momentum", "volatility", "risk",
        "backtest", "allocate", "portfolio", "sentiment"
    ]
    
    for intent in technical_intents:
        registry.register_intent_mapping(IntentRouteMapping(
            intent=intent,
            route="dispatcher_exec",
            priority=10,
        ))
    
    # Soft intent mappings
    registry.register_intent_mapping(IntentRouteMapping(
        intent="soft",
        route="llm_soft",
        priority=10,
    ))
    registry.register_intent_mapping(IntentRouteMapping(
        intent="horizon_advice",
        route="llm_soft",
        priority=10,
    ))
    
    # Unknown → slot_filler (higher priority than default fallback)
    registry.register_intent_mapping(IntentRouteMapping(
        intent="unknown",
        route="slot_filler",
        priority=5,
    ))
    
    # Custom router for Codex Hunters expedition
    def codex_expedition_router(state: Dict[str, Any]) -> Optional[str]:
        """Check if Codex Hunters expedition should be triggered."""
        # Skip if already has tickers
        if state.get("tickers") or state.get("entity_ids"):
            return None
        
        # Trigger on discovery-mode queries
        if state.get("screening_filters", {}).get("mode") == "discovery":
            return "codex_expedition"
        
        return None
    
    registry.register_custom_router(codex_expedition_router, priority=100)
    
    return registry


# ===========================================================================
# FINANCE GRAPH PLUGIN
# ===========================================================================

class FinanceGraphPlugin(GraphPlugin):
    """
    Finance domain plugin for LangGraph integration.
    
    Provides:
    - Domain-specific nodes (screener, portfolio, etc.)
    - Finance intent registry
    - Finance route registry
    - State extensions (tickers, budget, horizon)
    """
    
    def __init__(self):
        self._parser = FinanceParser()
        self._intent_registry = create_finance_intent_registry()
        self._route_registry = create_finance_route_registry()
        self._response_formatter = FinanceResponseFormatter()
        self._slot_filler = FinanceSlotFiller()
    
    def get_response_formatter(self) -> ResponseFormatter:
        """Return finance-specific response formatter."""
        return self._response_formatter
    
    def get_slot_filler(self) -> SlotFiller:
        """Return finance-specific slot filler."""
        return self._slot_filler
    
    def get_domain_name(self) -> str:
        return "finance"
    
    def get_nodes(self) -> Dict[str, Callable]:
        """
        Return finance-specific nodes.
        
        These nodes are added to the graph when finance domain is active.
        """
        # Import nodes lazily to avoid circular dependencies
        nodes = {}
        
        try:
            from core.orchestration.langgraph.node.screener_node import screener_node
            nodes["screener"] = screener_node
        except ImportError:
            logger.warning("screener_node not available")
        
        try:
            from core.orchestration.langgraph.node.portfolio_node import portfolio_node
            nodes["portfolio"] = portfolio_node
        except ImportError:
            logger.warning("portfolio_node not available")
        
        try:
            from core.orchestration.langgraph.node.sentiment_node import sentiment_node
            nodes["sentiment"] = sentiment_node
        except ImportError:
            logger.warning("sentiment_node not available")
        
        return nodes
    
    def get_route_map(self) -> Dict[str, str]:
        """
        Return intent → route mappings.
        
        This is used by route_node to determine the next node.
        """
        route_map = {}
        for mapping in self._route_registry._intent_mappings:
            route_map[mapping.intent] = mapping.route
        return route_map
    
    def get_intents(self) -> List[str]:
        """Return list of finance intents."""
        return self._intent_registry.get_intent_labels()
    
    def get_state_extensions(self) -> Dict[str, Any]:
        """
        Return default values for finance state extensions.
        
        These are merged into the initial state.
        """
        return {
            # Ticker fields
            "tickers": [],
            "ticker_count": 0,
            "company_names": [],
            
            # Budget fields
            "budget": None,
            "currency": "USD",
            
            # Horizon fields
            "horizon": None,
            "horizon_months": None,
            
            # Screening filters
            "risk_tolerance": None,
            "momentum_breakout": False,
            "value_screening": False,
            "divergence_detection": False,
            "sector_filter": None,
            
            # Technical data
            "raw_output": {},
            "technical_signals": [],
            
            # Portfolio
            "portfolio_id": None,
            "portfolio_context": {},
        }
    
    def get_domain_keywords(self) -> List[str]:
        """
        Return keywords that identify finance entities.
        
        Used by vault_node for domain-appropriate protection.
        """
        return ["ticker", "tickers", "entity_ids", "stock", "portfolio", "budget"]
    
    def get_entry_pipeline(self) -> List[str]:
        """
        Return finance-specific nodes for entry pipeline.
        
        These are inserted after parse/intent_detection, before routing.
        """
        # Finance needs entity resolution early in the pipeline
        return ["entity_resolver"]
    
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        """
        Return additional edges after routing.
        
        Format: (source_node, target_node)
        """
        return [
            # Sentiment analysis connects to exec
            ("sentiment", "exec"),
            # Screener connects to compose
            ("screener", "compose"),
            # Portfolio analysis connects to compose
            ("portfolio", "compose"),
        ]
    
    def get_parser(self) -> FinanceParser:
        """Return finance parser instance."""
        return self._parser
    
    def get_intent_registry(self) -> IntentRegistry:
        """Return finance intent registry."""
        return self._intent_registry
    
    def get_route_registry(self) -> RouteRegistry:
        """Return finance route registry."""
        return self._route_registry
    
    def validate_state(self, state: Dict[str, Any]) -> List[str]:
        """
        Validate state for finance domain.
        
        Returns list of validation errors.
        """
        errors = []
        
        # Check for required fields based on intent
        intent = state.get("intent")
        
        if intent == "allocate":
            if not state.get("budget"):
                errors.append("Allocation requires budget field")
        
        # Validate tickers if present
        tickers = state.get("tickers", [])
        if tickers:
            for ticker in tickers:
                if not self._parser.validate_entity(ticker):
                    errors.append(f"Unknown ticker: {ticker}")
        
        return errors


# ===========================================================================
# FACTORY FUNCTION
# ===========================================================================

def get_finance_plugin() -> FinanceGraphPlugin:
    """
    Get finance domain plugin instance.
    
    Usage:
        from domains.finance_plugin import get_finance_plugin
        
        plugin = get_finance_plugin()
        GraphEngine().with_plugin(plugin).build()
    """
    return FinanceGraphPlugin()


# ===========================================================================
# EXPORTS
# ===========================================================================

__all__ = [
    "FinanceGraphPlugin",
    "FinanceParser",
    "FinanceStateExtension",
    "get_finance_plugin",
    "create_finance_intent_registry",
    "create_finance_route_registry",
]
