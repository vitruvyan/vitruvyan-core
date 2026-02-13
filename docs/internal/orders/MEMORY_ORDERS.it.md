# Memory Orders

<p class="kb-subtitle">Coerenza dual-memory: drift detection, health aggregation e sync planning tra Archivarium (PostgreSQL) e Mnemosyne (Qdrant).</p>

- **Layer epistemico**: Truth (Memory & Coherence)
- **Mandato**: proteggere l’integrità epistemica della conoscenza salvata su due sistemi di memoria
- **Output**: `CoherenceReport`, `SystemHealth`, `SyncPlan` *(solo planning)*

## Charter (mandato + non-goals)

### Mandato

- monitorare la **coerenza** (drift) tra Postgres e Qdrant
- aggregare lo **stato di salute** delle dipendenze (datastore + bus + embedding service)
- produrre **sync plans** (insert/delete/clear) senza eseguirli

### Non-goals

- niente scritture in LIVELLO 1 (no DB, no Qdrant, no StreamBus)
- niente “RAG answer synthesis”: non genera risposte finali per l’utente
- nessuna mutazione autonoma di default: l’esecuzione sync è delegata a worker/service

## Interfacce

- **HTTP (LIVELLO 2)**: `services/api_memory_orders/` espone `/coherence`, `/sync`, `/health/*`
- **Cognitive Bus (LIVELLO 2)**: adapter possono publish/consume eventi `memory.*` (opzionale)
- **Threshold di governance**: soglie drift configurabili (env + tuple immutabili)

## Contratto eventi (Cognitive Bus)

Definiti in `vitruvyan_core/core/governance/memory_orders/events/memory_events.py`:

- `memory.coherence.requested` / `memory.coherence.checked`
- `memory.health.requested` / `memory.health.checked`
- `memory.sync.requested` / `memory.sync.completed` / `memory.sync.failed`
- `memory.audit.recorded`

## Mappa del codice

- **LIVELLO 1 (puro, niente I/O)**: `vitruvyan_core/core/governance/memory_orders/`
  - Consumers: `consumers/coherence_analyzer.py`, `consumers/health_aggregator.py`, `consumers/sync_planner.py`
  - Oggetti dominio: `domain/memory_objects.py`
  - Rules/thresholds: `governance/thresholds.py`, `governance/health_rules.py`
  - Eventi: `events/memory_events.py`
- **LIVELLO 2 (service + adapters + I/O)**: `services/api_memory_orders/`
  - HTTP routes: `api/routes.py`
  - Bus orchestration: `adapters/bus_adapter.py`
  - Persistence: `adapters/persistence.py`

---

## Pipeline (happy path)

### Coherence check

1. `POST /coherence` (service) richiede un coherence check
2. L’adapter legge i conteggi:
   - record Postgres con `embedded=true`
   - punti Qdrant nella collection target
3. LIVELLO 1 `CoherenceAnalyzer.process(CoherenceInput)` ritorna un `CoherenceReport`
4. Il service ritorna il report e può emettere `memory.coherence.checked`

### Sync planning

1. `POST /sync` richiede un sync plan (mode: `incremental` o `full`)
2. L’adapter preleva snapshot (limitati da `limit`)
3. LIVELLO 1 `SyncPlanner.process(SyncInput)` ritorna un `SyncPlan`
4. Il service ritorna il piano (l’esecuzione è out-of-scope)

---

## Agenti / Consumers (LIVELLO 1)

### `CoherenceAnalyzer` — drift calculation (conteggi → report)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/coherence_analyzer.py`
- Input: `CoherenceInput(pg_count, qdrant_count, thresholds, table, collection)`
- Output: `CoherenceReport(status, drift_percentage, drift_absolute, recommendation, …)`

**Dettagli implementativi**:

- `drift_absolute = abs(pg_count - qdrant_count)`
- `drift_percentage = drift_absolute / max(pg_count, qdrant_count) * 100` (edge case: entrambi 0 → 0%)
- mapping soglie:
  - `< healthy` → `healthy`
  - `>= healthy` e `< warning` → `warning`
  - `>= warning` → `critical`

### `HealthAggregator` — health componenti (components → system health)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/health_aggregator.py`
- Input: dict con `components: tuple[ComponentHealth, ...]` + `summary` opzionale
- Output: `SystemHealth(overall_status, components, summary, timestamp)`

**Dettagli implementativi**:

- overall status:
  - se esiste `unhealthy` → `critical`
  - altrimenti se esiste `degraded` → `degraded`
  - altrimenti → `healthy`

### `SyncPlanner` — sync planning (snapshot → operazioni)

- File: `vitruvyan_core/core/governance/memory_orders/consumers/sync_planner.py`
- Input: `SyncInput(pg_data, qdrant_data, mode, source_table, target_collection)`
- Output: `SyncPlan(operations, estimated_duration_s, mode)`

**Dettagli implementativi**:

- `mode="full"`:
  - `delete` per clear della collection target
  - `insert` per ogni record Postgres
- `mode="incremental"`:
  - insert per id mancanti in Qdrant
  - delete per id orfani in Qdrant
- stima durata: `len(operations) * OPERATION_TIME_S` (oggi `0.1s` per op)

---

## Service (LIVELLO 2) — API surface

Vedi la pagina admin: `docs/internal/services/MEMORY_ORDERS_API.md`.
