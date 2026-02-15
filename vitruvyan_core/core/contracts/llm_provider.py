"""
ILLMProvider — Protocol for pluggable LLM providers.

Allows LLMAgent to work with OpenAI, Anthropic, local models, or any
backend that implements this protocol.  The default implementation uses
the OpenAI SDK, but verticals/tests can swap in alternative providers
without changing any node or service code.

Usage (type-checking only — no runtime registration needed)::

    from core.contracts.llm_provider import ILLMProvider

    class AnthropicProvider:
        \"\"\"Implements ILLMProvider structurally (duck typing).\"\"\"
        def complete(self, prompt, *, system_prompt=None, model=None, **kw):
            ...
        def complete_json(self, prompt, *, system_prompt=None, model=None, **kw):
            ...

    provider: ILLMProvider = AnthropicProvider()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ILLMProvider(Protocol):
    """Structural protocol for LLM providers.

    Any class matching this interface is automatically a valid provider
    (structural subtyping — no inheritance needed).
    """

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
        """Single-turn text completion.

        Returns:
            Response text (str).
        """
        ...

    def complete_json(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """JSON-structured output.

        Returns:
            Parsed dict from the LLM response.
        """
        ...

    def complete_with_messages(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
        """Multi-turn conversation.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.

        Returns:
            Response text.
        """
        ...

    def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """OpenAI Function Calling / tool-use.

        Returns:
            Raw API response dict (tool_calls, content, etc.).
        """
        ...

    async def acomplete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Async single-turn completion."""
        ...
