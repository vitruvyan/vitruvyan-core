"""
Vitruvyan Core — Governance Rule Registry
==========================================

Domain-agnostic registry for governance compliance rules.

The GovernanceRuleRegistry allows domains to:
- Register domain-specific compliance rules (finance, healthcare, legal, etc.)
- Extend the default generic ruleset with domain rules
- Keep core governance rules domain-agnostic

Philosophy:
----------
Compliance rules are domain-specific. What constitutes a "violation" differs
between finance (prescriptive language = regulatory risk), healthcare (HIPAA
violations), and legal (unauthorized legal advice). The core provides only
generic governance rules (security, performance, quality, hallucination).
Domain-specific compliance rules are loaded from domain plugins.

Pattern mirrors IntentRegistry and ExecutionRegistry.

Author: Vitruvyan Core Team
Created: February 14, 2026
Status: PRODUCTION
Version: 1.0
"""

import importlib
import logging
from typing import Dict, List, Optional, Tuple

from .rule import Rule, RuleSet

logger = logging.getLogger(__name__)


class GovernanceRuleRegistry:
    """
    Registry for domain-specific governance rules.

    Usage:

        registry = GovernanceRuleRegistry()

        # Load domain plugin rules
        registry.register_domain("finance")
        # → imports domains.finance.governance_rules.get_domain_rules()

        # Get combined ruleset (generic + domain)
        ruleset = registry.get_ruleset()
    """

    def __init__(self):
        self._generic_rules: Tuple[Rule, ...] = ()
        self._domain_rules: Dict[str, Tuple[Rule, ...]] = {}
        self._active_domain: Optional[str] = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def set_generic_rules(self, rules: Tuple[Rule, ...]) -> None:
        """Set the baseline generic rules (security, performance, quality)."""
        self._generic_rules = rules
        logger.info(f"[GovernanceRuleRegistry] Generic rules loaded: {len(rules)} rules")

    def register_domain(self, domain: str) -> None:
        """
        Load domain-specific rules from ``domains.<domain>.governance_rules``.

        The module must expose ``get_domain_rules() -> Tuple[Rule, ...]``.
        """
        if domain in self._domain_rules:
            logger.debug(f"[GovernanceRuleRegistry] Domain '{domain}' already registered")
            self._active_domain = domain
            return

        module_path = f"domains.{domain}.governance_rules"
        try:
            mod = importlib.import_module(module_path)
            fn = getattr(mod, "get_domain_rules", None)
            if fn is None:
                logger.warning(
                    f"[GovernanceRuleRegistry] {module_path} has no get_domain_rules()"
                )
                self._domain_rules[domain] = ()
            else:
                domain_rules = fn()
                self._domain_rules[domain] = tuple(domain_rules)
                logger.info(
                    f"[GovernanceRuleRegistry] Domain '{domain}' registered: "
                    f"{len(domain_rules)} rules"
                )
        except ImportError:
            logger.warning(
                f"[GovernanceRuleRegistry] No governance plugin for domain '{domain}' "
                f"(module {module_path} not found). Using generic rules only."
            )
            self._domain_rules[domain] = ()

        self._active_domain = domain

    def register_rules(self, domain: str, rules: Tuple[Rule, ...]) -> None:
        """Directly register rules for a domain (without module import)."""
        self._domain_rules[domain] = rules
        self._active_domain = domain
        logger.info(
            f"[GovernanceRuleRegistry] Domain '{domain}' registered (direct): "
            f"{len(rules)} rules"
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_all_rules(self, domain: Optional[str] = None) -> Tuple[Rule, ...]:
        """
        Get combined generic + domain-specific rules.

        Args:
            domain: Override active domain. If None, uses last registered domain.

        Returns:
            Tuple of all applicable Rule objects.
        """
        target = domain or self._active_domain
        domain_rules = self._domain_rules.get(target, ()) if target else ()
        return self._generic_rules + domain_rules

    def get_ruleset(
        self,
        domain: Optional[str] = None,
        version: str = "v1.0",
    ) -> RuleSet:
        """
        Build a combined RuleSet from generic + domain rules.

        Args:
            domain: Override active domain.
            version: RuleSet version string.

        Returns:
            Frozen RuleSet ready for use in Orthodoxy verdicts.
        """
        rules = self.get_all_rules(domain)
        target = domain or self._active_domain or "generic"
        return RuleSet.create(
            version=version,
            rules=rules,
            description=(
                f"Governance ruleset for domain '{target}'. "
                f"Generic: {len(self._generic_rules)}, "
                f"Domain: {len(rules) - len(self._generic_rules)}. "
                f"Total: {len(rules)} rules."
            ),
        )

    @property
    def active_domain(self) -> Optional[str]:
        return self._active_domain

    @property
    def registered_domains(self) -> List[str]:
        return list(self._domain_rules.keys())


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_registry: Optional[GovernanceRuleRegistry] = None


def get_governance_rule_registry() -> GovernanceRuleRegistry:
    """Get or create the singleton GovernanceRuleRegistry."""
    global _registry
    if _registry is None:
        _registry = GovernanceRuleRegistry()
    return _registry
