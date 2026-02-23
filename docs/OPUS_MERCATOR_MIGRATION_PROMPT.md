# OPUS MERCATOR MIGRATION PROMPT
## Vitruvyan Finance Domain → vitruvyan-core

---

## Mission

You are working on a clone of **vitruvyan-core** (`/home/caravaggio/vitruvyan-core`), the domain-agnostic framework.

Your mission: **read the financial domain logic from vitruvyan** (`/home/caravaggio/vitruvyan`) module by module, understand it deeply, and transplant it into vitruvyan-core respecting BOTH contracts AND tree structure.

vitruvyan-core already has:
- **322 Python files** with contracts, ABCs, frozen types, and service scaffolding
- **13 Docker services** with Dockerfiles and docker-compose.yml (1,050 lines)
- **Complete orchestration contracts**: `GraphPlugin` ABC, `BaseGraphState` (~30 fields), `NodeContract`, `IntentRegistry`, `RouteRegistry`
- **Complete governance contracts**: `Verdict` (frozen, 201 LOC), `Finding` (frozen, 83 LOC), `Rule` (289 LOC), `VerdictEngine` (298 LOC)
- **Complete Neural Engine contracts**: `IDataProvider` (169 LOC), `IScoringStrategy` (179 LOC), `engine.py` (306 LOC), `composite.py`, `ranking.py`, `scoring.py`
- **Complete VPAR contracts**: VEE (engine, analyzer, generator, memory_adapter, types), VARE (engine, types), VWRE (engine, types), VSGS (engine, types)
- **`domains/finance/`** with `graph_plugin.py` (742 LOC), `intent_config.py`, `slot_filler.py`, `response_formatter.py`
- **`services/*/adapters/`** pattern for every service (bus_adapter, persistence, domain-specific)

Your job is NOT to rewrite contracts. They exist. Your job is to **fill the adapters and domain implementations with real finance logic from vitruvyan**.

---

## Architecture: 3 Layers

```
LAYER 1 — vitruvyan_core/core/          (CONTRACTS — already done, DO NOT modify)
    governance/orthodoxy_wardens/domain/verdict.py     ← frozen Verdict
    governance/orthodoxy_wardens/governance/rule.py     ← RuleSet + registry
    neural_engine/engine.py                            ← GenericAggregationEngine
    orchestration/graph_engine.py                      ← GraphPlugin ABC
    orchestration/base_state.py                        ← BaseGraphState
    vpar/vee/vee_engine.py                             ← VEE with ExplainabilityProvider
    vpar/vare/vare_engine.py                           ← VARE with RiskProvider
    synaptic_conclave/transport/streams.py             ← StreamBus

LAYER 2 — services/api_*/                (DOCKER SERVICES — your primary target)
    adapters/bus_adapter.py         ← Connect to StreamBus
    adapters/persistence.py         ← PostgreSQL/Qdrant I/O
    adapters/<domain_specific>.py   ← Finance-specific logic goes HERE
    api/routes.py                   ← REST endpoints
    models/schemas.py               ← Pydantic models
    monitoring/health.py            ← Health checks
    main.py                         ← FastAPI bootstrap
    streams_listener.py             ← Redis Streams consumer

LAYER 3 — vitruvyan_core/domains/finance/  (DOMAIN PLUGIN — your secondary target)
    graph_plugin.py                 ← FinanceGraphPlugin (partially done, 742 LOC)
    intent_config.py                ← Finance intents
    slot_filler.py                  ← Finance slot filling
    response_formatter.py           ← Finance response formatting
    entity_resolver_config.py       ← Ticker resolution
    execution_config.py             ← Execution handlers
    governance_rules.py             ← Finance-specific rules
```

---

## Source: Vitruvyan (Finance Implementation)

Path: `/home/caravaggio/vitruvyan`  
GitHub: `dbaldoni/vitruvyan` (branch `main`)

### Key Source Files per Module

#### 1. Orthodoxy Wardens (Priority: HIGH)
**Read these files:**
```
vitruvyan/core/cognitive_bus/orthodoxy/                    ← Inline orthodoxy logic
vitruvyan/core/agents/validators/architectural_guardrails.py  ← 845 lines, main validation
vitruvyan/core/agents/validators/audit_executor.py         ← Audit execution
vitruvyan/docker/services/api_orthodoxy_wardens/main.py    ← Docker service entry
vitruvyan/docker/services/api_orthodoxy_wardens/routes.py  ← REST API
vitruvyan/docker/services/api_orthodoxy_wardens/streams_listener.py ← Bus listener
```

**Transplant INTO:**
```
core: services/api_orthodoxy_wardens/adapters/roles.py        ← Finance-specific role logic
core: services/api_orthodoxy_wardens/adapters/workflows.py    ← Finance audit workflows
core: services/api_orthodoxy_wardens/adapters/orthodoxy_db_manager.py ← Finance DB queries
core: services/api_orthodoxy_wardens/adapters/event_handlers.py ← Finance event handling
```

**What to extract:**
- PostgreSQL queries from architectural_guardrails.py (the finance-specific validation rules)
- Finance-specific audit patterns (ticker validation, z-score ranges, sentiment bounds)
- The 5 warden roles: Confessor, Penitent, Chronicler, Inquisitor, Abbot
- Stream channels and event patterns used

**What NOT to transplant:**
- Direct `psycopg2.connect()` → use `PostgresAgent()` (already in core at `core/agents/postgres_agent.py`)
- Direct Qdrant client → use `QdrantAgent()` (already in core at `core/agents/qdrant_agent.py`)
- `OrthodoxyVerdict` as mutable dict → core already has frozen `Verdict` dataclass

---

#### 2. Memory Orders (Priority: HIGH — smallest module)
**Read these files:**
```
vitruvyan/core/memory_orders/coherence.py                  ← Single function, hardcoded SQL
vitruvyan/core/memory_orders/__init__.py                   ← Module init
vitruvyan/core/agents/memory_orders/                       ← Memory agent logic
vitruvyan/docker/services/api_memory_orders/main.py        ← Docker service
vitruvyan/docker/services/api_memory_orders/routes.py      ← REST API
vitruvyan/docker/services/api_memory_orders/streams_listener.py
```

