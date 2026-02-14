# API Vault Keepers

> **Memory Custodians Service — LIVELLO 2 Infrastructure Layer**

REST API service for data integrity, backup, recovery, and audit operations. Guards the sanctity of stored knowledge across PostgreSQL and Qdrant systems.

## Sacred Order

**Domain**: Truth (Memory & Archival)  
**Mandate**: Integrity monitoring, backup/recovery, immutable audit trails  
**Layer**: LIVELLO 2 (Service — Infrastructure, API, Docker)

---

## Quick Start

### Local Development
```bash
cd services/api_vault_keepers
pip install -r requirements.txt
python main.py
```

### Docker
```bash
cd infrastructure/docker
docker compose up -d api_vault_keepers
```

### API Usage
```python
import requests

# Check data integrity
response = requests.post("http://localhost:8007/vault/integrity_check", json={
    "scope": "full",
    "correlation_id": "manual_check_001"
})
print(response.json())
# {"overall_status": "...", "findings": [...], ...}

# Create backup
response = requests.post("http://localhost:8007/vault/backup", json={
    "mode": "full",
    "include_vectors": True
})
print(response.json())
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/vault_keepers/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_vault_keepers/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

### Service Components

```
api_vault_keepers/
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

All endpoints are under `/vault`.

- `GET /vault/health` — Service and dependency health
- `GET /vault/status` — Comprehensive vault status
- `POST /vault/integrity_check` — Validate cross-store integrity
- `POST /vault/backup` — Execute backup workflow
- `POST /vault/restore` — Dry-run or execute restore workflow
- `POST /vault/archive` — Archive external content payload

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
SERVICE_PORT=8007
SERVICE_HOST=0.0.0.0

# Backup settings
BACKUP_RETENTION_DAYS=30
```

---

## Development

### Testing
```bash
pytest tests/
```

### Building
```bash
docker build -t api_vault_keepers .
```

### Deployment
```bash
docker compose up -d --build api_vault_keepers api_vault_keepers_listener
```

---

## Related Components

- **Core**: `vitruvyan_core/core/governance/vault_keepers/` — Pure domain logic
- **Bus**: Events published to `vault.*` channels
- **Dependencies**: PostgreSQL, Qdrant, Redis Streams, backup storage
