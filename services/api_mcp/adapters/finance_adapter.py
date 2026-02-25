"""
Finance vertical adapter for MCP Server.

Activated when MCP_DOMAIN=finance.
Handles tool alias compatibility and finance signal source hints without
touching the core service contracts.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

logger = logging.getLogger(__name__)


def _get_finance_helpers():
    """Import finance MCP helpers with local/package fallback."""
    try:
        from domains.finance.mcp_server.finance_config import (
            FinanceMCPConfig,
            build_finance_phrase_samples,
            get_finance_signal_source_candidates,
            normalize_finance_args,
            resolve_finance_tool_name,
        )
    except ModuleNotFoundError:
        try:
            from vitruvyan_core.domains.finance.mcp_server.finance_config import (
                FinanceMCPConfig,
                build_finance_phrase_samples,
                get_finance_signal_source_candidates,
                normalize_finance_args,
                resolve_finance_tool_name,
            )
        except ModuleNotFoundError:
            finance_module = _load_finance_module_from_path()
            FinanceMCPConfig = finance_module.FinanceMCPConfig
            build_finance_phrase_samples = finance_module.build_finance_phrase_samples
            get_finance_signal_source_candidates = (
                finance_module.get_finance_signal_source_candidates
            )
            normalize_finance_args = finance_module.normalize_finance_args
            resolve_finance_tool_name = finance_module.resolve_finance_tool_name

    return (
        FinanceMCPConfig,
        build_finance_phrase_samples,
        get_finance_signal_source_candidates,
        normalize_finance_args,
        resolve_finance_tool_name,
    )


def _load_finance_module_from_path():
    """Load finance_config.py directly to avoid heavy parent package imports."""
    resolved = Path(__file__).resolve()
    candidate_paths = []
    for base in [resolved.parent, *resolved.parents]:
        candidate_paths.append(
            base / "vitruvyan_core" / "domains" / "finance" / "mcp_server" / "finance_config.py"
        )
        candidate_paths.append(
            base / "domains" / "finance" / "mcp_server" / "finance_config.py"
        )

    module_path = next((path for path in candidate_paths if path.exists()), None)
    if module_path is None:
        raise ModuleNotFoundError("Cannot locate finance_config.py for MCP finance adapter")
    module_name = "mcp_finance_config_dynamic"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Cannot load finance module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FinanceAdapter:
    """Finance adapter for MCP tool aliasing and signal source selection."""

    def __init__(self):
        self._finance_config = None

    @property
    def config(self):
        if self._finance_config is None:
            finance_config_cls, *_ = _get_finance_helpers()
            self._finance_config = finance_config_cls()
        return self._finance_config

    def resolve_tool_name(self, tool_name: str) -> str:
        """Map legacy finance tool name to canonical MCP executor name."""
        *_, resolve_finance_tool_name = _get_finance_helpers()
        return resolve_finance_tool_name(tool_name)

    def normalize_args(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize finance tool arguments into canonical MCP args."""
        *_, normalize_finance_args, _resolve = _get_finance_helpers()
        return normalize_finance_args(tool_name, args)

    def get_signal_source_candidates(self) -> Dict[str, tuple[str, ...]]:
        """Get ordered sentiment source candidates for finance queries."""
        (
            _finance_config_cls,
            _build_phrase_samples,
            get_finance_signal_source_candidates,
            _normalize_finance_args,
            _resolve_finance_tool_name,
        ) = _get_finance_helpers()

        service_config = get_config()
        return get_finance_signal_source_candidates(
            table_override=service_config.finance.signal_table or None,
            entity_column_override=service_config.finance.signal_entity_column or None,
        )

    def build_phrase_samples(self, entity_id: str, limit: int = 3) -> list[str]:
        """Generate fallback phrase samples (finance style)."""
        _, build_finance_phrase_samples, *_ = _get_finance_helpers()
        return build_finance_phrase_samples(entity_id=entity_id, limit=limit)


_finance_adapter: Optional[FinanceAdapter] = None


def is_finance_enabled() -> bool:
    """Check whether finance vertical is active for MCP server."""
    return get_config().service.domain == "finance"


def get_finance_adapter() -> Optional[FinanceAdapter]:
    """Get singleton finance adapter when MCP_DOMAIN=finance."""
    global _finance_adapter
    if not is_finance_enabled():
        return None

    if _finance_adapter is None:
        _finance_adapter = FinanceAdapter()
        logger.info("Finance vertical adapter loaded (MCP_DOMAIN=finance)")

    return _finance_adapter
