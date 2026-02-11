# Appendix O — Orthodoxy Wardens: Sacred Order of Truth & Governance
*Epistemic Integrity Through Immutable Judgment*

---

## Overview

The **Orthodoxy Wardens** are Vitruvyan's compliance tribunal — a Sacred Order responsible for auditing, validating, and judging every output before it reaches the user. They implement a five-status verdict system inspired by Roman jurisprudence, including the explicit ability to say "I don't know" (`non_liquet`), which prevents confident hallucinations.

**Sacred Order**: Truth & Governance  
**Architecture**: Two-level (Foundational + Service)  
**Status**: Production (Feb 9, 2026) — 4 FASI completed, 153 tests, 0.15s  

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Domain Objects](#2-domain-objects)
3. [Events](#3-events)
4. [Consumers (SacredRole)](#4-consumers-sacredrole)
5. [Governance Engine](#5-governance-engine)
6. [Service Layer (LIVELLO 2)](#6-service-layer-livello-2)
7. [Pipeline Flow](#7-pipeline-flow)
8. [Testing](#8-testing)
9. [Directory Structure](#9-directory-structure)
10. [Golden Rules](#10-golden-rules)
11. [Implementation History](#11-implementation-history)

---

## 1. Architecture

Orthodoxy Wardens follows the **Two-Level Sacred Order Pattern** — a strict separation between pure domain logic and infrastructure concerns.

### Level 1 — Foundational (`vitruvyan_core/core/governance/orthodoxy_wardens/`)

**Pure Python. No infrastructure. Importable. Testable in isolation.**

Contains: domain objects, decision logic, event definitions, consumers, governance engine.  
Does NOT contain: database connections, bus listeners, API endpoints, Docker.

### Level 2 — Service (`services/api_orthodoxy_wardens/`)

**Infrastructure. Bus. Database. API. Docker.**

Contains: FastAPI app, StreamBus adapters, PostgreSQL persistence, health checks.  
Imports FROM Level 1. **Never the other way around.**

```
Level 1 (Foundational)              Level 2 (Service)
──────────────────────              ──────────────────
      domain/              ←── imports ──  adapters/bus_adapter.py
      consumers/           ←── imports ──  adapters/bus_adapter.py
      governance/          ←── imports ──  adapters/bus_adapter.py
      events/              ←── imports ──  streams_listener.py
                                           adapters/persistence.py  →  PostgreSQL/Qdrant
```

> **"Il giudice (core) non tocca mai il database. Il cancelliere (service) lo fa per lui."**

---

## 2. Domain Objects

All domain objects are **frozen dataclasses** — immutable after creation.

### Confession (`domain/confession.py`)

An audit request entering the tribunal. Created by the Confessor from raw events.

```python
@dataclass(frozen=True)
class Confession:
    confession_id: str           # UUID, required
    trigger_type: str            # code_commit | scheduled | manual | output_validation | event
    scope: str                   # complete_realm | single_service | single_output | single_event
    urgency: str                 # critical | high | routine | low
    source: str                  # Originating service
    timestamp: str               # ISO 8601, required
    correlation_id: Optional[str] = None
    metadata: tuple = ()         # Frozen tuple of (key, value) pairs
```

**Validation**: `__post_init__` enforces valid `trigger_type`, `scope`, and `urgency` via frozensets.

### Finding (`domain/finding.py`)

An individual observation discovered during examination.

```python
@dataclass(frozen=True)
class Finding:
    finding_id: str              # UUID, required (first positional arg)
    finding_type: str            # violation | warning | observation | anomaly
    severity: str                # critical | high | medium | low
    category: str                # compliance | security | performance | quality |
                                 # data_quality | hallucination | architectural | epistemic
    message: str                 # Human-readable description
    source_rule: str             # Rule ID that generated this finding
    context: tuple = ()          # Frozen evidence tuple
```

### Verdict (`domain/verdict.py`)

The **most important domain object** — the final judgment on a Confession. Five statuses implement the Socratic Pattern:

| Status | Meaning | `should_send` | When |
|--------|---------|---------------|------|
| `blessed` | Valid, high confidence | `True` | Clean output, no issues |
| `purified` | Corrected, errors removed | `True` | Issues found and fixed |
| `heretical` | Rejected, hallucination/violation | `False` | Fatal issues, blocked |
| `non_liquet` | Insufficient confidence | `True` (with disclaimer) | "I don't know" |
| `clarification_needed` | Input too ambiguous | `False` | Ask user for more info |

```python
@dataclass(frozen=True)
class Verdict:
    status: str                  # One of 5 statuses above
    confidence: float            # 0.0 - 1.0
    findings: tuple              # All Findings from examination
    explanation: str             # Human-readable reasoning
    should_send: bool            # Whether output reaches the user
    ruleset_version: Optional[str] = None  # SHA-256 of RuleSet used
    # non_liquet specific:
    what_we_know: tuple = ()
    what_is_uncertain: tuple = ()
    uncertainty_sources: tuple = ()
    best_guess: Optional[str] = None
```

**Factory methods** (canonical creation):
- `Verdict.blessed(confidence, findings, explanation, ruleset_version)`
- `Verdict.purified(confidence, findings, explanation, ruleset_version)`
- `Verdict.heretical(findings, explanation, confidence=0.95, ruleset_version)`
- `Verdict.non_liquet(confidence, what_we_know, what_is_uncertain, uncertainty_sources, best_guess, findings, ruleset_version)`
- `Verdict.clarification_needed(explanation, findings, ruleset_version)`

### LogDecision (`domain/log_decision.py`)

The Chronicler's decision on how to archive a Verdict.

```python
@dataclass(frozen=True)
class LogDecision:
    action: str                  # skip | log_standard | log_critical_audit
    category: Optional[str] = None
    reason: str = ""
```

**Factories**: `LogDecision.skip(reason)`, `LogDecision.critical_audit(category, reason)`, `LogDecision.standard(category, reason)`

---

## 3. Events

### OrthodoxyEvent (`events/orthodoxy_events.py`)

Frozen event envelope for all Orthodoxy Wardens events.

```python
@dataclass(frozen=True)
class OrthodoxyEvent:
    event_type: str              # One of 17 constants below
    payload: tuple               # Frozen (key, value) pairs
    timestamp: str               # ISO 8601, required
    source: str = "orthodoxy_wardens"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
```

**17 Event Type Constants**:

| Category | Events |
|----------|--------|
| Lifecycle | `CONFESSION_RECEIVED`, `EXAMINATION_STARTED`, `EXAMINATION_COMPLETED` |
| Verdict | `VERDICT_RENDERED`, `VERDICT_BLESSED`, `VERDICT_PURIFIED`, `VERDICT_HERETICAL`, `VERDICT_NON_LIQUET`, `VERDICT_CLARIFICATION` |
| Action | `CORRECTION_REQUESTED`, `CORRECTION_APPLIED`, `CORRECTION_FAILED` |
| Archive | `ARCHIVE_REQUESTED`, `ARCHIVE_COMPLETED` |
| System | `HEARTBEAT`, `ERROR`, `RULESET_UPDATED` |

All constants are plain strings (no Enum), following the Synaptic Conclave convention.

---

## 4. Consumers (SacredRole)

All consumers inherit from **SacredRole** — a pure ABC with no I/O.

```python
class SacredRole(ABC):
    @property
    @abstractmethod
    def role_name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def can_handle(self, event) -> bool: ...

    @abstractmethod
    def process(self, event) -> Any: ...
```

### Confessor (`consumers/confessor.py`) — Intake Officer

**Input**: Raw event (OrthodoxyEvent or dict)  
**Output**: `Confession`

Normalizes incoming events into a structured Confession. Handles both OrthodoxyEvent objects and raw dicts. Assigns `confession_id` (UUID), maps trigger types, extracts metadata.

### Inquisitor (`consumers/inquisitor.py`) — Examiner

**Input**: `{"confession": Confession, "text": str, "code": str}`  
**Output**: `InquisitorResult(findings, examined_categories, examination_notes)`

Examines content using two classifier strategies:
- **PatternClassifier**: Regex-based finding generation against the RuleSet
- **ASTClassifier**: Python AST analysis for code (handles SyntaxError gracefully → "anomaly")

Each finding gets a unique `finding_id` (UUID).

### Penitent (`consumers/penitent.py`) — Correction Advisor

**Input**: `Verdict`  
**Output**: `CorrectionPlan(corrections, summary)`

Generates correction recommendations based on verdict status:
- `heretical` → Mandatory corrections with "rewrite" or "block" strategies
- `purified` → Advisory corrections with "annotate" strategy
- `blessed` → No corrections needed
- `non_liquet` → "escalate" strategy

Each correction is a `CorrectionRequest` with validated `strategy` and `priority` fields.

### Chronicler (`consumers/chronicler.py`) — Archive Strategist

**Input**: `Verdict`  
**Output**: `ChronicleDecision(directives, log_decision, summary)`

Decides archival strategy based on verdict severity:
- `heretical` → All destinations (postgresql, qdrant, blockchain), 365-day retention
- `purified` → postgresql + qdrant, 180-day retention
- `blessed` → postgresql only, 30-day retention
- `non_liquet` → postgresql + qdrant (for future retrieval learning), 90-day retention

Each `ArchiveDirective` specifies destination (validated against `VALID_DESTINATIONS`), format, and retention days.

---

## 5. Governance Engine

### Rule (`governance/rule.py`)

Immutable definition of a single compliance check.

```python
@dataclass(frozen=True)
class Rule:
    rule_id: str                 # e.g., "compliance.prescriptive_language.001"
    category: str                # compliance | security | performance | quality | ...
    subcategory: str             # Finer classification
    severity: str                # critical | high | medium | low
    pattern: str                 # Regex pattern
    description: str             # Human-readable explanation
    enabled: bool = True
```

### RuleSet (`governance/rule.py`)

Versioned, frozen collection of Rules with SHA-256 checksum.

```python
RuleSet.create(
    version="v2.3",
    rules=(rule1, rule2, ...),
    description="Production compliance ruleset"
)
```

**DEFAULT_RULESET**: 35 rules across 6 categories (compliance, security, performance, quality, data_quality, hallucination).

The checksum is computed automatically from serialized rules — every Verdict references the exact RuleSet version that produced it, enabling **full audit replay**.

### PatternClassifier (`governance/classifier.py`)

Matches text against RuleSet patterns. Returns `(category, confidence)`.

### ASTClassifier (`governance/classifier.py`)

Parses Python code into AST, detects structural issues. Returns "anomaly" (not "warning") on SyntaxError.

### VerdictEngine (`governance/verdict_engine.py`)

The core judgment algorithm:

1. **Score** findings by severity × category weights (`ScoringWeights`)
2. **Threshold** the aggregate score to determine verdict status
3. **Render** a `Verdict` with explanation, findings, and ruleset checksum
4. **Decide logging** via `decide_logging()` → `LogDecision`

```python
engine = VerdictEngine()
verdict = engine.render(
    findings=result.findings,
    ruleset=DEFAULT_RULESET,
    confession_id="abc-123"
)
log_decision = engine.decide_logging(verdict)
```

### Workflow (`governance/workflow.py`)

Predefined step sequences:

- **FULL_AUDIT_WORKFLOW** (7 steps): intake → classify → examine → evaluate → judge → correct → archive
- **QUICK_VALIDATION_WORKFLOW** (3 steps): intake → examine → judge

Each `WorkflowStep` has `name`, `description`, `required` flag, and `timeout_seconds`.

---

## 6. Service Layer (LIVELLO 2)

The service layer follows `SERVICE_PATTERN.md` — a replicable template for all Sacred Orders.

### config.py — Single Source of Environment

All `os.getenv()` calls centralized. No env vars scattered across files.

```python
class Settings:
    SERVICE_NAME = "api_orthodoxy_wardens"
    REDIS_URL = os.getenv("REDIS_URL", "redis://vitruvyan_redis_master:6379")
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "orthodoxy_wardens")
    SACRED_CHANNELS = [
        "orthodoxy.audit.requested",
        "orthodoxy.validation.requested",
        "neural_engine.screening.completed",
        "babel.sentiment.completed",
        "memory.write.completed",
        "vee.explanation.completed",
        "langgraph.response.completed",
    ]
```

### adapters/bus_adapter.py — The Pipeline Bridge

Bridges infrastructure events to pure domain consumers. This is **the only file that wires the pipeline**.

```python
class OrthodoxyBusAdapter:
    def __init__(self, ruleset=None):
        self.confessor = Confessor()
        self.inquisitor = Inquisitor()
        self.verdict_engine = VerdictEngine()
        self.penitent = Penitent()
        self.chronicler = Chronicler()
        self.ruleset = ruleset or DEFAULT_RULESET

    def handle_event(self, event: dict) -> dict:
        confession = self.confessor.process(event)       # 1. Intake
        result = self.inquisitor.process({...})           # 2. Examine
        verdict = self.verdict_engine.render(...)         # 3. Judge
        plan = self.penitent.process(verdict)             # 4. Correct
        chronicle = self.chronicler.process(verdict)      # 5. Archive
        return {
            "confession_id": confession.confession_id,
            "verdict": serialize(verdict),
            "correction_plan": serialize(plan),
            "chronicle_decision": serialize(chronicle),
            "findings_count": len(result.findings),
        }

    def handle_quick_validation(self, event: dict) -> dict:
        # Steps 1-3 only (no correction, no chronicle)
        ...
```

### adapters/persistence.py — Single I/O Point

The **only file that touches databases**. Core domain objects never import this.

```python
class PersistenceAdapter:
    def __init__(self, pg=None, qdrant=None):
        self._pg = pg       # Lazy-loaded PostgresAgent
        self._qdrant = qdrant  # Lazy-loaded QdrantAgent

    def save_verdict(self, pipeline_result: dict) -> bool: ...
    def save_chronicle(self, pipeline_result: dict) -> bool: ...
    def get_recent_findings(self, limit=50) -> list: ...
    def get_verdict_stats(self, days=7) -> dict: ...
```

### streams_listener.py — Bus Entry Point

Wraps legacy `redis_listener.py` via `ListenerAdapter` for Redis Streams consumption.  
7 sacred channels subscribed. Uses `wrap_legacy_listener()` from Synaptic Conclave.

---

## 7. Pipeline Flow

```
 ┌───────────────────────────────────────────────────────────────────┐
 │  INFRASTRUCTURE (Level 2)                                        │
 │                                                                   │
 │  Redis Streams ──→ streams_listener.py                           │
 │  HTTP Request  ──→ routes/                                        │
 │       │                                                           │
 │       ▼                                                           │
 │  adapters/bus_adapter.py  (OrthodoxyBusAdapter)                  │
 │       │                                                           │
 ├───────┼───────────────────────────────────────────────────────────┤
 │       │  PURE DOMAIN (Level 1)                                   │
 │       ▼                                                           │
 │  ┌─────────┐    ┌────────────┐    ┌──────────────┐              │
 │  │Confessor│───→│ Inquisitor │───→│VerdictEngine │              │
 │  │ (intake)│    │ (examine)  │    │   (judge)    │              │
 │  └─────────┘    └────────────┘    └──────┬───────┘              │
 │       event→Confession  Confession→      │                       │
 │                         Findings    Findings→Verdict             │
 │                                          │                       │
 │                              ┌───────────┼───────────┐          │
 │                              ▼                       ▼          │
 │                        ┌──────────┐          ┌────────────┐     │
 │                        │ Penitent │          │ Chronicler │     │
 │                        │(correct) │          │ (archive)  │     │
 │                        └──────────┘          └────────────┘     │
 │                     Verdict→CorrectionPlan  Verdict→Chronicle   │
 │                                                                   │
 ├───────────────────────────────────────────────────────────────────┤
 │  PERSISTENCE (Level 2)                                           │
 │       │                                                           │
 │       ▼                                                           │
 │  adapters/persistence.py ──→ PostgreSQL (audit_findings)         │
 │                          ──→ Qdrant (semantic archive)            │
 │                          ──→ Blockchain (immutable anchor)        │
 └───────────────────────────────────────────────────────────────────┘
```

---

## 8. Testing

### Test Inventory

| Suite | File | Tests | FASE | What it covers |
|-------|------|-------|------|----------------|
| Governance Engine | `test_governance_engine.py` | 54 | FASE 2 | Rule, RuleSet, Classifier, VerdictEngine, Workflow |
| Consumers | `test_consumers.py` | 79 | FASE 3 | Confessor, Inquisitor, Penitent, Chronicler, full pipeline |
| Bus Adapter | `test_bus_adapter.py` | 20 | FASE 4 | OrthodoxyBusAdapter, serialization, quick validation |
| **Total** | | **153** | | **0.15s execution time** |

### Running Tests

```bash
cd vitruvyan-core

# All pure tests (no infra required)
python3 -m pytest vitruvyan_core/core/governance/orthodoxy_wardens/tests/ \
  --ignore=vitruvyan_core/core/governance/orthodoxy_wardens/tests/test_orthodoxy_bus.py \
  -v --tb=short

# Quick check
python3 -m pytest vitruvyan_core/core/governance/orthodoxy_wardens/tests/test_bus_adapter.py \
  vitruvyan_core/core/governance/orthodoxy_wardens/tests/test_governance_engine.py \
  vitruvyan_core/core/governance/orthodoxy_wardens/tests/test_consumers.py -q
```

**Note**: `test_orthodoxy_bus.py` is a pre-existing infrastructure test requiring Redis — skip for pure unit testing.

### Test Philosophy

- **100% pure**: No database, no Redis, no Docker needed
- **Deterministic**: Same input → same output, every time
- **Fast**: 153 tests in 0.15 seconds
- **Full pipeline coverage**: From raw event dict through to Verdict + CorrectionPlan + ChronicleDecision

---

## 9. Directory Structure

### Level 1 — Foundational

```
vitruvyan_core/core/governance/orthodoxy_wardens/
├── _legacy/                          # Frozen pre-refactoring agents (DO NOT MODIFY)
│   ├── chronicler_agent.py (657L)
│   ├── docker_manager.py (678L)
│   ├── git_monitor.py (596L)
│   └── schema_validator.py (267L)
├── domain/                           # Frozen dataclasses
│   ├── confession.py
│   ├── finding.py
│   ├── verdict.py
│   └── log_decision.py
├── events/                           # Event type constants + envelope
│   └── orthodoxy_events.py
├── consumers/                        # Pure SacredRole implementations
│   ├── base.py (SacredRole ABC)
│   ├── confessor.py
│   ├── inquisitor.py
│   ├── penitent.py
│   └── chronicler.py
├── governance/                       # Decision engine
│   ├── rule.py (Rule + RuleSet + DEFAULT_RULESET)
│   ├── classifier.py (Pattern + AST)
│   ├── verdict_engine.py (VerdictEngine + ScoringWeights)
│   └── workflow.py (Workflow + predefined flows)
├── monitoring/
│   └── metrics.py (Prometheus metric names)
├── philosophy/
│   └── charter.md (Sacred Order charter)
├── tests/
│   ├── test_governance_engine.py (54 tests)
│   ├── test_consumers.py (79 tests)
│   └── test_bus_adapter.py (20 tests)
├── examples/
│   ├── example_confession_to_verdict.py
│   ├── example_governance_pipeline.py
│   └── example_tribunal_pipeline.py
├── SACRED_ORDER_PATTERN.md
└── README.md
```

### Level 2 — Service

```
services/api_orthodoxy_wardens/
├── main.py                           # FastAPI app (target: <50 lines)
├── config.py                         # Centralized environment variables
├── adapters/
│   ├── bus_adapter.py                # Pipeline bridge (Confessor→...→Chronicler)
│   └── persistence.py                # Single I/O point (PostgreSQL, Qdrant)
├── api/
│   └── routes.py                     # HTTP endpoints
├── models/
│   └── schemas.py                    # Pydantic request/response schemas
├── monitoring/
│   └── health.py                     # Health checks + Conclave listeners
├── streams_listener.py               # Redis Streams entry point
├── redis_listener.py                 # Legacy listener (wrapped by streams_listener)
└── docs/
    ├── API_REFERENCE.md
    ├── ARCHITECTURAL_DECISIONS.md
    └── ORTHODOXY_WARDENS_GUIDE.md
```

### Flat Services Layout (12 services)

```
services/
├── SERVICE_PATTERN.md                # Canonical replicable template
├── api_babel_gardens/
├── api_codex_hunters/
├── api_conclave/
├── api_embedding/
├── api_graph/
├── api_mcp/
├── api_memory_orders/
├── api_neural_engine/
├── api_orthodoxy_wardens/
├── api_pattern_weavers/
├── api_semantic/
└── api_vault_keepers/
```

---

## 10. Golden Rules

### Architectural Invariants

| Rule | Rationale |
|------|-----------|
| Core never imports from service | Dependency flows one way: service → core |
| All domain objects are frozen | Immutability = auditability = trust |
| No `psycopg2.connect()` in core | All I/O through `PersistenceAdapter` |
| No `StreamBus` in consumers | Pure `process(input) → result`, no infra |
| Every Verdict references `ruleset_version` | Full audit replay capability |
| Confessor validates trigger_type | Invalid inputs rejected at intake, not deep in pipeline |
| Finding requires `finding_id` first | UUID per observation enables granular tracking |
| `_legacy/` is frozen | Pre-refactoring code preserved for reference, never modified |

### Naming Conventions

| Object | Naming | Example |
|--------|--------|---------|
| Event types | `SCREAMING_SNAKE` | `VERDICT_RENDERED` |
| Domain objects | `PascalCase` | `Confession`, `Finding`, `Verdict` |
| Consumers | Role noun | `Confessor`, `Inquisitor`, `Penitent`, `Chronicler` |
| Rule IDs | `category.subcategory.NNN` | `compliance.prescriptive_language.001` |
| Service dirs | `api_<order>` | `api_orthodoxy_wardens` |

### Common Mistakes to Avoid

- **Using `Verdict.to_dict()`** — Verdict is a frozen dataclass, use `dataclasses.asdict(verdict)`
- **Passing `trigger_type="commit"`** — Valid values: `code_commit`, `scheduled`, `manual`, `output_validation`, `event`
- **Creating `Finding` without `finding_id`** — It's the first required positional argument
- **Creating `OrthodoxyEvent` without `timestamp`** — Required field, not optional
- **Importing `PostgresAgent` in consumers** — Consumers are pure; persistence belongs in adapters
- **Using `RuleSet(...)` directly** — Use factory `RuleSet.create(version, rules, description)`

---

## 11. Implementation History

| FASE | Date | Commit | Description | Files | Tests Added |
|------|------|--------|-------------|-------|-------------|
| 0 | Feb 9, 2026 | `87883a1` | Legacy isolation: 4 files → `_legacy/` | 34 | — |
| 1 | Feb 9, 2026 | `87883a1` | Domain objects, events, SacredRole ABC, monitoring, philosophy | (same) | — |
| 2 | Feb 9, 2026 | `cb994a0` | Governance Engine: Rule, Classifier, VerdictEngine, Workflow | 9 | 54 |
| 3 | Feb 9, 2026 | `0ecd957` | Consumers: Confessor, Inquisitor, Penitent, Chronicler | 8 | 79 |
| 4 | Feb 9, 2026 | `f3196e8` | Service slimming: flat services/, adapters, SERVICE_PATTERN.md | 103 | 20 |

**Total**: 153 tests, 100% passing, 0.15s execution time.

### Design Decisions

1. **LangGraph only in service layer** — Core uses declarative dicts, not LangGraph nodes
2. **RuleSet is frozen, config-driven** — No decorators, no runtime mutation, SHA-256 versioned
3. **Chronicler = LogDecision engine** — No psutil, no DB, pure archival strategy
4. **SacredRole ABC is pure** — `process(input) → result`, no StreamBus, no I/O
5. **VINCOLANTE execution order** — FASE 0→1→2→3→4, each building on the previous

---

## References

- **Sacred Order Pattern**: `vitruvyan_core/core/governance/orthodoxy_wardens/SACRED_ORDER_PATTERN.md`
- **Service Pattern**: `services/SERVICE_PATTERN.md`
- **Philosophy Charter**: `vitruvyan_core/core/governance/orthodoxy_wardens/philosophy/charter.md`
- **Appendix D**: Truth & Integrity Layer (parent context)
- **Appendix L**: Synaptic Conclave (Cognitive Bus integration)

---

*Created: February 9, 2026*  
*Architecture Version: 1.0 (FASE 0-4 Complete)*  
*Sacred Order: Truth & Governance*
