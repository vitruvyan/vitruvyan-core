"""
Enterprise vertical adapter for MCP Enterprise Server.

Handles tool alias compatibility and enterprise signal source hints.
Mirrors the finance_adapter.py pattern from core MCP.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _get_enterprise_helpers():
    """Import enterprise MCP helpers with local/package fallback."""
    try:
        from domains.enterprise.mcp_server.enterprise_config import (
            EnterpriseMCPConfig,
            build_enterprise_phrase_samples,
            get_enterprise_signal_source_candidates,
            get_enterprise_tool_schemas,
            normalize_enterprise_args,
            resolve_enterprise_tool_name,
        )
    except ModuleNotFoundError:
        try:
            from core.domains.enterprise.mcp_server.enterprise_config import (
                EnterpriseMCPConfig,
                build_enterprise_phrase_samples,
                get_enterprise_signal_source_candidates,
                get_enterprise_tool_schemas,
                normalize_enterprise_args,
                resolve_enterprise_tool_name,
            )
        except ModuleNotFoundError:
            module = _load_enterprise_module_from_path()
            EnterpriseMCPConfig = module.EnterpriseMCPConfig
            build_enterprise_phrase_samples = module.build_enterprise_phrase_samples
            get_enterprise_signal_source_candidates = module.get_enterprise_signal_source_candidates
            get_enterprise_tool_schemas = module.get_enterprise_tool_schemas
            normalize_enterprise_args = module.normalize_enterprise_args
            resolve_enterprise_tool_name = module.resolve_enterprise_tool_name

    return (
        EnterpriseMCPConfig,
        build_enterprise_phrase_samples,
        get_enterprise_signal_source_candidates,
        get_enterprise_tool_schemas,
        normalize_enterprise_args,
        resolve_enterprise_tool_name,
    )


def _load_enterprise_module_from_path():
    """Load enterprise_config.py directly to avoid heavy parent package imports."""
    resolved = Path(__file__).resolve()
    candidate_paths = []
    for base in [resolved.parent, *resolved.parents]:
        candidate_paths.append(
            base / "vitruvyan_core" / "domains" / "enterprise" / "mcp_server" / "enterprise_config.py"
        )
        candidate_paths.append(
            base / "domains" / "enterprise" / "mcp_server" / "enterprise_config.py"
        )

    module_path = next((path for path in candidate_paths if path.exists()), None)
    if module_path is None:
        raise ModuleNotFoundError("Cannot locate enterprise_config.py for MCP enterprise adapter")

    module_name = "mcp_enterprise_config_dynamic"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Cannot load enterprise module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class EnterpriseAdapter:
    """Enterprise adapter for MCP tool aliasing and ERP arg normalization."""

    def __init__(self):
        self._enterprise_config = None

    @property
    def config(self):
        if self._enterprise_config is None:
            config_cls, *_ = _get_enterprise_helpers()
            self._enterprise_config = config_cls()
        return self._enterprise_config

    def resolve_tool_name(self, tool_name: str) -> str:
        """Map enterprise tool name to canonical MCP executor name."""
        *_, resolve_fn = _get_enterprise_helpers()
        return resolve_fn(tool_name)

    def normalize_args(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize enterprise tool arguments into canonical MCP args."""
        (_, _, _, _, normalize_fn, _) = _get_enterprise_helpers()
        return normalize_fn(tool_name, args)

    def get_signal_source_candidates(self) -> Dict[str, tuple[str, ...]]:
        """Get ordered signal source candidates for enterprise queries."""
        (_, _, get_candidates, _, _, _) = _get_enterprise_helpers()
        return get_candidates()

    def get_tool_schemas(self) -> list[dict]:
        """Get enterprise-specific OpenAI Function Calling schemas."""
        (_, _, _, get_schemas, _, _) = _get_enterprise_helpers()
        return get_schemas()

    def build_phrase_samples(self, entity_id: str, limit: int = 3) -> list[str]:
        """Generate fallback phrase samples (enterprise style)."""
        (_, build_fn, _, _, _, _) = _get_enterprise_helpers()
        return build_fn(entity_id=entity_id, limit=limit)


_enterprise_adapter: Optional[EnterpriseAdapter] = None


def get_enterprise_adapter() -> EnterpriseAdapter:
    """Get singleton enterprise adapter."""
    global _enterprise_adapter
    if _enterprise_adapter is None:
        _enterprise_adapter = EnterpriseAdapter()
        logger.info("Enterprise vertical adapter loaded")
    return _enterprise_adapter