**Transplant INTO:**
```
core: services/api_memory_orders/adapters/pg_reader.py      ← Finance PostgreSQL queries
core: services/api_memory_orders/adapters/qdrant_reader.py  ← Finance Qdrant queries
core: services/api_memory_orders/adapters/persistence.py    ← Finance coherence I/O
```

**What to extract:**
- PostgreSQL ↔ Qdrant coherence checking logic (count comparison, drift calculation)
- Finance-specific table names (`sentiment_scores`, `screener_results`, `trend_logs`)
- Finance-specific Qdrant collections (`phrases_embeddings`, `conversations_embeddings`, `momentum_vectors`, `trend_vectors`)
- Memory sync scheduling logic

---

#### 3. Codex Hunters (Priority: MEDIUM)
**Read these files:**
```
vitruvyan/core/codex_hunters/                              ← Full module
vitruvyan/core/codex_hunters/domain/base_hunter.py         ← BaseHunter with execute()
vitruvyan/core/codex_hunters/domain/scribe.py              ← Finance data indicators
vitruvyan/core/codex_hunters/domain/cassandra.py           ← Risk prophet
vitruvyan/core/codex_hunters/consumers/                    ← Consumer implementations
vitruvyan/core/codex_hunters/config/                       ← Config files
vitruvyan/docker/services/api_codex_hunters/main.py        ← Docker service
```

**Transplant INTO:**
```
core: services/api_codex_hunters/adapters/persistence.py    ← Finance data I/O
core: services/api_codex_hunters/adapters/bus_adapter.py    ← Finance bus channels
```

**What to extract:**
- Finance data collection logic (Reddit, GNews, financial APIs, yfinance)
- Scribe's finance indicators (RSI, MACD, SMA, EMA)
- Cassandra's risk prophecy formulas
- Codex scheduler patterns (cron-like scheduling)

**Critical rename:** `BaseHunter.execute()` → core uses `BaseConsumer.process()` signature. Adapt the method name.

---

#### 4. Babel Gardens (Priority: MEDIUM)
**Read these files:**
```
vitruvyan/core/babel_gardens/                              ← Module root
vitruvyan/core/babel_gardens/modules/                      ← Sub-engines
vitruvyan/core/babel_gardens/schemas/                      ← Data schemas
vitruvyan/docker/services/api_babel_gardens/main.py        ← Docker service (port 8009)
vitruvyan/docker/services/api_babel_gardens/embedding_engine.py ← MiniLM-L6-v2
vitruvyan/docker/services/api_babel_gardens/sentiment_fusion.py ← FinBERT + Gemma
vitruvyan/docker/services/api_babel_gardens/emotion_engine.py   ← Emotion detection
```

**Transplant INTO:**
```
core: services/api_babel_gardens/adapters/embedding.py      ← Finance embedding config
core: services/api_babel_gardens/adapters/persistence.py    ← Finance sentiment storage
core: services/api_babel_gardens/adapters/bus_adapter.py    ← Finance bus channels
core: services/api_babel_gardens/plugins/                   ← Finance plugin (if exists)
```

**What to extract:**
- Sentiment fusion weights (FinBERT + Gemma cooperation)
- Language detection pipeline (84 languages, Unicode range analysis)
- Finance-specific sentiment mapping (score 0-1 → -1 to +1 for DB)
- Emotion detection patterns (finance anxiety, FOMO, euphoria)
- PyTorch model loading and inference pipeline

**Critical:** PyTorch/model loading should go into adapters, NOT into core modules.

---

#### 5. Vault Keepers (Priority: MEDIUM-HIGH)
**Read these files:**
```
vitruvyan/core/vault_keepers/                              ← Module root (if exists)
vitruvyan/core/agents/vault_keepers/archivist_agent.py     ← 1,609 lines! Main agent
vitruvyan/core/agents/vault_keepers/sentinel_agent.py      ← Portfolio risk monitoring
vitruvyan/docker/services/api_vault_keepers/main.py        ← Docker service
vitruvyan/docker/services/api_vault_keepers/streams_listener.py
```

**Transplant INTO:**
```
core: services/api_vault_keepers/adapters/persistence.py    ← Finance archival I/O
core: services/api_vault_keepers/adapters/bus_adapter.py    ← Finance bus channels
```

**What to extract:**
- Archival logic (pg_dump, gzip, subprocess calls for backup)
- Sentinel's finance-specific portfolio monitoring (threshold rules, concentration risk)
- Finance-specific table names used by archivist
- Signal archival logic

**Critical:** `subprocess` calls (pg_dump/gzip) are infrastructure → adapters/persistence.py

---

#### 6. Orchestration / LangGraph (Priority: CRITICAL)
**Read these files:**
```
vitruvyan/core/langgraph/node/*.py                         ← ALL 30+ node files
vitruvyan/core/langgraph/shared/graph_state.py             ← ~110 field state dict
vitruvyan/core/langgraph/shared/graph_flow.py              ← Graph compilation
vitruvyan/core/langgraph/shared/graph_runner.py            ← Graph execution
vitruvyan/core/langgraph/listeners/                        ← Listener implementations
```

**Transplant INTO:**
```
core: domains/finance/graph_plugin.py                       ← FinanceGraphPlugin (EXTEND, 742 LOC exists)
core: domains/finance/intent_config.py                      ← Finance intents (EXISTS)
core: domains/finance/slot_filler.py                        ← Finance slots (EXISTS)
core: domains/finance/response_formatter.py                 ← Finance formatting (EXISTS)
core: domains/finance/execution_config.py                   ← Finance execution (EXISTS)
core: services/api_graph/adapters/graph_adapter.py          ← Finance graph builder
```

**What to extract:**
- All 30+ finance node implementations → register via `FinanceGraphPlugin.get_nodes()`
- Finance-specific state fields (tickers, budget, horizon, sector, etc.) → `FinanceStateExtension`
- Intent patterns (sentiment, trend, momentum, etc.) → `intent_config.py`
- Route mapping (dispatcher_exec, comparison_exec, etc.) → extend existing config
- The 14 Neural Engine factors integration

