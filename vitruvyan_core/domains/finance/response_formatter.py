# vitruvyan_core/domains/finance/response_formatter.py
"""
FinanceResponseFormatter - Finance-specific response formatting.

Extracts finance-specific logic from compose_node.py:
- Verdict generation
- Gauge (momentum/trend/volatility)
- Comparison matrix
- Onboarding cards
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from core.orchestration.compose.response_formatter import (
    ResponseFormatter,
    FormattedResponse,
    ConversationType,
    RawEngineOutput,
)


class FinanceConversationType(Enum):
    """Finance-specific conversation types."""
    SINGLE_ENTITY_ANALYSIS = "single_entity_analysis"
    MULTI_ENTITY_COMPARISON = "multi_entity_comparison"
    ALLOCATION_PREVIEW = "allocation_preview"
    SCREENING = "screening"
    ONBOARDING = "onboarding"
    CONVERSATIONAL = "conversational"


# Technical intents that require Neural Engine processing
TECHNICAL_INTENTS = [
    "analysis",
    "compare",
    "screening",
    "news",
    "price",
    "composition",
    "allocation",
    "portfolio_summary",
]


def generate_final_verdict(composite_score: float) -> Dict[str, Any]:
    """
    Generate a final verdict card based on composite score.
    
    Extracted from compose_node.py (line 307).
    
    Args:
        composite_score: The composite score from Neural Engine (-1 to 1)
        
    Returns:
        Dictionary with verdict details for frontend rendering
    """
    if composite_score >= 0.5:
        return {
            "verdict": "strong_buy",
            "label": "Strong Buy",
            "color": "green",
            "confidence": "high",
            "score": composite_score,
            "icon": "trending_up",
        }
    elif composite_score >= 0.2:
        return {
            "verdict": "buy",
            "label": "Buy",
            "color": "lightgreen",
            "confidence": "medium",
            "score": composite_score,
            "icon": "arrow_upward",
        }
    elif composite_score > -0.2:
        return {
            "verdict": "hold",
            "label": "Hold",
            "color": "yellow",
            "confidence": "neutral",
            "score": composite_score,
            "icon": "remove",
        }
    elif composite_score > -0.5:
        return {
            "verdict": "sell",
            "label": "Sell",
            "color": "orange",
            "confidence": "medium",
            "score": composite_score,
            "icon": "arrow_downward",
        }
    else:
        return {
            "verdict": "strong_sell",
            "label": "Strong Sell",
            "color": "red",
            "confidence": "high",
            "score": composite_score,
            "icon": "trending_down",
        }


def generate_gauge(
    momentum_z: Optional[float],
    trend_z: Optional[float],
    vola_z: Optional[float],
    sentiment_z: Optional[float],
) -> Dict[str, Any]:
    """
    Generate gauge (traffic light) for each factor.
    
    Extracted from compose_node.py (line 366).
    
    Args:
        momentum_z: Momentum z-score
        trend_z: Trend z-score
        vola_z: Volatility z-score
        sentiment_z: Sentiment z-score
        
    Returns:
        Dictionary with color codes for each factor
    """
    def score_to_color(score: Optional[float], invert: bool = False) -> str:
        """Convert z-score to traffic light color."""
        if score is None:
            return "gray"
        # For volatility, higher is worse (invert)
        if invert:
            score = -score
        if score > 0.5:
            return "green"
        elif score > 0:
            return "lightgreen"
        elif score > -0.5:
            return "yellow"
        elif score > -1:
            return "orange"
        else:
            return "red"
    
    return {
        "momentum": {
            "value": momentum_z,
            "color": score_to_color(momentum_z),
            "label": "Momentum",
        },
        "trend": {
            "value": trend_z,
            "color": score_to_color(trend_z),
            "label": "Trend",
        },
        "volatility": {
            "value": vola_z,
            "color": score_to_color(vola_z, invert=True),  # High vol = bad
            "label": "Volatility",
        },
        "sentiment": {
            "value": sentiment_z,
            "color": score_to_color(sentiment_z),
            "label": "Sentiment",
        },
    }


def generate_comparison_matrix(
    entity_ids: List[str],
    raw_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate comparison matrix for multi-entity comparison.
    
    Extracted from compose_node.py (line 423).
    
    Args:
        entity_ids: List of entities to compare
        raw_output: Raw output from Neural Engine
        
    Returns:
        List of entity rows sorted by composite score
    """
    ranking = raw_output.get("ranking", {})
    rows = []
    
    for group in ["entities", "etf", "funds"]:
        items = ranking.get(group, [])
        for item in items:
            entity_id = item.get("entity_id")
            if entity_id in entity_ids:
                factors = item.get("factors", {})
                rows.append({
                    "entity_id": entity_id,
                    "composite_score": item.get("composite_score"),
                    "momentum_z": factors.get("momentum_z"),
                    "trend_z": factors.get("trend_z"),
                    "vola_z": factors.get("vola_z"),
                    "sentiment_z": factors.get("sentiment_z"),
                    "rank": 0,  # Will be set after sorting
                })
    
    # Sort by composite score descending
    rows.sort(key=lambda x: x.get("composite_score") or -999, reverse=True)
    
    # Assign ranks
    for i, row in enumerate(rows):
        row["rank"] = i + 1
    
    return rows


