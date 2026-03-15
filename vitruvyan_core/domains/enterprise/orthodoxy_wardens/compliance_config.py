# domains/enterprise/orthodoxy_wardens/compliance_config.py
"""
Enterprise Orthodoxy Configuration — Compliance Domain Pack

Strictness defaults and ruleset metadata for enterprise governance.
Mirrors finance FinanceOrthodoxyConfig pattern.

Enterprise governance enforces:
- GDPR / data protection compliance
- No unauthorized PII disclosure
- No legal/tax/fiduciary advice
- Factual accuracy (no hallucinated ERP data)
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class EnterpriseOrthodoxyConfig:
    """Frozen compliance configuration for enterprise domain."""

    domain_name: str = "enterprise"
    ruleset_version: str = "v1.0-enterprise"

    # Strictness controls
    strict_mode: bool = True
    confidence_floor: float = 0.70

    # Governance categories active for this domain
    active_categories: tuple = (
        "enterprise.gdpr",
        "enterprise.legal",
        "enterprise.finance",
        "enterprise.data_integrity",
    )

    # Event defaults for orthodoxy verdicts
    event_channel: str = "orthodoxy.enterprise.verdict"
    event_version: str = "1.0.0"


_DEFAULT = EnterpriseOrthodoxyConfig()


def get_enterprise_ruleset_version() -> str:
    """Return the active enterprise ruleset version."""
    return _DEFAULT.ruleset_version


def get_enterprise_event_defaults() -> Dict[str, Any]:
    """Return default event metadata for enterprise orthodoxy verdicts."""
    return {
        "domain": _DEFAULT.domain_name,
        "ruleset_version": _DEFAULT.ruleset_version,
        "strict_mode": _DEFAULT.strict_mode,
        "confidence_floor": _DEFAULT.confidence_floor,
        "event_channel": _DEFAULT.event_channel,
        "event_version": _DEFAULT.event_version,
    }
