# core/llm/prompts/_legacy/__init__.py
"""
⚠️ LEGACY PROMPTS — ARCHIVED

These files contain the original finance-specific hardcoded prompts.
Preserved for backward compatibility and reference.

Migration:
- Finance prompts moved to: vitruvyan_core/domains/finance/prompts/
- Generic prompts available in: core/llm/prompts/registry.py
- New domains should register via: PromptRegistry.register_domain()

Files:
- base_prompts.py: Original VITRUVYAN_SYSTEM_PROMPT_V1_0
- scenario_prompts.py: Original SCENARIO_PROMPTS_V1_0

Archived: 2026-02-10
"""

from .base_prompts import (
    VITRUVYAN_SYSTEM_PROMPT_V1_0,
    get_base_prompt,
    get_compact_prompt
)

from .scenario_prompts import (
    SCENARIO_PROMPTS_V1_0,
    SCENARIO_TYPES,
    get_scenario_prompt,
    get_combined_prompt
)

__all__ = [
    "VITRUVYAN_SYSTEM_PROMPT_V1_0",
    "SCENARIO_PROMPTS_V1_0",
    "SCENARIO_TYPES",
    "get_base_prompt",
    "get_compact_prompt",
    "get_scenario_prompt",
    "get_combined_prompt"
]
