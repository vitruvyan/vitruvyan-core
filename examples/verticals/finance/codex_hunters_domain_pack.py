#!/usr/bin/env python3
"""
Finance Domain Pack — Codex Hunters (Pilot)
==========================================

This is an EXAMPLE "domain pack" showing how a vertical (finance) plugs into the
domain-agnostic Codex Hunters core:

- Load `CodexConfig` from YAML (domain choices: tables, sources, stream prefix)
- Register source-specific normalizers for RestorerConsumer

This file is intentionally non-production: it documents the pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from vitruvyan_core.core.governance.codex_hunters.domain.config import CodexConfig
from vitruvyan_core.core.governance.codex_hunters.consumers.restorer import RestorerConsumer


def normalize_yfinance_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example normalizer for a finance source.

    Goal: vendor payload -> canonical `normalized_data` keys.
    Keep it deterministic, minimal, and schema-friendly.
    """
    if not raw:
        return {}

    out: Dict[str, Any] = {}
    for key, value in raw.items():
        k = str(key).lower().replace(" ", "_").replace("-", "_")
        out[k] = value

    # Example: ensure common finance fields exist (domain choice)
    if "currency" not in out:
        out["currency"] = "USD"

    return out


def build_finance_restorer(config_path: Path) -> RestorerConsumer:
    config = CodexConfig.from_yaml(config_path)
    restorer = RestorerConsumer(config=config)
    restorer.register_normalizer("yfinance", normalize_yfinance_payload)
    return restorer


if __name__ == "__main__":
    cfg = Path("examples/verticals/finance/config/codex_hunters_finance.yaml")
    restorer = build_finance_restorer(cfg)
    print("OK: finance RestorerConsumer ready. sources=", list(restorer.config.sources.keys()))
