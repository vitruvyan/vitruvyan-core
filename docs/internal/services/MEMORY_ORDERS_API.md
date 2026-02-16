---
tags:
  - api
  - memory
  - sacred-orders
  - admin
---

# 🌐 Memory Orders API

<p class="kb-subtitle">LIVELLO 2 service for coherence checks, RAG health aggregation, and sync planning.</p>

## 📍 Location

- Service: `services/api_memory_orders/`
- Pure core: `vitruvyan_core/core/governance/memory_orders/`

## 🚪 Base URL / Port

- Config default: `MEMORY_API_PORT=8016` (`services/api_memory_orders/config.py`)

> Deploy note: other documents may refer to a different “fleet” port. Treat docker-compose mapping as the source of truth.

## 🧭 Endpoints (implemented)

Defined in `services/api_memory_orders/api/routes.py`:

- `GET /` — service info
- `GET /health` — simple health check
- `GET /health/rag` — full dependency + coherence health (returns `503` when degraded/critical)
- `POST /coherence` — drift analysis between Postgres and Qdrant
- `POST /sync` — sync planning (planning only, no execution)
- `GET /metrics` — Prometheus (defined in `services/api_memory_orders/main.py`)

## 🧾 Request/Response models

See `services/api_memory_orders/models/schemas.py`.

### 📉 `POST /coherence`

Request (`CoherenceRequest`):

- `table: str = "entities"`
- `collection: str | null`
- `embedded_column: str = "embedded"`

Response (`CoherenceResponse`):

- `status: healthy|warning|critical`
- `drift_percentage: float`
- `recommendation: str`
- `pg_count: int`
- `qdrant_count: int`
- `drift_absolute: int`
- `timestamp: str`
- `table: str`
- `collection: str`

### 🔁 `POST /sync`

Request (`SyncRequest`):

- `mode: incremental|full` (default `incremental`)
- `table: str = "entities"`
- `collection: str | null`
- `limit: int = 1000`

Response (`SyncResponse`):

- `operations: SyncOperationResponse[]`
- `estimated_duration_s: float`
- `mode: str`
- `total_operations: int`

## ⚙️ Env vars (service-level)

Loaded in `services/api_memory_orders/config.py`:

- Service: `MEMORY_API_PORT`, `LOG_LEVEL`
- Postgres: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Qdrant: `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_URL`
- External checks: `EMBEDDING_API_URL`, `BABEL_GARDENS_URL`
- Coherence thresholds: `COHERENCE_THRESHOLD_HEALTHY`, `COHERENCE_THRESHOLD_WARNING`
- Audit: `MEMORY_AUDIT_TABLE`
- Flags: `ENABLE_AUTO_SYNC`, `ENABLE_PROMETHEUS`
