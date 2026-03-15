# domains/enterprise/babel_gardens/sentiment_config.py
"""
Enterprise Sentiment Configuration — Babel Gardens Domain Pack

Multi-model fusion weights and boost config for enterprise domain.
Mirrors finance FinanceSentimentConfig pattern.

Enterprise uses LLM-first (Nuclear Option) with no specialized model
(no FinBERT equivalent; ERP queries don't need financial sentiment).
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class EnterpriseSentimentConfig:
    """Frozen configuration for enterprise signal fusion."""

    domain_name: str = "enterprise"

    # Fusion weights (LLM-first — Nuclear Option)
    fusion_weights: Dict[str, float] = field(default_factory=lambda: {
        "llm": 0.65,              # Primary — enterprise queries are natural language
        "multilingual": 0.35,     # Cross-language support
    })

    # Boost factors for non-English and enterprise-specific context
    multilingual_boost: float = 1.3
    enterprise_context_boost: float = 1.15

    # Emotion vocabulary (enterprise-relevant subset)
    emotion_vocabulary: tuple = (
        "concerned", "satisfied", "frustrated",
        "urgent", "neutral", "optimistic",
        "confused", "confident",
    )


_DEFAULT = EnterpriseSentimentConfig()


def get_enterprise_fusion_weights() -> Dict[str, float]:
    """Return enterprise signal fusion weights."""
    return dict(_DEFAULT.fusion_weights)


def get_enterprise_model_boost(
    language: str = "en", is_enterprise: bool = True
) -> float:
    """Return contextual boost factor for the active model."""
    boost = 1.0
    if language != "en":
        boost *= _DEFAULT.multilingual_boost
    if is_enterprise:
        boost *= _DEFAULT.enterprise_context_boost
    return round(boost, 3)
