"""
Codex Hunters Governance Layer

Contains domain-agnostic quality rules, deduplication engines, and validation logic
for data acquisition and canonicalization.

All business rules are CONFIG-driven (QualityConfig from YAML), not hardcoded.

Sacred Laws (from philosophy/charter.md):
1. Ontological Purity: No domain semantics in core
2. Deterministic Dedup: Hash-based keys (not date/time)
3. Quality by Evidence: Validation grounded in data provenance
4. Config-Driven: All thresholds from runtime injection
"""

__all__ = []
