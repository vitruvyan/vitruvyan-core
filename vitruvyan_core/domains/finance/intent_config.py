"""
Finance Domain — Intent Configuration
======================================

Registers finance-specific intents and screening filters
into the IntentRegistry for intent_detection_node.

This is the ONLY place where finance vocabulary lives.
The core intent_detection_node is domain-agnostic.

Usage:
    from domains.finance.intent_config import register_finance_intents
    
    registry = IntentRegistry(domain_name="finance")
    register_finance_intents(registry)
    prompt = registry.build_classification_prompt(user_input)

Author: Vitruvyan Core Team
Created: February 12, 2026
"""

from core.orchestration.intent_registry import (
    IntentDefinition,
    IntentRegistry,
    ScreeningFilter,
)


def register_finance_intents(registry: IntentRegistry) -> IntentRegistry:
    """
    Register all finance-domain intents and screening filters.
    
    Args:
        registry: IntentRegistry to populate
        
    Returns:
        The same registry (for chaining)
    """
    # ------------------------------------------------------------------
    # INTENTS
    # ------------------------------------------------------------------
    intents = [
        IntentDefinition(
            name="trend",
            description="Entity analysis, technical analysis",
            examples=[
                "Analizza AAPL",
                "How is NVDA doing?",
                "Analyze Tesla stock",
            ],
            synonyms=["analizza", "analyze", "study"],
            requires_entities=True,
        ),
        IntentDefinition(
            name="risk",
            description="Risk assessment of specific entities",
            examples=[
                "What's the risk on TSLA?",
                "Rischio portafoglio",
            ],
            synonyms=["rischio"],
            requires_entities=True,
        ),
        IntentDefinition(
            name="collection",
            description="Portfolio / collection management",
            examples=[
                "My portfolio",
                "Analizza il mio portafoglio",
                "Portfolio review",
            ],
            synonyms=["portfolio", "portafoglio", "portfolio_review"],
        ),
        IntentDefinition(
            name="sentiment",
            description="Market sentiment analysis",
            examples=[
                "Sentiment AAPL",
                "What people think about NVDA",
            ],
            synonyms=[],
        ),
        IntentDefinition(
            name="momentum",
            description="Momentum indicators (RSI, MACD, breakout detection)",
            examples=[
                "Trova titoli con forte momentum breakout",
                "Strong momentum stocks",
            ],
            synonyms=[],
        ),
        IntentDefinition(
            name="volatility",
            description="Volatility analysis",
            examples=[
                "Volatility on AAPL",
                "Volatilità NVDA",
            ],
            synonyms=["volatilità"],
        ),
        IntentDefinition(
            name="backtest",
            description="Backtesting strategies",
            examples=[
                "Backtest RSI strategy on AAPL",
            ],
            synonyms=[],
        ),
        IntentDefinition(
            name="allocate",
            description="Asset allocation",
            examples=[
                "Investi 5000 euro in tech",
                "Allocate $10000",
            ],
            synonyms=[
                "invest", "investire", "comprare",
                "buy", "acquista", "acquisto",
            ],
            requires_amount=True,
        ),
        IntentDefinition(
            name="horizon_advice",
            description="Investment time horizon questions",
            examples=[
                "Quanto tempo tenere AAPL?",
                "Best horizon for tech stocks?",
            ],
            synonyms=[],
        ),
    ]
    for intent in intents:
        registry.register_intent(intent)

    # ------------------------------------------------------------------
    # SCREENING FILTERS
    # ------------------------------------------------------------------
    filters = [
        ScreeningFilter(
            name="risk_tolerance",
            description="User risk preference",
            value_type="enum",
            enum_values=["low", "medium", "high"],
            keywords=["conservative", "prudent", "stable", "balanced",
                       "aggressive", "growth", "prudente", "conservativo"],
        ),
        ScreeningFilter(
            name="momentum_breakout",
            description="Strong momentum / breakout entities",
            value_type="bool",
            keywords=["breakout", "momentum forte", "explosive",
                       "rottura resistenza"],
        ),
        ScreeningFilter(
            name="value_screening",
            description="Undervalued entities",
            value_type="bool",
            keywords=["sottovalutati", "undervalued", "cheap",
                       "buon prezzo", "bargain", "economici"],
        ),
        ScreeningFilter(
            name="divergence_detection",
            description="Divergence / contrarian signals",
            value_type="bool",
            keywords=["divergenza", "divergence", "segnale contrarian",
                       "reversal", "inversione"],
        ),
        ScreeningFilter(
            name="multi_timeframe_filter",
            description="Multi-timeframe consensus",
            value_type="bool",
            keywords=["consensus multi-timeframe", "allineamento timeframe",
                       "trend confermato su tutti i timeframe"],
        ),
        ScreeningFilter(
            name="sector",
            description="Sector filter",
            value_type="enum",
            enum_values=[
                "Technology", "Healthcare", "Energy", "Financial Services",
                "Consumer Cyclical", "Industrials", "Real Estate",
                "Basic Materials", "Communication Services", "Utilities",
                "Consumer Defensive",
            ],
            keywords=[],
        ),
        ScreeningFilter(
            name="mode",
            description="Analysis mode",
            value_type="enum",
            enum_values=["analyze", "discovery", "comparative", "sector"],
            keywords=[],
        ),
    ]
    for f in filters:
        registry.register_filter(f)

    return registry


