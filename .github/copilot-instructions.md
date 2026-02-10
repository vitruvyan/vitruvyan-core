# Copilot Instructions — Vitruvyan OS (`vitruvyan-core`)
*Domain-agnostic epistemic operating system. Finance/trading terms in this repo are legacy from an upstream implementation and should be treated as **examples**, not as the repo’s identity.*

---

## Purpose (keep this file small, but useful)
This file is the **high-signal, stable context** Copilot needs to work productively in this repo.

- Prefer **OS-agnostic naming** in new code (entities, signals, events), even if older docs/examples mention tickers/markets.
- If you need deep specs, use the **Appendix docs** in `.github/` (linked at the end) instead of expanding this file.

---

## Sacred Orders (Epistemic Hierarchy)
| Order | Domain | Responsibility |
|------:|--------|----------------|
| Perception | Ingestion | Acquire + normalize external inputs |
| Memory | Persistence | Store structured + semantic state |
| Reason | Computation | Produce deterministic / explainable outputs |
| Discourse | Orchestration | Turn system state into narratives / UX payloads |
| Truth | Governance | Validate outputs, audit, enforce invariants |

---

## Sacred Orders Refactoring — NON-NEGOTIABLE PATTERN (Feb 2026)
**All Sacred Orders MUST follow this two-level architecture. Pattern is mandatory, not optional.**

### Refactoring Status
| Sacred Order | LIVELLO 1 (Pure Domain) | LIVELLO 2 (Service) | Conformance | Reference |
|--------------|-------------------------|---------------------|-------------|-----------|
| **Memory Orders** | ✅ Complete | ✅ Complete | **100%** | Template (Coherence) |
| **Vault Keepers** | ✅ Complete | ✅ Complete | **100%** | Template (Memory/Archival) |
| **Orthodoxy Wardens** | ✅ Complete | ✅ Complete | **95%** | Template (Truth/Governance) |
| Babel Gardens | ⏳ Planned | ⏳ Planned | 0% | 832 lines main.py |
| Codex Hunters | ⏳ Planned | ⏳ Planned | 0% | 987 lines main.py |
| Pattern Weavers | ⏳ Planned | ⏳ Planned | 0% | 163 lines main.py |

**Last updated**: Feb 10, 2026 (3/6 Sacred Orders conformant, 3 pending)

---

### SACRED_ORDER_PATTERN — Mandatory Structure

#### LIVELLO 1: Pure Domain Layer (`vitruvyan_core/core/governance/<order>/`)
**Zero I/O. Pure Python. Testable standalone. No external dependencies (PostgreSQL/Redis/Qdrant/httpx).**

**Required directories** (create ALL 10):
```
vitruvyan_core/core/governance/<order>/
├── domain/              # Frozen dataclasses (immutable DTOs)
├── consumers/           # Pure process() functions (dict → dataclass, NO I/O)
├── governance/          # Rules, classifiers, engines (data-driven)
├── events/              # Channel name constants, event envelopes
├── monitoring/          # Metric NAME constants ONLY (no prometheus_client)
├── philosophy/          # charter.md (identity, mandate, invariants)
│   └── charter.md
├── docs/                # Implementation notes, design decisions
├── examples/            # Usage examples (pure Python, no service dependencies)
├── tests/               # Unit tests (pytest, no Docker/Redis/Postgres)
└── _legacy/             # Pre-refactoring code (frozen archive, read-only)
```

**Import rules (LIVELLO 1)**:
- ✅ Relative imports ONLY: `from .domain import Event`, `from ..events import CHANNELS`
- ✅ Core utilities: `from core.agents.postgres_agent import PostgresAgent` (TYPE HINTS ONLY, never instantiate)
- ❌ FORBIDDEN: `import httpx`, `import psycopg2`, `import qdrant_client`, `from services.*`
- ❌ FORBIDDEN: Instantiate PostgresAgent/QdrantAgent/StreamBus in consumers
- ❌ FORBIDDEN: Absolute imports across Sacred Orders: `from core.governance.orthodoxy_wardens.*`

#### LIVELLO 2: Service Layer (`services/api_<order>/`)
**Infrastructure, I/O, HTTP, Docker. Orchestrates LIVELLO 1 via adapters.**

**Required structure** (create ALL):
```
services/api_<order>/
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
└── _legacy/             # Pre-refactoring service code (frozen archive)
```

