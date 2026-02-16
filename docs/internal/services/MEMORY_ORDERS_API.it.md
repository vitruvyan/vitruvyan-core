---
tags:
  - api
  - memory
  - sacred-orders
  - admin
---

# 🌐 Memory Orders API

<p class="kb-subtitle">Service LIVELLO 2 per coherence check, health aggregation (RAG) e sync planning.</p>

## 📍 Location

- Service: `services/api_memory_orders/`
- Core puro: `vitruvyan_core/core/governance/memory_orders/`

## 🚪 Base URL / Porta

- Default config: `MEMORY_API_PORT=8016` (`services/api_memory_orders/config.py`)

> Nota deploy: altri documenti possono citare una “fleet port” diversa. In deploy fa fede docker-compose.

## 🧭 Endpoint (implementati)

Definiti in `services/api_memory_orders/api/routes.py`:

- `GET /` — info servizio
- `GET /health` — health check semplice
- `GET /health/rag` — health completo (ritorna `503` se degraded/critical)
- `POST /coherence` — drift analysis tra Postgres e Qdrant
- `POST /sync` — sync planning (solo planning, nessuna esecuzione)
- `GET /metrics` — Prometheus (definito in `services/api_memory_orders/main.py`)

## 🧾 Modelli request/response

Vedi `services/api_memory_orders/models/schemas.py`.

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

## ⚙️ Env vars (service)

Caricate in `services/api_memory_orders/config.py`:

- Service: `MEMORY_API_PORT`, `LOG_LEVEL`
- Postgres: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Qdrant: `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_URL`
- Health checks: `EMBEDDING_API_URL`, `BABEL_GARDENS_URL`
- Soglie coerenza: `COHERENCE_THRESHOLD_HEALTHY`, `COHERENCE_THRESHOLD_WARNING`
- Audit: `MEMORY_AUDIT_TABLE`
- Flag: `ENABLE_AUTO_SYNC`, `ENABLE_PROMETHEUS`
