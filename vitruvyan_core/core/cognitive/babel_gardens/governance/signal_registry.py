"""
Babel Gardens — Comprehension Plugin & Signal Contributor Registries
====================================================================

Two registries:
1. ComprehensionPluginRegistry → domain plugins that shape the unified LLM prompt
2. SignalContributorRegistry   → domain model contributors (Layer 2)

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 26, 2026 14:00 UTC

Author: Vitruvyan Core Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional

try:
    from contracts.comprehension import (
        ComprehensionResult,
        IComprehensionPlugin,
        ISignalContributor,
    )
except ModuleNotFoundError:
    from vitruvyan_core.contracts.comprehension import (
        ComprehensionResult,
        IComprehensionPlugin,
        ISignalContributor,
    )

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Generic Comprehension Plugin (always available)
# ─────────────────────────────────────────────────────────────

_GENERIC_ONTOLOGY_PROMPT = """\
=== ONTOLOGY SECTION ===
Extract structured ontology from the user query.

Produce the "ontology" JSON object with EXACTLY these fields:
{
  "gate": {
    "verdict": "in_domain" | "out_of_domain" | "ambiguous",
    "domain": "generic",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief>"
  },
  "entities": [
    {"raw": "<text>", "canonical": "<normalized>", "entity_type": "concept"|"entity"|"person"|"organization"|"location"|"event", "confidence": <0.0-1.0>}
  ],
  "intent_hint": "question"|"command"|"exploration"|"comparison"|"unknown",
  "topics": ["<topic1>"],
  "sentiment_hint": "positive"|"negative"|"neutral"|"mixed",
  "temporal_context": "real_time"|"historical"|"forward_looking",
  "language": "<ISO 639-1>",
  "complexity": "simple"|"compound"|"multi_intent"
}
"""

_GENERIC_SEMANTICS_PROMPT = """\
=== SEMANTICS SECTION ===
Analyze HOW the text is expressed — sentiment, emotion, and linguistic quality.

Produce the "semantics" JSON object with EXACTLY these fields:
{
  "sentiment": {
    "label": "positive"|"negative"|"neutral"|"mixed",
    "score": <-1.0 to 1.0>,
    "confidence": <0.0-1.0>,
    "magnitude": <0.0-1.0>,
    "aspects": [{"aspect": "<topic>", "sentiment": "<label>", "score": <-1.0 to 1.0>}],
    "reasoning": "<brief>"
  },
  "emotion": {
    "primary": "<emotion>",
    "secondary": ["<emotion>"],
    "intensity": <0.0-1.0>,
    "confidence": <0.0-1.0>,
    "cultural_context": "<style or neutral>",
    "reasoning": "<brief>"
  },
  "linguistic": {
    "text_register": "formal"|"informal"|"technical"|"colloquial"|"neutral",
    "irony_detected": true|false,
    "ambiguity_score": <0.0-1.0>,
    "code_switching": true|false
  }
}

