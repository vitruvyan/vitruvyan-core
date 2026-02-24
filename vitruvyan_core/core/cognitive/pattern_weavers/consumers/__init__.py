"""
Pattern Weavers - Consumer Layer
================================

Pure processing units. No I/O, no external dependencies.

Consumers:
- WeaverConsumer: Main semantic contextualization logic
- KeywordMatcherConsumer: Keyword-based matching fallback

Base:
- BaseConsumer: Abstract base with validation
- ProcessResult: Operation result dataclass
"""

from .base import BaseConsumer, ProcessResult
from .weaver import WeaverConsumer
from .keyword_matcher import KeywordMatcherConsumer
from .llm_compiler import LLMCompilerConsumer


__all__ = [
    "BaseConsumer",
    "ProcessResult",
    "WeaverConsumer",
    "KeywordMatcherConsumer",
    "LLMCompilerConsumer",
]
