# Babel Gardens — Governance Layer

## Purpose

Contains **domain-agnostic rules and quality thresholds** for semantic signal extraction.

**Design Principle**: Rules are DATA, not behavior.
- Quality thresholds loaded from YAML config (not hardcoded)
- Signal validation based on confidence intervals
- Multi-model consensus scoring

## Contents (Future)

- `quality_rules.py`: Frozen dataclasses for signal quality constraints
- `signal_validator.py`: Confidence threshold enforcement
- `fusion_engine.py`: Multi-signal correlation rules

## Sacred Invariants

1. **No domain semantics**: Rules apply to ANY signal type (finance, cyber, healthcare)
2. **Config-driven**: All thresholds from `SignalConfig.from_yaml()`
3. **Explainable**: Every validation includes provenance metadata

## Example

```python
from .quality_rules import SignalQualityRules

rules = SignalQualityRules(
    min_confidence=0.7,  # Generic threshold
    require_extraction_trace=True
)

# Applies to finance sentiment OR cyber threat severity
assert rules.validate(signal_result)
```

---

**Last Updated**: Feb 12, 2026 (SACRED_ORDER_PATTERN conformance)
