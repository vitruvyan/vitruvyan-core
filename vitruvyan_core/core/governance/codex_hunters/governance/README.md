# Codex Hunters — Governance Layer

## Purpose

Contains **domain-agnostic rules and quality engines** for data acquisition validation.

**Design Principle**: Rules are DATA (from YAML config), not hardcoded behavior.
- Quality thresholds injected at runtime via `QualityConfig`
- Deduplication based on deterministic hashing (Charter-compliant)
- Validation grounded in data provenance

## Contents (Future)

- `quality_rules.py`: Frozen dataclasses for acquisition quality constraints
- `dedup_engine.py`: Deterministic hash-based deduplication
- `entity_validator.py`: Domain-agnostic entity validation

## Sacred Invariants

1. **Storage-agnostic**: No Postgres/Qdrant assumptions in logic
2. **Deterministic dedup**: Hash-based keys (NOT timestamp-based)
3. **Config-driven**: All thresholds from `CodexConfig.from_yaml()`
4. **Explainable**: Every validation includes provenance metadata

## Example

```python
from .quality_rules import QualityRules
from ..domain.config import CodexConfig

config = CodexConfig.from_yaml("deployments/healthcare.yaml")
rules = QualityRules(min_completeness=config.min_completeness)

# Applies to finance entities OR healthcare patients OR legal cases
assert rules.validate(discovered_entity)
```

---

**Last Updated**: Feb 12, 2026 (SACRED_ORDER_PATTERN conformance)
