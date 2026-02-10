"""
Babel Gardens - Pure Consumers
==============================

Pure processing logic for Babel Gardens.
NO I/O - all consumers work with in-memory data only.

Consumers:
- SynthesisConsumer: Linguistic vector fusion
- TopicClassifierConsumer: Topic classification from configurable taxonomy
- LanguageDetectorConsumer: Language detection (heuristic)

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026)
"""

from .base import BaseConsumer, ProcessResult
from .synthesis import SynthesisConsumer
from .classifiers import TopicClassifierConsumer, LanguageDetectorConsumer

__all__ = [
    # Base
    "BaseConsumer",
    "ProcessResult",
    # Consumers
    "SynthesisConsumer",
    "TopicClassifierConsumer",
    "LanguageDetectorConsumer",
]
