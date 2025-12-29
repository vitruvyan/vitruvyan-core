# core/prompts/__init__.py
"""
🎯 Vitruvyan Prompt Management System

Centralizzato versioning e gestione dei prompt LLM.
Tutti i prompt sono Git-versionabili per tracking, A/B testing, e rollback.

Struttura:
- base_prompts.py: VITRUVYAN_SYSTEM_PROMPT principale
- scenario_prompts.py: Prompt specifici per scenari (analysis, recommendation, portfolio)
- emotion_fragments.py: Fragment emotivi per adattamento contestuale
- version.py: Gestione versioning prompt

Utilizzo:
    from core.prompts import get_active_prompt, PROMPT_VERSION
    
    prompt = get_active_prompt("detailed_analysis", language="it")
"""

from .base_prompts import (
    VITRUVYAN_SYSTEM_PROMPT_V1_0,
    get_base_prompt
)

from .scenario_prompts import (
    get_scenario_prompt,
    get_combined_prompt,
    SCENARIO_TYPES
)

from .version import (
    ACTIVE_PROMPT_VERSION,
    get_prompt_version,
    list_available_versions
)

__all__ = [
    "VITRUVYAN_SYSTEM_PROMPT_V1_0",
    "get_base_prompt",
    "get_scenario_prompt",
    "get_combined_prompt",
    "SCENARIO_TYPES",
    "ACTIVE_PROMPT_VERSION",
    "get_prompt_version",
    "list_available_versions"
]
