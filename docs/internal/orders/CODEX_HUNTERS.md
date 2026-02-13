# Codex Hunters

<p class="kb-subtitle">Discovery, normalization, deduplication, and storage-ready binding for raw source payloads.</p>

Codex Hunters is the **data acquisition and canonicalization** order: it turns “raw source payloads” into **deterministic, deduplicated, storage-ready entities**.

> This page documents **the current implementation** (LIVELLO 1 consumers + what LIVELLO 2 orchestrates around them).

## Code map

- **LIVELLO 1 (pure domain, no I/O)**: `vitruvyan_core/core/governance/codex_hunters/`
  - Consumers: `consumers/tracker.py`, `consumers/restorer.py`, `consumers/binder.py`
  - Domain model: `domain/entities.py`, `domain/config.py`
  - Examples: `examples/*_example.py`
- **LIVELLO 2 (service + adapters + bus + persistence)**: `services/api_codex_hunters/`
  - Bus orchestration: `adapters/bus_adapter.py`
  - API: `api/routes.py`
  - Streams listener: `streams_listener.py`

## Core domain objects (what moves through the pipeline)

- `DiscoveredEntity` → produced by Tracker (`status=discovered`)
- `RestoredEntity` → produced by Restorer (`status=restored`)
- `BoundEntity` → produced by Binder (`status=bound`)

## Pipeline (conceptual)

1. **Tracker** validates discovery request and turns raw payload into a `DiscoveredEntity`
2. **Restorer** normalizes and quality-scores data into a `RestoredEntity`
3. **Binder** binds the restored entity to storage refs and outputs a `BoundEntity`

The service layer performs I/O (Postgres/Qdrant, bus emission, rate limiting).

---

## Agents / Consumers

### `TrackerConsumer` — discovery + validation

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/tracker.py`
- Responsibilities:
  - validate required input fields (`entity_id`, `source`)
  - validate that `source` exists in `CodexConfig.sources`
  - build a `DiscoveredEntity` (domain object)
  - compute a **deterministic dedupe key** based on `entity_id + source + raw_data hash`
- Notes:
  - `prepare_discovery_config()` returns validated sources + rate-limit metadata for the adapter (the pure consumer does not enforce rate limiting)
  - `validate_entity_id()` is intentionally permissive (override in a vertical/service if needed)

**Input (expected)**:

- `entity_id: str`
- `source: str`
- `raw_data: dict` (provided by adapter)

**Output**:

- `data["entity"] = DiscoveredEntity`
- `data["dedupe_key"] = str`

**How it works (important details)**:

- `dedupe_key`:
  - hashes `raw_data` via `json.dumps(sort_keys=True)` → `sha256` (first 8 chars)
  - then hashes `f"{entity_id}:{source}:{data_hash}"` → `sha256` (first 16 chars)
- `DiscoveredEntity.metadata` includes `record_count` and `has_data`

---

### `RestorerConsumer` — normalization + quality scoring

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/restorer.py`
- Responsibilities:
  - normalize raw data (default: key cleaning, nested dict/list normalization)
  - validate normalized structure (e.g. “empty data”, “high null ratio”)
  - compute a `quality_score` using config-driven penalties
  - output a `RestoredEntity`
- Extensibility:
  - supports per-source `normalizers` (registerable functions) for domain/vertical specialization

**Input (expected)**:

- `entity: DiscoveredEntity | dict`

**Output**:

- `data["entity"] = RestoredEntity`

**How it works (important details)**:

- Default normalizer:
  - normalizes keys (`lower()`, spaces and `-` → `_`)
  - recursively normalizes nested dicts/lists
  - adds `_normalized_at` ISO timestamp
- Validation (default):
  - empty normalized payload → error
  - “high null ratio” (> 0.5) → error
- Quality score:
  - starts from `1.0`
  - subtracts `len(errors) * config.quality.penalty_per_error`
  - subtracts `null_ratio * config.quality.penalty_null_ratio`
  - clamps to `[0.0, 1.0]`

---

### `BinderConsumer` — binding + payload preparation (still pure)

- File: `vitruvyan_core/core/governance/codex_hunters/consumers/binder.py`
- Responsibilities:
  - generate deterministic `dedupe_key` for normalized payloads
  - prepare **storage references** (table/collection names from config)
  - optionally generate an `embedding_id` if an embedding vector is provided
  - output a domain-agnostic `BoundEntity` + data needed by LIVELLO 2

**Input (expected)**:

- `entity: RestoredEntity | dict`
- `embedding: list[float]` (optional; injected by adapter)

**Output**:

- `data["bound_entity"] = BoundEntity`
- `data["normalized_data"] = dict`
- `data["embedding"] = list[float] | None`
- `data["quality_score"] = float`
- `data["dedupe_key"] = str`

**How it works (important details)**:

- `dedupe_key` hashes `json.dumps(normalized_data, sort_keys=True)` (first 32 hex chars)
- `embedding_id` is **unique, not deterministic** (it includes a UTC timestamp)
- Helper methods exist for provider payloads (`_prepare_postgres_payload`, `_prepare_qdrant_payload`), but `process()` does not currently return them.

---

## Service layer (LIVELLO 2) orchestration

### `BusAdapter`

- File: `services/api_codex_hunters/adapters/bus_adapter.py`
- Responsibilities:
  - lazy-load pure consumers from LIVELLO 1
  - emit events to `StreamBus` (when available)
  - delegate actual persistence to the persistence adapter

## Implementation notes (current caveats)

- Restorer’s default `_normalized_at` timestamp makes the normalized payload **non-deterministic**.
  - If you use Binder’s `dedupe_key` for real deduplication, strip `_normalized_at` (or move it to metadata) in the service layer/vertical.

## Domain specialization (finance pilot)

Codex Hunters is domain-agnostic. The finance vertical binds:

- the **meaning** of `entity_id` (e.g. ticker)
- the configured sources, tables, and stream namespaces
- optional normalization functions in the service layer

Reference: `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`
