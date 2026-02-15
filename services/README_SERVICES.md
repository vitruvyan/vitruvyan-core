# services/ — Microservices Layer (LIVELLO 2)

> **Last Updated**: February 12, 2026  
> **Purpose**: Docker-based REST APIs wrapping vitruvyan_core components  
> **Type**: LIVELLO 2 (I/O, orchestration, HTTP endpoints)

---

## 🎯 Cosa Contiene

`services/` contiene i **microservizi** che espongono la core library via REST API. Ogni service è un thin wrapper Docker che:
- Importa moduli da `vitruvyan_core/`
- Fornisce API HTTP (FastAPI)
- Gestisce I/O (PostgreSQL, Redis, Qdrant, file system)
- Implementa adapters per orchestrare LIVELLO 1

**Caratteristiche**:
- ✅ **Stateless**: Ogni service è indipendente
- ✅ **Dockerized**: Deploy via `docker compose`
- ✅ **Event-Driven**: Comunicazione via Redis Streams (StreamBus)
- ✅ **Thin Wrappers**: Business logic in `vitruvyan_core/`, solo I/O qui

---

## 📂 Struttura

```
services/
├── api_babel_gardens/          # Linguistic analysis service
│   ├── main.py                 → FastAPI app (< 100 lines)
│   ├── config.py               → Environment variables
│   ├── adapters/               → Bus + persistence orchestration
│   ├── api/                    → HTTP routes
│   ├── Dockerfile
│   └── docs/                   → Service-specific docs
│
├── api_codex_hunters/          # Data discovery & mapping service
│   ├── main.py
│   ├── adapters/
│   └── docs/
│
├── api_graph/                  # LangGraph orchestration API
│   ├── main.py
│   ├── adapters/
│   └── docs/
│
├── api_mcp/                    # Model Context Protocol gateway
│   ├── main.py                 → MCP server (OpenAI Function Calling)
│   ├── adapters/
│   └── docs/                   → MCP refactoring, audit
│
├── api_memory_orders/          # Memory & coherence service
│   ├── main.py
│   ├── adapters/
│   │   ├── bus_adapter.py      → Orchestrates LIVELLO 1 consumers
│   │   └── persistence.py      → PostgresAgent, QdrantAgent
│   └── docs/
│
├── api_neural/                 # Neural engine API
│   ├── main.py
│   └── docs/
│
├── api_orthodoxy_wardens/      # Governance & validation service
│   ├── main.py
│   ├── adapters/
│   └── docs/
│
├── api_pattern_weavers/        # Pattern analysis service
│   ├── main.py
│   ├── adapters/
│   └── docs/
│
└── api_vault_keepers/          # Archival & persistence service
    ├── main.py
    ├── adapters/
    │   ├── bus_adapter.py
    │   └── persistence.py
    └── docs/
```

---

## 🏗️ Service Pattern (LIVELLO 2 Standard)

Ogni service segue il **SACRED_ORDER_PATTERN** (LIVELLO 2):

### Required Structure

```
services/api_<name>/
├── main.py              # < 100 lines (FastAPI bootstrap ONLY)
├── config.py            # ALL os.getenv() centralized
├── adapters/
│   ├── bus_adapter.py   # Orchestrates LIVELLO 1 consumers + StreamBus
│   └── persistence.py   # ONLY I/O point (PostgresAgent, QdrantAgent)
├── api/
│   └── routes.py        # Thin HTTP endpoints (validate → delegate → return)
├── models/
│   └── schemas.py       # Pydantic request/response models
├── monitoring/
│   └── health.py        # Health checks, Prometheus metrics
├── streams_listener.py  # Redis Streams consumer (background process)
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
└── docs/                # Service-specific documentation
```

### main.py Target: < 100 Lines

**Regole**:
- Max 100 righe (87 Orthodoxy, 59 Vault, 93 Memory)
- Istanzia solo FastAPI app + global connectors
- Delega routing a `api/routes.py`
- Delega I/O a `adapters/`

**Esempio**:
```python
# main.py (< 100 lines)
from fastapi import FastAPI
from .config import SERVICE_NAME, PORT
from .api.routes import router

app = FastAPI(title=SERVICE_NAME)
app.include_router(router)

# Global adapters (initialized once)
from .adapters.bus_adapter import BusOrchestrator
from .adapters.persistence import PersistenceLayer

bus = BusOrchestrator()
db = PersistenceLayer()
```

