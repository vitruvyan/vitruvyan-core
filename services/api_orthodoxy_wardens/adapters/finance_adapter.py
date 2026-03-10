"""
Finance Vertical Adapter
========================

Loads finance-specific governance rules when ORTHODOXY_DOMAIN=finance.
This adapter wires domain rules into LIVELLO 2 without modifying LIVELLO 1.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from core.governance.orthodoxy_wardens.governance.rule import (
        DEFAULT_RULES,
    )
    from core.governance.orthodoxy_wardens.governance.rule_registry import (
        get_governance_rule_registry,
    )
except ModuleNotFoundError:
    from vitruvyan_core.core.governance.orthodoxy_wardens.governance.rule import DEFAULT_RULES
    from vitruvyan_core.core.governance.orthodoxy_wardens.governance.rule_registry import (
        get_governance_rule_registry,
    )

from ..config import settings

logger = logging.getLogger(__name__)

_VALID_TRIGGER_TYPES = {"code_commit", "scheduled", "manual", "output_validation", "event"}
_VALID_SCOPES = {"complete_realm", "single_service", "single_output", "single_event"}


def _get_finance_config_helpers():
    """Import finance orthodoxy config helpers with local/package fallback."""
    try:
        from domains.finance.orthodoxy_wardens.compliance_config import (
            FinanceOrthodoxyConfig,
            get_finance_event_defaults,
            get_finance_ruleset_version,
        )
    except ModuleNotFoundError:
        from core.domains.finance.orthodoxy_wardens.compliance_config import (
            FinanceOrthodoxyConfig,
            get_finance_event_defaults,
            get_finance_ruleset_version,
        )

    return FinanceOrthodoxyConfig, get_finance_event_defaults, get_finance_ruleset_version


def _load_finance_domain_rules():
    """Load finance governance rules from domain package."""
    try:
        from domains.finance.governance_rules import get_domain_rules
    except ModuleNotFoundError:
        from core.domains.finance.governance_rules import get_domain_rules
    return tuple(get_domain_rules())


class FinanceAdapter:
    """Finance adapter for Orthodoxy Wardens governance pipeline."""

    def __init__(self):
        self._config = None
        self._ruleset = None

    @property
    def config(self):
        if self._config is None:
            config_cls, _, _ = _get_finance_config_helpers()
            self._config = config_cls()
        return self._config

    def build_ruleset(self, force_refresh: bool = False):
        """Build and cache finance-aware ruleset (generic + domain rules)."""
        if self._ruleset is not None and not force_refresh:
            return self._ruleset

        _, _, get_finance_ruleset_version = _get_finance_config_helpers()

        registry = get_governance_rule_registry()
        registry.set_generic_rules(DEFAULT_RULES)

        domain_rules = _load_finance_domain_rules()
        registry.register_rules(self.config.domain_name, domain_rules)

        version = settings.ORTHODOXY_RULESET_VERSION or get_finance_ruleset_version()
        self._ruleset = registry.get_ruleset(domain=self.config.domain_name, version=version)
        logger.info(
            "Finance ruleset initialized: version=%s total_rules=%d",
            self._ruleset.version,
            self._ruleset.rule_count,
        )
        return self._ruleset

    def get_rules_stats(self) -> Dict[str, Any]:
        """Summarize active rules for diagnostics endpoints."""
        ruleset = self.build_ruleset()
        by_category: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for rule in ruleset.active_rules:
            by_category[rule.category] = by_category.get(rule.category, 0) + 1
            by_severity[rule.severity] = by_severity.get(rule.severity, 0) + 1
        return {
            "domain": self.config.domain_name,
            "ruleset_version": ruleset.version,
            "ruleset_checksum": ruleset.checksum,
            "total_rules": ruleset.rule_count,
            "active_rules": ruleset.active_count,
            "by_category": by_category,
            "by_severity": by_severity,
        }

    def build_event(
        self,
        text: str,
        code: str = "",
        trigger_type: str | None = None,
        scope: str | None = None,
        source: str | None = None,
    ) -> Dict[str, Any]:
        """Build normalized finance event payload for adapter pipelines."""
        _, get_finance_event_defaults, _ = _get_finance_config_helpers()
        defaults = get_finance_event_defaults()
        resolved_trigger = trigger_type if trigger_type in _VALID_TRIGGER_TYPES else defaults["trigger_type"]
        resolved_scope = scope if scope in _VALID_SCOPES else defaults["scope"]

        return {
            "trigger_type": resolved_trigger,
            "scope": resolved_scope,
            "source": source or defaults["source"],
            "text": text,
            "code": code or "",
        }


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active for orthodoxy wardens."""
    return settings.ORTHODOXY_DOMAIN == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """Get finance adapter singleton when ORTHODOXY_DOMAIN=finance."""
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (ORTHODOXY_DOMAIN=finance)")

    return _finance_adapter
