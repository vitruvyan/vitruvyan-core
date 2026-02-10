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
response = requests.post("http://localhost:8000/coherence/check", json={
    "pg_count": 1000,
    "qdrant_count": 980
})
print(response.json())
# {"status": "healthy", "drift_percentage": 2.0, "recommendation": "incremental_sync"}

# Get health status
response = requests.get("http://localhost:8000/health")
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

### Coherence Analysis
- `POST /coherence/check` — Analyze drift between PostgreSQL and Qdrant
- `GET /coherence/history` — Get coherence check history

### Health Monitoring
- `GET /health` — Overall service health
- `GET /health/components` — Individual component health status

### Synchronization
- `POST /sync/plan` — Generate synchronization plan
- `POST /sync/execute` — Execute planned synchronization

### Events
- `GET /events/recent` — Recent coherence events
- `POST /events/publish` — Publish custom coherence event

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
MEMORY_ORDERS_PORT=8000
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
- **Dependencies**: PostgreSQL, Qdrant, Redis Streams</content>
<parameter name="filePath">/home/vitruvyan/vitruvyan-core/services/api_memory_orders/README.md