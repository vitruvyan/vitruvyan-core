# core/cognitive/babel_gardens/__init__.py
"""
Babel Gardens — Sacred Order #2
================================

Tower of Linguistic Unity for multilingual AI capabilities.

LIVELLO 1 exports (pure domain, no I/O):
- Domain: BabelConfig, TopicConfig, entities
- Consumers: SynthesisConsumer, TopicClassifierConsumer
- Events: Channels, EventEnvelope
- Monitoring: MetricNames, HealthCheckNames

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026 - Domain-Agnostic Refactoring)
"""

# Domain layer
from .domain import (
    BabelConfig,
    get_config,
    set_config,
    load_config_from_yaml,
    TopicConfig,
    TopicCategory,
    # Entities
    EmbeddingResult,
    SentimentResult,
    EmotionResult,
    ProcessingStatus,
)

# Pure consumers
from .consumers import (
    SynthesisConsumer,
    TopicClassifierConsumer,
    LanguageDetectorConsumer,
    ProcessResult,
)

# Events
from .events import Channels, EventEnvelope

# Monitoring
from .monitoring import MetricNames, HealthCheckNames

# Legacy compatibility (deprecated - do not import at module level)
# These require infrastructure (Postgres, Redis) and should not pollute LIVELLO 1
# Use: from core.cognitive.babel_gardens._legacy.xxx import YYY
LinguisticSynthesisEngine = None
babel_gardens_listener = None

__all__ = [
    # Config
    "BabelConfig",
    "get_config",
    "set_config",
    "load_config_from_yaml",
    "TopicConfig",
    "TopicCategory",
    # Entities
    "EmbeddingResult",
    "SentimentResult",
    "EmotionResult",
    "ProcessingStatus",
    # Consumers
    "SynthesisConsumer",
    "TopicClassifierConsumer",
    "LanguageDetectorConsumer",
    "ProcessResult",
    # Events
    "Channels",
    "EventEnvelope",
    # Monitoring
    "MetricNames",
    "HealthCheckNames",
    # Legacy (deprecated)
    "LinguisticSynthesisEngine",
    "babel_gardens_listener",
]
