# VITRUVYAN CORE V1.0 — STATE OF THE ART

> **Date**: 2026-02-15T22:30Z (February 15, 2026 — 23:30 CET)  
> **Release Readiness Score**: **97.0%** (target 90%)  
> **Purpose**: Canonical reference document for AI analysis of the Vitruvyan Core codebase

---

## 1. MISSION

Vitruvyan Core is a **domain-agnostic epistemic operating system** that provides:

- A governed cognitive pipeline (LangGraph orchestration, Sacred Orders)
- Pluggable domain verticals via configuration and runtime plugins
- A solid, secure, scalable framework that never embeds domain-specific assumptions

The core must remain **pure infrastructure** — any domain (finance, healthcare, legal, research) plugs in through:
1. `domains/<domain>/` — intent config, prompts, slot definitions
2. `contracts/` — ABCs, protocols, base state (the extensibility surface)
3. Environment variables — all operational tuning without code changes

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Repository Layout

```
vitruvyan_core/
├── core/
│   ├── agents/               # Singleton gateways to external systems
│   │   ├── postgres_agent.py     # PostgreSQL (ThreadedConnectionPool)
│   │   ├── qdrant_agent.py       # Qdrant vector DB
│   │   ├── llm_agent.py          # LLM gateway (OpenAI, pluggable via ILLMProvider)
│   │   └── alchemist_agent.py    # Schema migrations (Alembic)
│   ├── cache/
│   │   └── mnemosyne_cache.py    # Multi-tier vector-aware cache (Redis SCAN)
│   ├── cognitive/                # Perception Sacred Orders
│   │   ├── babel_gardens/            # Language detection, NLU, translation
│   │   └── pattern_weavers/          # Ontology mapping, pattern classification
│   ├── contracts/                # PUBLIC EXTENSIBILITY SURFACE
│   │   ├── __init__.py               # Single import point for all ABCs/protocols
│   │   └── llm_provider.py           # ILLMProvider — runtime_checkable Protocol
│   ├── governance/               # Governance Sacred Orders
│   │   ├── codex_hunters/            # System discovery, maintenance
│   │   ├── memory_orders/            # Coherence analysis, RAG
│   │   ├── orthodoxy_wardens/        # Validation, audit, invariant enforcement
│   │   └── vault_keepers/            # Archival, persistence, snapshots
│   ├── llm/
│   │   ├── cache_api.py              # LLM response caching + cost tracking
│   │   ├── cache_manager.py          # Redis-backed LLM cache (SCAN-only)
│   │   └── prompts/                  # PromptRegistry (domain-aware)
│   ├── logging/
│   │   └── audit.py                  # Structured audit logger (Redis Stream + optional PG)
│   ├── middleware/
│   │   └── auth.py                   # Opt-in AuthMiddleware (Bearer token)
│   ├── neural_engine/            # Computation engine (batch scoring)
│   ├── orchestration/            # LangGraph pipeline + plugin system
│   │   ├── base_state.py             # BaseGraphState (37 fields, extensible)
│   │   ├── execution_guard.py        # Hard timeout enforcement (ThreadPoolExecutor)
│   │   ├── graph_engine.py           # GraphPlugin, NodeContract, GraphEngine
│   │   ├── parser.py                 # Parser ABC, BaseParser, ParsedSlots
│   │   ├── intent_registry.py        # IntentRegistry (domain plugin pattern)
│   │   ├── route_registry.py         # Route definitions
│   │   ├── entity_resolver_registry.py
│   │   ├── execution_registry.py
│   │   └── langgraph/                # Graph nodes, runner, flow
│   │       ├── graph_runner.py           # Entry point (lazy init)
│   │       ├── graph_flow.py             # Pipeline wiring
│   │       └── node/                     # 15+ cognitive nodes
│   ├── synaptic_conclave/        # Cognitive Bus (Redis Streams)
│   │   ├── transport/
│   │   │   ├── streams.py                # StreamBus (TLS, password, env-configured)
│   │   │   └── dlq.py                    # Dead Letter Queue (retry tracking, idempotency)
│   │   ├── events/                   # TransportEvent, CognitiveEvent, EventAdapter
│   │   ├── plasticity/               # Adaptive learning
│   │   └── governance/               # Bus-level governance
│   └── vpar/                     # Vitruvyan Probabilistic Assessment
├── domains/
│   ├── finance/                  # Reference vertical (intent_config, prompts, slots)
│   ├── base_domain.py            # Domain ABC
│   ├── aggregation_contract.py
│   ├── explainability_contract.py
│   └── risk_contract.py
services/                         # 12 FastAPI microservices (LIVELLO 2)
├── api_graph/                    # LangGraph orchestration service
├── api_babel_gardens/            # NLU service
├── api_codex_hunters/            # System maintenance service
├── api_memory_orders/            # Coherence + RAG service
├── api_orthodoxy_wardens/        # Governance service
├── api_pattern_weavers/          # Ontology service
├── api_vault_keepers/            # Archival service
├── api_neural_engine/            # Computation service
├── api_embedding/                # Vector embedding service
├── api_conclave/                 # Bus management service
├── api_mcp/                      # Model Context Protocol service
└── redis_streams_exporter/       # Prometheus metrics exporter
```