Primary emotions: frustrated, excited, curious, anxious, confident, satisfied, bored, skeptical, neutral.
Sarcasm/irony: detect it — "perfetto, un altro errore" = frustrated, NOT satisfied.
Factual statements with no opinion = neutral sentiment, low magnitude.
"""


class GenericComprehensionPlugin(IComprehensionPlugin):
    """Default domain-agnostic comprehension plugin."""

    def get_domain_name(self) -> str:
        return "generic"

    def get_ontology_prompt_section(self) -> str:
        return _GENERIC_ONTOLOGY_PROMPT

    def get_semantics_prompt_section(self) -> str:
        return _GENERIC_SEMANTICS_PROMPT

    def get_entity_types(self) -> List[str]:
        return ["concept", "entity", "person", "organization", "location", "event"]

    def get_gate_keywords(self) -> List[str]:
        return []

    def get_intent_vocabulary(self) -> List[str]:
        return ["question", "command", "exploration", "comparison", "unknown"]

    def get_topic_vocabulary(self) -> List[str]:
        return []


# ─────────────────────────────────────────────────────────────
# Comprehension Plugin Registry
# ─────────────────────────────────────────────────────────────

class ComprehensionPluginRegistry:
    """
    Registry for domain comprehension plugins.

    Each domain registers ONE plugin that shapes both the ontology
    and semantics sections of the unified LLM prompt.
    """

    def __init__(self):
        self._plugins: Dict[str, IComprehensionPlugin] = {}
        self._generic = GenericComprehensionPlugin()
        self._plugins["generic"] = self._generic
        self._default_domain: Optional[str] = None

    def register(self, plugin: IComprehensionPlugin) -> None:
        """Register a domain comprehension plugin."""
        name = plugin.get_domain_name()
        if name in self._plugins and name != "generic":
            logger.warning(f"Overwriting comprehension plugin for domain '{name}'")
        self._plugins[name] = plugin
        logger.info(
            f"Comprehension plugin registered: domain='{name}', "
            f"entity_types={plugin.get_entity_types()}"
        )

    def set_default_domain(self, domain: str) -> None:
        """Set the default domain used when resolve() gets 'auto'."""
        if domain not in self._plugins:
            logger.warning(
                f"set_default_domain('{domain}') — domain not yet registered, "
                f"available: {list(self._plugins.keys())}"
            )
        self._default_domain = domain
        logger.info(f"Default comprehension domain set to '{domain}'")

    def get(self, domain: str) -> IComprehensionPlugin:
        """Get plugin by domain. Falls back to generic."""
        return self._plugins.get(domain, self._generic)

    def resolve(self, domain: str) -> IComprehensionPlugin:
        """
        Resolve domain to plugin.

        - 'auto' → default domain if set, else best available, else generic
        - explicit domain → look up or fall back to generic
        """
        if domain == "auto":
            # 1. Explicit default set by service layer
            if self._default_domain and self._default_domain in self._plugins:
                return self._plugins[self._default_domain]
            # 2. Single domain-specific plugin registered → use it
            non_generic = [d for d in self._plugins if d != "generic"]
            if len(non_generic) == 1:
                return self._plugins[non_generic[0]]
            # 3. Fall back to generic
            return self._generic
        return self.get(domain)

    @property
    def registered_domains(self) -> List[str]:
        return list(self._plugins.keys())

    def has_domain(self, domain: str) -> bool:
        return domain in self._plugins


# ─────────────────────────────────────────────────────────────
# Signal Contributor Registry
# ─────────────────────────────────────────────────────────────

class SignalContributorRegistry:
    """
    Registry for Layer 2 domain signal contributors.

    Contributors are specialized models (FinBERT, SecBERT, BioBERT, …)
    that live in domain code and produce SignalEvidence objects.
    """

    def __init__(self):
        self._contributors: Dict[str, ISignalContributor] = {}

    def register(self, contributor: ISignalContributor) -> None:
        """Register a signal contributor."""
        name = contributor.get_contributor_name()
        if name in self._contributors:
            logger.warning(f"Overwriting signal contributor '{name}'")
        self._contributors[name] = contributor
        logger.info(
            f"Signal contributor registered: name='{name}', "
            f"signals={contributor.get_signal_names()}"
        )

    def get(self, name: str) -> Optional[ISignalContributor]:
        """Get contributor by name. Returns None if not found."""
        return self._contributors.get(name)

    def get_all(self) -> List[ISignalContributor]:
        """Get all registered contributors."""
        return list(self._contributors.values())

    def get_available(self) -> List[ISignalContributor]:
        """Get only contributors whose models are loaded and ready."""
        return [c for c in self._contributors.values() if c.is_available()]

    @property
    def registered_names(self) -> List[str]:
        return list(self._contributors.keys())

    def has_contributor(self, name: str) -> bool:
        return name in self._contributors


# ─────────────────────────────────────────────────────────────
# Module-level singletons
# ─────────────────────────────────────────────────────────────

_comprehension_registry: Optional[ComprehensionPluginRegistry] = None
_signal_registry: Optional[SignalContributorRegistry] = None


def get_comprehension_registry() -> ComprehensionPluginRegistry:
    """Get global comprehension plugin registry (lazy init)."""
    global _comprehension_registry
    if _comprehension_registry is None:
        _comprehension_registry = ComprehensionPluginRegistry()
    return _comprehension_registry


def get_signal_contributor_registry() -> SignalContributorRegistry:
    """Get global signal contributor registry (lazy init)."""
    global _signal_registry
    if _signal_registry is None:
        _signal_registry = SignalContributorRegistry()
    return _signal_registry


__all__ = [
    "GenericComprehensionPlugin",
    "ComprehensionPluginRegistry",
    "SignalContributorRegistry",
    "get_comprehension_registry",
    "get_signal_contributor_registry",
]
