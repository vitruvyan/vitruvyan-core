# vitruvyan_core/core/orchestration/compose/__init__.py
"""
Compose layer abstractions for domain-agnostic response composition.

This package provides the base classes and utilities for composing
responses in the orchestration layer, allowing domain plugins to
inject their own formatting logic.
"""

from vitruvyan_core.core.orchestration.compose.base_composer import (
    BaseComposer,
    ComposerResult,
)
from vitruvyan_core.core.orchestration.compose.response_formatter import (
    ResponseFormatter,
    FormattedResponse,
    ConversationType,
)
from vitruvyan_core.core.orchestration.compose.slot_filler import (
    SlotFiller,
    SlotQuestion,
)

__all__ = [
    "BaseComposer",
    "ComposerResult",
    "ResponseFormatter",
    "FormattedResponse",
    "ConversationType",
    "SlotFiller",
    "SlotQuestion",
]
