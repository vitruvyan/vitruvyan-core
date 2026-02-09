# governance/

> Decision engine core — rules, classifiers, verdict rendering, workflow declarations.

## Status: ✅ FASE 2 COMPLETE

This directory contains the **pure governance logic** — the brain of the tribunal.

### Contents

| File | Lines | Description |
|------|-------|-------------|
| `rule.py` | ~270 | `Rule` + `RuleSet` — frozen, versioned compliance rules (35 default) |
| `classifier.py` | ~240 | `PatternClassifier` (regex) + `ASTClassifier` (Python AST) |
| `verdict_engine.py` | ~250 | `VerdictEngine` — Findings → Verdict + LogDecision |
| `workflow.py` | ~210 | Declarative workflow definitions (frozen data, NOT LangGraph) |

### Quick Usage

```python
from vitruvyan_core.core.governance.orthodoxy_wardens.governance import (
    DEFAULT_RULESET, classify_text, VerdictEngine,
)

# 1. Classify text against rules
findings = classify_text("buy now AAPL guaranteed returns")

# 2. Render verdict
engine = VerdictEngine()
verdict = engine.render(findings, DEFAULT_RULESET)

print(verdict.status)       # "heretical"
print(verdict.confidence)   # 0.87
print(verdict.is_blocking)  # True

# 3. Decide logging
log_decision = engine.decide_logging(verdict)
print(log_decision.should_log)  # True
print(log_decision.severity)    # "critical"
```

### Architectural Constraints

- **Pure functions**: No I/O, no network, no database, no side effects
- **Rules are DATA**: Loaded from config, frozen after creation, versioned with SHA-256
- **Classifier observes**: `(text, ruleset) → tuple[Finding, ...]` — no decisions
- **VerdictEngine judges**: `(findings, ruleset) → Verdict` — no execution
- **Workflows declare**: Frozen pipeline shape — service layer (LIVELLO 2) executes
- **Finance rules in config**: MiFID/FINRA regex → YAML config, NOT hardcoded in core

### Default RuleSet (v1.0)

| Category | Count | Severities |
|----------|-------|------------|
| compliance | 14 | 3 critical, 5 high, 2 medium |
| security | 9 | 4 critical, 5 high |
| performance | 6 | 2 high, 2 medium, 2 low |
| quality | 3 | 1 medium, 2 low |
| hallucination | 3 | 1 critical, 2 high |
| **Total** | **35** | |
