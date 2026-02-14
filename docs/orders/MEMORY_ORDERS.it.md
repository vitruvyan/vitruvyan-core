# Memory Orders

## A cosa serve

- Drift calculation (PostgreSQL ↔ Qdrant)
- Health aggregation sulle dipendenze di memoria
- Sync planning (solo planning; esecuzione in LIVELLO 2)

- **Livello epistemico**: Memoria & Coerenza
- **Mandato**: mantenere coerenza tra **Archivarium** (PostgreSQL) e **Mnemosyne** (Qdrant)
- **Output**: report coerenza, health snapshot, piani di sync (no I/O in LIVELLO 1)

## Charter (Mandato + Non-goals)

### Mandato
Fornire logica di coerenza deterministica e spiegabile: drift, health aggregation, sync planning.

### Non-goals
- Nessun accesso DB/Qdrant in LIVELLO 1.
- Non “fixa” dati direttamente; pianifica operazioni che LIVELLO 2 esegue.

## Interfacce

### Contratto eventi (Cognitive Bus)
Definiti in `vitruvyan_core/core/governance/memory_orders/events/memory_events.py`:

- `memory.coherence.requested` → `memory.coherence.checked`
- `memory.health.requested` → `memory.health.checked`
- `memory.sync.requested` → `memory.sync.completed | memory.sync.failed`

### Servizio (LIVELLO 2)
- `services/api_memory_orders/` — orchestrazione + boundary I/O (Redis/DB/Qdrant)

## Pipeline (happy path)

1. **CoherenceAnalyzer** calcola drift → `CoherenceReport`
2. **HealthAggregator** aggrega health → `SystemHealth`
3. **SyncPlanner** produce un `SyncPlan` deterministico

## Mappa codice

### LIVELLO 1 (pure)
- `vitruvyan_core/core/governance/memory_orders/domain/`
- `vitruvyan_core/core/governance/memory_orders/consumers/`
- `vitruvyan_core/core/governance/memory_orders/governance/thresholds.py`

### LIVELLO 2 (adapters)
- `services/api_memory_orders/`

## Verticalizzazione (pilota finanza)

Il dominio “lega” Memory Orders scegliendo naming e collezioni (es. `tickers`, `ticker_embeddings`) e la policy di esecuzione sync nel service layer.