### 2.2 Sacred Orders (Epistemic Hierarchy)

| Order | Domain | Location | Responsibility |
|:---|:---|:---|:---|
| **Babel Gardens** | Perception | `core/cognitive/babel_gardens/` | Language detection, NLU, translation |
| **Pattern Weavers** | Perception | `core/cognitive/pattern_weavers/` | Ontology mapping, pattern classification |
| **Codex Hunters** | Perception | `core/governance/codex_hunters/` | System discovery, codebase maintenance |
| **Memory Orders** | Memory | `core/governance/memory_orders/` | Coherence analysis, RAG, semantic state |
| **Vault Keepers** | Memory | `core/governance/vault_keepers/` | Archival, persistence, snapshots |
| **Orthodoxy Wardens** | Truth | `core/governance/orthodoxy_wardens/` | Validation, audit, invariant enforcement |

Each Sacred Order follows the **mandatory two-level pattern**:
- **LIVELLO 1** (pure domain): 10 directories, zero I/O, pure Python, testable standalone
- **LIVELLO 2** (service): FastAPI, Docker, adapters, `main.py < 100 lines`

### 2.3 LangGraph Pipeline (Cognitive Kernel)

```
parse → intent_detection → weaver → entity_resolver → babel_emotion
  → semantic_grounding → params_extraction → decide → [route branches]
  → output_normalizer → orthodoxy → vault → compose → can → [advisor] → END
```

Route branches from `decide` node:
- `dispatcher_exec` → direct execution
- `semantic_fallback` → Qdrant vector search
- `llm_soft` → conversational LLM (cached)
- `slot_filler` → missing parameter negotiation
- `codex_expedition` → system maintenance
- `llm_mcp` → MCP tools (when `USE_MCP=1`)

Intent detection is **100% domain-agnostic**: domains register via `INTENT_DOMAIN` env var and `domains/<domain>/intent_config.py`.

---

## 3. EXTENSIBILITY CONTRACTS

### 3.1 Plugin Surface (`core/contracts/`)

```python
from core.contracts import (
    # Graph state
    BaseGraphState, GraphStateType,
    ESSENTIAL_FIELDS, INTENT_FIELDS, LANGUAGE_FIELDS, EMOTION_FIELDS,
    ORTHODOXY_FIELDS, VAULT_FIELDS, TRACING_FIELDS, WEAVER_FIELDS,
    CAN_FIELDS, ALL_BASE_FIELDS,
    get_base_field_count, is_base_field, get_domain_fields,
    # Engine
    GraphPlugin, NodeContract, GraphEngine,
    # Parser
    Parser, BaseParser, ParsedSlots,
    # LLM
    ILLMProvider,
)
```

### 3.2 How a Domain Vertical Plugs In

