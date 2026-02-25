"""
Volatility Perception - Heuristic Lexicon Extractor
===================================================

Implements the finance signal `volatility_perception` in range [0, 1].
This signal is defined as heuristic in YAML (`heuristic:lexicon`).
"""

from datetime import datetime, timezone
from typing import Dict

from core.cognitive.babel_gardens.domain import SignalExtractionResult, SignalSchema

VOLATILITY_LEXICON: Dict[str, float] = {
    # English
    "volatile": 0.7,
    "volatility": 0.8,
    "turbulent": 0.7,
    "turbulence": 0.75,
    "crash": 0.95,
    "plunge": 0.9,
    "surge": 0.6,
    "spike": 0.65,
    "selloff": 0.85,
    "sell-off": 0.85,
    "panic": 0.9,
    "freefall": 0.95,
    "whipsaw": 0.8,
    "rollercoaster": 0.7,
    "correction": 0.6,
    "flash crash": 0.95,
    "circuit breaker": 0.9,
    "margin call": 0.85,
    "black swan": 0.95,
    "meltdown": 0.9,
    "contagion": 0.8,
    "uncertainty": 0.5,
    "unstable": 0.6,
    "erratic": 0.65,
    "swing": 0.5,
    "fluctuation": 0.55,
    "gyration": 0.6,
    # Italian
    "volatilità": 0.8,
    "crollo": 0.9,
    "turbolenza": 0.75,
    "panico": 0.9,
    "ribasso": 0.5,
    "oscillazione": 0.55,
    "instabile": 0.6,
    "incertezza": 0.5,
    "vendita massiva": 0.85,
    # Spanish
    "volatilidad": 0.8,
    "desplome": 0.9,
    "turbulencia": 0.75,
    "pánico": 0.9,
    "caída": 0.6,
    "oscilación": 0.55,
    # French
    "volatilité": 0.8,
    "effondrement": 0.9,
    "krach": 0.95,
    "panique": 0.9,
    "chute": 0.6,
    # German
    "volatilität": 0.8,
    "absturz": 0.9,
    "panik": 0.9,
    "einbruch": 0.85,
    "schwankung": 0.55,
}


def extract_volatility_perception(text: str, schema: SignalSchema) -> SignalExtractionResult:
    """Extract `volatility_perception` with max-intensity lexicon scoring."""
    if schema.name != "volatility_perception":
        raise ValueError(f"Expected 'volatility_perception', got '{schema.name}'")

    text_lower = text.lower()
    matched_terms: Dict[str, float] = {}

    for term, weight in VOLATILITY_LEXICON.items():
        if term in text_lower:
            matched_terms[term] = weight

    if matched_terms:
        raw_value = max(matched_terms.values())
        confidence = min(1.0, 0.3 + (len(matched_terms) * 0.15))
    else:
        raw_value = 0.0
        confidence = 0.1

    normalized_value = schema.normalize_value(raw_value)

    return SignalExtractionResult(
        signal_name="volatility_perception",
        value=normalized_value,
        confidence=confidence,
        extraction_trace={
            "method": "heuristic:lexicon",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "matched_terms": matched_terms,
            "computation": f"max({list(matched_terms.values()) or [0.0]}) = {raw_value:.3f}",
            "lexicon_size": len(VOLATILITY_LEXICON),
        },
        metadata={
            "text_length": len(text),
            "terms_matched": len(matched_terms),
        },
    )
