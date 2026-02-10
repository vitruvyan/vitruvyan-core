# vitruvyan_core/domains/finance/__init__.py
"""
Finance domain package.

Provides finance-specific implementations for the Vitruvyan orchestration layer:
- ResponseFormatter for verdict/gauge/comparison formatting
- SlotFiller for investment-related slot questions
"""

from domains.finance.response_formatter import (
    FinanceResponseFormatter,
    FinanceConversationType,
    TECHNICAL_INTENTS,
    FACTOR_PHRASES,
    generate_final_verdict,
    generate_gauge,
    generate_comparison_matrix,
    generate_onboarding_cards,
    generate_factor_narrative,
)
from domains.finance.slot_filler import (
    FinanceSlotFiller,
    FINANCE_SLOTS,
    DEFAULT_QUESTIONS,
    EMOTION_QUESTIONS,
)

__all__ = [
    # Response formatter
    "FinanceResponseFormatter",
    "FinanceConversationType",
    "TECHNICAL_INTENTS",
    "FACTOR_PHRASES",
    "generate_final_verdict",
    "generate_gauge",
    "generate_comparison_matrix",
    "generate_onboarding_cards",
    "generate_factor_narrative",
    # Slot filler
    "FinanceSlotFiller",
    "FINANCE_SLOTS",
    "DEFAULT_QUESTIONS",
    "EMOTION_QUESTIONS",
]