**Critical:**
- Core `BaseGraphState` has ~30 fields. Vitruvyan has ~110. The ~80 finance fields go into `FinanceStateExtension` (TypedDict inheritance)
- Every node function signature must match `NodeContract`: `(state: Dict[str, Any]) → Dict[str, Any]`
- DO NOT hardcode node imports in graph_flow.py — register via plugin

---

#### 7. Neural Engine (Priority: CRITICAL — hardest module)
**Read these files:**
```
vitruvyan/core/logic/neural_engine/engine_core.py          ← 2,861 lines! THE MONOLITH
vitruvyan/docker/services/api_neural_engine/main.py        ← Docker service (port 8003)
vitruvyan/docker/services/api_neural_engine/routes.py      ← REST API
```

**Transplant INTO:**
```
core: services/api_neural_engine/adapters/                  ← Finance data provider implementation
core: services/api_neural_engine/modules/engine_orchestrator.py ← Finance orchestration
```

**What to extract:**
- The 14 factor calculation functions (A-L + P + Earnings) → implement `IDataProvider` contract
- Profile definitions (short_spec, balanced_mid, etc.) → implement `IScoringStrategy` contract
- PostgreSQL data queries (hardcoded `DB_PARAMS = {"host": "161.97.140.157"}`) → adapters/persistence.py
- JSON response building → adapters/ or response formatter
- The 5 screening profiles with weights

**Critical:**
- Core has `IDataProvider.get_universe()` and `IDataProvider.get_features()` — vitruvyan has these inline in engine_core.py
- Core has `IScoringStrategy.compute_composite_scores()` — vitruvyan has this as inline weight multiplication
- Core has `GenericAggregationEngine` (306 LOC) that orchestrates provider + strategy → DO NOT duplicate
- Move `psycopg2.connect(host="161.97.140.157"...)` to adapter with env vars

---

#### 8. VPAR (VEE, VARE, VWRE, VSGS) (Priority: HIGH)
**Read these files:**
```
vitruvyan/core/logic/vitruvyan_proprietary/vee/vee_engine.py    ← 741 LOC
vitruvyan/core/logic/vitruvyan_proprietary/vare_engine.py       ← 753 LOC
vitruvyan/core/logic/vitruvyan_proprietary/vwre_engine.py       ← VWRE engine
vitruvyan/core/langgraph/node/semantic_grounding_node.py        ← VSGS inline
```

**Transplant INTO:**
- VEE: Implement `ExplainabilityProvider` for finance (core has the ABC in `vpar/vee/`)
- VARE: Implement `RiskProvider` for finance (move `yfinance`, `SPY`, `risk_free_rate=0.02` to provider)
- VWRE: Implement `AggregationProvider` for finance (factor names, profile weights)
- VSGS: Extract inline logic → implement `VSGSEngine` contract from `vpar/vsgs/`

**What to extract:**
- VEE: `kpi_categories` (momentum, trend, volatility, sentiment, fundamentals), template generation, Italian→English transformation
- VARE: `yfinance` data fetching, SPY benchmark, 4 risk dimensions (market, volatility, liquidity, correlation)
- VWRE: Factor contribution math, profile weight mapping
- VSGS: Qdrant semantic search, context injection into LangGraph state

---

## Golden Rules

### NEVER DO
❌ Modify files in `vitruvyan_core/core/` LAYER 1 contracts (they are DONE)
❌ Use direct `psycopg2.connect()` — always use `PostgresAgent()` from `core/agents/postgres_agent.py`
❌ Use direct `qdrant_client.QdrantClient()` — always use `QdrantAgent()` from `core/agents/qdrant_agent.py`
❌ Import between services (service A importing from service B) — use REST API or StreamBus
❌ Hardcode database IPs, ports, passwords — use environment variables
❌ Put finance-specific logic in LAYER 1 — it goes in LAYER 2 (adapters) or LAYER 3 (domains/finance/)
❌ Create mutable domain objects where core has frozen ones — core's `@dataclass(frozen=True)` is law
❌ Use Pub/Sub — it is DEPRECATED. Only Redis Streams via `StreamBus`
❌ Duplicate logic that core already has (VerdictEngine, RuleRegistry, GraphEngine, etc.)

### ALWAYS DO
✅ Use `PostgresAgent()` and `QdrantAgent()` for ALL database access
✅ Use frozen dataclasses from core's `domain/` directories
✅ Use `StreamBus` from `core/synaptic_conclave/transport/streams.py` for event communication
✅ Register finance nodes via `FinanceGraphPlugin.get_nodes()`, not hardcoded imports
✅ Put finance-specific PostgreSQL table names in adapter config, not inline
✅ Use environment variables for all external service URLs and credentials
✅ Use `adapters/bus_adapter.py` pattern for bus integration per service
✅ Use `adapters/persistence.py` pattern for database I/O per service
✅ Test imports after each module (`python -c "from X import Y"`)
✅ Commit after each module with descriptive message

---

## Execution Order

Work **one module at a time**, in this order:

### Phase A — Governance Foundation
1. **Memory Orders** (smallest, ~450 LOC, lowest risk) — warm-up module
2. **Orthodoxy Wardens** (~960 LOC, high impact) — governance for everything else

### Phase B — Data Pipeline
3. **Codex Hunters** (~1,020 LOC) — data ingestion
4. **Babel Gardens** (~860 LOC) — linguistic processing

### Phase C — Orchestration + Vault
5. **Vault Keepers** (~1,040 LOC) — archival and monitoring
6. **Orchestration/LangGraph** (~1,260 LOC, CRITICAL) — graph compilation

### Phase D — Computation Core
7. **Neural Engine** (~1,620 LOC, HARDEST) — the 2,861-line monolith decomposition
8. **VPAR** (~1,560 LOC) — VEE, VARE, VWRE, VSGS providers

### Per-Module Workflow

For EACH module, follow this exact workflow:

```
1. READ vitruvyan source files (listed above per module)
   - Understand the finance-specific logic
   - Identify PostgreSQL queries, table names, Qdrant collections
   - Note external API calls (yfinance, httpx, etc.)
   - Note hardcoded values (IPs, ports, thresholds)

2. READ core's existing contracts for this module
   - Check domain/ types (frozen dataclasses)
   - Check events/ (event schemas)
   - Check consumers/ (base classes)
   - Check governance/ (rules, registries)

3. READ core's existing service scaffolding
   - services/api_*/adapters/ (what's stubbed vs implemented)
   - services/api_*/api/routes.py (what endpoints exist)
   - services/api_*/main.py (what's bootstrapped)

4. IMPLEMENT by filling adapters with real finance logic
   - All finance DB queries → adapters/persistence.py
   - All bus interactions → adapters/bus_adapter.py
   - All domain-specific logic → adapters/<specific>.py
   - All domain config → domains/finance/ (if orchestration)

5. VERIFY
   - python -c "from services.api_X.adapters.Y import Z"
   - Check frozen types are used (not mutable dicts)
   - Check no direct psycopg2/qdrant_client usage
   - Check no hardcoded IPs/passwords

6. BUILD & TEST DOCKER SERVICE
   - docker compose -f infrastructure/docker/docker-compose.yml build <service>
   - docker compose -f infrastructure/docker/docker-compose.yml up -d <service>
   - curl http://localhost:<port>/health
   - Check logs: docker logs core_<service> --tail 50

7. COMMIT
   - git add the changed files (core module + service + Dockerfile)
   - git commit -m "feat(mercator): Module N — <name> finance logic + Docker service"
```

---

## Docker Service Pairing (Module + Service Together)

**CRITICAL**: Each module migration MUST include its paired Docker service.
Never migrate a module without also completing its Docker service.
The pattern is: read vitruvyan's `docker/services/api_X/*.py`, understand the FastAPI routes and listeners, then fill core's `services/api_X/` scaffolding with real finance logic.

### Service Port Mapping (vitruvyan → core)

| Service | vitruvyan Port | core Port (external) | core Container |
|---|---|---|---|
| Graph (LangGraph) | 8004 | 9004→8004 | core_graph |
| Neural Engine | 8003 | 9003→8003 | core_neural_engine |
| Orthodoxy Wardens | 8006 | 9006→8006 | core_orthodoxy_wardens |
| Babel Gardens | 8009 | 9009→8009 | core_babel_gardens |
| Memory Orders | 8016 | 9016→8016 | core_memory_orders |
| Vault Keepers | 8007(new) | 9007→8007 | core_vault_keepers |
| Conclave | 8012(new) | 9012→8012 | core_conclave |
| Codex Hunters | (no ext port) | 9017→8017 | core_codex_hunters |
| MCP Server | 8020 | 8020→8020 | core_mcp |
| Embedding | 8010 | 9010→8010 | core_embedding |
| Pattern Weavers | 8017 | (TBD) | (TBD) |
| Shadow Traders | 8025→8020 | (TBD) | (TBD) |
| Portfolio Guardian | 8021 | (TBD) | (TBD) |

### Dockerfile Mapping (vitruvyan → core)

| vitruvyan Dockerfile | core Dockerfile |
|---|---|
| `docker/dockerfiles/Dockerfile.orthodoxy_wardens` | `infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens` |
| `docker/dockerfiles/Dockerfile.api_memory_orders` | `infrastructure/docker/dockerfiles/Dockerfile.api_memory_orders` |
| `docker/dockerfiles/Dockerfile.api_codex_hunters` | `infrastructure/docker/dockerfiles/Dockerfile.api_codex_hunters` |
| `docker/dockerfiles/Dockerfile.api_babel_gardens` | `infrastructure/docker/dockerfiles/Dockerfile.api_babel_gardens` |
| `docker/dockerfiles/Dockerfile.vault_keepers` | `infrastructure/docker/dockerfiles/Dockerfile.vault_keepers` |
| `docker/dockerfiles/Dockerfile.api_graph` | `infrastructure/docker/dockerfiles/Dockerfile.api_graph` |
| `docker/dockerfiles/Dockerfile.api_neural` | `infrastructure/docker/dockerfiles/Dockerfile.api_neural` |
| `docker/dockerfiles/Dockerfile.api_conclave` | `infrastructure/docker/dockerfiles/Dockerfile.api_conclave` |
| `docker/services/api_mcp_server/Dockerfile` | `infrastructure/docker/dockerfiles/Dockerfile.api_mcp` |
| `docker/services/api_pattern_weavers/Dockerfile` | `infrastructure/docker/dockerfiles/Dockerfile.api_weavers` |
| `docker/services/api_shadow_traders/Dockerfile` | (CREATE: `Dockerfile.shadow_traders`) |
| `docker/services/api_portfolio_guardian/Dockerfile`(1) | `infrastructure/docker/dockerfiles/Dockerfile.portfolio_guardian` |
| `docker/services/api_sentinel_agent/Dockerfile` | (MERGE into portfolio_guardian) |

### Per-Module Docker File-by-File Mapping

---

#### Module 1: Orthodoxy Wardens — Docker Service

**vitruvyan source** (`docker/services/api_orthodoxy_wardens/`, 2,601 LOC):
```
main_orthodoxy_wardens.py     ← FastAPI app, routes, audit endpoints
main_audit_broken.py          ← Broken audit endpoint (legacy, skip)
__init__.py                   ← Module init
```

**core destination** (`services/api_orthodoxy_wardens/`, scaffolding exists):
```
main.py                       ← FastAPI bootstrap (EXISTS, fill with real routes)
config.py                     ← Service config (EXISTS)
api/routes.py                 ← REST endpoints (EXISTS scaffolding → fill from main_orthodoxy_wardens.py)
adapters/persistence.py       ← PostgreSQL queries (EXISTS → fill with finance queries)
adapters/bus_adapter.py       ← StreamBus channels (EXISTS → fill with finance channels)
adapters/roles.py             ← 5 warden roles (EXISTS → fill from vitruvyan role logic)
adapters/workflows.py         ← Audit workflows (EXISTS → fill from audit logic)
adapters/orthodoxy_db_manager.py ← DB manager (EXISTS → fill finance table queries)
adapters/event_handlers.py    ← Event handling (EXISTS → fill from vitruvyan event patterns)
models/schemas.py             ← Pydantic models (EXISTS → fill from vitruvyan API contracts)
monitoring/health.py          ← Health check (EXISTS)
streams_listener.py           ← Redis Streams consumer (EXISTS → fill channel subscriptions)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.orthodoxy_wardens` (EXISTS in core)  
**docker-compose**: `core_orthodoxy_wardens`, port 9006→8006  

