"""
Prompt Policy Enforcement
=========================

Lightweight policy application for prompt composition.

The core defines the mechanism; verticals define the content.
Policy is applied as post-processing on the resolved prompt text.

Author: vitruvyan-core
Date: March 10, 2026
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from contracts.prompting import PromptPolicy

logger = logging.getLogger(__name__)

# ── Language-agnostic policy fragments ───────────────────────────────────────

_LIMITATION_FRAGMENTS: Dict[str, str] = {
    "en": "\nIMPORTANT: Always declare your limitations. If you are uncertain, say so explicitly.",
    "it": "\nIMPORTANTE: Dichiara sempre i tuoi limiti. Se non sei certo, dillo esplicitamente.",
    "es": "\nIMPORTANTE: Declara siempre tus limitaciones. Si no estás seguro, dilo explícitamente.",
    "fr": "\nIMPORTANT: Déclarez toujours vos limites. Si vous n'êtes pas sûr, dites-le explicitement.",
}

_EVIDENCE_FRAGMENTS: Dict[str, str] = {
    "en": "\nAlways cite evidence and sources when available. Do not fabricate information.",
    "it": "\nCita sempre evidenze e fonti quando disponibili. Non fabbricare informazioni.",
    "es": "\nCita siempre evidencias y fuentes cuando estén disponibles. No fabriques información.",
    "fr": "\nCitez toujours les preuves et sources disponibles. Ne fabriquez pas d'informations.",
}

_DOMAIN_BOUNDARY_FRAGMENTS: Dict[str, str] = {
    "en": "\nStay within your domain of expertise. Decline requests outside your scope.",
    "it": "\nResta nel tuo dominio di competenza. Declina richieste fuori dal tuo ambito.",
    "es": "\nMantente dentro de tu dominio de experiencia. Rechaza solicitudes fuera de tu alcance.",
    "fr": "\nRestez dans votre domaine d'expertise. Refusez les demandes hors de votre champ.",
}


def apply_policy(
    prompt: str,
    policy: PromptPolicy,
    language: str = "en",
) -> str:
    """
    Apply policy constraints to a resolved prompt.

    Appends non-negotiable fragments based on active policy flags.
    Returns the original prompt unchanged if no constraints are active.

    Args:
        prompt: The resolved system prompt text.
        policy: Policy constraints to enforce.
        language: ISO 639-1 language code for fragment selection.

    Returns:
        Prompt with policy fragments appended (if any).
    """
    if not policy.has_constraints:
        return prompt

    parts = [prompt]

    if policy.must_declare_limitations:
        parts.append(_LIMITATION_FRAGMENTS.get(language, _LIMITATION_FRAGMENTS["en"]))

    if policy.must_cite_evidence:
        parts.append(_EVIDENCE_FRAGMENTS.get(language, _EVIDENCE_FRAGMENTS["en"]))

    if policy.must_stay_in_domain:
        parts.append(_DOMAIN_BOUNDARY_FRAGMENTS.get(language, _DOMAIN_BOUNDARY_FRAGMENTS["en"]))

    # Append domain-specific disclaimers (provided by the vertical)
    disclaimer = policy.required_disclaimers.get(language)
    if not disclaimer:
        disclaimer = policy.required_disclaimers.get("en")
    if disclaimer:
        parts.append(f"\nDISCLAIMER: {disclaimer}")

    return "".join(parts)
