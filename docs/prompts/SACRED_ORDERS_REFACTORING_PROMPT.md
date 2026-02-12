# Sacred Orders Refactoring — Copilot Continuation Prompt

> **Use this prompt to give Copilot full context when continuing refactoring from the VPS.**
> Created: Feb 2026 | Repository: vitruvyan-core | Branch: main

---

## 🎯 MISSION

You are continuing the Sacred Orders refactoring of the `vitruvyan-core` repository.

**Two services are ALREADY DONE and serve as templates:**
- ✅ `api_orthodoxy_wardens` — complex service (119-line main.py, full domain pipeline)
- ✅ `api_conclave` — lightweight service (55-line main.py, observatory/bridge)

**Your job is to apply the SAME SERVICE_PATTERN to these 6 services, IN THIS ORDER:**
1. **Vault Keepers** (1027-line monolithic main.py → split to modules)
2. **MCP Server** (1040-line monolithic main.py → split to modules)
3. **Codex Hunters** (987-line monolithic main.py → split to modules)
4. **Pattern Weavers** (163-line monolithic main.py → split to modules)
5. **Memory Orders** (413-line monolithic main.py → split to modules)
6. **Babel Gardens** (832-line monolithic main.py → split to modules)

All these orders require a **listener in the Synaptic Conclave** (Redis Streams).

---

## 📁 REPOSITORY STRUCTURE

```
vitruvyan-core/
├── vitruvyan_core/
│   └── core/
│       ├── governance/                    # LIVELLO 1 — Pure domain
│       │   ├── SACRED_ORDER_PATTERN.md    # ← READ THIS (canonical L1 template)
│       │   ├── orthodoxy_wardens/         # ✅ DONE (template for complex orders)
│       │   │   ├── domain/               # frozen dataclasses
│       │   │   ├── consumers/            # pure process() roles
│       │   │   ├── governance/           # rules, classifier, verdict_engine
│       │   │   ├── events/               # channel constants
│       │   │   ├── monitoring/           # metric names (no prometheus_client)
│       │   │   ├── philosophy/           # charter.md
│       │   │   ├── _legacy/              # pre-refactoring artifacts
│       │   │   └── tests/               
│       │   ├── vault_keepers/             # ⏳ HAS 8 py files, needs consumers/ governance/ domain/
│       │   ├── codex_hunters/             # ⏳ HAS 13 py files, needs consumers/ governance/ domain/
│       │   ├── memory_orders/             # ⏳ HAS 4 py files, needs consumers/ governance/ domain/
│       │   └── semantic_sync/             # ⏳ 2 py files
│       ├── synaptic_conclave/             # Cognitive Bus (DO NOT MODIFY)
│       │   ├── transport/streams.py       # StreamBus — canonical transport
│       │   └── consumers/                 # ListenerAdapter, wrap_legacy_listener
│       └── agents/                        # PostgresAgent, QdrantAgent (shared)
│
├── services/                              # LIVELLO 2 — FastAPI services
│   ├── SERVICE_PATTERN.md                 # ← READ THIS (canonical L2 template)
│   ├── api_orthodoxy_wardens/             # ✅ DONE (template)
│   │   ├── main.py          (119 lines)
│   │   ├── config.py
│   │   ├── adapters/
│   │   │   ├── bus_adapter.py
│   │   │   └── persistence.py
│   │   ├── api/routes.py
│   │   ├── models/schemas.py
│   │   ├── monitoring/health.py
│   │   ├── core/            (service-specific logic)
│   │   └── streams_listener.py
│   ├── api_conclave/                      # ✅ DONE (lightweight template)
│   │   ├── main.py          (55 lines)
│   │   ├── config.py
│   │   ├── adapters/
│   │   │   ├── bus_adapter.py
│   │   │   └── persistence.py (stub)
│   │   ├── api/routes.py
│   │   ├── models/schemas.py
│   │   ├── monitoring/metrics.py
│   │   ├── _legacy/          (archived 691-line monolith)
│   │   └── streams_listener.py
│   ├── api_vault_keepers/                 # ❌ MONOLITHIC (1027-line main.py)
│   ├── api_mcp/                           # ❌ MONOLITHIC (1040-line main.py)
│   ├── api_codex_hunters/                 # ❌ MONOLITHIC (987-line main.py)
│   ├── api_pattern_weavers/               # ❌ MONOLITHIC (163-line main.py)
│   ├── api_memory_orders/                 # ❌ MONOLITHIC (413-line main.py)
│   └── api_babel_gardens/                 # ❌ MONOLITHIC (832-line main.py)
│
└── infrastructure/docker/
    ├── docker-compose.yml                 # 827 lines, all services defined
    └── dockerfiles/
        ├── Dockerfile.orthodoxy_wardens   # ✅ Template
        ├── Dockerfile.vault_keepers       # Exists, needs update
        ├── Dockerfile.api_codex_hunters
        ├── Dockerfile.api_babel_gardens
        ├── Dockerfile.api_memory_orders
        └── Dockerfile.api_weavers
```

