# domains/enterprise/memory_orders/enterprise_config.py
"""
Enterprise Memory Configuration — Memory Orders Domain Pack

Coherence thresholds and source mappings for enterprise ERP data.
Mirrors finance FinanceMemoryConfig pattern.

Enterprise sources:
- Primary: partners table + partner_embeddings collection
- Secondary: conversations_embeddings (RAG tier)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass(frozen=True)
class EnterpriseMemoryConfig:
    """Frozen coherence configuration for enterprise domain."""

    domain_name: str = "enterprise"

    # Primary data sources (ERP entities stored in PostgreSQL + Qdrant)
    primary_table: str = "partners"
    primary_collection: str = "partner_embeddings"

    # Conversation memory (RAG tier — shared across domains)
    conversation_collection: str = "conversations_embeddings"

    # Drift thresholds (PG ↔ Qdrant coherence)
    healthy_drift_threshold: float = 5.0   # < 5% = healthy
    warning_drift_threshold: float = 15.0  # 5-15% = warning, > 15% = critical

    # Source candidates for coherence checks
    source_candidates: List[str] = field(default_factory=lambda: [
        "partners",
        "invoices",
        "sale_orders",
        "products",
        "employees",
    ])


_DEFAULT = EnterpriseMemoryConfig()


def get_enterprise_thresholds() -> Dict[str, float]:
    """Return enterprise coherence drift thresholds."""
    return {
        "healthy": _DEFAULT.healthy_drift_threshold,
        "warning": _DEFAULT.warning_drift_threshold,
    }


def get_enterprise_default_sources() -> Dict[str, Any]:
    """Return enterprise primary source configuration."""
    return {
        "primary_table": _DEFAULT.primary_table,
        "primary_collection": _DEFAULT.primary_collection,
        "conversation_collection": _DEFAULT.conversation_collection,
        "source_candidates": list(_DEFAULT.source_candidates),
    }
