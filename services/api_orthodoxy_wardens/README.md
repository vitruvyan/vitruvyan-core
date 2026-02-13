# API Orthodoxy Wardens

> **Last updated**: February 13, 2026

> **Epistemic Tribunal Service — LIVELLO 2 Infrastructure Layer**

REST API service for compliance evaluation, truth validation, and decision rendering. The epistemic judge that examines outputs and renders verdicts without executing corrections.

## Sacred Order

**Domain**: Truth & Governance  
**Mandate**: Classify inputs, evaluate outputs, render verdicts, admit uncertainty  
**Layer**: LIVELLO 2 (Service — Infrastructure, API, Docker)

---

## Quick Start

### Local Development
```bash
cd services/api_orthodoxy_wardens
pip install -r requirements.txt
python main.py
```

### Docker
```bash
cd infrastructure/docker
docker compose up -d api_orthodoxy_wardens
```

### API Usage
```python
import requests

# Evaluate output compliance
response = requests.post("http://localhost:8002/judge/evaluate", json={
    "input_text": "What is Apple's market cap?",
    "output_text": "Apple's market cap is approximately $3.2 trillion",
    "ruleset_version": "1.0"
})
print(response.json())
# {"verdict": "blessed", "confidence": 0.95, "evidence": [...]}

# Get verdict history
response = requests.get("http://localhost:8002/judge/history")
print(response.json())
```

---

## Architecture

### Two-Level Pattern

| Level | Location | Purpose | Dependencies |
|-------|----------|---------|--------------|
| **LIVELLO 1** | `vitruvyan_core/core/governance/orthodoxy_wardens/` | Pure domain logic | None (stdlib only) |
| **LIVELLO 2** | `services/api_orthodoxy_wardens/` | Infrastructure, API, Docker | PostgreSQL, Qdrant, Redis |

**Direction: service → core** (ONE-WAY). LIVELLO 2 imports LIVELLO 1, never reverse.

### Service Components

```
api_orthodoxy_wardens/
├── main.py              FastAPI bootstrap (< 100 lines)
├── config.py            Environment variables, settings
├── adapters/
│   ├── bus_adapter.py   Orchestrates LIVELLO 1 + StreamBus events
│   ├── persistence.py   I/O layer (PostgresAgent, QdrantAgent)
│   ├── roles.py         SacredRole implementations (promoted from _legacy/core)
│   ├── workflows.py     Workflow orchestration (promoted from _legacy/core)
│   ├── event_handlers.py  Event handling logic (promoted from _legacy/core)
│   └── orthodoxy_db_manager.py  DB operations (promoted from _legacy/core)
├── api/
│   └── routes.py        HTTP endpoints (validate → delegate → return)
├── models/
│   └── schemas.py       Pydantic request/response models
├── monitoring/
│   └── health.py        Health checks, metrics
├── streams_listener.py  Redis Streams consumer (background)
├── examples/            API usage examples and test scripts
├── Dockerfile           Container definition
└── requirements.txt     Python dependencies
```

> **Feb 13, 2026**: `_legacy/` directory deleted. 4 load-bearing runtime files
> (roles, workflows, event_handlers, orthodoxy_db_manager) promoted from
> `_legacy/core/` to `adapters/`. All import paths in main.py, api/routes.py,
> and monitoring/health.py updated accordingly.

---

## API Endpoints

### Judgment Operations
- `POST /judge/evaluate` — Evaluate output against compliance rules
- `POST /judge/classify` — Classify input by category and severity
- `GET /judge/history` — Get verdict history

### Rules Management
- `GET /rules/versions` — List available ruleset versions
- `GET /rules/{version}` — Get specific ruleset
- `POST /rules/validate` — Validate ruleset syntax

### Evidence & Audit
- `GET /evidence/{verdict_id}` — Get evidence chain for verdict
- `GET /audit/verdicts` — Audit trail of all verdicts
- `POST /audit/search` — Search verdict history

### Tribunal Operations
- `POST /tribunal/confess` — Submit confession for judgment
- `GET /tribunal/queue` — Get pending judgments
- `POST /tribunal/batch` — Process batch of confessions

---

## Verdict Types

| Verdict | Meaning | Action |
|---------|---------|--------|
| `blessed` | Output valid | Send to user |
| `purified` | Output corrected | Send corrected version |
| `heretical` | Output rejected | Block delivery |
| `non_liquet` | Insufficient confidence | Send with uncertainty |
| `clarification_needed` | Input ambiguous | Ask user to rephrase |

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
ORTHODOXY_WARDENS_PORT=8002
ORTHODOXY_WARDENS_HOST=0.0.0.0

# Judgment settings
DEFAULT_RULESET_VERSION=1.0
CONFIDENCE_THRESHOLD=0.7
```

---

## Development

### Testing
```bash
pytest tests/
```

### Building
```bash
docker build -t api_orthodoxy_wardens .
```

### Deployment
```bash
docker compose up -d --build api_orthodoxy_wardens api_orthodoxy_wardens_listener
```

---

## Related Components

- **Core**: `vitruvyan_core/core/governance/orthodoxy_wardens/` — Pure domain logic
- **Bus**: Events published to `orthodoxy.*` channels
- **Dependencies**: PostgreSQL, Qdrant, Redis Streams</content>
<parameter name="filePath">/home/vitruvyan/vitruvyan-core/services/api_orthodoxy_wardens/README.md