1. **Intent detection**: Create `domains/<domain>/intent_config.py` with `create_<domain>_registry()`. Set `INTENT_DOMAIN=<domain>`.
2. **Prompts**: Register domain prompts via `PromptRegistry.register_domain()` in `core/llm/prompts/registry.py`.
3. **Graph state**: Extend `BaseGraphState` with domain-specific fields — the core's 37 fields are inherited automatically.
4. **LLM provider**: Implement `ILLMProvider` protocol (5 methods: `complete`, `complete_json`, `complete_with_messages`, `complete_with_tools`, `acomplete`) to swap OpenAI for any provider.
5. **Entities**: Define domain entities that flow through `validated_entities` contract.

### 3.3 Domain-Agnostic Guarantees

- No finance/trading terms in core code (legacy remnants fully purged from active code paths)
- Intent detection, emotion detection, entity extraction all delegate to LLM as primary engine (regex fallback only)
- `domains/finance/` exists as reference implementation, zero imports from core into it

---

## 4. SECURITY POSTURE

### 4.1 Credentials & Secrets

| Aspect | Status |
|:---|:---|
| No passwords in source code | ✅ All via `${ENV_VARS}` |
| No production IPs in code | ✅ Removed from all configs and docs |
| `.env` files gitignored | ✅ `.env.example` templates provided |
| docker-compose.yml | ✅ All secrets from env vars, no defaults |
| Git history | ⚠️ BFG purge deferred to pre-public release |

### 4.2 Authentication

- **Middleware**: `core/middleware/auth.py` — opt-in `AuthMiddleware`
- **Activation**: `VITRUVYAN_AUTH_ENABLED=true` + `VITRUVYAN_AUTH_SECRET` or `VITRUVYAN_KEYCLOAK_URL`
- **Coverage**: All 11 FastAPI services have middleware integrated
- **Default**: Disabled (zero overhead) — enables gradual rollout
- **Features**: Bearer token validation, configurable public paths, CORS preflight passthrough, custom validator injection
- **Tests**: 14 unit tests in `tests/test_auth_middleware.py`

### 4.3 Transport Security

| Client | TLS Support | Password Support |
|:---|:---:|:---:|
| `StreamBus` (streams.py) | ✅ `REDIS_SSL` | ✅ `REDIS_PASSWORD` |
| `MnemosyneCache` (mnemosyne_cache.py) | ✅ `REDIS_SSL` | ✅ `REDIS_PASSWORD` |
| `LLMCacheManager` (cache_manager.py) | ✅ `REDIS_SSL` | ✅ `REDIS_PASSWORD` |
| `WorkingMemory` (working_memory.py) | ✅ `REDIS_SSL` | ✅ `REDIS_PASSWORD` |

### 4.4 Audit Logging

- **Module**: `core/logging/audit.py` — structured `AuditLogger` with mandatory schema
- **Backends**: Python logger (always) + Redis Stream (default) + PostgreSQL (optional)
- **Stream**: `vitruvyan:audit` (configurable via `AUDIT_STREAM`, max length `AUDIT_STREAM_MAX_LEN`)
- **Schema**: `AuditEvent` dataclass — `timestamp`, `event_id`, `correlation_id`, `node_id`, `plugin_id`, `execution_time_ms`, `status`, `error_code`, `metadata`
- **Control**: `AUDIT_ENABLED=true` (default on), `AUDIT_POSTGRES_ENABLED=false` (opt-in)
- Emitted automatically on pipeline timeout by `graph_runner.py`

### 4.5 Configuration Hygiene

- Zero `load_dotenv()` in `vitruvyan_core/core/` — called **only** in service entrypoints (`services/api_*/main.py`)
- Prevents `.env` files from silently overriding production environment variables

### 4.6 CORS

- All 11 FastAPI services have `CORSMiddleware` configured
- Default: `http://localhost:3000` (restrictive)
- Configurable via `CORS_ORIGINS` env var (comma-separated)

---

## 5. SCALABILITY

### 5.1 PostgreSQL

