"""
Finance Sentiment Configuration
===============================

Finance-specific fusion weights, model boosting, and calibration config.
These override agnostic defaults when BABEL_DOMAIN=finance.

Ported from upstream multi-model sentiment fusion logic:
- LLM remains primary ("Nuclear Option")
- FinBERT contributes domain-specific signals
- Multilingual model supports cross-language robustness
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class FinanceSentimentConfig:
    """Finance-specific sentiment fusion configuration."""

    # Multi-model fusion weights (must sum to 1.0)
    fusion_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "llm": 0.45,  # LLM primary sentiment
            "finbert": 0.35,  # finance specialist
            "multilingual": 0.20,  # cross-language fallback/support
        }
    )

    # Language/content-aware boost factors
    multilingual_boost: float = 1.3
    finbert_boost: float = 1.2

    # Confidence calibration adjustments
    disagreement_penalty: float = 0.8
    agreement_bonus: float = 1.1
    confidence_power: float = 0.8

    # Online calibration parameters
    max_calibration_samples: int = 10000
    calibration_learning_rate: float = 0.01

    # FinBERT model defaults
    finbert_model: str = "ProsusAI/finbert"
    finbert_device: str = "cpu"
    finbert_max_length: int = 512
    finbert_batch_size: int = 16


def get_finance_fusion_weights() -> Dict[str, float]:
    """Return default finance fusion weights."""
    return FinanceSentimentConfig().fusion_weights


def get_finance_model_boost(language: str, is_financial: bool) -> Dict[str, float]:
    """
    Compute adjusted model weights based on language and content type.

    Non-English text boosts multilingual support.
    Financial context boosts FinBERT contribution.
    """
    config = FinanceSentimentConfig()
    weights = dict(config.fusion_weights)

    if language.lower() != "en" and "multilingual" in weights:
        weights["multilingual"] *= config.multilingual_boost

    if is_financial and "finbert" in weights:
        weights["finbert"] *= config.finbert_boost

    total = sum(weights.values())
    if total > 0:
        weights = {key: value / total for key, value in weights.items()}

    return weights
