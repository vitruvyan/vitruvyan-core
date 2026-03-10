"""
Context Budget Manager — Token Budget Allocation for LLM Calls
===============================================================

Calculates and allocates the available context window across competing
inputs: system prompt, RAG chunks, conversation history, inline context,
and the response reservation.

Domain-agnostic: the core provides the mechanism. Verticals set priorities.

Usage:
    from core.llm.context_budget import ContextBudgetManager, ContextItem

    budget = ContextBudgetManager(model_context_window=128_000)
    items = [
        ContextItem(content=system_prompt, priority=0, source="system_prompt"),
        ContextItem(content=rag_chunk_1,   priority=1, source="rag"),
        ContextItem(content=rag_chunk_2,   priority=1, source="rag"),
        ContextItem(content=history_text,  priority=2, source="history"),
    ]
    selected = budget.allocate(items, max_response_tokens=1024)
    # selected contains only items that fit within the budget

Author: vitruvyan-core
Date: March 10, 2026
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Model context-window registry ────────────────────────────────────────────
# Conservative estimates. Verticals can extend via register_model().

_MODEL_CONTEXT_WINDOWS: Dict[str, int] = {
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
    "claude-sonnet": 200_000,
    "claude-opus": 200_000,
    "claude-haiku": 200_000,
}


def register_model(name: str, context_window: int) -> None:
    """Register (or override) a model's context window size."""
    _MODEL_CONTEXT_WINDOWS[name] = context_window


def get_context_window(model: str) -> int:
    """Return context window for a model. Falls back to 128k if unknown."""
    return _MODEL_CONTEXT_WINDOWS.get(model, 128_000)


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class ContextItem:
    """A piece of content competing for context-window space."""

    content: str
    priority: int = 1                  # 0 = highest (system prompt), higher = less important
    source: str = "unknown"            # "system_prompt", "rag", "history", "inline"
    estimated_tokens: int = 0          # Auto-computed if 0
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.estimated_tokens <= 0:
            self.estimated_tokens = estimate_tokens(self.content)


def estimate_tokens(text: str) -> int:
    """Fast heuristic: ~1.3 tokens per whitespace-delimited word."""
    if not text:
        return 0
    return max(1, int(len(text.split()) * 1.3))


# ── Budget manager ───────────────────────────────────────────────────────────

class ContextBudgetManager:
    """
    Allocates context-window budget across competing inputs.

    The manager sorts items by priority (0 = must-include) and greedily
    packs as many as fit within the remaining budget after reserving
    space for the model response.
    """

    def __init__(
        self,
        model_context_window: int = 128_000,
        safety_margin: int = 500,
    ):
        self.model_context_window = model_context_window
        self.safety_margin = safety_margin

    @classmethod
    def for_model(cls, model: str, safety_margin: int = 500) -> ContextBudgetManager:
        """Create a budget manager configured for a specific model."""
        return cls(
            model_context_window=get_context_window(model),
            safety_margin=safety_margin,
        )

    def available_budget(
        self,
        system_prompt_tokens: int = 0,
        max_response_tokens: int = 1024,
    ) -> int:
        """How many tokens remain for RAG + history + inline after prompt + response."""
        used = system_prompt_tokens + max_response_tokens + self.safety_margin
        return max(0, self.model_context_window - used)

    def allocate(
        self,
        items: List[ContextItem],
        max_response_tokens: int = 1024,
    ) -> List[ContextItem]:
        """
        Select items that fit within the budget, ordered by priority.

        Items with lower priority numbers are included first.
        Within the same priority, order is preserved (FIFO).

        Returns:
            Subset of items that fit, in original insertion order.
        """
        if not items:
            return []

        budget = self.model_context_window - max_response_tokens - self.safety_margin
        if budget <= 0:
            return []

        # Sort by priority (stable sort preserves insertion order within tier)
        indexed = list(enumerate(items))
        indexed.sort(key=lambda pair: pair[1].priority)

        selected_indices: List[int] = []
        remaining = budget

        for original_idx, item in indexed:
            if item.estimated_tokens <= remaining:
                selected_indices.append(original_idx)
                remaining -= item.estimated_tokens

        # Return in original insertion order
        selected_indices.sort()
        return [items[i] for i in selected_indices]