---

## 🏗️ THE TWO-LEVEL ARCHITECTURE

### LIVELLO 1 — Foundational (`vitruvyan_core/core/governance/<order>/`)
**Pure Python. No I/O. No infrastructure. Testable in isolation.**

Must contain:
```
<order>/
├── domain/          # @dataclass(frozen=True) objects
├── consumers/       # Pure process() roles (SacredRole ABC)
├── governance/      # Rules, classifier, verdict engine
├── events/          # Channel constants, event envelope
├── monitoring/      # Metric NAME constants (no prometheus_client!)
├── philosophy/      # charter.md
├── _legacy/         # Pre-refactoring files (frozen, DO NOT MODIFY)
├── tests/
└── __init__.py
```

**Rules:**
- `@dataclass(frozen=True)` for ALL domain objects
- `process()` is PURE: no side effects, no I/O, no network
- Collections use `tuple`, not `list`
- NO infrastructure imports (no StreamBus, Redis, PostgreSQL)
- Direction: `service → core` (NEVER `core → service`)

### LIVELLO 2 — Service (`services/api_<order>/`)
**Infrastructure. Bus. Database. API. Docker.**

Must contain:
```
api_<order>/
├── main.py              # < 200 lines. Bootstrap + adapter only
├── config.py            # ALL env vars centralized (no scattered os.getenv)
├── adapters/
│   ├── bus_adapter.py   # StreamBus ↔ pure domain bridge
│   └── persistence.py   # ONLY I/O point (PostgresAgent, QdrantAgent)
├── api/routes.py        # HTTP endpoints (validate → delegate → return)
├── models/schemas.py    # Pydantic schemas
├── monitoring/          # Health, Prometheus
├── streams_listener.py  # Redis Streams entry point
├── redis_listener.py    # Legacy Pub/Sub listener (kept for wrap_legacy_listener)
└── _legacy/             # Archived monolithic main.py
```

**Rules:**
- main.py < 200 lines (ideally < 100)
- routes are THIN: validate → call adapter → return
- persistence.py is the ONLY file touching databases
- __init__.py exports needed for other files

---

## 🔧 REFACTORING PROCESS (Per Service)

### Step 1: READ the monolithic main.py
Identify:
- FastAPI app creation & endpoints → `api/routes.py`
- Pydantic models / request/response schemas → `models/schemas.py`
- Environment variables / config → `config.py`
- Database operations (PostgresAgent, QdrantAgent) → `adapters/persistence.py`
- StreamBus / event emission logic → `adapters/bus_adapter.py`
- Business logic classes → move to LIVELLO 1 `vitruvyan_core/core/governance/<order>/`
- Prometheus metrics → `monitoring/metrics.py` or `monitoring/health.py`
- Startup/shutdown logic → stays in `main.py` (slim)

### Step 2: CREATE the modular structure
```bash
cd services/api_<order>/
mkdir -p adapters api models monitoring _legacy
touch adapters/__init__.py api/__init__.py models/__init__.py monitoring/__init__.py _legacy/__init__.py
```

### Step 3: EXTRACT modules
1. `config.py` — all `os.getenv()` calls centralized
2. `models/schemas.py` — all Pydantic BaseModel classes
3. `adapters/persistence.py` — all PostgresAgent/QdrantAgent usage
4. `adapters/bus_adapter.py` — StreamBus bridge + domain pipeline
5. `api/routes.py` — all `@app.get/post/...` endpoints → use `APIRouter`
6. `monitoring/metrics.py` or `monitoring/health.py` — Prometheus + health

