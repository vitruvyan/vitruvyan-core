"""
Enterprise Vault Configuration
===============================

Enterprise-specific runtime defaults for Vault Keepers.
Adapted for ERP data archival (partners, invoices, sale orders, products).
Italian fiscal compliance: 10-year retention for invoices/accounting.
This package remains pure configuration (no I/O).
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class EnterpriseVaultConfig:
    """Enterprise vertical defaults for vault archival and backup workflows."""

    domain_name: str = "enterprise"

    # Backup defaults
    default_backup_mode: str = "full"
    default_include_vectors: bool = True

    # Integrity defaults
    default_integrity_scope: str = "full"

    # Retention defaults
    # Italian fiscal law: 10 years for invoices/accounting (Art. 2220 Codice Civile)
    # GDPR: data minimization — shorter for non-fiscal data
    archive_retention_days: int = 3650  # 10 years (fiscal compliance)
    signal_retention_days: int = 1825   # 5 years (operational signals)
    operational_retention_days: int = 730  # 2 years (CRM, pipeline, logs)

    # Archive metadata defaults
    default_archive_content_type: str = "erp_snapshot"
    default_source_order: str = "enterprise"
    allowed_archive_types: tuple[str, ...] = (
        "erp_snapshot",
        "audit_result",
        "invoice_archive",
        "partner_archive",
        "compliance_report",
        "system_state",
        "agent_log",
        "generic",
    )
    channel_content_type_map: Dict[str, str] = field(
        default_factory=lambda: {
            "orthodoxy.enterprise.verdict": "audit_result",
            "orthodoxy.audit.completed": "audit_result",
            "vault.snapshot.requested": "system_state",
            "vault.archive.requested": "generic",
            "enterprise.invoice.archived": "invoice_archive",
            "enterprise.partner.archived": "partner_archive",
            "enterprise.compliance.completed": "compliance_report",
        }
    )
    source_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "memory": "memory_orders",
            "memoryorders": "memory_orders",
            "pattern": "pattern_weavers",
            "babel": "babel_gardens",
            "orthodoxy": "orthodoxy_wardens",
            "erp": "enterprise",
            "odoo": "enterprise",
            "connector": "enterprise",
        }
    )

    # Retention tiers: content_type → retention_days override
    retention_tiers: Dict[str, int] = field(
        default_factory=lambda: {
            "invoice_archive": 3650,      # 10 years (fiscal)
            "compliance_report": 3650,     # 10 years (regulatory)
            "audit_result": 2555,          # 7 years
            "partner_archive": 1825,       # 5 years (GDPR)
            "erp_snapshot": 1825,          # 5 years
            "system_state": 730,           # 2 years
            "agent_log": 365,             # 1 year
            "generic": 730,               # 2 years
        }
    )


def get_enterprise_retention_days(
    signal: bool = False,
    content_type: str | None = None,
) -> int:
    """Return retention days based on content type or signal/archive default."""
    cfg = EnterpriseVaultConfig()

    if content_type:
        tier = cfg.retention_tiers.get(content_type)
        if tier is not None:
            return tier

    return cfg.signal_retention_days if signal else cfg.archive_retention_days


def normalize_enterprise_archive_content_type(
    content_type: str | None,
    channel: str | None = None,
) -> str:
    """Normalize arbitrary archive type names to Vault core allowed values."""
    cfg = EnterpriseVaultConfig()

    if channel:
        mapped = cfg.channel_content_type_map.get(channel)
        if mapped in cfg.allowed_archive_types:
            return mapped

    normalized = (content_type or "").strip().lower()
    if normalized in cfg.allowed_archive_types:
        return normalized

    if "audit" in normalized or "compliance" in normalized:
        return "audit_result"
    if any(marker in normalized for marker in ("invoice", "fattura", "billing")):
        return "invoice_archive"
    if any(marker in normalized for marker in ("partner", "customer", "client", "fornitore")):
        return "partner_archive"
    if any(marker in normalized for marker in ("snapshot", "backup", "state", "restore")):
        return "system_state"
    if "log" in normalized:
        return "agent_log"

    return cfg.default_archive_content_type if normalized else "generic"


def normalize_enterprise_source_order(source_order: str | None) -> str:
    """Normalize source order alias to canonical snake_case."""
    cfg = EnterpriseVaultConfig()
    normalized = (source_order or cfg.default_source_order).strip().lower().replace(" ", "_")
    return cfg.source_aliases.get(normalized, normalized or cfg.default_source_order)