def generate_onboarding_cards() -> List[Dict[str, Any]]:
    """
    Generate onboarding cards for first-time users.
    
    Extracted from compose_node.py (line 490).
    
    Returns:
        List of onboarding card definitions
    """
    return [
        {
            "id": "risk_profile",
            "title": "What's your risk tolerance?",
            "type": "single_choice",
            "options": [
                {"value": "conservative", "label": "Conservative", "icon": "shield"},
                {"value": "moderate", "label": "Moderate", "icon": "balance"},
                {"value": "aggressive", "label": "Aggressive", "icon": "rocket"},
            ],
        },
        {
            "id": "time_horizon",
            "title": "What's your investment horizon?",
            "type": "single_choice",
            "options": [
                {"value": "short", "label": "Short-term (< 1 year)", "icon": "sprint"},
                {"value": "medium", "label": "Medium-term (1-5 years)", "icon": "timer"},
                {"value": "long", "label": "Long-term (5+ years)", "icon": "hourglass"},
            ],
        },
        {
            "id": "experience",
            "title": "How would you describe your investment experience?",
            "type": "single_choice",
            "options": [
                {"value": "beginner", "label": "Beginner", "icon": "school"},
                {"value": "intermediate", "label": "Intermediate", "icon": "psychology"},
                {"value": "expert", "label": "Expert", "icon": "military_tech"},
            ],
        },
        {
            "id": "interests",
            "title": "What sectors interest you?",
            "type": "multi_choice",
            "options": [
                {"value": "tech", "label": "Technology", "icon": "computer"},
                {"value": "finance", "label": "Finance", "icon": "account_balance"},
                {"value": "healthcare", "label": "Healthcare", "icon": "local_hospital"},
                {"value": "energy", "label": "Energy", "icon": "bolt"},
                {"value": "consumer", "label": "Consumer", "icon": "shopping_cart"},
            ],
        },
    ]


# Factor phrases for different languages
FACTOR_PHRASES = {
    "en": {
        "momentum": ("momentum positive", "momentum weak"),
        "trend": ("trend strong", "trend weak"),
        "volatility": ("volatility high", "volatility contained"),
        "sentiment": ("sentiment bullish", "sentiment bearish"),
    },
    "it": {
        "momentum": ("momentum positivo", "momentum debole"),
        "trend": ("trend forte", "trend debole"),
        "volatility": ("volatilità alta", "volatilità contenuta"),
        "sentiment": ("sentiment rialzista", "sentiment ribassista"),
    },
    "es": {
        "momentum": ("momentum positivo", "momentum débil"),
        "trend": ("tendencia fuerte", "tendencia débil"),
        "volatility": ("volatilidad alta", "volatilidad contenida"),
        "sentiment": ("sentimiento alcista", "sentimiento bajista"),
    },
    "fr": {
        "momentum": ("momentum positif", "momentum faible"),
        "trend": ("tendance forte", "tendance faible"),
        "volatility": ("volatilité haute", "volatilité contenue"),
        "sentiment": ("sentiment haussier", "sentiment baissier"),
    },
}


