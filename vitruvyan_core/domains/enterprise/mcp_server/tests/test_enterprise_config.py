"""Tests for enterprise MCP configuration helpers."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[5]
CORE_DIR = ROOT_DIR / "vitruvyan_core"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from domains.enterprise.mcp_server.enterprise_config import (  # noqa: E402
    EnterpriseMCPConfig,
    build_enterprise_phrase_samples,
    get_enterprise_signal_source_candidates,
    get_enterprise_tool_schemas,
    normalize_enterprise_args,
    resolve_enterprise_tool_name,
)


def test_resolve_enterprise_tool_aliases():
    assert resolve_enterprise_tool_name("query_partners") == "screen_entities"
    assert resolve_enterprise_tool_name("analyze_invoices") == "screen_entities"
    assert resolve_enterprise_tool_name("compare_partners") == "compare_entities"
    assert resolve_enterprise_tool_name("query_business_health") == "query_signals"
    assert resolve_enterprise_tool_name("generate_business_report") == "generate_vee_summary"
    assert resolve_enterprise_tool_name("analyze_erp_context") == "extract_semantic_context"
    # Canonical pass-through
    assert resolve_enterprise_tool_name("screen_entities") == "screen_entities"
    # Unknown returns as-is
    assert resolve_enterprise_tool_name("unknown_tool") == "unknown_tool"


def test_normalize_partner_ids_to_entity_ids():
    result = normalize_enterprise_args("query_partners", {"partner_ids": ["P001", "P002"]})
    assert result["entity_ids"] == ["P001", "P002"]
    assert "partner_ids" not in result


def test_normalize_invoice_ids_to_entity_ids():
    result = normalize_enterprise_args("analyze_invoices", {"invoice_ids": ["INV-001"]})
    assert result["entity_ids"] == ["INV-001"]


def test_normalize_query_signals_args():
    result = normalize_enterprise_args(
        "query_business_health",
        {"partner_id": "P001", "days": 60, "include_phrases": True},
    )
    assert result["entity_id"] == "P001"
    assert result["time_window"] == 60
    assert result["include_context"] is True
    assert "partner_id" not in result
    assert "days" not in result


def test_normalize_query_signals_clamps_window():
    result = normalize_enterprise_args("query_signals", {"entity_id": "X", "time_window": 999})
    assert result["time_window"] == 365  # max for enterprise


def test_normalize_compare_criteria():
    result = normalize_enterprise_args("compare_partners", {
        "partner_ids": ["P1", "P2"],
        "criteria": "revenue",
    })
    assert result["criteria"] == "factor_1"
    assert result["entity_ids"] == ["P1", "P2"]


def test_signal_source_candidates():
    candidates = get_enterprise_signal_source_candidates()
    assert "enterprise_signals" in candidates["tables"]
    assert "entity_id" in candidates["entity_columns"]


def test_phrase_samples_limit():
    samples = build_enterprise_phrase_samples("Acme Corp", limit=2)
    assert len(samples) == 2
    assert "Acme Corp" in samples[0]


def test_tool_schemas_has_enterprise_tools():
    schemas = get_enterprise_tool_schemas()
    names = {s["function"]["name"] for s in schemas}
    assert "query_partners" in names
    assert "analyze_invoices" in names
    assert "compare_partners" in names
    assert "query_business_health" in names
    assert "generate_business_report" in names
    assert "analyze_erp_context" in names


def test_config_frozen():
    cfg = EnterpriseMCPConfig()
    assert cfg.domain_name == "enterprise"
    assert cfg.max_signal_window_days == 365