---

## 🔌 Sacred Orders Services (6/9)

| Service | Sacred Order | Port | LIVELLO 1 | Status |
|---------|--------------|------|-----------|--------|
| **api_memory_orders** | Memory Orders | 9008 | `core/governance/memory_orders/` | ✅ 100% |
| **api_vault_keepers** | Vault Keepers | 9007 | `core/governance/vault_keepers/` | ✅ 100% |
| **api_orthodoxy_wardens** | Orthodoxy Wardens | 9006 | `core/governance/orthodoxy_wardens/` | ✅ 100% |
| **api_codex_hunters** | Codex Hunters | 9005 | `core/governance/codex_hunters/` | ✅ 100% |
| **api_babel_gardens** | Babel Gardens | 9009 | `core/cognitive/babel_gardens/` | ✅ 100% |
| **api_pattern_weavers** | Pattern Weavers | 9011 | `core/cognitive/pattern_weavers/` | ✅ 100% |

---

## 🌐 Other Services (3/9)

| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| **api_graph** | LangGraph orchestration | 9004 | ✅ Operational |
| **api_neural** | Neural engine API | 9003 | ✅ Operational |
| **api_mcp** | Model Context Protocol gateway | 8020 | ✅ Production (domain-agnostic) |

---

## 🚀 Deploy & Usage

### Docker Compose

```bash
cd infrastructure/docker
docker compose up -d --build <service_name>
```

**Esempi**:
```bash
# Deploy Memory Orders + listener
docker compose up -d --build memory_orders memory_orders_listener

# Deploy Vault Keepers
docker compose up -d --build vault_keepers vault_keepers_listener

# Deploy MCP Gateway
docker compose up -d --build mcp
```

### Health Check

```bash
# Check service health
curl http://localhost:<PORT>/health

# Examples
curl http://localhost:9008/health  # Memory Orders
curl http://localhost:9007/health  # Vault Keepers
curl http://localhost:8020/health  # MCP Gateway
```

### API Documentation

Ogni service espone Swagger UI:
```
http://localhost:<PORT>/docs
```

---

## 📡 Event-Driven Communication

Services comunicano via **Redis Streams** (StreamBus):

### Publisher Example

```python
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.publish("vault.archive.requested", {
    "entity_id": "entity_1",
    "snapshot_data": {...}
})
```

### Consumer Example (streams_listener.py)

```python
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus
from .adapters.bus_adapter import BusOrchestrator

bus = StreamBus()
orchestrator = BusOrchestrator()

# Create consumer group
bus.create_consumer_group("vault.archive.requested", "vault_keepers")

# Consume events
for event in bus.consume("vault.archive.requested", "vault_keepers", "vault_1"):
    orchestrator.handle_archive_request(event.payload)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)
```

---

## 📚 Documentazione

Ogni service ha `docs/` subdirectory (locality-first):

- **api_mcp/docs/** — MCP server refactoring, audit, constitutional compliance
- **api_orthodoxy_wardens/docs/** — Orthodoxy service docs, Grafana dashboard fixes
- **Altro** — Vedere cartelle individuali

**Global services docs**: [../docs/services/](../docs/services/)

---

## 🎯 Design Principles

1. **Thin Wrappers**: Business logic in `vitruvyan_core/`, solo I/O/HTTP qui
2. **main.py < 100 Lines**: Bootstrap minimale, delega a adapters/api
3. **Adapters Pattern**: `bus_adapter.py` orchestra LIVELLO 1, `persistence.py` gestisce I/O
4. **Event-Driven**: StreamBus per comunicazione inter-service
5. **Stateless**: Ogni service indipendente, scalabile orizzontalmente

---

## 📖 Link Utili

- **[Vitruvyan Core](../vitruvyan_core/README_VITRUVYAN_CORE.md)** — Core library che questi servizi wrappano
- **[Infrastructure](../infrastructure/README_INFRASTRUCTURE.md)** — Docker Compose, Grafana, Prometheus
- **[Docs Portal](../docs/index.md)** — Entry point documentazione
- **[SACRED_ORDER_PATTERN](../vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md)** — Pattern tecnico completo

---

**Purpose**: Esporre vitruvyan_core via REST API, gestire I/O e orchestrazione.  
**Pattern**: LIVELLO 2 (thin wrappers, adapters, event-driven).  
**Status**: 9 services operativi, 6/9 Sacred Orders al 100% conformance.
