# SERVICE_PATTERN.md — Canonical Service Template (LIVELLO 2)

> **"Il giudice (core) non tocca mai il database. Il cancelliere (service) lo fa per lui."**

This document defines the replicable structure for every Sacred Order service.
All services under `services/api_<order>/` MUST follow this pattern.

---

## Directory Structure

```
services/api_<order>/
├── main.py                  # FastAPI app (< 50 lines)
├── config.py                # All env vars, centralized
├── routes/
│   ├── __init__.py
│   └── audit.py             # HTTP endpoints (validation + delegation)
├── adapters/
│   ├── __init__.py
│   ├── bus_adapter.py       # StreamBus ↔ pure consumer bridge
│   └── persistence.py       # ONLY I/O point (PostgresAgent, QdrantAgent)
├── streams_listener.py      # Redis Streams entry point
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Principles

### 1. main.py < 50 lines
Creates FastAPI app, includes router, defines lifespan (startup/shutdown).
NO business logic. NO imports from `core.agents.*` directly.

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .routes import router
from .adapters.bus_adapter import OrderBusAdapter

adapter = OrderBusAdapter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    adapter.start()
    yield
    adapter.stop()

app = FastAPI(title=settings.SERVICE_NAME, lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}
```

### 2. config.py — Single Source of Environment
All env vars declared once. No `os.getenv()` scattered across files.

```python
import os

class Settings:
    SERVICE_NAME = "api_orthodoxy_wardens"
    REDIS_URL = os.getenv("REDIS_URL", "redis://vitruvyan_redis_master:6379")
    PG_HOST = os.getenv("PG_HOST", "161.97.140.157")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "vitruvyan")
    PG_USER = os.getenv("PG_USER", "vitruvyan_user")
    CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "orthodoxy_wardens")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
```

### 3. routes/ — Validation + Delegation
HTTP endpoints validate input (Pydantic), delegate to core consumers, persist via adapters.
Routes are THIN: validate → call adapter → return response.

```python
from fastapi import APIRouter, HTTPException
from ..adapters.bus_adapter import OrderBusAdapter
from ..adapters.persistence import PersistenceAdapter

router = APIRouter(prefix="/v1")

@router.post("/audit")
async def initiate_audit(request: AuditRequest):
    adapter = OrderBusAdapter()
    result = adapter.handle_audit(request.dict())
    return result
```

### 4. adapters/bus_adapter.py — The Bridge
Bridges infrastructure (StreamBus events, HTTP requests) to pure domain consumers.
This is where the pipeline lives: Confessor → Inquisitor → VerdictEngine → Penitent → Chronicler.

```python
from vitruvyan_core.core.governance.orthodoxy_wardens.consumers.confessor import Confessor
from vitruvyan_core.core.governance.orthodoxy_wardens.consumers.inquisitor import Inquisitor
from vitruvyan_core.core.governance.orthodoxy_wardens.consumers.penitent import Penitent
from vitruvyan_core.core.governance.orthodoxy_wardens.consumers.chronicler import Chronicler
from vitruvyan_core.core.governance.orthodoxy_wardens.governance.verdict_engine import VerdictEngine
from vitruvyan_core.core.governance.orthodoxy_wardens.governance.rule import DEFAULT_RULESET

class OrderBusAdapter:
    """Bridges infrastructure to pure domain consumers."""

    def __init__(self):
        self.confessor = Confessor()
        self.inquisitor = Inquisitor()
        self.verdict_engine = VerdictEngine()
        self.penitent = Penitent()
        self.chronicler = Chronicler()
        self.ruleset = DEFAULT_RULESET

    def handle_event(self, event: dict) -> dict:
        # 1. Intake: event → Confession
        confession = self.confessor.process(event)

        # 2. Examine: confession → findings
        result = self.inquisitor.process({
            "confession": confession,
            "text": event.get("text", ""),
            "code": event.get("code", "")
        })

        # 3. Judge: findings → verdict
        verdict = self.verdict_engine.render(
            findings=result.findings,
            ruleset=self.ruleset,
            confession_id=confession.confession_id
        )

        # 4. Correct: verdict → correction plan
        plan = self.penitent.process(verdict)

        # 5. Archive: verdict → chronicle decision
        chronicle = self.chronicler.process(verdict)

        return {
            "confession_id": confession.confession_id,
            "verdict": verdict.to_dict(),
            "correction_plan": plan,
            "chronicle": chronicle
        }
```

### 5. adapters/persistence.py — ONLY I/O Point
The ONLY file that touches databases. All other code is pure.

```python
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent

class PersistenceAdapter:
    """Single I/O point for the service. Core never imports this."""

    def __init__(self):
        self.pg = PostgresAgent()
        self.qdrant = QdrantAgent()

    def save_verdict(self, verdict: dict, confession_id: str):
        self.pg.execute(
            "INSERT INTO audit_findings (...) VALUES (%s, ...)",
            (confession_id, verdict["status"], ...)
        )
        self.pg.connection.commit()

    def save_chronicle(self, chronicle: dict):
        # Archive to appropriate destination
        ...

    def get_recent_findings(self, limit: int = 50) -> list:
        return self.pg.fetch(
            "SELECT * FROM audit_findings ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
```

### 6. streams_listener.py — Bus Entry Point
Consumes Redis Streams, delegates to bus_adapter. Handles graceful shutdown.

```python
import asyncio
import signal
from .config import settings
from .adapters.bus_adapter import OrderBusAdapter
from core.synaptic_conclave.transport.streams import StreamBus

async def main():
    bus = StreamBus(redis_url=settings.REDIS_URL)
    adapter = OrderBusAdapter()

    channels = ["orthodoxy.audit.requested", "orthodoxy.validation.requested"]
    bus.create_consumer_group(channels[0], settings.CONSUMER_GROUP)

    for event in bus.consume(channels[0], settings.CONSUMER_GROUP, "worker_1"):
        result = adapter.handle_event(event.payload)
        bus.acknowledge(event.stream, settings.CONSUMER_GROUP, event.event_id)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Why | Fix |
|---|---|---|
| `psycopg2.connect()` in routes | Scattered I/O | Use `PersistenceAdapter` |
| Business logic in main.py | Untestable | Move to bus_adapter |
| `os.getenv()` in routes | Hard to find | Use `config.py` |
| Core importing from adapters | Breaks purity | Core → adapters → core (one-way) |
| 300-line main.py | Unreadable | Split into routes/ + adapters/ |
| Direct database in consumers | Violates Level 1 purity | Consumers return dicts, adapters persist |

---

## Dependency Flow

```
main.py
  ├── routes/        → adapters/bus_adapter  → vitruvyan_core (pure domain)
  ├── adapters/
  │   ├── bus_adapter.py    → vitruvyan_core consumers, governance
  │   └── persistence.py    → PostgresAgent, QdrantAgent (I/O)
  └── streams_listener.py   → adapters/bus_adapter (same pipeline)
```

**Direction**: `service → core` (NEVER `core → service`)

---

## Replication Checklist

When creating a new Sacred Order service:

- [ ] Copy this structure
- [ ] Replace `<order>` with service name
- [ ] Define channels in config.py
- [ ] Import pure consumers from `vitruvyan_core.core.governance.<order>.consumers`
- [ ] Wire pipeline in bus_adapter.py
- [ ] Create persistence.py for that order's tables
- [ ] Create routes/ for HTTP endpoints
- [ ] Write Dockerfile
- [ ] Add to docker-compose.yml
- [ ] Test: `python -m pytest` + `curl /health`

---

*Created: FASE 4 — Service Slimming (Feb 2026)*
*Pattern Version: 1.0*
