# governance/

> Rules, classifiers, and verdict rendering logic.

## Status: FASE 2 (Planned)

This directory will contain the **decision engine core** — the brain of the tribunal.

### Planned Contents

| File | Description |
|------|-------------|
| `ruleset.py` | `RuleSet` — frozen, config-driven compliance rules |
| `classifier.py` | Severity/category classification engine |
| `verdict_engine.py` | Aggregates findings into final verdict |

## Design Decision: RuleSet

RuleSets are **declarative data**, not code:
- Loaded from YAML/JSON config at startup
- Frozen after loading (immutable)
- Versioned with a hash (for audit trail)
- No decorator patterns, no magic — just data

```python
# Conceptual shape (FASE 2 implementation)
@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str          # "compliance", "data_quality", etc.
    pattern: str           # Regex or keyword pattern
    severity: str          # "critical", "high", etc.
    description: str

@dataclass(frozen=True)
class RuleSet:
    version: str
    rules: tuple[Rule, ...]
    checksum: str          # SHA-256 of serialized rules
```

## Constraints

- Rules are **DATA**, not behavior
- No finance-specific content (that goes in config yaml, not in core)
- Verdict engine is pure: `(findings, ruleset) → verdict`
- Classificr is pure: `(raw_text, ruleset) → finding`
