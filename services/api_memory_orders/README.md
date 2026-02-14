# API Memory Orders

> **Dual-Memory Coherence Service — LIVELLO 2 Infrastructure Layer**

REST API service for monitoring epistemic integrity between Archivarium (PostgreSQL) and Mnemosyne (Qdrant). Provides endpoints for coherence analysis, health aggregation, and synchronization planning.

## Sacred Order

**Domain**: Memory & Persistence  
**Mandate**: Monitor coherence, aggregate health, plan synchronization  
**Layer**: LIVELLO 2 (Service — Infrastructure, API, Docker)

---

## Quick Start

### Local Development
```bash
cd services/api_memory_orders
pip install -r requirements.txt
python main.py
```

### Docker
```bash
cd infrastructure/docker
docker compose up -d api_memory_orders
```

### API Usage
```python
import requests

# Check coherence
response = requests.post("http://localhost:8016/coherence", json={
    "table": "entities",
    "collection": "entities_embeddings"
})
print(response.json())
# {"status": "healthy", "drift_percentage": 2.0, ...}

# Get health status
response = requests.get("http://localhost:8016/health")
print(response.json())
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/memory_orders/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_memory_orders/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

### Service Components

```
api_memory_orders/
├── main.py              FastAPI bootstrap (< 100 lines)
├── config.py            Environment variables, settings
├── adapters/
│   ├── bus_adapter.py   Orchestrates LIVELLO 1 + StreamBus events
│   └── persistence.py   I/O layer (PostgresAgent, QdrantAgent)
├── api/
│   └── routes.py        HTTP endpoints (validate → delegate → return)
├── models/
│   └── schemas.py       Pydantic request/response models
├── monitoring/
│   └── health.py        Health checks, metrics
├── streams_listener.py  Redis Streams consumer (background)
├── examples/            API usage examples and test scripts
├── Dockerfile           Container definition
├── requirements.txt     Python dependencies
└── _legacy/             Pre-refactoring code
```

---

## API Endpoints

- `GET /health` — Liveness/health endpoint
- `GET /health/rag` — Full component + coherence health report
- `POST /coherence` — Analyze drift between PostgreSQL and Qdrant
- `POST /sync` — Generate synchronization plan
- `GET /` — Service metadata and endpoint listing

---

## Configuration

Environment variables (set in `config.py`):

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=vitruvyan
QDRANT_HOST=localhost:6333

# Redis (Cognitive Bus)
REDIS_HOST=localhost
REDIS_PORT=6379

# Service
MEMORY_ORDERS_PORT=8016
MEMORY_ORDERS_HOST=0.0.0.0
```

---

## Development

### Testing
```bash
pytest tests/
```

### Building
```bash
docker build -t api_memory_orders .
```

### Deployment
```bash
docker compose up -d --build api_memory_orders api_memory_orders_listener
```

---

## Related Components

- **Core**: `vitruvyan_core/core/governance/memory_orders/` — Pure domain logic
- **Bus**: Events published to `memory.coherence.*` channels
- **Dependencies**: PostgreSQL, Qdrant, Redis Streams
