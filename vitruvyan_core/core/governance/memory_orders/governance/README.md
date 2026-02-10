# governance/

> **Rules, thresholds, classifiers. Data-driven, not behavior.**

## Constraints

- Rules are DATA, not behavior — configuration, not decorators
- Frozen dataclasses for rule sets — immutable, versioned
- No domain-specific patterns in core — regex/enums → config files
- Checksum for audit trail — SHA-256 of serialized rules

---

## Contents

| File | Description |
|------|-------------|
| `thresholds.py` | Coherence drift thresholds (frozen config) |
| `health_rules.py` | Component health aggregation rules |

---

**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1 — governance)
