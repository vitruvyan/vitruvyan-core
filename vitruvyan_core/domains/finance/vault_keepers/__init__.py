"""
Finance Vertical - Vault Keepers Integration
============================================

Domain-specific configuration for finance archival and backup defaults.
Loaded when VAULT_DOMAIN=finance.
"""

from .finance_config import (
    FinanceVaultConfig,
    get_finance_backup_defaults,
    get_finance_retention_days,
    normalize_finance_archive_content_type,
    normalize_finance_source_order,
)

__all__ = [
    "FinanceVaultConfig",
    "get_finance_backup_defaults",
    "normalize_finance_archive_content_type",
    "normalize_finance_source_order",
    "get_finance_retention_days",
]
