# core/prompts/__init__.py
"""
🎯 Vitruvyan Prompt Management System — Domain-Agnostic

Provides a PromptRegistry for domains to register their own prompts.
Core provides infrastructure; domains provide content.

Architecture:
- registry.py: Domain-agnostic PromptRegistry (NEW)
- version.py: Version management
- _legacy/: Finance-specific prompts (archived)

New usage (recommended):
    from core.llm.prompts.registry import PromptRegistry, register_generic_domain
    
    # Register generic OS prompts
    register_generic_domain()
    
    # Or register domain-specific prompts
    from vitruvyan_core.domains.finance.prompts import register_finance_prompts
    register_finance_prompts()
    
    # Get prompts
    prompt = PromptRegistry.get_combined("finance", "detailed_analysis", "it", assistant_name="Vitruvyan")

Legacy usage (backward compatible):
    from core.llm.prompts import get_base_prompt, get_scenario_prompt
    prompt = get_base_prompt("it")  # Falls back to _legacy
"""

from .registry import PromptRegistry, register_generic_domain, GENERIC_IDENTITY, GENERIC_SCENARIOS
from .version import ACTIVE_PROMPT_VERSION, get_prompt_version, list_available_versions

# Auto-register generic OS prompts as fallback domain
register_generic_domain()

# Backward-compatible imports from legacy
try:
    from ._legacy import (
        VITRUVYAN_SYSTEM_PROMPT_V1_0,
        SCENARIO_TYPES,
        get_base_prompt,
        get_scenario_prompt,
        get_combined_prompt
    )
except ImportError:
    VITRUVYAN_SYSTEM_PROMPT_V1_0 = None
    SCENARIO_TYPES = []
    get_base_prompt = None
    get_scenario_prompt = None
    get_combined_prompt = None

__all__ = [
    # New API
    "PromptRegistry",
    "register_generic_domain",
    "GENERIC_IDENTITY",
    "GENERIC_SCENARIOS",
    # Version management
    "ACTIVE_PROMPT_VERSION",
    "get_prompt_version",
    "list_available_versions",
    # Legacy (backward compatible)
    "VITRUVYAN_SYSTEM_PROMPT_V1_0",
    "SCENARIO_TYPES",
    "get_base_prompt",
    "get_scenario_prompt",
    "get_combined_prompt"
]
