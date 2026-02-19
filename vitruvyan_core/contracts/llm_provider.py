"""
ILLMProvider - Protocol for pluggable LLM providers.

Canonical location: ``vitruvyan_core/contracts``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ILLMProvider(Protocol):
    """Structural protocol for LLM providers."""

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
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
        ...

    def complete_with_messages(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
        ...

    def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        ...

    async def acomplete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        ...
