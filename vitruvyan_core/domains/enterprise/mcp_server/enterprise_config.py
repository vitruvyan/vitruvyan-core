"""
Enterprise MCP configuration and compatibility mapping.

Enterprise tool aliases and argument normalization for ERP-domain MCP tools.
Maps enterprise-specific tool names to canonical MCP executors, and normalizes
ERP entity arguments (partner_id, invoice_id, etc.) to generic entity_id.

Pure configuration/transforms only — NO I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    """Deduplicate non-empty strings preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = (raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


@dataclass(frozen=True)
class EnterpriseMCPConfig:
    """Enterprise defaults used by the MCP service adapter."""

    domain_name: str = "enterprise"
    default_language: str = "it"
    default_screen_profile: str = "balanced"
    default_signal_window_days: int = 30
    min_signal_window_days: int = 1
    max_signal_window_days: int = 365  # Enterprise needs longer windows than finance

    # Candidate sources for query_signals
    primary_signal_table: str = "enterprise_signals"
    primary_entity_column: str = "entity_id"
    legacy_signal_table: str = "partner_signals"
    legacy_entity_column: str = "partner_id"
    score_column: str = "signal_score"
    tag_column: str = "signal_category"
    created_at_column: str = "created_at"

    # Enterprise tool aliases → canonical executors
    tool_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            # Enterprise-specific aliases
            "query_partners": "screen_entities",
            "analyze_invoices": "screen_entities",
            "query_crm_pipeline": "screen_entities",
            "analyze_sales": "screen_entities",
            "query_employees": "screen_entities",
            "compare_partners": "compare_entities",
            "compare_products": "compare_entities",
            "query_business_health": "query_signals",
            "query_compliance_risk": "query_signals",
            "generate_business_report": "generate_vee_summary",
            "analyze_erp_context": "extract_semantic_context",
            # Canonical pass-through
            "screen_entities": "screen_entities",
            "compare_entities": "compare_entities",
            "query_signals": "query_signals",
            "generate_vee_summary": "generate_vee_summary",
            "extract_semantic_context": "extract_semantic_context",
        }
    )

    screen_profile_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "revenue_focus": "aggressive",
            "risk_averse": "conservative",
            "balanced": "balanced",
            "aggressive": "aggressive",
            "conservative": "conservative",
            "custom": "custom",
        }
    )

    compare_criteria_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "composite": "composite",
            "revenue": "factor_1",
            "payment_reliability": "factor_2",
            "order_volume": "factor_3",
            "satisfaction": "factor_4",
            "growth": "factor_5",
            "factor_1": "factor_1",
            "factor_2": "factor_2",
            "factor_3": "factor_3",
            "factor_4": "factor_4",
            "factor_5": "factor_5",
        }
    )

    # Entity type mapping: ERP-specific → canonical entity_id/entity_ids
    entity_field_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "partner_id": "entity_id",
            "partner_ids": "entity_ids",
            "invoice_id": "entity_id",
            "invoice_ids": "entity_ids",
            "product_id": "entity_id",
            "product_ids": "entity_ids",
            "employee_id": "entity_id",
            "employee_ids": "entity_ids",
            "order_id": "entity_id",
            "order_ids": "entity_ids",
            "lead_id": "entity_id",
            "lead_ids": "entity_ids",
        }
    )


def resolve_enterprise_tool_name(tool_name: str) -> str:
    """Resolve enterprise/ERP tool names to canonical executor names."""
    cfg = EnterpriseMCPConfig()
    return cfg.tool_aliases.get((tool_name or "").strip(), (tool_name or "").strip())