**Import rules (LIVELLO 2)**:
- ✅ Import LIVELLO 1: `from core.governance.<order>.consumers import MyConsumer`
- ✅ Import agents: `from core.agents.postgres_agent import PostgresAgent`
- ✅ Import bus: `from core.synaptic_conclave.transport.streams import StreamBus`
- ❌ FORBIDDEN: LIVELLO 1 imports LIVELLO 2 (service → core only, ONE-WAY)
- ❌ FORBIDDEN: Cross-service imports: `from api_orthodoxy_wardens.*` in api_vault_keepers

**main.py target**: < 100 lines (87 lines Orthodoxy, 59 lines Vault, 93 lines Memory)

---

### Step-by-Step Refactoring Procedure (MANDATORY)

**When starting a Sacred Order refactoring, follow this exact sequence:**

#### FASE 0: Audit & Archive Legacy Code
1. **List root directory**: `ls -lh vitruvyan_core/core/governance/<order>/`
2. **Identify violations**: Any `.py` files NOT in subdirectories = violation
3. **Move to consumers/**: Large Python files (agents, analyzers, processors) → `consumers/`
4. **Archive impure code**: Files with I/O/HTTP/DB logic → `_legacy/`
5. **Update cross-file imports**: Search for `from core.governance.<order>.<filename>` and fix paths

#### FASE 1: Create LIVELLO 1 Structure
1. **Create 10 directories**: `mkdir -p {domain,consumers,governance,events,monitoring,philosophy,docs,examples,tests,_legacy}`
2. **Create charter.md**: Document Sacred Order identity, mandate, invariants
3. **Create __init__.py**: All directories need `__init__.py` (empty or with `__all__`)
4. **Verify isolation**: `python3 -c "from core.governance.<order>.consumers import X; print('✅ Pure')"` (must work without Redis/Postgres/Docker)

#### FASE 2: Create LIVELLO 2 Adapters
1. **Create `adapters/bus_adapter.py`**:
   - Instantiate LIVELLO 1 consumers
   - Orchestrate consumer calls
   - Emit events to StreamBus
   - NO business logic (delegate to consumers)
2. **Create `adapters/persistence.py`**:
   - Instantiate PostgresAgent/QdrantAgent
   - Wrapper methods for DB operations
   - ALL I/O must go through this adapter
3. **Verify**: No `PostgresAgent()` or `QdrantAgent()` in main.py or routes.py

#### FASE 3: Reduce main.py to < 100 Lines
1. **Current size**: `wc -l services/api_<order>/main.py`
2. **Condense docstring**: Max 3 lines (title, description, version)
3. **Consolidate imports**: Group by category (stdlib, fastapi, local)
4. **Remove decorative comments**: No ASCII art, no `# ── Section ──` separators
5. **Consolidate logging**: Max 4-5 logger.info calls in startup function
6. **Simplify startup**: Global declarations in 1-3 lines, startup logic < 15 lines
7. **Remove redundant endpoints**: /health handled by api/routes.py, remove duplicates
8. **Final check**: `wc -l main.py` must show < 100

#### FASE 4: Clean Service Layer
1. **Archive extra directories**: `mkdir -p _legacy/ && mv {core,docs,examples,utils} _legacy/` (if they exist)
2. **Update import paths**: `rg "from api_<order>.core" -l` → change to `_legacy.core`
3. **Verify structure**: `ls services/api_<order>/` should show ONLY: main.py, config.py, adapters/, api/, models/, monitoring/, streams_listener.py, Dockerfile, requirements.txt, _legacy/

#### FASE 5: Test & Deploy
1. **Rebuild Docker**: `cd infrastructure/docker && docker compose build <order> <order>_listener`
2. **Restart containers**: `docker stop core_<order> core_<order>_listener && docker rm core_<order> core_<order>_listener`
3. **Deploy**: `docker compose up -d --no-deps <order> <order>_listener`
4. **Verify logs**: `docker logs core_<order> --tail=50` (no ModuleNotFoundError, no import errors)
5. **Test endpoints**: `curl http://localhost:<port>/health` (200 OK)

#### FASE 6: Git Commit
```bash
git add -A
git commit -m "refactor(<order>): SACRED_ORDER_PATTERN conformance - X% → Y%

LIVELLO 1:
- Moved N files (X,XXX lines) to consumers/
- Created 10-directory structure

LIVELLO 2:
- main.py: X → Y lines (-Z%)
- Archived legacy code to _legacy/
- Created adapters/bus_adapter.py, adapters/persistence.py

Test: Docker healthy, endpoints 200 OK"
git push origin main
```

---

### Verification Checklist (Run After Every Refactoring)

**LIVELLO 1 Compliance**:
```bash
# 1. Structure complete (10 directories)
ls vitruvyan_core/core/governance/<order>/ | grep -E "domain|consumers|governance|events|monitoring|philosophy|docs|examples|tests|_legacy" | wc -l
# Expected: 10

# 2. No root Python files (except __init__.py)
find vitruvyan_core/core/governance/<order>/ -maxdepth 1 -name "*.py" ! -name "__init__.py"
# Expected: (empty)

# 3. Pure imports (no infrastructure dependencies)
python3 -c "from core.governance.<order>.consumers import *; print('✅ Pure')"
# Expected: ✅ Pure (no errors)

# 4. No service imports in LIVELLO 1
rg "from services\." vitruvyan_core/core/governance/<order>/ && echo "❌ VIOLATION" || echo "✅ OK"
# Expected: ✅ OK
```

**LIVELLO 2 Compliance**:
```bash
# 1. main.py size < 100 lines
wc -l services/api_<order>/main.py
# Expected: < 100

# 2. Required files exist
ls services/api_<order>/{config.py,adapters/bus_adapter.py,adapters/persistence.py,api/routes.py}
# Expected: all exist

# 3. No PostgresAgent/QdrantAgent in main.py
rg "PostgresAgent\(\)|QdrantAgent\(\)" services/api_<order>/main.py && echo "❌ VIOLATION" || echo "✅ OK"
# Expected: ✅ OK

# 4. Docker container healthy
docker ps --filter "name=core_<order>" --format "{{.Status}}"
# Expected: Up X minutes (healthy)
```

---

### Templates & Reference Implementations

**Use these as copy-paste starting points for new refactorings:**

1. **Memory Orders** (100% conformant): 
   - LIVELLO 1: `vitruvyan_core/core/governance/memory_orders/`
   - LIVELLO 2: `services/api_memory_orders/`
   - main.py: 93 lines ✅
   - Best for: Coherence analysis, RAG, semantic operations

2. **Vault Keepers** (100% conformant):
   - LIVELLO 1: `vitruvyan_core/core/governance/vault_keepers/`
   - LIVELLO 2: `services/api_vault_keepers/`
   - main.py: 59 lines ✅
   - Best for: Archival, persistence, snapshot operations

3. **Orthodoxy Wardens** (95% conformant):
   - LIVELLO 1: `vitruvyan_core/core/governance/orthodoxy_wardens/`
   - LIVELLO 2: `services/api_orthodoxy_wardens/`
   - main.py: 87 lines ✅
   - Best for: Governance, validation, audit operations

**Pattern documents**:
- `vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md` (canonical specification)
- `services/SERVICE_PATTERN.md` (LIVELLO 2 structure)
- `SACRED_ORDERS_REFACTORING_PLAN.md` (roadmap + checklist)

---

### Common Mistakes to Avoid

❌ **WRONG**: Creating only 5-6 directories (missing philosophy/, docs/, examples/, tests/)
✅ **RIGHT**: Create all 10 directories, even if some are empty (future-proofing)

❌ **WRONG**: Leaving `.py` files in `vitruvyan_core/core/governance/<order>/` root
✅ **RIGHT**: ALL code files in subdirectories (consumers/, governance/, domain/)

❌ **WRONG**: `from core.governance.orthodoxy_wardens.code_analyzer import X` in LIVELLO 1
✅ **RIGHT**: `from .consumers.code_analyzer import X` (relative imports)

❌ **WRONG**: Instantiating `PostgresAgent()` in consumers/
✅ **RIGHT**: Pass database connection as function parameter (dependency injection)

❌ **WRONG**: main.py 150 lines with ASCII art, verbose logging, inline logic
✅ **RIGHT**: main.py < 100 lines, minimal comments, delegate to adapters/

❌ **WRONG**: Importing across Sacred Orders: `from core.governance.vault_keepers.* in orthodoxy_wardens`
✅ **RIGHT**: Communicate via StreamBus events (channel: `vault.archive.completed`)

❌ **WRONG**: `docker compose up -d` fails with "container name conflict"
✅ **RIGHT**: `docker stop core_<order> && docker rm core_<order>` before recreating

---

## Repo layout (what exists here)
- `vitruvyan_core/`: the reusable OS core (agents, bus, governance primitives, contracts)
- `services/`: reference microservices (examples of how to wire the core in a running system)
- `tests/`: unit/integration tests and helpers
- `docs/`: long-form system docs
- `.github/`: “appendix” architecture documents and contributor automation

---

## Import conventions (important)
Most runnable code in `services/` imports the core as `core.*` (e.g. `from core.agents.postgres_agent import PostgresAgent`).
That works because the runtime/container typically adds `vitruvyan_core/` to `PYTHONPATH` (or installs it).

- When adding new modules under `vitruvyan_core/core/`, prefer imports that match existing usage (`core.<...>`).
- Avoid mixing `vitruvyan_core.core.<...>` and `core.<...>` in the same service.

---

## Non‑negotiable invariants (do not violate)

### 1) Service boundaries
- Do **not** directly import implementation code across services; communicate via **REST** or the **event bus**.
- Keep “transport/orchestration” concerns separate from “domain logic” (verticals plug in; core stays generic).

### 2) Persistence access (PostgreSQL / Qdrant)
- Use the agents:
  - PostgreSQL: `core.agents.postgres_agent.PostgresAgent` (`vitruvyan_core/core/agents/postgres_agent.py`)
  - Qdrant: `core.agents.qdrant_agent.QdrantAgent` (`vitruvyan_core/core/agents/qdrant_agent.py`)
- Do **not** create raw clients directly in business logic (e.g. `psycopg2.connect(...)`, `qdrant_client.QdrantClient(...)`) unless the repo explicitly introduces a new agent.
- Never put secrets in docs/commands. Use environment variables (`POSTGRES_*`, `QDRANT_*`, etc.) and placeholders.

**Minimal patterns**
```python
from core.agents.postgres_agent import PostgresAgent

pg = PostgresAgent()
rows = pg.fetch("SELECT 1 AS ok")

with pg.transaction():
    pg.execute("INSERT INTO events (id, payload) VALUES (%s, %s)", ("evt_1", "{}"))
```

### 3) Synaptic Conclave (Cognitive Bus = Redis Streams)
- Streams are the canonical transport. Prefer `StreamBus`:
  - `core.synaptic_conclave.transport.streams.StreamBus` (`vitruvyan_core/core/synaptic_conclave/transport/streams.py`)
- Channel naming: dot notation `<service>.<domain>.<action>` (e.g. `codex.discovery.mapped`).
- Consumers must:
  - be **autonomous** (create consumer groups with `mkstream=True` where applicable)
  - **acknowledge** events after handling to avoid redelivery
  - consume via a generator pattern (don’t load unbounded events into memory)
- Sacred invariant: the bus is **payload-blind** (no semantic routing/correlation/synthesis in transport).

**Minimal consumer pattern**
```python
from core.synaptic_conclave.transport.streams import StreamBus

bus = StreamBus()
bus.create_consumer_group("codex.discovery.mapped", "vault_keepers")  # mkstream=True by default

for event in bus.consume("codex.discovery.mapped", "vault_keepers", "vault_1"):
    handle(event)  # event is TransportEvent (payload is opaque to the bus)
    bus.acknowledge(event.stream, "vault_keepers", event.event_id)
```

**Event envelope (single source of truth)**
- Transport layer (bus-level): `core.synaptic_conclave.events.event_envelope.TransportEvent`
- Cognitive layer (consumer-level): `core.synaptic_conclave.events.event_envelope.CognitiveEvent`
- Adapter boundary: `core.synaptic_conclave.events.event_envelope.EventAdapter`

Do not invent new “event shapes” in random services; use these types or wrap them explicitly.

### 4) Language + narrative rules (OS-agnostic interpretation)
- Treat language detection / multilingual preprocessing as a **Perception** responsibility.
- Treat narrative generation as a **Discourse** responsibility.
- Do **not** introduce backend language-switching logic in multiple nodes without an explicit product decision; keep prompts/templates centralized and consistent.

### 5) “Client validation” contract (generalized from upstream UI)
If a client sends an explicit, validated list (e.g. `validated_entities`, `validated_tickers`):
- Backend must **respect it** and must **not re-extract** entities from raw text.
- An **explicit empty list** means “conversational / no entities selected”; do not silently override it with extraction.

This rule generalizes beyond finance. Replace “ticker” with any domain entity:
- `validated_entities is None` → server may attempt extraction (CLI calls, low-trust clients)
- `validated_entities == []` → user explicitly chose “no entities”
- `validated_entities == [...]` → user explicitly chose entities; trust the list

### 6) Testing bias guardrail
- Avoid biased, repetitive fixtures (e.g., the same few “top entities” in every test).
- Prefer generating diverse test inputs when possible (see `tests/` helpers and guidelines).

---

## Golden Rules (must stay true)
Use these as the “quick mental checklist” while coding. If a change violates one of these, stop and redesign.

- **Core stays generic**: put domain logic in verticals/services, not in `vitruvyan_core/core/`.
- **No cross-service imports**: services talk via **REST** or **StreamBus** events.
- **Agents only for persistence**: use `PostgresAgent` / `QdrantAgent`; no raw DB/vector clients in business logic.
- **No secrets in repo text**: commands/docs must use env vars/placeholders (never real passwords/hosts/tokens).
- **Streams, not Pub/Sub**: Redis Streams is the canonical transport; acknowledge after handling; generator consumption.
- **Bus is payload-blind**: transport never inspects/correlates/routes semantically/synthesizes events.
- **Validated lists are authoritative**: if a client provides `validated_*`, respect it (including explicit `[]`).
- **Bias-aware tests**: avoid tiny repetitive fixtures that overfit (prefer diversity/generators).

---

## Where new code should go (rule of thumb)
- OS primitives / reusable infrastructure → `vitruvyan_core/core/`
  - agents, bus, contracts, governance, orchestration helpers
- Domain contracts / interfaces → `vitruvyan_core/domains/`
  - keep them generic (schema-free), focused on inputs/outputs and invariants
- Domain/vertical implementations → prefer `services/` (reference implementations) or a dedicated domain package
  - avoid baking a single vertical’s assumptions into `core/`

If you’re tempted to add finance-specific rules into `core/`, stop and ask:
“Can this be expressed as a domain contract + a vertical implementation instead?”

---

## Quick workflow (safe defaults)
- Search code: `rg "<pattern>"`
- Run tests: `pytest`
- If using reference services: prefer `docker compose up -d --build <service>` (no hardcoded hostnames/passwords in docs)

---

## Legacy vocabulary (upstream artifacts → OS terms)
You will see finance-heavy names in historical docs and a few helpers. Map them mentally:
- “ticker/entity” → “entity”
- “screening/ranking” → “batch scoring”
- “sentiment” → “text signal”
- “portfolio” → “collection/working set”

Prefer OS terms in new code unless you are working inside an explicitly finance vertical.

---

## References (deep docs; do not duplicate here)
- Neural Engine example vertical: `.github/Vitruvyan_Appendix_A_Neural_engine.md`
- Proprietary algorithms (historical context): `.github/Vitruvyan_Appendix_B_Proprietary_Algorithms.md`
- Roadmap: `.github/Vitruvyan_Appendix_C_Epistemic_Roadmap_2026.md`
- Truth & integrity layer: `.github/Vitruvyan_Appendix_D_Truth_and_Integrity_Layer.md`
- RAG system (example): `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Conversational layer: `.github/Vitruvyan_Appendix_F_Conversational_Layer.md`
- Conversational architecture V1: `.github/Vitruvyan_Appendix_G_ Conversational_Architecture_V1.md`
- Ledger system (example): `.github/Vitruvyan_Appendix_H_Blockchain_Ledger.md`
- Pattern Weavers (example): `.github/Vitruvyan_Appendix_I_Pattern_Weavers.md`
- LangGraph exec summary: `.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md`
- Babel Gardens (example vertical): `.github/Vitruvyan_Appendix_K_Babel_Gardens.md`
- MCP integration: `.github/Vitruvyan_Appendix_K_MCP_Integration.md`
- Synaptic Conclave (bus): `.github/Vitruvyan_Appendix_L_Synaptic_Conclave.md`
- UI architecture (example client): `.github/Vitruvyan_Appendix_L_UI_Architecture.md`
- Shadow trading (example vertical): `.github/Vitruvyan_Appendix_M_Shadow_Trading.md`
- Portfolio architects (example vertical): `.github/Vitruvyan_Appendix_N_Portfolio_Architects.md`
