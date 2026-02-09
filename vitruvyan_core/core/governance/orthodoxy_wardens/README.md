# Orthodoxy Wardens — Sacred Order #5: Truth & Governance

> **"Il giudice non è mai il boia."** — The judge is never the executioner.

Orthodoxy Wardens is an **epistemic tribunal**: it receives confessions (audit requests),
examines evidence, renders verdicts, and archives decisions. It **never** executes
corrections, restarts services, or writes to databases directly.

## Architecture

```
orthodoxy_wardens/
├── domain/          Frozen dataclasses: Confession, Finding, Verdict, LogDecision
├── events/          Event type constants + OrthodoxyEvent envelope
├── consumers/       SacredRole ABC + decision engine implementations (FASE 3)
├── governance/      Rules, classifiers, verdict engine (FASE 2)
├── monitoring/      Prometheus metric name constants
├── philosophy/      Decision Engine Charter — the "why"
├── docs/            Extended documentation
├── examples/        Usage examples and test fixtures
├── tests/           Unit tests
└── _legacy/         Pre-refactoring files (to be removed after FASE 4)
```

## Domain Model

```
Confession ──examine──▶ Finding[] ──aggregate──▶ Verdict
                                                    │
                                              LogDecision (meta)
```

### Verdict Statuses
| Status | Meaning | Action |
|--------|---------|--------|
| `blessed` | Output valid | Send to user |
| `purified` | Output corrected | Send corrected version |
| `heretical` | Output rejected | Block delivery |
| `non_liquet` | Insufficient confidence | Send with uncertainty |
| `clarification_needed` | Input ambiguous | Ask user to rephrase |

## Layer Separation

| Concern | Foundational (this package) | Service (api_orthodoxy_wardens/) |
|---------|---------------------------|----------------------------------|
| What to judge | ✅ Domain objects, rules | ❌ |
| How to reason | ✅ SacredRole.process() | ❌ |
| Where to listen | ❌ | ✅ StreamBus, Redis |
| How to persist | ❌ | ✅ PostgreSQL, Qdrant |
| How to expose | ❌ | ✅ FastAPI endpoints |

## Quick Start

```python
from core.governance.orthodoxy_wardens.domain import Confession, Finding, Verdict

# Create a confession (audit request)
confession = Confession(
    confession_id="confession_20260209_120000",
    trigger_type="output_validation",
    scope="single_output",
    urgency="critical",
    source="langgraph.orthodoxy_node",
    timestamp="2026-02-09T12:00:00Z",
)

# Create findings
finding = Finding(
    finding_id="finding_20260209_120001_001",
    finding_type="violation",
    severity="critical",
    category="hallucination",
    message="LLM claimed revenue of $10 trillion for AAPL",
    source_rule="rule_numeric_hallucination_v1",
)

# Render verdict
verdict = Verdict.heretical(
    findings=(finding,),
    explanation="Blocked: numeric hallucination detected",
)

assert verdict.is_blocking is True
assert verdict.should_send is False
```

## Refactoring Status

| Phase | Description | Status |
|-------|-------------|--------|
| FASE 0 | Delete/move legacy files | ✅ Complete |
| FASE 1 | Domain objects + events + ABC | ✅ Complete |
| FASE 2 | Governance engine (RuleSet, classifier) | ⏳ Planned |
| FASE 3 | Consumers (Confessor, Inquisitor, Penitent, Chronicler) | ⏳ Planned |
| FASE 4 | Service layer slimming | ⏳ Planned |

## See Also

- [philosophy/charter.md](philosophy/charter.md) — Decision Engine Charter
- [SACRED_ORDER_PATTERN.md](../../SACRED_ORDER_PATTERN.md) — Canonical template for all Sacred Orders