def normalize_enterprise_args(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize enterprise tool arguments into canonical MCP shape.

    Examples:
    - query_partners(partner_ids=[...]) -> screen_entities(entity_ids=[...])
    - query_business_health(partner_id='P001', days=30) -> query_signals(entity_id='P001', time_window=30)
    """
    cfg = EnterpriseMCPConfig()
    canonical_tool = resolve_enterprise_tool_name(tool_name)
    normalized: Dict[str, Any] = dict(args or {})

    # Map ERP entity fields to canonical entity_id/entity_ids
    for erp_field, canonical_field in cfg.entity_field_aliases.items():
        value = normalized.pop(erp_field, None)
        if value is not None and canonical_field not in normalized:
            normalized[canonical_field] = value

    if canonical_tool == "screen_entities":
        profile = str(normalized.get("profile", cfg.default_screen_profile)).strip().lower()
        normalized["profile"] = cfg.screen_profile_aliases.get(profile, "balanced")

    elif canonical_tool == "compare_entities":
        criteria = str(normalized.get("criteria", "composite")).strip().lower()
        normalized["criteria"] = cfg.compare_criteria_aliases.get(criteria, "composite")

    elif canonical_tool == "query_signals":
        # Normalize days → time_window
        days = normalized.pop("days", None)
        if days is not None and "time_window" not in normalized:
            normalized["time_window"] = days

        window = int(normalized.get("time_window", cfg.default_signal_window_days))
        window = max(cfg.min_signal_window_days, min(cfg.max_signal_window_days, window))
        normalized["time_window"] = window

        include_phrases = normalized.pop("include_phrases", None)
        if include_phrases is not None and "include_context" not in normalized:
            normalized["include_context"] = bool(include_phrases)

    elif canonical_tool == "generate_vee_summary":
        language = str(normalized.get("language", cfg.default_language)).strip().lower()
        normalized["language"] = language or cfg.default_language

    return normalized


def get_enterprise_signal_source_candidates(
    table_override: Optional[str] = None,
    entity_column_override: Optional[str] = None,
) -> Dict[str, tuple[str, ...]]:
    """Return ordered fallback candidates for enterprise signal reads."""
    cfg = EnterpriseMCPConfig()
    return {
        "tables": _ordered_unique(
            (
                table_override or "",
                cfg.primary_signal_table,
                cfg.legacy_signal_table,
            )
        ),
        "entity_columns": _ordered_unique(
            (
                entity_column_override or "",
                cfg.primary_entity_column,
                cfg.legacy_entity_column,
            )
        ),
    }


def build_enterprise_phrase_samples(entity_id: str, limit: int = 3) -> list[str]:
    """Build deterministic fallback phrases for enterprise entities."""
    canonical = (entity_id or "entity").strip() or "entity"
    samples = [
        f"Strong business relationship with {canonical}",
        f"{canonical} shows consistent payment patterns",
        f"Growing order volume from {canonical}",
    ]
    bounded_limit = max(0, int(limit))
    return samples[:bounded_limit]


def get_enterprise_tool_schemas() -> list[dict]:
    """
    Return enterprise-specific OpenAI Function Calling tool schemas.

    These are domain-specialized descriptions that help the LLM understand
    ERP-specific operations. The LLM uses these schemas for ontological
    understanding — no regex/template matching.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "query_partners",
                "description": (
                    "Query and rank business partners (customers, suppliers) using "
                    "Vitruvyan multi-factor scoring. Returns composite scores based on "
                    "revenue, payment reliability, order volume, and growth metrics. "
                    "Use for: 'mostrami i clienti principali', 'top customers by revenue', "
                    "'analisi fornitori'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "partner_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of partner IDs or names. Max 10.",
                            "minItems": 1,
                            "maxItems": 10,
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["balanced", "revenue_focus", "risk_averse"],
                            "description": "Scoring profile. Default: balanced.",
                            "default": "balanced",
                        },
                    },
                    "required": ["partner_ids"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_invoices",
                "description": (
                    "Analyze invoices with multi-factor scoring: payment status, "
                    "aging, amount, and overdue risk. Use for: 'fatture scadute', "
                    "'analisi crediti', 'invoice aging report'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "invoice_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of invoice IDs. Max 10.",
                            "minItems": 1,
                            "maxItems": 10,
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["balanced", "revenue_focus", "risk_averse"],
                            "default": "balanced",
                        },
                    },
                    "required": ["invoice_ids"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_partners",
                "description": (
                    "Compare business partners side-by-side on multiple criteria: "
                    "revenue, payment reliability, order volume, satisfaction, growth. "
                    "Use for: 'confronta Cliente A e Cliente B', 'compare suppliers'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "partner_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Partners to compare. Min 2, max 5.",
                            "minItems": 2,
                            "maxItems": 5,
                        },
                        "criteria": {
                            "type": "string",
                            "enum": ["composite", "revenue", "payment_reliability", "order_volume", "satisfaction", "growth"],
                            "default": "composite",
                        },
                    },
                    "required": ["partner_ids"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_business_health",
                "description": (
                    "Query business health signals for an entity: revenue trend, "
                    "operational urgency, compliance risk. Returns signal scores "
                    "and context. Use for: 'salute aziendale', 'business health', "
                    "'trend fatturato di ClienteX'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "partner_id": {
                            "type": "string",
                            "description": "Partner/entity identifier.",
                        },
                        "time_window": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 365,
                            "description": "Time window in days. Default: 30.",
                            "default": 30,
                        },
                        "include_context": {
                            "type": "boolean",
                            "description": "Include contextual data. Default: true.",
                            "default": True,
                        },
                    },
                    "required": ["partner_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_business_report",
                "description": (
                    "Generate a narrative business report for an entity. Returns "
                    "comprehensive analysis with scoring rationale. Use for: "
                    "'report su ClienteX', 'genera analisi fornitore'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "partner_id": {
                            "type": "string",
                            "description": "Partner/entity identifier.",
                        },
                        "language": {
                            "type": "string",
                            "enum": ["it", "en", "es", "fr", "de"],
                            "description": "Output language. Default: it.",
                            "default": "it",
                        },
                    },
                    "required": ["partner_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_erp_context",
                "description": (
                    "Extract semantic context from an enterprise/ERP query. "
                    "Identifies business concepts, entity types, time periods, "
                    "and operational intent. Use for understanding what the user "
                    "is asking about in ERP terms."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "User query text about ERP/business data.",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    ]