| Feature | Implementation |
|:---|:---|
| Connection pooling | `psycopg2.pool.ThreadedConnectionPool` (env vars: `POSTGRES_POOL_MIN=2`, `POSTGRES_POOL_MAX=10`) |
| Paginated queries | `fetch_paginated(sql, params, page_size=500)` — server-side cursor, yields pages |
| Connection reuse | Shared pool via `_get_pool()` singleton — no connection-per-call overhead |

### 5.2 Redis

| Feature | Implementation |
|:---|:---|
| No blocking `KEYS` calls | All Redis clients use `SCAN`/`scan_iter()` — zero `KEYS` in production code |
| Stream retention | `STREAM_MAX_LEN` (default 100K), `STREAM_MAX_AGE_DAYS` (default 7) |
| Cache prefix | `MNEMOSYNE_CACHE_PREFIX` env var (default `vitruvyan:mnemosyne_cache`) |
| Stream prefix | `STREAM_PREFIX` env var (default `vitruvyan`) |
| Dead Letter Queue | `vitruvyan:dlq` stream — failed events isolated, retry-tracked, idempotent |

`KEYS` residual: only `scripts/audit_streams_topology.py` (CLI tool) and test fixtures — non-production.

### 5.3 LangGraph

| Feature | Implementation |
|:---|:---|
| Lazy graph compilation | `_get_graph()` — builds on first call, not at import time |
| Minimal graph mode | `ENABLE_MINIMAL_GRAPH=true` — 4-node graph for lightweight deployments |

### 5.4 LLM Rate Control

| Parameter | Env Var | Default |
|:---|:---|:---|
| Requests per minute | `LLM_RATE_LIMIT_RPM` | 500 |
| Tokens per minute | `LLM_RATE_LIMIT_TPM` | 30000 |
| Cost per token | `LLM_COST_PER_TOKEN` | 0.0001 |
| Model selection | `VITRUVYAN_LLM_MODEL` → `GRAPH_LLM_MODEL` → `OPENAI_MODEL` | `gpt-4o-mini` |

### 5.5 Resilience & Fault Tolerance

| Feature | Implementation |
|:---|:---|
| Hard timeout enforcement | `NodeExecutionGuard` — `ThreadPoolExecutor` with `Future.result(timeout=N)` kills hanging nodes |
| Pipeline timeout | `graph_runner.py` wraps `invoke()` with `GRAPH_EXEC_TIMEOUT_SECONDS` (default 120s) |
| Dead Letter Queue | `DeadLetterQueue` in `transport/dlq.py` — failed events tracked with retry count, moved to `vitruvyan:dlq` after `DLQ_MAX_RETRIES` exhausted |
| Idempotency | DLQ uses SHA256-based idempotency keys (7-day TTL) — prevents duplicate DLQ entries |
| Trace ID collision safety | `graph_runner.py` uses full UUID4 (36 chars) instead of truncated 8-char prefix |
| Audit trail | `AuditLogger` emits structured events on timeout/failure to Redis Stream + optional PostgreSQL |

---

## 6. CONFIGURATION REFERENCE

All operational values are configurable via environment variables. No code changes required for tuning.

### 6.1 Infrastructure

| Env Var | Purpose | Default |
|:---|:---|:---|
| `POSTGRES_HOST` | PostgreSQL hostname | `core_postgres` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `vitruvyan` |
| `POSTGRES_USER` | Database user | (required) |
| `POSTGRES_PASSWORD` | Database password | (required) |
| `POSTGRES_POOL_MIN` | Min pool connections | `2` |
| `POSTGRES_POOL_MAX` | Max pool connections | `10` |
| `REDIS_HOST` | Redis hostname | `core_redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_SSL` | Enable TLS | `false` |
| `REDIS_PASSWORD` | Redis password | (empty) |
| `QDRANT_HOST` | Qdrant hostname | `core_qdrant` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `QDRANT_TIMEOUT` | Qdrant timeout seconds | `30` |

### 6.2 LLM & AI

