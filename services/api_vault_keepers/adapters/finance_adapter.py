"""
Finance Vertical Adapter
========================

Loads finance-specific archival defaults when VAULT_DOMAIN=finance.
Keeps Vault Keepers core agnostic by applying logic at LIVELLO 2 only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from api_vault_keepers.config import settings

logger = logging.getLogger(__name__)


def _get_finance_helpers():
    """Import finance vault helpers with local and package fallback."""
    try:
        from domains.finance.vault_keepers.finance_config import (
            FinanceVaultConfig,
            get_finance_backup_defaults,
            get_finance_retention_days,
            normalize_finance_archive_content_type,
            normalize_finance_source_order,
        )
    except ModuleNotFoundError:
        from vitruvyan_core.domains.finance.vault_keepers.finance_config import (
            FinanceVaultConfig,
            get_finance_backup_defaults,
            get_finance_retention_days,
            normalize_finance_archive_content_type,
            normalize_finance_source_order,
        )

    return (
        FinanceVaultConfig,
        get_finance_backup_defaults,
        get_finance_retention_days,
        normalize_finance_archive_content_type,
        normalize_finance_source_order,
    )


class FinanceAdapter:
    """Finance adapter for Vault Keepers archive and backup defaults."""

    def __init__(self):
        self._config = None

    @property
    def finance_config(self):
        if self._config is None:
            finance_config_cls, *_ = _get_finance_helpers()
            cfg = finance_config_cls()
            self._config = finance_config_cls(
                default_backup_mode=settings.VAULT_FINANCE_DEFAULT_BACKUP_MODE
                or cfg.default_backup_mode,
                default_include_vectors=settings.VAULT_FINANCE_INCLUDE_VECTORS,
                archive_retention_days=settings.VAULT_FINANCE_ARCHIVE_RETENTION_DAYS,
                signal_retention_days=settings.VAULT_FINANCE_SIGNAL_RETENTION_DAYS,
            )
        return self._config

    def resolve_backup_params(
        self,
        mode: Optional[str],
        include_vectors: Optional[bool],
    ) -> Dict[str, Any]:
        """Resolve effective backup parameters for finance operations."""
        _, get_finance_backup_defaults, *_ = _get_finance_helpers()
        defaults = get_finance_backup_defaults()
        valid_modes = {"full", "incremental"}

        resolved_mode = (mode or self.finance_config.default_backup_mode or defaults["mode"]).lower()
        if resolved_mode not in valid_modes:
            resolved_mode = defaults["mode"]

        resolved_vectors = (
            self.finance_config.default_include_vectors
            if include_vectors is None
            else bool(include_vectors)
        )

        return {
            "mode": resolved_mode,
            "include_vectors": resolved_vectors,
        }

    def resolve_archive_request(
        self,
        content_type: Optional[str],
        source_order: Optional[str],
        channel: Optional[str] = None,
    ) -> Dict[str, str]:
        """Normalize archive request metadata to Vault core contract values."""
        (
            _finance_config_cls,
            _get_finance_backup_defaults,
            _get_finance_retention_days,
            normalize_finance_archive_content_type,
            normalize_finance_source_order,
        ) = _get_finance_helpers()

        normalized_type = normalize_finance_archive_content_type(
            content_type=content_type,
            channel=channel,
        )
        normalized_source = normalize_finance_source_order(source_order)
        return {
            "content_type": normalized_type,
            "source_order": normalized_source,
        }

    def resolve_signal_retention_days(self, retention_days: Optional[int]) -> int:
        """Resolve retention days for finance signal timeseries archival."""
        _, _, get_finance_retention_days, *_ = _get_finance_helpers()
        if isinstance(retention_days, int) and retention_days > 0:
            return retention_days
        return max(
            self.finance_config.signal_retention_days,
            get_finance_retention_days(signal=True),
        )

    def get_runtime_config(self) -> Dict[str, Any]:
        """Expose active finance runtime configuration."""
        cfg = self.finance_config
        return {
            "domain": cfg.domain_name,
            "default_backup_mode": cfg.default_backup_mode,
            "default_include_vectors": cfg.default_include_vectors,
            "default_integrity_scope": cfg.default_integrity_scope,
            "archive_retention_days": cfg.archive_retention_days,
            "signal_retention_days": cfg.signal_retention_days,
            "default_archive_content_type": cfg.default_archive_content_type,
            "default_source_order": cfg.default_source_order,
        }


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active for vault keepers."""
    return settings.VAULT_DOMAIN == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """Get finance adapter singleton when VAULT_DOMAIN=finance."""
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (VAULT_DOMAIN=finance)")

    return _finance_adapter