def generate_factor_narrative(
    entity_id: str,
    factors: Dict[str, Optional[float]],
    language: str = "en",
) -> str:
    """
    Generate narrative description of factors.
    
    Args:
        entity_id: The entity being described
        factors: Factor z-scores (momentum_z, trend_z, vola_z, sentiment_z)
        language: ISO language code
        
    Returns:
        Human-readable narrative
    """
    phrases = FACTOR_PHRASES.get(language, FACTOR_PHRASES["en"])
    desc = []
    
    def factor_phrase(name: str, val: Optional[float]) -> str:
        if val is None:
            return f"{name} not available"
        pos, neg = phrases[name]
        return pos if val > 0 else neg
    
    if factors.get("momentum_z") is not None:
        desc.append(factor_phrase("momentum", factors.get("momentum_z")))
    if factors.get("trend_z") is not None:
        desc.append(factor_phrase("trend", factors.get("trend_z")))
    if factors.get("vola_z") is not None:
        desc.append(factor_phrase("volatility", factors.get("vola_z")))
    if factors.get("sentiment_z") is not None:
        desc.append(factor_phrase("sentiment", factors.get("sentiment_z")))
    
    if desc:
        return f"{entity_id}: {', '.join(desc)}."
    return f"{entity_id}: Data being processed."


