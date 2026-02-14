# Memory Orders

## What it does

- Drift calculation (PostgreSQL ↔ Qdrant)
- Health aggregation across memory dependencies
- Sync planning (planning-only; execution lives in LIVELLO 2)

- **Epistemic Layer**: Memory & Coherence
- **Mandate**: maintain coherence between **Archivarium** (PostgreSQL) and **Mnemosyne** (Qdrant)
- **Outputs**: coherence reports, health snapshots, sync plans (no I/O in LIVELLO 1)

## Charter (Mandate + Non-goals)

### Mandate
Provide deterministic, explainable coherence logic: drift measurement, health aggregation, and sync planning.

### Non-goals
- Does not perform DB reads/writes in LIVELLO 1.
- Does not “fix” data directly; it plans sync operations for LIVELLO 2 to execute.

## Interfaces

### Event contract (Cognitive Bus)
Defined in `vitruvyan_core/core/governance/memory_orders/events/memory_events.py`:

- `memory.coherence.requested` → `memory.coherence.checked`
- `memory.health.requested` → `memory.health.checked`
- `memory.sync.requested` → `memory.sync.completed | memory.sync.failed`

### Service (LIVELLO 2)
- `services/api_memory_orders/` — orchestration + I/O boundary (Redis/DB/Qdrant)

## Pipeline (happy path)

1. **CoherenceAnalyzer** computes drift (counts/ratios) → `CoherenceReport`
2. **HealthAggregator** merges component health → `SystemHealth`
3. **SyncPlanner** produces a deterministic `SyncPlan` (operations list)

## Code map

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/memory_orders/domain/` — frozen DTOs
- `vitruvyan_core/core/governance/memory_orders/consumers/` — coherence/health/sync planners
- `vitruvyan_core/core/governance/memory_orders/governance/thresholds.py` — drift thresholds

### LIVELLO 2 (adapters)
- `services/api_memory_orders/` — StreamBus subscriptions + DB/Qdrant agents

## Verticalization (finance pilot)

Memory Orders remains domain-agnostic; a vertical “binds” it by choosing:

- the canonical entity storage/table naming (e.g. finance `tickers`)
- which Qdrant collections represent the vertical memory (e.g. `ticker_embeddings`)
- how sync operations are executed in service/adapters (batch size, retries, scheduling)
