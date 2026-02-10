# Memory Orders

> **Dual-Memory Coherence System — Pure Domain Layer (LIVELLO 1)**

Foundational module for maintaining epistemic integrity between Archivarium (PostgreSQL) and Mnemosyne (Qdrant).

## Sacred Order

**Domain**: Memory & Persistence  
**Mandate**: Monitor coherence, aggregate health, plan synchronization  
**Layer**: LIVELLO 1 (Pure Domain — No I/O, No Infrastructure)

---

## Quick Start

```python
from vitruvyan_core.core.governance.memory_orders.domain import CoherenceInput, CoherenceReport
from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceAnalyzer
from vitruvyan_core.core.governance.memory_orders.governance import DEFAULT_THRESHOLDS

# Pure coherence analysis (no database required)
analyzer = CoherenceAnalyzer()
input_data = CoherenceInput(
    pg_count=1000,
    qdrant_count=980,
    thresholds=DEFAULT_THRESHOLDS.as_tuple()
)
report = analyzer.process(input_data)

print(f"Status: {report.status}")  # 'healthy'
print(f"Drift: {report.drift_percentage:.2f}%")  # 2.0%
print(f"Recommendation: {report.recommendation}")
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/memory_orders/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_memory_orders/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

---

## Structure

```
memory_orders/
├── domain/                # Frozen dataclasses (immutable DTOs)
│   └── memory_objects.py  # CoherenceInput, CoherenceReport, ComponentHealth, etc.
│
├── consumers/             # Pure decision engines (NO I/O)
│   ├── base.py            # MemoryRole ABC
│   ├── coherence_analyzer.py    # Drift calculation (pure math)
│   ├── health_aggregator.py     # Component status aggregation
│   └── sync_planner.py          # Sync operation planning
│
├── governance/            # Rules, thresholds, classifiers
│   ├── thresholds.py      # Coherence drift thresholds (frozen config)
│   └── health_rules.py    # Health aggregation rules
│
├── events/                # Event definitions, channel constants
│   └── memory_events.py   # MEMORY_COHERENCE_CHECKED, MemoryEvent envelope
│
├── monitoring/            # Metric name constants (NO prometheus_client)
│   └── metrics.py         # COHERENCE_DRIFT_PCT, HEALTH_STATUS, etc.
│
├── philosophy/            # Design charter, invariants
│   └── charter.md         # Identity, mandate, architectural decisions
│
├── _legacy/               # Pre-refactoring files (FROZEN, DO NOT MODIFY)
│   ├── coherence.py       # Old mixed I/O + logic (782 lines total)
│   ├── rag_health.py
│   └── phrase_sync.py
│
├── docs/                  # Extended documentation
├── examples/              # Standalone usage examples
├── tests/                 # Unit tests (pure, no infra)
└── README.md              # This file
```

---

## Packages

### domain/
Immutable domain objects. All `@dataclass(frozen=True)`. No I/O.

**Exports**:
- `CoherenceInput`, `CoherenceReport`
- `ComponentHealth`, `SystemHealth`
- `SyncInput`, `SyncOperation`, `SyncPlan`

### consumers/
Pure decision engines. `process()` is deterministic, no side effects.

**Exports**:
- `MemoryRole` (ABC)
- `CoherenceAnalyzer` — drift calculation
- `HealthAggregator` — component status aggregation
- `SyncPlanner` — sync operation planning

### governance/
Rules, thresholds, classifiers (data-driven, not behavior).

**Exports**:
- `CoherenceThresholds`, `DEFAULT_THRESHOLDS`
- `aggregate_component_statuses()`, `calculate_health_score()`

### events/
Channel constants + event envelopes.

**Exports**:
- Channel constants: `MEMORY_COHERENCE_CHECKED`, `MEMORY_HEALTH_CHECKED`, `MEMORY_SYNC_COMPLETED`
- Event envelope: `MemoryEvent`

### monitoring/
Prometheus metric NAME constants (no collectors).

**Exports**:
- `COHERENCE_DRIFT_PCT`, `HEALTH_STATUS`, `SYNC_OPERATIONS_TOTAL`, etc.

---

## Refactoring Status

| Phase | Status | Deliverables |
|-------|--------|-------------|
| **FASE 0** | ✅ Complete | Legacy files moved to `_legacy/` |
| **FASE 1** | ✅ Complete | LIVELLO 1 structure created (10 subdirs) |
| **FASE 2** | ⏳ Next | LIVELLO 2 adapters (bus_adapter, persistence, routes, config) |
| **FASE 3** | ⏳ Planned | main.py reduced to < 100 lines |
| **FASE 4** | ⏳ Planned | Tests pass, Docker rebuild successful |

**Migration**: `SACRED_ORDERS_REFACTORING_PLAN.md`  
**Pattern**: `vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md`  
**Templates**: Orthodoxy Wardens (Truth), Vault Keepers (Memory)

---

## Testing

All LIVELLO 1 code is pure → testable without infrastructure.

```bash
# Unit tests (no Docker, no PostgreSQL, no Redis)
pytest vitruvyan_core/core/governance/memory_orders/tests/

# Test imports (verify purity)
python3 -c "from vitruvyan_core.core.governance.memory_orders.consumers import CoherenceAnalyzer; print('✅ Pure')"
```

---

## Philosophy

Read `philosophy/charter.md` for:
- Identity & mandate
- Invariants (read-only checks, pure logic, configurable thresholds, event emission, audit trail, immutable objects)
- Architectural decisions (why two memory systems, why separate coherence from sync, why event-driven)
- Integration points
- Evolution timeline

---

## References

- **Coherence Algorithm**: `_legacy/coherence.py` (original implementation, 235 lines)
- **Health Checks**: `_legacy/rag_health.py` (original implementation, 277 lines)
- **Sync Planning**: `_legacy/phrase_sync.py` (original implementation, 270 lines)
- **Service Layer**: `services/api_memory_orders/` (LIVELLO 2, in progress)
- **Cognitive Bus**: `vitruvyan_core/core/synaptic_conclave/` (event transport)

---

**Created**: Feb 10, 2026  
**Refactoring**: FASE 1 complete  
**Status**: 🔄 In Progress (FASE 2 next)  
**Pattern Version**: 1.0 (Sacred Order Pattern)