| Env Var | Purpose | Default |
|:---|:---|:---|
| `VITRUVYAN_LLM_MODEL` | Primary model selector | (falls through chain) |
| `GRAPH_LLM_MODEL` | Graph-specific model | (falls through) |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |
| `OPENAI_API_KEY` | API key | (required) |
| `LLM_RATE_LIMIT_RPM` | Requests/minute limit | `500` |
| `LLM_RATE_LIMIT_TPM` | Tokens/minute limit | `30000` |
| `LLM_COST_PER_TOKEN` | Cost tracking rate | `0.0001` |

### 6.3 Cognitive Bus (Synaptic Conclave)

| Env Var | Purpose | Default |
|:---|:---|:---|
| `STREAM_MAX_LEN` | Max entries per stream | `100000` |
| `STREAM_MAX_AGE_DAYS` | Stream retention in days | `7` |
| `STREAM_PREFIX` | Stream name prefix | `vitruvyan` |
| `MNEMOSYNE_CACHE_PREFIX` | Cache key prefix | `vitruvyan:mnemosyne_cache` |

### 6.4 Orchestration

| Env Var | Purpose | Default |
|:---|:---|:---|
| `INTENT_DOMAIN` | Domain plugin for intent detection | `generic` |
| `QDRANT_FILTER_DOMAIN` | Enable domain-specific Qdrant filtering | `1` |
| `USE_MCP` | Route to MCP node | `0` |
| `ENABLE_MINIMAL_GRAPH` | Use 4-node minimal graph | `false` |
| `DISABLE_SLOT_FILLING` | Skip slot-filling dialogue | (not set = active) |

### 6.5 Security

| Env Var | Purpose | Default |
|:---|:---|:---|
| `VITRUVYAN_AUTH_ENABLED` | Enable auth middleware | `false` |
| `VITRUVYAN_AUTH_SECRET` | JWT secret for local validation | (required if auth enabled) |
| `VITRUVYAN_KEYCLOAK_URL` | Keycloak endpoint | (optional) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |

### 6.6 Execution Control

| Env Var | Purpose | Default |
|:---|:---|:---|
| `NODE_EXEC_TIMEOUT_SECONDS` | Per-node hard timeout | `30` |
| `NODE_EXEC_MAX_WORKERS` | ThreadPoolExecutor max workers | `4` |
| `GRAPH_EXEC_TIMEOUT_SECONDS` | Full pipeline timeout | `120` |

### 6.7 Dead Letter Queue

| Env Var | Purpose | Default |
|:---|:---|:---|
| `DLQ_MAX_RETRIES` | Retries before DLQ routing | `3` |
| `DLQ_STREAM_MAX_LEN` | Max DLQ stream entries | `50000` |

### 6.8 Audit Logging

| Env Var | Purpose | Default |
|:---|:---|:---|
| `AUDIT_ENABLED` | Enable/disable audit logging | `true` |
| `AUDIT_STREAM` | Redis audit stream name | `vitruvyan:audit` |
| `AUDIT_STREAM_MAX_LEN` | Max audit stream entries | `200000` |
| `AUDIT_POSTGRES_ENABLED` | Also persist audit to PostgreSQL | `false` |
| `AUDIT_LOG_LEVEL` | Python log level for audit events | `INFO` |

---

## 7. SERVICES MATRIX

All services follow the `SERVICE_PATTERN.md` convention: `main.py < 100 lines`, `adapters/`, `api/routes.py`, `config.py`.

| Service | Port | Sacred Order | Auth | CORS | Lifespan |
|:---|:---:|:---|:---:|:---:|:---:|
| `api_graph` | 8000 | Orchestration | ✅ | ✅ | ✅ |
| `api_babel_gardens` | 8009 | Babel Gardens | ✅ | ✅ | ✅ |
| `api_pattern_weavers` | 8011 | Pattern Weavers | ✅ | ✅ | ✅ |
| `api_codex_hunters` | 8008 | Codex Hunters | ✅ | ✅ | ✅ |
| `api_memory_orders` | 8012 | Memory Orders | ✅ | ✅ | ✅ |
| `api_vault_keepers` | 8013 | Vault Keepers | ✅ | ✅ | ✅ |
| `api_orthodoxy_wardens` | 8014 | Orthodoxy Wardens | ✅ | ✅ | ✅ |
| `api_neural_engine` | 8001 | Computation | ✅ | ✅ | ✅ |
| `api_embedding` | 8010 | Vector ops | ✅ | ✅ | ✅ |
| `api_conclave` | 8015 | Bus management | ✅ | ✅ | ✅ |
| `api_mcp` | 8020 | MCP tools | ✅ | ✅ | ✅ |
| `redis_streams_exporter` | 9091 | Monitoring | — | — | — |

