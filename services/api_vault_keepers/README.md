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
response = requests.post("http://localhost:8001/integrity/check", json={
    "target": "postgresql",
    "scope": "full"
})
print(response.json())
# {"status": "blessed", "corruption_detected": false, "details": {...}}

# Create backup
response = requests.post("http://localhost:8001/backup/create", json={
    "type": "full",
    "systems": ["postgresql", "qdrant"]
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

### Integrity Monitoring
- `POST /integrity/check` — Validate data integrity across systems
- `GET /integrity/status` — Get current integrity status
- `GET /integrity/history` — Integrity check history

### Backup Operations
- `POST /backup/create` — Create new backup (full/incremental)
- `GET /backup/list` — List available backups
- `GET /backup/{id}/status` — Check backup status

### Recovery Operations
- `POST /recovery/plan` — Generate recovery plan
- `POST /recovery/execute` — Execute data recovery
- `GET /recovery/history` — Recovery operation history

### Audit Trail
- `GET /audit/events` — Immutable audit events
- `GET /audit/search` — Search audit trail
- `POST /audit/record` — Record custom audit event

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
VAULT_KEEPERS_PORT=8001
VAULT_KEEPERS_HOST=0.0.0.0

# Backup settings
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/data/backups
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
- **Dependencies**: PostgreSQL, Qdrant, Redis Streams, backup storage</content>
<parameter name="filePath">/home/vitruvyan/vitruvyan-core/services/api_vault_keepers/README.md