"""
Finance Vault Configuration
===========================

Minimal finance-specific runtime defaults for Vault Keepers.
This package remains pure configuration (no I/O).
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class FinanceVaultConfig:
    """Finance vertical defaults for vault archival and backup workflows."""

    domain_name: str = "finance"

    # Backup defaults
    default_backup_mode: str = "full"
    default_include_vectors: bool = True

    # Integrity defaults
    default_integrity_scope: str = "full"

    # Retention defaults (regulatory-grade long retention)
    archive_retention_days: int = 1825
    signal_retention_days: int = 1825

    # Archive metadata defaults
    default_archive_content_type: str = "audit_result"
    default_source_order: str = "finance"
    allowed_archive_types: tuple[str, ...] = (
        "audit_result",
        "eval_result",
        "system_state",
        "agent_log",
        "generic",
    )
    channel_content_type_map: Dict[str, str] = field(
        default_factory=lambda: {
            "orthodoxy.audit.completed": "audit_result",
            "audit.vault.requested": "audit_result",
            "engine.eval.completed": "eval_result",
            "vault.snapshot.requested": "system_state",
            "vault.archive.requested": "generic",
        }
    )
    source_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "memory": "memory_orders",
            "memoryorders": "memory_orders",
            "pattern": "pattern_weavers",
            "babel": "babel_gardens",
            "orthodoxy": "orthodoxy_wardens",
            "engine": "neural_engine",
        }
    )


def get_finance_backup_defaults() -> Dict[str, object]:
    """Return default backup mode and vector policy for finance."""
    cfg = FinanceVaultConfig()
    return {
        "mode": cfg.default_backup_mode,
        "include_vectors": cfg.default_include_vectors,
    }


def normalize_finance_archive_content_type(
    content_type: str | None,
    channel: str | None = None,
) -> str:
    """Normalize arbitrary archive type names to Vault core allowed values."""
    cfg = FinanceVaultConfig()

    if channel:
        mapped = cfg.channel_content_type_map.get(channel)
        if mapped in cfg.allowed_archive_types:
            return mapped

    normalized = (content_type or "").strip().lower()
    if normalized in cfg.allowed_archive_types:
        return normalized

    if "audit" in normalized:
        return "audit_result"
    if any(marker in normalized for marker in ("eval", "screening", "sentiment", "signal")):
        return "eval_result"
    if any(marker in normalized for marker in ("snapshot", "backup", "state", "restore")):
        return "system_state"
    if "log" in normalized:
        return "agent_log"

    return cfg.default_archive_content_type if normalized else "generic"


def normalize_finance_source_order(source_order: str | None) -> str:
    """Normalize source order alias to canonical snake_case."""
    cfg = FinanceVaultConfig()
    normalized = (source_order or cfg.default_source_order).strip().lower().replace(" ", "_")
    return cfg.source_aliases.get(normalized, normalized or cfg.default_source_order)


def get_finance_retention_days(signal: bool = False) -> int:
    """Return retention days for archive or signal timeseries payloads."""
    cfg = FinanceVaultConfig()
    return cfg.signal_retention_days if signal else cfg.archive_retention_days