class FinanceResponseFormatter(ResponseFormatter):
    """
    Finance-specific response formatter.
    
    Implements ResponseFormatter ABC with finance-specific logic for:
    - Verdict generation (composite score → buy/sell/hold)
    - Gauge generation (factor z-scores → traffic lights)
    - Comparison matrix for multi-entity analysis
    - Finance onboarding cards
    """
    
    def __init__(self, technical_intents: Optional[List[str]] = None):
        """
        Initialize the formatter.
        
        Args:
            technical_intents: List of intents requiring Neural Engine
        """
        self.technical_intents = technical_intents or TECHNICAL_INTENTS
    
    def detect_conversation_type(
        self,
        state: Dict[str, Any],
        raw_output: Optional[RawEngineOutput] = None,
    ) -> ConversationType:
        """
        Detect finance-specific conversation type.
        
        Logic extracted from compose_node.py (line 254).
        """
        intent = state.get("intent", "")
        entity_ids = state.get("entity_ids", [])
        has_ne_results = raw_output and "ranking" in raw_output
        user_input = state.get("input_text", "")
        
        # Onboarding detection
        if not entity_ids and intent in ("", "onboarding", "greeting"):
            return ConversationType.ONBOARDING
        
        # Single entity analysis
        if len(entity_ids) == 1 and intent in ("analysis", "price", "news"):
            return ConversationType.SINGLE_ENTITY
        
        # Multi-entity comparison
        if len(entity_ids) > 1 and intent in ("compare", "screening", "allocation"):
            return ConversationType.MULTI_ENTITY
        
        # Technical intent without clear entity count
        if intent in self.technical_intents:
            if len(entity_ids) <= 1:
                return ConversationType.SINGLE_ENTITY
            else:
                return ConversationType.MULTI_ENTITY
        
        # Default: conversational
        return ConversationType.CONVERSATIONAL
    
    def format_single_entity(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format single-entity analysis with verdict and gauge.
        """
        factors = entity_data.get("factors", entity_data)  # factors or flat dict
        composite = entity_data.get("composite_score")
        
        # Generate narrative
        narrative = generate_factor_narrative(entity_id, factors, language)
        
        # Add borderline warning if applicable
        if composite is not None and -0.2 < composite < 0.2:
            warnings = {
                "en": ", but the score is borderline: consider the risk",
                "it": ", ma il punteggio è borderline: valuta attentamente il rischio",
                "es": ", pero la puntuación es borderline: considera el riesgo",
            }
            narrative = narrative.rstrip(".") + warnings.get(language, warnings["en"]) + "."
        
        # Generate verdict and gauge
        verdict = generate_final_verdict(composite) if composite is not None else None
        gauge = generate_gauge(
            momentum_z=factors.get("momentum_z"),
            trend_z=factors.get("trend_z"),
            vola_z=factors.get("vola_z"),
            sentiment_z=factors.get("sentiment_z"),
        )
        
        return FormattedResponse(
            conversation_type=ConversationType.SINGLE_ENTITY,
            narrative=narrative,
            verdict=verdict,
            gauge=gauge,
            domain_data={
                "entity_id": entity_id,
                "composite_score": composite,
                "factors": factors,
            },
        )
    
    def format_multi_entity(
        self,
        entity_ids: List[str],
        raw_output: RawEngineOutput,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format multi-entity comparison with matrix.
        """
        comparison_matrix = generate_comparison_matrix(entity_ids, raw_output)
        
        # Generate narrative
        if comparison_matrix:
            top = comparison_matrix[0]
            narratives = {
                "en": f"{top['entity_id']} ranks first among {len(entity_ids)} entities with a composite score of {top.get('composite_score', 'N/A'):.2f}.",
                "it": f"{top['entity_id']} si classifica primo tra {len(entity_ids)} entità con un punteggio composito di {top.get('composite_score', 'N/A'):.2f}.",
                "es": f"{top['entity_id']} ocupa el primer lugar entre {len(entity_ids)} entidades con una puntuación compuesta de {top.get('composite_score', 'N/A'):.2f}.",
            }
            narrative = narratives.get(language, narratives["en"])
        else:
            narratives = {
                "en": f"Comparing {len(entity_ids)} entities.",
                "it": f"Confronto di {len(entity_ids)} entità.",
                "es": f"Comparando {len(entity_ids)} entidades.",
            }
            narrative = narratives.get(language, narratives["en"])
        
        return FormattedResponse(
            conversation_type=ConversationType.MULTI_ENTITY,
            narrative=narrative,
            comparison_matrix=comparison_matrix,
            domain_data={
                "entity_ids": entity_ids,
                "entity_count": len(entity_ids),
            },
        )
    
    def format_onboarding(
        self,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format finance onboarding with interactive cards.
        """
        cards = generate_onboarding_cards()
        
        narratives = {
            "en": "Welcome to your investment assistant! Let's set up your profile to provide personalized insights.",
            "it": "Benvenuto nel tuo assistente agli investimenti! Impostiamo il tuo profilo per offrirti approfondimenti personalizzati.",
            "es": "¡Bienvenido a tu asistente de inversiones! Configuremos tu perfil para brindarte información personalizada.",
        }
        
        return FormattedResponse(
            conversation_type=ConversationType.ONBOARDING,
            narrative=narratives.get(language, narratives["en"]),
            cards=cards,
        )
    
    def format_no_data(
        self,
        language: str,
        state: Dict[str, Any],
    ) -> FormattedResponse:
        """
        Format no-data response with finance-specific messaging.
        """
        messages = {
            "en": "Market data is not currently available, but we are processing it. Please try again in a few minutes.",
            "it": "I dati di mercato non sono momentaneamente disponibili, ma li stiamo elaborando. Riprova tra qualche minuto.",
            "es": "Los datos de mercado no están disponibles en este momento, pero los estamos procesando. Vuelve a intentarlo en unos minutos.",
        }
        
        return FormattedResponse(
            conversation_type=ConversationType.NO_DATA,
            narrative=messages.get(language, messages["en"]),
            domain_data={
                "entity_ids": state.get("entity_ids", []),
                "route": "no_data",
            },
        )