### Step 4: SLIM main.py
Target: < 100 lines. Only:
- `from fastapi import FastAPI`
- Import router, config, adapter
- Create app, include router
- `@app.on_event("startup")` → init adapter
- `@app.get("/health")` (or delegate to router)
- `if __name__ == "__main__": uvicorn.run(...)`

### Step 5: ARCHIVE old main.py
```bash
cp main.py _legacy/main_<order>.py
```

### Step 6: UPDATE streams_listener.py
If it already exists, verify it follows the pattern:
```python
from redis_listener import <LegacyListener>
from core.synaptic_conclave.consumers import wrap_legacy_listener

async def main():
    legacy_listener = <LegacyListener>()
    sacred_channels = ["<order>.*.requested", ...]
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="<order>_name",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"
    )
    await adapter.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 7: REBUILD & TEST
```bash
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker

# Rebuild the service
docker compose build <service_name>

# Start the API
docker compose up -d <service_name>

# Start the listener
docker compose up -d <service_name>_listener

# Test health
curl http://localhost:<port>/health

# Test listener (Redis PING)
docker exec <listener_container> redis-cli -h omni_redis PING

# Check logs
docker logs <container_name> --tail 50
docker logs <listener_container> --tail 50
```

### Step 8: GIT COMMIT
```bash
git add services/api_<order>/ vitruvyan_core/core/governance/<order>/
git commit -m "refactor(<order>): SERVICE_PATTERN alignment - FASE 1-5

- Extracted config.py, adapters/, api/routes.py, models/, monitoring/
- Slimmed main.py from <N> → <M> lines
- Archived old main.py to _legacy/
- Created LIVELLO 1 domain objects, consumers, governance [if applicable]
- Verified streams_listener.py and bus_adapter.py
- Docker rebuild + health check passed"
```

---

## ⚖️ GOLDEN TEMPLATES

### config.py Template
```python
"""<Order> — Service Configuration"""
import os

class Settings:
    SERVICE_NAME = "api_<order>"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "<default_port>"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Redis / Cognitive Bus
    REDIS_HOST = os.getenv("REDIS_HOST", "omni_redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "<order>_group")
    CONSUMER_NAME = os.getenv("CONSUMER_NAME", "<order>_worker_1")

    # Sacred Channels
    SACRED_CHANNELS = [
        "<order>.<domain>.<action>",
        # ...
    ]

    # PostgreSQL (host machine)
    PG_HOST = os.getenv("PG_HOST", "161.97.140.157")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "vitruvyan")
    PG_USER = os.getenv("PG_USER", "vitruvyan_user")

settings = Settings()
```

### main.py Template (Target < 100 lines)
```python
"""<Order> — Sacred Order API (LIVELLO 2 Entry Point)

Thin FastAPI shell. All logic delegated to:
  - api/routes.py            HTTP endpoints
  - adapters/bus_adapter.py  Domain pipeline bridge
  - adapters/persistence.py  Database I/O
  - monitoring/              Health + metrics
"""
import logging, sys
from fastapi import FastAPI

sys.path.append("/app")

from api_<order>.api.routes import router
from api_<order>.config import settings
from api_<order>.adapters.bus_adapter import <Order>BusAdapter

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger("<Order>")

app = FastAPI(title="<Order>", version="2.0.0")
app.include_router(router)

bus_adapter = None

@app.on_event("startup")
async def startup():
    global bus_adapter
    logger.info("Initializing <Order>")
    bus_adapter = <Order>BusAdapter()
    logger.info("<Order> ready")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT, log_level="info")
```

### adapters/bus_adapter.py Template
```python
"""<Order> — Bus Adapter (LIVELLO 2)

Bridges HTTP/Streams to pure domain consumers (LIVELLO 1).
"""
from core.synaptic_conclave.transport.streams import StreamBus
from api_<order>.config import settings