# ------------------------------------------------------------------
# PROFESSIONAL BOUNDARIES — context keywords per intent
# ------------------------------------------------------------------

CONTEXT_KEYWORDS: dict[str, list[str]] = {
    "risk": [
        "volatility", "volatilità", "rischio", "risk", "sicuro",
        "protezione", "hedge", "copertura", "difesa", "prudente",
        "conservativo", "safe", "protect", "defensive",
        "riesgo", "seguro", "protección", "volatilidad",
    ],
    "collection": [
        "collection", "portafoglio", "il mio", "mio", "my",
        "holdings", "posizioni", "investimenti", "asset",
        "allocazione", "my collection", "my holdings",
        "mi cartera", "mis inversiones",
    ],
    "sentiment": [
        "sentiment", "opinione", "opinion", "cosa pensa",
        "people think", "mercato dice", "buzz", "social",
        "reddit", "sentimiento", "opinión pública",
    ],
    "momentum": [
        "momentum", "breakout", "rottura", "resistenza",
        "esplosivo", "forte momentum", "accelerazione",
        "impulso", "spinta", "strong momentum",
    ],
    "volatility": [
        "volatilità", "volatility", "oscillazione", "instabilità",
        "fluttuazione", "variazione", "swing", "volatile",
    ],
    "allocate": [
        "investire", "comprare", "acquisto", "allocare", "budget",
        "capitale", "somma", "euro", "dollari", "$", "€",
        "invest", "buy", "allocate", "capital",
    ],
    # These intents are always allowed (no keyword check)
    "trend": [],
    "backtest": [],
    "soft": [],
    "horizon_advice": [],
    "unknown": [],
}

# Ambiguous patterns (regex) — always reject regardless of GPT classification
AMBIGUOUS_PATTERNS: list[str] = [
    r'\b(ho|posseggo|detengo)\s+(troppo|poco|tanto|molto)\s+[A-Z]{1,5}\b',
    r'\b(conviene|vale la pena)\s*\??$',
    r'\b(e|ma|però)\s+[A-Z]{1,5}\s*\??$',
    r'\b(i have|i hold)\s+(too much|too little)\s+[A-Z]{1,5}\b',
    r'\b(is it worth|should i)\s*\??$',
    r'\b(what about|how about)\s+[A-Z]{1,5}\s*\??$',
]


def create_finance_registry() -> IntentRegistry:
    """
    Factory: create a fully-configured finance IntentRegistry.
    
    Returns:
        IntentRegistry with all finance intents + filters registered
    """
    registry = IntentRegistry(domain_name="finance")
    register_finance_intents(registry)
    return registry