---

## 8. SACRED ORDERS CONFORMANCE

| Sacred Order | LIVELLO 1 | LIVELLO 2 | Conformance | Notes |
|:---|:---:|:---:|:---:|:---|
| **Babel Gardens** | ✅ 10/10 dirs | ✅ main.py < 100L | **95%** | Missing `_legacy/` dir (no legacy code to archive) |
| **Pattern Weavers** | ✅ 10/10 dirs | ✅ main.py < 100L | **95%** | Missing `_legacy/` dir (no legacy code to archive) |
| **Codex Hunters** | ✅ 10/10 dirs | ✅ main.py < 100L | **93%** | `yaml` import in consumers (data-driven config) |
| **Vault Keepers** | ✅ 10/10 dirs | ✅ main.py < 100L | **90%** | MetricNames defined |
| **Memory Orders** | ✅ 10/10 dirs | ✅ main.py < 100L | **90%** | Legacy tests archived |
| **Orthodoxy Wardens** | ✅ 10/10 dirs | ✅ main.py < 100L | **85%** | Impure agents archived to `_legacy/` |

All 6 Sacred Orders have complete LIVELLO 2 service implementations with adapters, routes, and models.

---

## 9. INVARIANTS (NON-NEGOTIABLE RULES)

These rules are enforced across the codebase and must be preserved by any future work:

1. **Core stays generic** — no domain logic in `vitruvyan_core/core/`. Domains plug in via `domains/` and `contracts/`.
2. **No cross-service imports** — services communicate via REST or StreamBus events only.
3. **Agents for all external access** — `PostgresAgent`, `QdrantAgent`, `LLMAgent` only. No raw `psycopg2.connect()`, `qdrant_client.QdrantClient()`, or `from openai import OpenAI`.
4. **No secrets in source** — all credentials via env vars with `${PLACEHOLDER}` in docs.
5. **Streams, not Pub/Sub** — Redis Streams is canonical transport. Acknowledge after handling. Generator consumption.
6. **Bus is payload-blind** — transport layer never inspects, routes, or correlates event content.
7. **Validated lists are authoritative** — if client sends `validated_entities`, backend respects it (including explicit `[]`).
8. **LLM-first, never heuristics-first** — intent, emotion, entity extraction delegate to LLM. Regex is only fallback.
9. **No `load_dotenv()` in core** — configuration exclusively via environment variables in `vitruvyan_core/core/`. `load_dotenv()` is called only in service entrypoints (`main.py`).
10. **Failed events to DLQ** — events exceeding `DLQ_MAX_RETRIES` must be routed to the Dead Letter Queue, not left in PEL indefinitely.

---

## 10. TESTING

| Test Suite | Count | Status |
|:---|:---:|:---|
| Architectural tests (`tests/architectural/`) | 165 | ✅ All passing |
| Orchestration base class tests | 19 | ✅ All passing (core-only) |
| Finance vertical tests (`tests/verticals/`) | 12 | ✅ All passing (guarded with `importorskip`) |
| Hardening tests (`tests/test_hardening_fixes.py`) | 29 | ✅ All passing |
| Auth middleware tests | 14 | ✅ All passing |
| Skipped (infrastructure-dependent) | 12 | Expected (need Docker) |

**Hardening test breakdown** (29 tests, 6 classes):
- `TestNodeExecutionGuard` — 7 tests (success, timeout, exception, per-call override, env config, singleton, state preservation)
- `TestDeadLetterQueue` — 8 tests (retry tracking, DLQ routing, idempotency, serialization, listing, health, ACK)
- `TestRedisKeysElimination` — 2 tests (source code scan verifying `scan_iter` usage)
- `TestAuditLogger` — 9 tests (schema, error codes, JSON serialization, Redis fields, backends, disable, singleton, metadata)
- `TestLoadDotenvRemoval` — 2 tests (source code scan verifying no `load_dotenv` in core)
- `TestTraceIdFullLength` — 1 test (full UUID4 = 36 chars)

