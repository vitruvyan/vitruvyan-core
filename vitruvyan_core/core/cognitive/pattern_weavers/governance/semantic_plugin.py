"""
Pattern Weavers — Semantic Plugin Registry
==========================================

Domain-agnostic plugin system for semantic compilation.
Plugins provide domain-specific prompts, entity types, and validation.

LIVELLO 1 — Pure Python, no I/O.

> **Last updated**: Feb 24, 2026 18:00 UTC

Author: Vitruvyan Core Team
Version: 3.0.0
"""

import logging
from typing import Dict, List, Optional

try:
    from contracts.pattern_weavers import ISemanticPlugin, OntologyPayload
except ModuleNotFoundError:
    from core.cognitive.pattern_weavers.domain import ISemanticPlugin, OntologyPayload

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Generic Plugin (always available, fallback)
# ─────────────────────────────────────────────────────────────

_GENERIC_SYSTEM_PROMPT = """\
You are a semantic compiler. Given a user query, extract structured ontology.

Return ONLY valid JSON matching this EXACT schema (no extra fields):
{
  "gate": {
    "verdict": "in_domain" | "out_of_domain" | "ambiguous",
    "domain": "generic",
    "confidence": <float 0.0-1.0>,
    "reasoning": "<brief explanation>"
  },
  "entities": [
    {
      "raw": "<text from query>",
      "canonical": "<normalized form>",
      "entity_type": "concept" | "entity" | "person" | "organization" | "location" | "event",
      "confidence": <float 0.0-1.0>
    }
  ],
  "intent_hint": "question" | "command" | "exploration" | "comparison" | "unknown",
  "topics": ["<topic1>", "<topic2>"],
  "sentiment_hint": "positive" | "negative" | "neutral" | "mixed",
  "temporal_context": "real_time" | "historical" | "forward_looking",
  "language": "<ISO 639-1 code>",
  "complexity": "simple" | "compound" | "multi_intent"
}

Gate rules:
- "in_domain" = query is about a concrete, identifiable topic
- "out_of_domain" = greeting, chitchat, nonsense
- "ambiguous" = unclear intent

Extract ALL named entities. If none found, return empty list.
"""


class GenericSemanticPlugin(ISemanticPlugin):
    """Default domain-agnostic plugin. Always registered."""

    def get_domain_name(self) -> str:
        return "generic"

    def get_system_prompt(self) -> str:
        return _GENERIC_SYSTEM_PROMPT

    def get_entity_types(self) -> List[str]:
        return ["concept", "entity", "person", "organization", "location", "event"]

    def get_gate_keywords(self) -> List[str]:
        return []  # No fast-path for generic

    def get_intent_vocabulary(self) -> List[str]:
        return ["question", "command", "exploration", "comparison", "unknown"]

    def get_topic_vocabulary(self) -> List[str]:
        return []  # Open vocabulary


# ─────────────────────────────────────────────────────────────
# Plugin Registry (singleton)
# ─────────────────────────────────────────────────────────────

class SemanticPluginRegistry:
    """
    Registry for domain semantic plugins.

    Plugins are registered at service startup. The registry provides
    lookup by domain name, with automatic fallback to the generic plugin.

    Thread-safe through the GIL (dict operations are atomic).
    """

    def __init__(self):
        self._plugins: Dict[str, ISemanticPlugin] = {}
        # Generic plugin is always available
        self._generic = GenericSemanticPlugin()
        self._plugins["generic"] = self._generic

    def register(self, plugin: ISemanticPlugin) -> None:
        """Register a domain plugin."""
        name = plugin.get_domain_name()
        if name in self._plugins and name != "generic":
            logger.warning(f"Overwriting existing plugin for domain '{name}'")
        self._plugins[name] = plugin
        logger.info(
            f"Semantic plugin registered: domain='{name}', "
            f"entity_types={plugin.get_entity_types()}"
        )

    def get(self, domain: str) -> ISemanticPlugin:
        """
        Get plugin by domain name.

        Returns generic plugin if domain not found.
        """
        return self._plugins.get(domain, self._generic)

    def resolve_domain(self, domain: str) -> ISemanticPlugin:
        """
        Resolve 'auto' to generic, or look up specific domain.

        Args:
            domain: 'auto' (use generic), or specific domain name

        Returns:
            Matching plugin, or generic fallback
        """
        if domain == "auto":
            return self._generic
        return self.get(domain)

    @property
    def registered_domains(self) -> List[str]:
        """Return list of registered domain names."""
        return list(self._plugins.keys())

    def has_domain(self, domain: str) -> bool:
        """Check if a domain plugin is registered."""
        return domain in self._plugins


# Module-level singleton
_registry: Optional[SemanticPluginRegistry] = None


def get_plugin_registry() -> SemanticPluginRegistry:
    """Get the global plugin registry (lazy init)."""
    global _registry
    if _registry is None:
        _registry = SemanticPluginRegistry()
    return _registry


def register_semantic_plugin(plugin: ISemanticPlugin) -> None:
    """Convenience: register a plugin in the global registry."""
    get_plugin_registry().register(plugin)


__all__ = [
    "GenericSemanticPlugin",
    "SemanticPluginRegistry",
    "get_plugin_registry",
    "register_semantic_plugin",
]
