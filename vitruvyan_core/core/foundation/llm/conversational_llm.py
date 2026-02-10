"""
Vitruvyan Core — Conversational LLM (Foundation Compatibility)
==============================================================

Re-exports ConversationalLLM from core.llm for backward compatibility.

Canonical location: core.llm.conversational_llm

Author: Vitruvyan Core Team  
Created: February 10, 2026
Status: COMPATIBILITY LAYER
"""

from core.llm.conversational_llm import ConversationalLLM

__all__ = ["ConversationalLLM"]