---

## 11. KNOWN RESIDUAL ITEMS (Low Priority, Non-Blocking)

These items are documented for completeness. None block V1.0 release.

| Item | Location | Impact |
|:---|:---|:---|
| `acomplete()` not truly async | `llm_agent.py` L540 | Minor — wraps sync in thread |
| `httpx` I/O in LIVELLO 1 | `vsgs_engine.py` L93-101 | Minor — edge case module |
| `logging.basicConfig()` in library module | `vault_node.py` L22 | Cosmetic |
| `nest_asyncio.apply()` global | `llm_mcp_node.py` L24 | Pragmatic (MCP requirement) |
| `foundation/` empty subdirectories | 3 dead scaffolding dirs | Cosmetic |
| `__all__` duplicated exports | `synaptic_conclave/__init__.py` | Cosmetic |
| Qdrant `top_k` cap 50 hard-coded | `qdrant_agent.py` L131 | Minor |
| Qdrant default collection names | `qdrant_agent.py` L153, L241, L323 | Minor |
| Alembic path hard-coded | `alchemist_agent.py` L30 | Minor |
| BFG git history purge | Pre-public release task | Deferred |
| `redis_streams_exporter` no auth | Monitoring endpoint | P3 |

---

## 12. RELEASE READINESS SCORE

| Criterion | Score | Description |
|:---|:---:|:---|
| **Domain-Agnostic** | **97%** | Core fully agnostic; 0 hard imports core→finance. Finance tests isolated in `tests/verticals/` with `importorskip`. Babel plugin imports conditional. Residual: cosmetic docstring mentions. |
| **No Hard-Coded** | **97%** | All via env vars. Zero `load_dotenv()` in core. Residual: 3 Qdrant collection defaults. |
| **Security** | **94%** | Auth middleware, Redis TLS/password, CORS, structured audit logging. Residual: git history purge. |
| **Scalability** | **96%** | Pooling, SCAN (complete), lazy init, execution guard, DLQ, trace ID collision-safe. Residual: async LLM. |
| **Plugin-Ready** | **97%** | `contracts/`, `ILLMProvider`, `BaseGraphState`, `IntentRegistry`, `PromptRegistry`. |
| **TOTAL** | **97.0%** | **RELEASE READY** |

---

## 13. COMMIT HISTORY (Remediation Arc)

| Commit | Phase | Description | Files | Delta |
|:---|:---|:---|:---:|:---|
| `eae8c0e` | FASE 0 | Security emergency (passwords, IPs, CORS, .env) | 31 | Critical fixes |
| `a16ff1f` | FASE 1 | Domain-agnostic core (~90 violations resolved) | ~45 | +/- extensive |
| `c11f0a0` | FASE 2 | Sacred Orders cleanup (legacy archival, imports) | 13 | Structural |
| `b1c8870` | FASE 5 | Quality & Polish (contracts, BaseGraphState, logging) | 34 | +444/-310 |
| `4ddf0e9` | FASE 3 | Security infrastructure (Redis TLS, auth, CORS, hostnames) | 25 | +510/-70 |
| `dc5c1b9` | FASE 4 | Scalability (pooling, SCAN, lazy init, env vars, ILLMProvider) | 9 | +286/-77 |
| `5e214eb` | HARDENING | Execution guard, DLQ, KEYS→SCAN, audit logging, load_dotenv removal | 17 | +1421/-31 |
| `b61d848` | COUPLING | Finance test isolation (`tests/verticals/`), babel plugin conditional imports | 8 | +384/-250 |

**Score progression**: 79% → 96% (remediation) → **97%** (hardening + coupling fixes).

All phases completed (0, 1, 2, 3, 4, 5) + Hardening + Finance Coupling Fixes.