**Migration action**: Read `main_orthodoxy_wardens.py` (2,601 LOC). Extract:
- FastAPI routes → `api/routes.py`
- PostgreSQL audit queries → `adapters/persistence.py` + `adapters/orthodoxy_db_manager.py`
- Warden role logic → `adapters/roles.py`
- Stream channel subscriptions → `streams_listener.py`
- Pydantic request/response models → `models/schemas.py`

---

#### Module 2: Memory Orders — Docker Service

**vitruvyan source** (`docker/services/api_memory_orders/`, 408 LOC):
```
main_memory.py                ← FastAPI app, coherence endpoints
```

**core destination** (`services/api_memory_orders/`, scaffolding exists):
```
main.py                       ← FastAPI bootstrap (EXISTS → fill)
config.py                     ← Service config (EXISTS)
api/routes.py                 ← REST endpoints (EXISTS → fill from main_memory.py)
adapters/persistence.py       ← Coherence I/O (EXISTS → fill with finance table names)
adapters/pg_reader.py         ← PostgreSQL reader (EXISTS → fill with finance SQL)
adapters/qdrant_reader.py     ← Qdrant reader (EXISTS → fill with finance collections)
adapters/bus_adapter.py       ← StreamBus channels (EXISTS → fill)
models/schemas.py             ← Pydantic models (EXISTS → fill)
monitoring/health.py          ← Health check (EXISTS)
reconciliation/               ← 4 reconciliation files (EXISTS — core BONUS, vitruvyan doesn't have this)
streams_listener.py           ← Redis Streams consumer (EXISTS → fill)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.api_memory_orders` (EXISTS)  
**docker-compose**: `core_memory_orders`, port 9016→8016 + `core_memory_orders_listener`  

**Migration action**: Read `main_memory.py` (408 LOC). Extract:
- Coherence check logic (PostgreSQL ↔ Qdrant row count comparison) → `adapters/persistence.py`
- Finance-specific table/collection names → `adapters/pg_reader.py` + `adapters/qdrant_reader.py`
- FastAPI routes → `api/routes.py`
- NOTE: Core has reconciliation/ module (conflict_resolver, duplicate_detector, orphan_detector, version_reconciler) that vitruvyan lacks — PRESERVE these, they're core BONUS features

---

#### Module 3: Codex Hunters — Docker Service

**vitruvyan source** (`docker/services/api_codex_hunters/`, 1,425 LOC):
```
main.py                       ← FastAPI app, hunter endpoints, scheduler
event_hunter_standalone.py    ← Standalone event hunter (Reddit/GNews)
redis_listener.py             ← Legacy pub/sub listener (DEPRECATED)
streams_listener.py           ← Redis Streams consumer
```

**core destination** (`services/api_codex_hunters/`, scaffolding exists):
```
main.py                       ← FastAPI bootstrap (EXISTS → fill from vitruvyan main.py)
config.py                     ← Service config (EXISTS)
api/routes.py                 ← REST endpoints (EXISTS → fill hunter trigger routes)
adapters/persistence.py       ← Data storage (EXISTS → fill with finance data I/O)
adapters/bus_adapter.py       ← StreamBus channels (EXISTS → fill)
models/schemas.py             ← Pydantic models (EXISTS → fill)
monitoring/health.py          ← Health check (EXISTS)
streams_listener.py           ← Redis Streams consumer (EXISTS → fill)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.api_codex_hunters` (EXISTS)  
**docker-compose**: `core_codex_hunters`  

**Migration action**: Read all 4 vitruvyan files (1,425 LOC). Extract:
- `main.py`: FastAPI routes, scheduler config → `api/routes.py` + `main.py`
- `event_hunter_standalone.py`: Reddit/GNews data collection → `adapters/persistence.py` (data logic)
- `streams_listener.py`: Channel subscriptions → `streams_listener.py`
- SKIP `redis_listener.py` (deprecated pub/sub)

---

#### Module 4: Babel Gardens — Docker Service (LARGEST: 8,212 LOC)

**vitruvyan source** (`docker/services/api_babel_gardens/`, 8,212 LOC):
```
main.py                                    ← 967 LOC, FastAPI app, all route definitions
modules/embedding_engine.py                ← 1,006 LOC, MiniLM-L6-v2 + language detection
modules/embedding_engine_cooperative.py    ← 585 LOC, cooperative embedding
modules/sentiment_fusion.py               ← 786 LOC, FinBERT + Gemma sentiment
modules/emotion_detector.py               ← 604 LOC, emotion classification
modules/cognitive_bridge.py               ← 649 LOC, LLM bridge
modules/profile_processor.py              ← 608 LOC, user profile processing
modules/__init__.py
schemas/api_models.py                     ← Pydantic API models
schemas/__init__.py
shared/base_service.py                    ← Base service utilities
shared/integrity_watcher.py              ← 548 LOC, data integrity
shared/model_manager.py                  ← 365 LOC, PyTorch model loading
shared/vector_cache.py                   ← 494 LOC, embedding cache
shared/__init__.py
redis_listener.py                        ← 643 LOC, legacy pub/sub (DEPRECATED)
streams_listener.py                      ← Redis Streams consumer
linguistic_synthesis.py                  ← Linguistic synthesis
__init__.py
```

