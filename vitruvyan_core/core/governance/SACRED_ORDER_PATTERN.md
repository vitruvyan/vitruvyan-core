# SACRED ORDER PATTERN — Canonical Template

> **Every Sacred Order follows this IDENTICAL structure.**
> This template is the industrial blueprint for Vitruvyan's epistemic architecture.
> First implemented for Orthodoxy Wardens (Feb 2026). All others replicate this.

---

## Applies To

| Sacred Order | Domain | Status |
|-------------|--------|--------|
| Orthodoxy Wardens | Truth & Governance | ✅ Refactored |
| Vault Keepers | Memory & Archival | ✅ Refactored |
| Codex Hunters | Perception & Discovery | ✅ Refactored|
| Pattern Weavers | Ontology | ✅ Refactored |
| Babel Gardens | Semantic Linguistic & Sentiment | ✅ Refactored |

---

## Two-Level Architecture

Every Sacred Order exists at TWO levels:

### Level 1 — Foundational (`vitruvyan_core/core/governance/<order>/`)
**Pure Python. No infrastructure. Importable. Testable in isolation.**

Contains: domain objects, decision logic, event definitions, metric names.  
Does NOT contain: database connections, bus listeners, API endpoints, Docker.

### Level 2 — Service (`services/api_<order>/`)
**Infrastructure. Bus. Database. API. Docker.**

Contains: FastAPI app, StreamBus adapters, PostgreSQL persistence, health checks.  
Imports FROM Level 1. Never the other way around.

```
Level 1 (Foundational)          Level 2 (Service)
──────────────────────          ──────────────────
      domain/            ←──── imports ────  core/adapters.py
      consumers/         ←──── imports ────  core/event_handlers.py
      events/            ←──── imports ────  listeners/
      monitoring/        ←──── imports ────  monitoring/health.py
```

---

## Level 1 — Foundational Directory Structure

```
<order>/
├── README.md                 # Package overview, quick start, refactoring status
├── __init__.py               # Package docstring + documented exports
│
├── domain/                   # Frozen dataclasses — the nouns
│   ├── README.md             # Constraints: frozen, no I/O, no external imports
│   ├── __init__.py           # Re-exports all domain objects
│   ├── <object_1>.py         # @dataclass(frozen=True), validation in __post_init__
│   ├── <object_2>.py
│   └── ...
│
├── consumers/                # Decision engines — the verbs
│   ├── README.md             # Contract: process() is pure, no side effects
│   ├── __init__.py
│   ├── base.py               # SacredRole ABC (or order-specific base)
│   ├── <consumer_1>.py       # Concrete role implementation
│   └── ...
│
├── governance/               # Rules, classifiers, engines
│   ├── README.md             # Design: rules are DATA not behavior
│   ├── __init__.py
│   ├── ruleset.py            # Frozen rule definitions (loaded from config)
│   ├── classifier.py         # Input classification logic
│   └── verdict_engine.py     # Final judgment aggregation
│
├── events/                   # Event type definitions
│   ├── README.md             # Naming: <order>.<domain>.<action>
│   ├── __init__.py
│   └── <order>_events.py     # Constants + event envelope dataclass
│
├── monitoring/               # Metric name constants (no collection)
│   ├── README.md             # Rule: definitions only, no prometheus_client
│   ├── __init__.py
│   └── metrics.py
│
├── philosophy/               # The "why" — decision charter
│   └── charter.md            # Identity, mandate, invariants, constraints
│
├── docs/                     # Extended documentation
│   └── README.md
│
├── examples/                 # Standalone usage examples
│   ├── README.md             # Rule: runs standalone, no infra needed
│   └── example_*.py
│
├── tests/                    # Unit tests (pure, no infra)
│   ├── README.md
│   ├── __init__.py
│   └── test_*.py
│
└── _legacy/                  # Transitional: pre-refactoring files
    ├── README.md             # Removal timeline, who still imports
    └── *.py                  # Frozen artifacts — DO NOT MODIFY
```

---

## Level 2 — Service Directory Structure

```
api_<order>/
├── README.md                 # Deployment guide, Docker config, API reference
├── __init__.py
├── main.py                   # <200 lines. Bootstrap + adapter registration ONLY
│
├── api/                      # HTTP endpoints
│   ├── README.md
│   ├── __init__.py
│   └── routes.py             # FastAPI router
│
├── core/                     # Service-specific logic (adapters, not domain)
│   ├── README.md
│   ├── __init__.py
│   ├── adapters.py           # SacredRole → StreamBus wrappers
│   ├── event_handlers.py     # Bus event → domain object translation
│   ├── workflows.py          # Runtime orchestration pipelines
│   └── db_manager.py         # PostgreSQL CRUD via PostgresAgent
│
├── models/                   # Pydantic schemas (API contracts)
│   ├── README.md
│   ├── __init__.py
│   └── schemas.py
│
├── listeners/                # Stream consumers
│   ├── README.md
│   ├── __init__.py
│   └── streams_listener.py   # ListenerAdapter wrapper
│
├── monitoring/               # Health checks, Prometheus endpoints
│   ├── README.md
│   ├── __init__.py
│   └── health.py
│
├── docs/                     # Service-specific documentation
│   ├── README.md
│   ├── API_REFERENCE.md
│   └── ARCHITECTURAL_DECISIONS.md
│
└── examples/                 # Integration examples (may require Docker)
    ├── README.md
    └── example_*.py
```

