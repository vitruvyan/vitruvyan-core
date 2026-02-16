---
tags:
  - sacred-orders
  - memory
  - governance
  - admin
---

# 🗂️ Memory Orders

> **Last Updated**: February 14, 2026

<p class="kb-subtitle">Dual-memory coherence: drift detection, health aggregation, and sync planning between Archivarium (PostgreSQL) and Mnemosyne (Qdrant).</p>

## 🎯 What it does

- 📉 **Drift calculation**: detects divergence between Postgres and Qdrant (counts/coverage drift)
- 🩺 **Health aggregation**: produces an overall health snapshot from component signals
- 🧭 **Sync planning**: outputs a plan of operations (insert/delete/clear) without executing it

- ⚖️ **Epistemic layer**: Truth (Memory & Coherence)
- 🛡️ **Mandate**: protect epistemic integrity of stored knowledge across two memory systems
- 📦 **Outputs**: `CoherenceReport`, `SystemHealth`, `SyncPlan` *(planning-only)*

## 📜 Charter (mandate + non-goals)

### ✅ Mandate

- monitor **coherence** (drift) between Postgres and Qdrant
- aggregate **health** across memory dependencies (datastores + bus + embedding service)
- produce **sync plans** (what to insert/delete/clear) without executing them

### 🚫 Non-goals

- no writes in LIVELLO 1 (no DB, no Qdrant, no StreamBus)
- no “RAG answer synthesis”: Memory Orders does not generate final user answers
- no autonomous mutation by default: sync execution is delegated to a worker/service

## 🔌 Interfaces

- **HTTP (LIVELLO 2)**: `services/api_memory_orders/` exposes `/coherence`, `/sync`, `/health/*`
- **Cognitive Bus (LIVELLO 2)**: adapters publish/consume `memory.*` events (optional)
- **Governance thresholds**: drift thresholds are configurable (env + frozen tuples)

## 📡 Event contract (Cognitive Bus)

Defined in `vitruvyan_core/core/governance/memory_orders/events/memory_events.py`:

- `memory.coherence.requested` / `memory.coherence.checked`
- `memory.health.requested` / `memory.health.checked`
- `memory.sync.requested` / `memory.sync.completed` / `memory.sync.failed`
- `memory.audit.recorded`

## 🧩 Code map

- **LIVELLO 1 (pure, no I/O)**: `vitruvyan_core/core/governance/memory_orders/`
  - Consumers: `consumers/coherence_analyzer.py`, `consumers/health_aggregator.py`, `consumers/sync_planner.py`
  - Domain objects: `domain/memory_objects.py`
  - Governance rules/thresholds: `governance/thresholds.py`, `governance/health_rules.py`
  - Events: `events/memory_events.py`
- **LIVELLO 2 (service + adapters + I/O)**: `services/api_memory_orders/`
  - HTTP routes: `api/routes.py`
  - Bus orchestration: `adapters/bus_adapter.py`
  - Persistence: `adapters/persistence.py`

---

## 🔁 Pipeline (happy path)

### 📉 Coherence check

1. `POST /coherence` (service) requests a coherence check
2. Adapter reads counts:
   - Postgres records with `embedded=true`
   - Qdrant points in target collection
3. LIVELLO 1 `CoherenceAnalyzer.process(CoherenceInput)` returns a `CoherenceReport`
4. Service returns the report and may emit `memory.coherence.checked`

### 🧭 Sync planning

1. `POST /sync` requests a sync plan (mode: `incremental` or `full`)
2. Adapter pulls source/target samples (bounded by `limit`)
3. LIVELLO 1 `SyncPlanner.process(SyncInput)` returns a `SyncPlan`
4. Service returns the plan (execution is out-of-scope)

---

## 🤖 Agents / Consumers (LIVELLO 1)

### 📉 `CoherenceAnalyzer` — drift calculation (counts → report)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/coherence_analyzer.py`
- Input: `CoherenceInput(pg_count, qdrant_count, thresholds, table, collection)`
- Output: `CoherenceReport(status, drift_percentage, drift_absolute, recommendation, …)`

**How it works (important details)**:

- `drift_absolute = abs(pg_count - qdrant_count)`
- `drift_percentage = drift_absolute / max(pg_count, qdrant_count) * 100` (edge case: both 0 → 0%)
- threshold mapping:
  - `< healthy` → `healthy`
  - `>= healthy` and `< warning` → `warning`
  - `>= warning` → `critical`

### 🩺 `HealthAggregator` — component health (components → system health)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/health_aggregator.py`
- Input: dict with `components: tuple[ComponentHealth, ...]` and optional `summary`
- Output: `SystemHealth(overall_status, components, summary, timestamp)`

**How it works (important details)**:

- overall status:
  - any `unhealthy` → `critical`
  - else any `degraded` → `degraded`
  - else → `healthy`

### 🧭 `SyncPlanner` — sync planning (data snapshots → operations)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/sync_planner.py`
- Input: `SyncInput(pg_data, qdrant_data, mode, source_table, target_collection)`
- Output: `SyncPlan(operations, estimated_duration_s, mode)`

**How it works (important details)**:

- `mode="full"`:
  - `delete` plan to clear target collection
  - `insert` plan for every Postgres record
- `mode="incremental"`:
  - inserts for ids missing in Qdrant
  - deletes for orphaned ids in Qdrant
- duration estimate: `len(operations) * OPERATION_TIME_S` (currently `0.1s` per op)

---

## 🌐 Service (LIVELLO 2) — API surface

See the admin page: `docs/internal/services/MEMORY_ORDERS_API.md`.