**core destination** (`services/api_babel_gardens/`, scaffolding exists WITH modules/):
```
main.py                                    ← FastAPI bootstrap (EXISTS → fill from vitruvyan main.py)
config.py                                  ← Service config (EXISTS)
api/routes_sentiment.py                    ← Sentiment endpoints (EXISTS → fill)
api/routes_embeddings.py                   ← Embedding endpoints (EXISTS → fill)
api/routes_emotion.py                      ← Emotion endpoints (EXISTS → fill)
api/routes_admin.py                        ← Admin endpoints (EXISTS → fill)
adapters/embedding.py                      ← Embedding adapter (EXISTS → fill with MiniLM config)
adapters/persistence.py                    ← DB storage (EXISTS → fill with finance sentiment storage)
adapters/bus_adapter.py                    ← StreamBus channels (EXISTS → fill)
modules/embedding_engine.py                ← (EXISTS in core! ← fill from vitruvyan 1,006 LOC)
modules/embedding_engine_cooperative.py    ← (EXISTS in core! ← fill from vitruvyan 585 LOC)
modules/sentiment_fusion.py               ← (EXISTS in core! ← fill from vitruvyan 786 LOC)
modules/emotion_detector.py               ← (EXISTS in core! ← fill from vitruvyan 604 LOC)
modules/cognitive_bridge.py               ← (EXISTS in core! ← fill from vitruvyan 649 LOC)
modules/profile_processor.py              ← (EXISTS in core! ← fill from vitruvyan 608 LOC)
plugins/finance_signals.py                ← (EXISTS in core — BONUS, finance-specific signals)
schemas/api_models.py                     ← (EXISTS in core! ← fill from vitruvyan schemas)
shared/base_service.py                    ← (EXISTS in core! ← fill)
shared/integrity_watcher.py              ← (EXISTS in core! ← fill from vitruvyan 548 LOC)
shared/model_manager.py                  ← (EXISTS in core! ← fill from vitruvyan 365 LOC)
shared/vector_cache.py                   ← (EXISTS in core! ← fill from vitruvyan 494 LOC)
streams_listener.py                      ← Redis Streams consumer (EXISTS → fill)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.api_babel_gardens` (EXISTS)  
**docker-compose**: `core_babel_gardens`, port 9009→8009  

**Migration action**: This is the LARGEST migration (8,212 LOC). Strategy:
1. Core already mirrors vitruvyan's `modules/`, `shared/`, `schemas/` structure exactly
2. Core has BONUS `plugins/finance_signals.py` and split routes (4 route files vs 1 monolithic main.py)
3. Fill each core `modules/*.py` from its vitruvyan counterpart (1:1 mapping)
4. Split vitruvyan `main.py` routes into core's `api/routes_sentiment.py`, `routes_embeddings.py`, `routes_emotion.py`, `routes_admin.py`
5. Fill `shared/*.py` files from vitruvyan counterparts
6. SKIP `redis_listener.py` (deprecated pub/sub)
7. PyTorch model loading stays in `shared/model_manager.py` (NOT in core contracts)

---

#### Module 5: Vault Keepers — Docker Service

**vitruvyan source** (`docker/services/api_vault_keepers/`, 1,567 LOC):
```
main_vault_keepers.py         ← FastAPI app, archival endpoints
main_backup.py                ← Backup orchestration (pg_dump, gzip)
redis_listener.py             ← Legacy pub/sub (DEPRECATED)
streams_listener.py           ← Redis Streams consumer
```

**core destination** (`services/api_vault_keepers/`, scaffolding exists):
```
main.py                       ← FastAPI bootstrap (EXISTS → fill)
config.py                     ← Service config (EXISTS)
api/routes.py                 ← REST endpoints (EXISTS → fill from main_vault_keepers.py)
adapters/persistence.py       ← Archival I/O (EXISTS → fill with backup logic from main_backup.py)
adapters/bus_adapter.py       ← StreamBus channels (EXISTS → fill)
models/schemas.py             ← Pydantic models (EXISTS → fill)
streams_listener.py           ← Redis Streams consumer (EXISTS → fill)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.vault_keepers` (EXISTS)  
**docker-compose**: `core_vault_keepers`, port 9007→8007  

**Migration action**: Read all 4 vitruvyan files (1,567 LOC). Extract:
- `main_vault_keepers.py`: FastAPI routes + archival logic → `api/routes.py` + `adapters/persistence.py`
- `main_backup.py`: pg_dump/gzip subprocess calls → `adapters/persistence.py` (infrastructure)
- `streams_listener.py`: Channel subscriptions → `streams_listener.py`
- SKIP `redis_listener.py` (deprecated)

---

#### Module 6: Orchestration / LangGraph — Docker Service (CRITICAL)

**vitruvyan source** (`docker/services/api_graph/`, 1,267 LOC):
```
main.py                       ← FastAPI app, /run endpoint, graph compilation
streams_listener.py           ← Redis Streams consumer
```

**ALSO read** (the REAL logic lives in core modules, NOT just docker service):
```
vitruvyan/core/langgraph/shared/graph_flow.py     ← Graph compilation (edges, nodes, routing)
vitruvyan/core/langgraph/shared/graph_runner.py    ← Graph execution, state management
vitruvyan/core/langgraph/shared/graph_state.py     ← ~110 field state dict
vitruvyan/core/langgraph/node/*.py                 ← ALL 30+ node implementations
```

**core destination** (`services/api_graph/`, scaffolding exists):
```
main.py                       ← FastAPI bootstrap (EXISTS → fill from vitruvyan main.py)
config.py                     ← Service config (EXISTS)
api/routes.py                 ← REST endpoints (EXISTS → fill /run, /health, /metrics)
adapters/graph_adapter.py     ← Graph builder adapter (EXISTS → fill with finance graph compilation)
adapters/persistence.py       ← DB storage (EXISTS → fill)
models/schemas.py             ← Pydantic models (EXISTS → fill)
monitoring/health.py          ← Health check (EXISTS)
```

**ALSO fill** (domain layer):
```
domains/finance/graph_plugin.py          ← FinanceGraphPlugin (EXISTS 742 LOC → EXTEND with all 30+ nodes)
domains/finance/intent_config.py         ← Finance intents (EXISTS → fill complete intent patterns)
domains/finance/slot_filler.py           ← Finance slots (EXISTS → fill)
domains/finance/execution_config.py      ← Execution handlers (EXISTS → fill)
domains/finance/response_formatter.py    ← Response formatting (EXISTS → fill)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.api_graph` (EXISTS)  
**docker-compose**: `core_graph`, port 9004→8004  