class <Order>BusAdapter:
    def __init__(self):
        self.bus = StreamBus(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    def emit(self, channel: str, data: dict, emitter: str = "<order>.api"):
        return self.bus.emit(channel=channel, payload=data, emitter=emitter)

    def handle_event(self, event: dict) -> dict:
        # Domain pipeline: call LIVELLO 1 consumers
        # Return result dict
        ...
```

### streams_listener.py Template
```python
#!/usr/bin/env python3
"""<Order> - Redis Streams Listener

Pattern: wrap_legacy_listener (zero-code-change migration)
"""
import asyncio, logging, sys

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/api_<order>')

from redis_listener import <LegacyListenerClass>
from core.synaptic_conclave.consumers import wrap_legacy_listener

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("<Order>StreamsWrapper")

async def main():
    legacy_listener = <LegacyListenerClass>()
    sacred_channels = [
        "<order>.<domain>.<action>",
        # ...
    ]
    adapter = wrap_legacy_listener(
        listener_instance=legacy_listener,
        name="<order>_listener",
        sacred_channels=sacred_channels,
        handler_method="handle_sacred_message"
    )
    await adapter.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("<Order> Listener stopped")
```

---

## ⚠️ CRITICAL GOTCHAS (Lessons Learned)

### 1. Stream Prefix Convention
StreamBus.emit() automatically adds `vitruvyan:` prefix to channel names.
- Channel `vault.archive.completed` becomes Redis key `vitruvyan:vault.archive.completed`
- ListenerAdapter consumes from the SAME prefixed key
- **DO NOT add `stream:` prefix** — this was a critical bug we fixed (commit 6bdcf83)

### 2. ThreadPool Sizing
ListenerAdapter uses a ThreadPoolExecutor. Default is 12 workers.
If a listener subscribes to >12 channels, it will hang.
- **FIX**: `ThreadPoolExecutor(max(len(channels) + 4, 16))`
- Already fixed in listener_adapter.py (commit 6bdcf83)

### 3. Prometheus Double Registration
If two modules try to register the same metric name, Prometheus throws.
- **Pattern**: Use `_safe_*` wrappers that catch `ValueError` on duplicate registration
- Or use `multiprocess_mode` / check if metric exists before creating

### 4. Listener Healthcheck
Listeners have NO web server → Dockerfile HEALTHCHECK with `curl` fails.
- **Runtime override**: `--health-cmd "redis-cli -h omni_redis PING"` or
- **Better**: Add `HEALTHCHECK` to docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "-h", "omni_redis", "PING"]
  interval: 30s
  timeout: 5s
  retries: 3
```

### 5. Dual Import Namespace
Dockerfile.orthodoxy_wardens copies `vitruvyan_core/` to `/app/vitruvyan_core/` AND creates symlink `/app/core → /app/vitruvyan_core/core`. This allows both:
- `from core.agents.postgres_agent import PostgresAgent` (legacy)
- `from vitruvyan_core.core.governance.orthodoxy_wardens.consumers import Confessor` (new)

**Vault Keepers Dockerfile uses different pattern**: copies `vitruvyan_core/core/` directly to `/app/core/`. Consider aligning to the orthodoxy pattern (copy vitruvyan_core + symlink).

### 6. sys.path in streams_listener.py
```python
sys.path.insert(0, '/app/api_<order>')  # Local package imports
sys.path.insert(0, '/app')               # Global core/ imports
```
**CRITICAL**: `/app` MUST be first in path so global `core/` (symlink) takes priority over local `api_<order>/core/` package (if the service has a core/ subdirectory).

### 7. PostgreSQL is on HOST MACHINE
- Host: `161.97.140.157:5432` (NOT in Docker, NOT `omni_postgres` for production data)
- `omni_postgres` is the vitruvyan-core local PostgreSQL (different from production)
- Always use `PostgresAgent()` from `core/agents/postgres_agent.py`
- NEVER use direct `psycopg2.connect()`

---

## 📋 PER-SERVICE NOTES

### 1. Vault Keepers (P1 — FIRST)
- **Current state**: `services/api_vault_keepers/` has only: `__init__.py`, `main.py` (1027 lines), `redis_listener.py`, `streams_listener.py`
- **LIVELLO 1** (`vitruvyan_core/core/governance/vault_keepers/`): Has 8 py files: archivist.py, chamberlain.py, courier.py, gdrive_uploader.py, keeper.py, sentinel.py + scripts/ + tests/
- **LIVELLO 1 gaps**: No `consumers/`, `governance/`, `domain/`, `events/`, `monitoring/`, `philosophy/` directories
- **main.py contains**: VaultGuardian, VaultArchivist, VaultSentinel, VaultChamberlain classes + FastAPI endpoints + Prometheus metrics + PostgresAgent/QdrantAgent calls + StreamBus event handling
- **Port**: 8007 (external 9007)
- **Sacred Channels**: `vault.archive.completed`, `vault.retrieval.requested`, `vault.snapshot.created`
- **Docker**: `Dockerfile.vault_keepers` exists, copies `vitruvyan_core/core/` to `/app/core/`
- **Listener**: `streams_listener.py` exists but needs verification after SERVICE_PATTERN split

### 2. MCP Server (P1)
- **Current state**: `services/api_mcp/` has only: `Dockerfile`, `README.md`, `main.py` (1040 lines), `requirements.txt`
- **LIVELLO 1**: NO governance module exists (MCP is infrastructure, not a Sacred Order per se)
- **Decision needed**: MCP may not need full LIVELLO 1 domain objects. Focus on LIVELLO 2 split only
- **main.py contains**: 6 MCP tools, Sacred Orders middleware, PostgreSQL vault, Prometheus metrics, FastAPI endpoints
- **Note**: MCP is NOT in `vitruvyan_core/core/governance/` — it lives only at LIVELLO 2

### 3. Codex Hunters (P2)
- **Current state**: `services/api_codex_hunters/` has: `__init__.py`, `main.py` (987 lines), `streams_listener.py`, `README.md`
- **LIVELLO 1** (`vitruvyan_core/core/governance/codex_hunters/`): Has 13 py files: base_hunter.py, binder.py, cartographer.py, conclave_cycle.py, event_hunter.py, expedition_leader.py, expedition_planner.py, hunter.py, inspector.py, restorer.py, scribe.py, tracker.py
- **LIVELLO 1 gaps**: No `consumers/`, `governance/`, `domain/`, `events/` directories
- **Sacred Channels**: `codex.discovery.mapped`, `codex.reddit.scraped`, `codex.news.collected`, `codex.refresh.scheduled`

### 4. Pattern Weavers (P3)
- **Current state**: `services/api_pattern_weavers/` has only: `Dockerfile`, `main.py` (163 lines), `requirements.txt`, `start.sh`
- **LIVELLO 1**: NOT in `vitruvyan_core/core/governance/` (no module exists yet)
- **Small service**: 163 lines may only need light splitting (config + routes extraction)
- **Sacred Channels**: `pattern_weavers.context.extracted`, `pattern_weavers.weave.completed`

### 5. Memory Orders (P3)
- **Current state**: `services/api_memory_orders/` has only: `__init__.py`, `main.py` (413 lines)
- **LIVELLO 1** (`vitruvyan_core/core/governance/memory_orders/`): Has 4 py files: coherence.py, phrase_sync.py, rag_health.py + scripts/ + tests/
- **LIVELLO 1 gaps**: No `consumers/`, `governance/`, `domain/`, `events/` directories
- **Note**: No `streams_listener.py` yet — needs to be created
- **Sacred Channels**: `memory.write.completed`, `memory.sync.requested`, `memory.coherence.checked`

### 6. Babel Gardens (P2)
- **Current state**: `services/api_babel_gardens/` has: `Dockerfile`, `README.md`, `__init__.py`, `main.py` (832 lines), `modules/`, `schemas/`, `shared/`, `streams_listener.py`
- **LIVELLO 1**: NOT in `vitruvyan_core/core/governance/` — Babel is discourse layer, not governance
- **Note**: Already has some modular structure (`modules/`, `schemas/`, `shared/`) — align to SERVICE_PATTERN naming
- **Sacred Channels**: `babel.sentiment.completed`, `babel.fusion.completed`, `babel.emotion.detected`, `babel.translation.completed`

---

## 🐳 DOCKER PATTERN

### Dockerfile Template (based on Orthodoxy Wardens)
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 vitruvyan && \
    useradd -u 1000 -g vitruvyan -m -s /bin/bash vitruvyan && \
    mkdir -p /app && chown vitruvyan:vitruvyan /app

WORKDIR /app
USER vitruvyan

COPY --chown=vitruvyan:vitruvyan infrastructure/docker/requirements/requirements.<order>.txt ./requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Service code
COPY --chown=vitruvyan:vitruvyan services/api_<order>/ /app/api_<order>/

# Core modules (preserving namespace)
COPY --chown=vitruvyan:vitruvyan vitruvyan_core/ /app/vitruvyan_core/
# Backward compat symlink
RUN ln -s /app/vitruvyan_core/core /app/core

ENV PYTHONPATH=/app
ENV PATH="/home/vitruvyan/.local/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:<port>/health || exit 1

EXPOSE <port>

CMD ["python", "-m", "uvicorn", "api_<order>.main:app", "--host", "0.0.0.0", "--port", "<port>"]
```

### docker-compose.yml Listener Pattern
```yaml
api_<order>_listener:
  build:
    context: ../..
    dockerfile: infrastructure/docker/dockerfiles/Dockerfile.<order>
  container_name: omni_<order>_listener
  restart: unless-stopped
  environment:
    - REDIS_HOST=omni_redis
    - REDIS_PORT=6379
    - <ORDER>_LISTENER_ENABLED=1
  networks:
    - omni-net
  depends_on:
    - redis
    - <api_service>
  command: ["python3", "/app/api_<order>/streams_listener.py"]
  healthcheck:
    test: ["CMD", "redis-cli", "-h", "omni_redis", "PING"]
    interval: 30s
    timeout: 5s
    retries: 3
```

---

## ✅ VERIFICATION CHECKLIST (After Each Service)

```bash
# 1. main.py line count (target < 200)
wc -l services/api_<order>/main.py

# 2. Directory structure
ls -la services/api_<order>/adapters/ services/api_<order>/api/ services/api_<order>/models/ services/api_<order>/monitoring/

# 3. config.py exists with centralized env vars
grep "os.getenv" services/api_<order>/config.py

# 4. No scattered os.getenv in other files
grep -rn "os.getenv" services/api_<order>/ --include="*.py" | grep -v config.py | grep -v _legacy/

# 5. Docker build
cd infrastructure/docker
docker compose build <service>

# 6. Start service + listener
docker compose up -d <service> <service>_listener

# 7. Health check
curl http://localhost:<port>/health

# 8. Listener logs
docker logs omni_<order>_listener --tail 30

# 9. Redis consumer groups created
docker exec omni_redis redis-cli KEYS "vitruvyan:*<order>*"
```

---

## 📚 REFERENCE FILES (Read in this order)

1. `services/SERVICE_PATTERN.md` (257 lines) — LIVELLO 2 canonical template
2. `vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md` (302 lines) — LIVELLO 1 canonical template
3. `SACRED_ORDERS_REFACTORING_PLAN.md` (484 lines) — Overall roadmap + per-service checklists
4. `services/api_orthodoxy_wardens/` — ✅ Complete complex service template
5. `services/api_conclave/` — ✅ Complete lightweight service template

---

## 🚨 DO NOT

- ❌ Modify `vitruvyan_core/core/synaptic_conclave/` (Cognitive Bus is DONE)
- ❌ Modify `services/api_orthodoxy_wardens/` or `services/api_conclave/` (templates, frozen)
- ❌ Use direct `psycopg2.connect()` — always `PostgresAgent()`
- ❌ Use direct `qdrant_client.QdrantClient()` — always `QdrantAgent()`
- ❌ Add `stream:` prefix to channels (StreamBus handles `vitruvyan:` prefix)
- ❌ Put business logic in main.py (delegate to adapters/ and LIVELLO 1)
- ❌ Put database calls anywhere except `adapters/persistence.py`
- ❌ Scatter `os.getenv()` — centralize ALL in config.py
- ❌ Delete legacy files — archive to `_legacy/` with timestamp
- ❌ Import from service into core (direction: service → core, NEVER reverse)

---

*Generated from working session Feb 2026. Orthodoxy Wardens + Conclave confirmed aligned.*
*Main branch at commit 6a25343 (pushed).*