---

## File Header Convention

Every `.py` file MUST begin with a docstring following this template:

```python
"""
<Sacred Order> — <Component Name>

<One-line description of what this file does.>
<Optional second line with additional context.>

Sacred Order: <Order Name>
Layer: Foundational | Service
"""
```

Example:
```python
"""
Orthodoxy Wardens — Verdict Domain Object

Final judgment rendered by the tribunal on a Confession.
Implements five statuses including non_liquet (Socratic uncertainty).

Sacred Order: Truth & Governance
Layer: Foundational (domain)
"""
```

---

## Domain Object Rules

1. **Always `@dataclass(frozen=True)`** — immutable after creation
2. **Collections use `tuple`**, not `list` — enforces immutability
3. **Metadata as `tuple[tuple[str, Any], ...]`** — not `dict` (mutable)
4. **Validation in `__post_init__`** — fail fast, explicit error messages
5. **Valid values in `frozenset` class attributes** — enum-like, no import
6. **Factory `@classmethod` methods** — canonical creation patterns
7. **NO I/O, NO imports from other packages** — only `dataclasses`, `typing`, stdlib

---

## Consumer (SacredRole) Rules

1. **`process()` is PURE** — no side effects, no I/O, no network
2. **Same input → same output** — deterministic, testable
3. **NO infrastructure imports** — no StreamBus, Redis, PostgreSQL
4. **Type enforcement at concrete level** — ABC uses `Any`
5. **`can_handle()` for selective routing** — not every event goes everywhere
6. **Service adapters wrap consumers** — for bus/DB integration

---

## Event Rules

1. **Dot notation**: `<order>.<domain>.<action>`
2. **String constants**, not enums — Redis Streams compatibility
3. **Event envelope is `frozen=True`** — immutable
4. **`to_dict()` / `from_dict()`** — bus serialization
5. **Define PUBLISH and CONSUME channel groups** — explicit contract

---

## Governance Rules

1. **Rules are DATA, not behavior** — YAML/JSON config, not decorators
2. **RuleSet is frozen after loading** — immutable, versioned
3. **Checksum for audit trail** — SHA-256 of serialized rules
4. **No domain-specific patterns in core** — finance regex → config files

---

## README Template

Every README follows this structure:

```markdown
# <folder_name>/

> <one-line description>

## Contents

| File | Description |
|------|-------------|
| ... | ... |

## Constraints

- <rule 1>
- <rule 2>
```

---

## Testing Pattern

| Layer | Test Type | Infrastructure | Location |
|-------|-----------|---------------|----------|
| Domain objects | Pure unit | None | `<order>/tests/` |
| Consumers | Pure unit | None | `<order>/tests/` |
| Events | Serialization roundtrip | None | `<order>/tests/` |
| Governance | Rule evaluation | None | `<order>/tests/` |
| Service adapters | Integration | Redis, PostgreSQL | `api_<order>/tests/` |
| API endpoints | Integration | Docker | `api_<order>/tests/` |

---

## Migration Protocol (FASE 0→4)

When refactoring an existing Sacred Order:

| Phase | Action | Deliverables |
|-------|--------|-------------|
| **FASE 0** | Move execution files to `_legacy/`, fix imports | `_legacy/` populated, zero broken imports |
| **FASE 1** | Create domain objects, events, ABC, monitoring, READMEs | All directories populated, pattern complete |
| **FASE 2** | Build governance engine (RuleSet, classifier, verdict) | `governance/` populated |
| **FASE 3** | Rewrite agents as pure consumers | `consumers/` populated, old agents deprecated |
| **FASE 4** | Slim service layer to thin adapter shell | `main.py` <200 lines, no legacy imports |

**Decision heuristic at every step**: *"Does this file DECIDE or EXECUTE?"*
- Decides → Foundational (Level 1)
- Executes → Service (Level 2)
- Domain-specific → Config file or vertical module

---

## Replication Checklist

When creating a NEW Sacred Order from scratch:

- [ ] Create foundational directory with all 10 subdirectories
- [ ] Create `domain/` with at least one frozen dataclass
- [ ] Create `events/` with channel constants + event envelope
- [ ] Create `consumers/base.py` with order-specific SacredRole
- [ ] Create `governance/__init__.py` (placeholder or rules)
- [ ] Create `monitoring/metrics.py` with metric name constants
- [ ] Create `philosophy/charter.md` with identity + invariants
- [ ] Create READMEs in ALL directories
- [ ] Create `__init__.py` with package docstring
- [ ] Update this file's "Applies To" table

---

*First implemented: Orthodoxy Wardens, February 2026*  
*Pattern version: 1.0*