**Migration action**: This is the MOST CRITICAL module. Strategy:
1. Service layer: Fill `api/routes.py` with /run endpoint from vitruvyan `main.py`
2. Adapter: Fill `adapters/graph_adapter.py` with graph compilation logic from `graph_flow.py`
3. Domain plugin: EXTEND `graph_plugin.py` (742 LOC exists) to register all 30+ finance nodes
4. State extension: Add ~80 finance-specific state fields as `FinanceStateExtension(TypedDict)`
5. Each vitruvyan node → a function registered via `FinanceGraphPlugin.get_nodes()`
6. CRITICAL: Do NOT hardcode node imports — use plugin registration pattern

---

#### Module 7: Neural Engine — Docker Service (HARDEST)

**vitruvyan source** (`docker/services/api_neural_engine/`, 206 LOC):
```
api_server.py                 ← FastAPI app, /screen endpoint (thin wrapper)
```

**THE REAL LOGIC** (2,861 LOC monolith):
```
vitruvyan/core/logic/neural_engine/engine_core.py  ← 2,861 lines! ALL 14 factors here
```

**core destination** (`services/api_neural_engine/`, scaffolding exists):
```
main.py                         ← FastAPI bootstrap (EXISTS → fill)
config.py                       ← Service config (EXISTS)
api/routes.py                   ← REST endpoints (EXISTS → fill /screen, /health)
adapters/babel_to_neural.py     ← Babel→Neural bridge (EXISTS → fill sentiment integration)
modules/engine_orchestrator.py  ← Engine orchestration (EXISTS → fill with screening logic)
schemas/api_models.py           ← API models (EXISTS → fill)
monitoring/metrics.py           ← Prometheus metrics (EXISTS → fill)
```

**ALSO fill** (core contracts — implement interfaces):
```
core: vitruvyan_core/core/neural_engine/engine.py       ← GenericAggregationEngine (EXISTS contract)
core: vitruvyan_core/core/neural_engine/composite.py    ← Composite scoring (EXISTS)
core: vitruvyan_core/core/neural_engine/ranking.py      ← Ranking (EXISTS)
core: vitruvyan_core/core/neural_engine/scoring.py      ← Scoring (EXISTS)
core: domains/finance/ (NEW)                            ← FinanceDataProvider(IDataProvider)
core: domains/finance/ (NEW)                            ← FinanceScoringStrategy(IScoringStrategy)
```

**Dockerfile**: `infrastructure/docker/dockerfiles/Dockerfile.api_neural` (EXISTS)  
**docker-compose**: `core_neural_engine`, port 9003→8003  

**Migration action**: This is the HARDEST module — decompose 2,861 LOC monolith. Strategy:
1. Service: Fill `api/routes.py` with /screen endpoint from `api_server.py` (206 LOC, thin)
2. Adapter: Fill `adapters/babel_to_neural.py` with sentiment→z-score conversion
3. Orchestrator: Fill `modules/engine_orchestrator.py` with screening orchestration
4. Domain: CREATE `domains/finance/data_provider.py` implementing `IDataProvider` (14 factors)
5. Domain: CREATE `domains/finance/scoring_strategy.py` implementing `IScoringStrategy` (5 profiles)
6. DECOMPOSE: Extract each of the 14 functions (A-L + P + Earnings) from engine_core.py into provider methods
7. CRITICAL: The monolith's SQL queries go into `adapters/` or provider, NOT into core contracts

---

#### Module 8: VPAR (VEE/VARE/VWRE/VSGS) — No Separate Docker Service

**NOTE**: VPAR engines do NOT have their own Docker services in vitruvyan. They are LIBRARIES called by other services (compose_node calls VEE, exec_node calls Neural Engine which uses VARE, etc.)

**vitruvyan source** (scattered across proprietary modules, ~1,560 LOC total):
```
core/logic/vitruvyan_proprietary/vee/vee_engine.py       ← VEE Engine (737 LOC)
core/logic/vitruvyan_proprietary/vee/vee_generator.py    ← VEE narrative generation
core/logic/vitruvyan_proprietary/vee/vee_analyzer.py     ← VEE factor analysis
core/logic/vitruvyan_proprietary/vare_engine.py          ← VARE risk engine (850 LOC)
core/logic/vitruvyan_proprietary/vwre_engine.py          ← VWRE attribution (600+ LOC)
```

**core destination** (contracts already exist, add FinanceProvider):
```
vitruvyan_core/core/vpar/vee/vee_engine.py           ← EXISTS (contract with ExplainabilityProvider)
vitruvyan_core/core/vpar/vee/vee_analyzer.py         ← EXISTS
vitruvyan_core/core/vpar/vee/vee_generator.py        ← EXISTS
vitruvyan_core/core/vpar/vare/vare_engine.py         ← EXISTS (contract with RiskProvider)
vitruvyan_core/core/vpar/vwre/vwre_engine.py         ← EXISTS (contract with AttributionProvider)
vitruvyan_core/core/vpar/vsgs/vsgs_engine.py         ← EXISTS
domains/finance/ (NEW)                                ← FinanceExplainabilityProvider
domains/finance/ (NEW)                                ← FinanceRiskProvider
domains/finance/ (NEW)                                ← FinanceAttributionProvider
```

**No Docker service needed** — VPAR is called as a library by api_graph and api_neural_engine services.

**Migration action**:
1. Read vitruvyan VEE/VARE/VWRE source files (finance-specific logic)
2. CREATE `domains/finance/vee_provider.py` implementing `ExplainabilityProvider` ABC
3. CREATE `domains/finance/vare_provider.py` implementing `RiskProvider` ABC
4. CREATE `domains/finance/vwre_provider.py` implementing `AttributionProvider` ABC
5. These providers contain the finance formulas (z-score ranges, ticker validation, screener integration)
6. Core contracts stay UNTOUCHED — only providers are new

---

### Additional Services (Lower Priority)

These services exist in vitruvyan but NOT yet scaffolded in core:

| Service | vitruvyan LOC | Action |
|---|---|---|
| api_mcp_server | 2,141 LOC (9 files) | Core has Dockerfile.api_mcp → scaffold service |
| api_shadow_traders | 2,324 LOC (3 files) | No core scaffold → CREATE after Phase D |
| api_portfolio_guardian | 685 LOC (1 file) | Core has Dockerfile → scaffold service |
| api_sentinel_agent | 167 LOC (1 file) | MERGE into portfolio_guardian |
| api_conclave | 727 LOC (2 files) | Core has scaffold → fill after Phase B |
| api_pattern_weavers | 167 LOC (1 file) | Core has scaffold → fill after Phase B |

---

## Vitruvyan Source Access

Both repos are on the same machine:
- **vitruvyan-core**: `/home/caravaggio/vitruvyan-core` (YOUR workspace)
- **vitruvyan**: `/home/caravaggio/vitruvyan` (READ-ONLY source of finance logic)

You can read vitruvyan files directly:
```bash
cat /home/caravaggio/vitruvyan/core/logic/neural_engine/engine_core.py | head -100
```

---

## Key Mappings: vitruvyan path → core path

| Vitruvyan Source | Core Destination | Type |
|---|---|---|
| `core/cognitive_bus/` | `vitruvyan_core/core/synaptic_conclave/` | Already migrated (Phase 1) |
| `core/codex_hunters/` | `vitruvyan_core/core/governance/codex_hunters/` + `services/api_codex_hunters/` | Contracts + Service |
| `core/memory_orders/` | `vitruvyan_core/core/governance/memory_orders/` + `services/api_memory_orders/` | Contracts + Service |
| `core/agents/validators/` | `vitruvyan_core/core/governance/orthodoxy_wardens/` + `services/api_orthodoxy_wardens/` | Contracts + Service |
| `core/agents/vault_keepers/` | `vitruvyan_core/core/governance/vault_keepers/` + `services/api_vault_keepers/` | Contracts + Service |
| `core/babel_gardens/` | `vitruvyan_core/core/cognitive/babel_gardens/` + `services/api_babel_gardens/` | Contracts + Service |
| `core/langgraph/` | `vitruvyan_core/core/orchestration/langgraph/` + `services/api_graph/` + `domains/finance/` | Contracts + Service + Domain |
| `core/logic/neural_engine/` | `vitruvyan_core/core/neural_engine/` + `services/api_neural_engine/` | Contracts + Service |
| `core/logic/vitruvyan_proprietary/vee/` | `vitruvyan_core/core/vpar/vee/` | Contracts (add FinanceProvider) |
| `core/logic/vitruvyan_proprietary/vare_engine.py` | `vitruvyan_core/core/vpar/vare/` | Contracts (add FinanceProvider) |
| `core/logic/vitruvyan_proprietary/vwre_engine.py` | `vitruvyan_core/core/vpar/vwre/` | Contracts (add FinanceProvider) |
| `core/pattern_weavers/` | `vitruvyan_core/core/cognitive/pattern_weavers/` + `services/api_pattern_weavers/` | Contracts + Service |
| `docker/services/api_*/` | `services/api_*/` | Service (routes, main.py) |
| (no equivalent) | `domains/finance/` | NEW — finance domain plugin |

---

## Finance-Specific Data to Preserve

### PostgreSQL Tables (from vitruvyan)
```
sentiment_scores        — combined_score, sentiment_tag, ticker, created_at
screener_results        — composite_z, rank, profile, ticker
trend_logs              — technical analysis results  
audit_findings          — orthodoxy audit logs
fundamentals            — 23 columns, revenue/eps/margins/debt
portfolio_holdings      — user portfolio positions
mcp_tool_calls          — MCP audit trail
ledger_anchors          — blockchain anchoring batches
```

### Qdrant Collections (from vitruvyan)
```
phrases_embeddings      — 34,581 points (Reddit/GNews + docs)
conversations_embeddings — 1,422+ points (user chat history)
momentum_vectors        — 519 tickers (RSI/MACD)
trend_vectors           — 517 tickers (SMA/EMA)
phrases_fused           — semantic + affective combined
semantic_clusters       — HDBSCAN clusters
weave_embeddings        — Pattern Weavers concepts
```

### 5 Screening Profiles
```
short_spec      — Short-term speculation
balanced_mid    — Balanced mid-term
momentum_focus  — Momentum-driven
trend_follow    — Trend following
sentiment_boost — Sentiment-weighted
```

### 14 Neural Engine Factors (A-L + P + Earnings)
These are the functions inside engine_core.py that calculate z-scores.
Each must map to `IDataProvider.get_features()` return columns.

### Service Ports (vitruvyan production)
```
8003 — Neural Engine API
8004 — LangGraph orchestration
8006 — Orthodoxy Wardens
8009 — Babel Gardens
8010 — Embedding API
8016 — Memory Orders
8017 — Pattern Weavers
8020 — MCP Server
6333 — Qdrant
6379 — Redis
5432 — PostgreSQL (host machine, NOT Docker)
```

---

## Verification Checklist (per module)

After completing each module, verify:

- [ ] No `psycopg2.connect()` anywhere (use `PostgresAgent`)
- [ ] No `qdrant_client.QdrantClient()` anywhere (use `QdrantAgent`)
- [ ] No hardcoded IPs or passwords (use env vars)
- [ ] All domain types are frozen dataclasses (match core contracts)
- [ ] All bus communication via `StreamBus` (no pub/sub)
- [ ] All finance logic in adapters/ or domains/finance/ (not in core/)
- [ ] Import paths use core's tree structure (e.g., `core.governance.orthodoxy_wardens.domain.verdict`)
- [ ] Docker service builds successfully: `docker compose build <service>`
- [ ] Python imports work: `python -c "from services.api_X import main"`

---

## Context Files

If you need architectural context, read:
- `/home/caravaggio/vitruvyan/.github/copilot-instructions.md` — Complete vitruvyan architecture (30,000+ words)
- `/home/caravaggio/vitruvyan/docs/MERCATOR_GAP_ANALYSIS_PHASES_2_5.md` — Detailed 8-module gap analysis (945 lines)
- `/home/caravaggio/vitruvyan/MERCATOR_REFACTOR_ROADMAP.md` — Phase 1-5 roadmap

---

*Generated: February 21, 2026*
*From: vitruvyan Mercator project (GitHub Copilot + Claude Opus session)*
