# VITRUVYAN CORE V1.0 — AUDIT DI RILASCIO

> **Data**: 15 Febbraio 2026  
> **Score attuale**: **79.0%** — Target minimo: **90%**  
> **FASE 1 completata**: Core domain-agnostic al 95% (~45 file, ~90 violazioni risolte)  
> **Restano**: FASE 0 (Sicurezza), FASE 2 (Sacred Orders), FASE 3 (Infrastruttura), FASE 4 (Scalabilità), FASE 5 (Qualità)

---

## STATO PER CRITERIO

| Criterio | Attuale | Target | Gap |
|:---|:---:|:---:|:---:|
| **Domain-Agnostic** | **95%** ✅ | 98% | Solo commenti/docstring residui |
| **No Hard-Coded** | **75%** | 96% | Password, IP, valori fissi |
| **Sicurezza** | **55%** 🔴 | 95% | Password esposta, no auth, no TLS Redis, CORS `*` |
| **Scalabilità** | **78%** | 93% | No pooling, `fetchall()`, `KEYS` O(N) |
| **Plugin-Ready** | **92%** ✅ | 95% | `contracts/` dir mancante, `BaseGraphState` extend |

---

## VIOLAZIONI CRITICHE APERTE

### 🔴 SEC-01: PASSWORD DATABASE NEL CODICE
- **File**: [orthodoxy_db_manager.py](services/api_orthodoxy_wardens/adapters/orthodoxy_db_manager.py) L39
- Password `@Caravaggio971_omni` hard-coded come default in `psycopg2.connect()`
- **Fix**: `os.getenv("POSTGRES_PASSWORD", "")` + ruotare password in produzione

### 🔴 SEC-02: IP PRODUZIONE NEL CODICE
- **File**: [api_graph/config.py](services/api_graph/config.py) L31-32, [api_orthodoxy_wardens/config.py](services/api_orthodoxy_wardens/config.py) L38
- IP VPS `161.97.140.157` hard-coded in CORS e Postgres config
- **Fix**: env var `CORS_ALLOWED_ORIGINS`, `POSTGRES_HOST`

### 🔴 SEC-03: CORS WILDCARD
- **File**: [api_neural_engine/config.py](services/api_neural_engine/config.py) L7
- `CORS_ORIGINS = "*"`
- **Fix**: whitelist via env var

### 🔴 SEC-04: ZERO AUTENTICAZIONE
- Tutti i 12 servizi senza middleware auth (no API key, no JWT, no OAuth)
- **Fix**: middleware auth condiviso in `vitruvyan_core/core/`

### 🔴 SEC-05: REDIS SENZA TLS/PASSWORD
- StreamBus, LLMCacheManager, WorkingMemory — nessun supporto TLS, `LLMCacheManager` ignora `REDIS_PASSWORD`
- **Fix**: supporto `REDIS_SSL=true` + `REDIS_PASSWORD` per tutti i client

### 🔴 STR-01: ORTHODOXY WARDENS LIVELLO 1 VIOLATO
- `confessor_agent.py` (1006L) e `inquisitor_agent.py` (569L) contengono LangGraph, LLM agent, file I/O in LIVELLO 1 Pure Domain
- **Fix**: spostare in `services/api_orthodoxy_wardens/adapters/` o `_legacy/`

---

## HARD-CODED VALUES (MEDIUM)

### Hostname inconsistenti tra servizi
| Prefisso | Servizi |
|----------|---------|
| `core_*` | api_graph, api_memory_orders, api_vault_keepers |
| `omni_*` | api_conclave, api_mcp, api_orthodoxy_wardens |
| `172.17.0.1` | api_codex_hunters |
| `localhost` | api_babel_gardens, api_pattern_weavers, api_embedding |

**Fix**: standardizzare su `core_*`, centralizzare in `config/api_config.py`.

### Hostname hard-coded nei nodi
| Nodo | Default |
|------|---------|
| intent_detection_node.py | `http://vitruvyan_babel_gardens:8009` |
| emotion_detector.py | `http://babel_gardens:8009` |
| llm_mcp_node.py | `http://omni_mcp:8020` |
| qdrant_node.py | `http://localhost:8010` |
| codex_hunters_node.py | `http://localhost:8008` |

### Valori operativi fissi
| Valore | File | Fix |
|--------|------|-----|
| `timeout=30` (ignora env var) | [qdrant_agent.py](vitruvyan_core/core/agents/qdrant_agent.py) L46 | `timeout=timeout` |
| `top_k` cap 50 | [qdrant_agent.py](vitruvyan_core/core/agents/qdrant_agent.py) L131 | Rendere configurabile |
| Collection `"phrases_embeddings"` | [qdrant_agent.py](vitruvyan_core/core/agents/qdrant_agent.py) L153 | Rendere obbligatorio |
| Collection `"semantic_states"` | [qdrant_agent.py](vitruvyan_core/core/agents/qdrant_agent.py) L241, L323 | Idem |
| Stream retention 100K / 7gg | [streams.py](vitruvyan_core/core/synaptic_conclave/transport/streams.py) L100-101 | Env vars |
| `cost_per_token = 0.0001` | [cache_api.py](vitruvyan_core/core/llm/cache_api.py) L180 | Env var |
| `rpm=500, tpm=30_000` | [llm_agent.py](vitruvyan_core/core/agents/llm_agent.py) L101-102 | Env vars |
| `"vitruvyan"` stream prefix | [streams.py](vitruvyan_core/core/synaptic_conclave/transport/streams.py) L137 | Env var |
| Cache prefix `"vitruvyan:mnemosyne_cache"` | [mnemosyne_cache.py](vitruvyan_core/core/cache/mnemosyne_cache.py) L91 | Configurabile |
| Alembic path hard-coded | [alchemist_agent.py](vitruvyan_core/core/agents/alchemist_agent.py) L30 | Parametro obbligatorio |
| `POSTGRES_PASSWORD = "your_password"` | [api_graph/config.py](services/api_graph/config.py) L40 | Default `""` |

---

## SCALABILITÀ

| Problema | File | Severità |
|----------|------|----------|
| `fetchall()` senza paginazione | [postgres_agent.py](vitruvyan_core/core/agents/postgres_agent.py) L131 | **HIGH** |
| No connection pooling PostgreSQL | [postgres_agent.py](vitruvyan_core/core/agents/postgres_agent.py) L76-80 | **HIGH** |
| `get_postgres()` crea connessione ogni call | [postgres_agent.py](vitruvyan_core/core/agents/postgres_agent.py) L242 | **MEDIUM** |
| `redis.keys()` O(N) blocking | [mnemosyne_cache.py](vitruvyan_core/core/cache/mnemosyne_cache.py) L282-284 | **MEDIUM** |
| `acomplete()` non è vero async | [llm_agent.py](vitruvyan_core/core/agents/llm_agent.py) L540 | **MEDIUM** |
| Graph compilato a import-time | [graph_runner.py](vitruvyan_core/core/orchestration/langgraph/graph_runner.py) L37-38 | **HIGH** |
| httpx I/O in LIVELLO 1 VSGS | [vsgs_engine.py](vitruvyan_core/core/vpar/vsgs/vsgs_engine.py) L93-101 | **MEDIUM** |

---

## PLUGIN — ITEMS APERTI

| Problema | Severità |
|----------|----------|
| Directory `contracts/` non esiste — creare + `ParserContract` formale | **MEDIUM** |
| `GraphState` estende `TypedDict` direttamente — implementare `BaseGraphState` + plugin injection | **MEDIUM** |

---

## SACRED ORDERS CONFORMANCE

| Sacred Order | Location | Problemi | Conformance |
|:---|:---|:---|---:|
| **Babel Gardens** | `core/cognitive/` | Manca `_legacy/` dir | **95%** |
| **Pattern Weavers** | `core/cognitive/` | Manca `_legacy/` dir | **95%** |
| **Codex Hunters** | `core/governance/` | Import yaml in consumers | **93%** |
| **Vault Keepers** | `core/governance/` | Tests import infra | **85%** |
| **Memory Orders** | `core/governance/` | `__init__.py.bak` residuo; `test_memory_orders_cycle.py` (692L) importa API rimosse → crash | **78%** |
| **Orthodoxy Wardens** | `core/governance/` | `confessor_agent.py` 1006L con LangGraph+LLM in LIVELLO 1 | **65%** |

**Note**:
- `copilot-instructions.md` indica erroneamente `governance/babel_gardens/` e `governance/pattern_weavers/` — sono in `cognitive/`
- LIVELLO 2: tutti i 6 servizi conformi (main.py < 100 righe, adapters/ completo)

---

## SERVIZI — SICUREZZA

| Servizio | Sicurezza | Priorità |
|:---|:---|:---:|
| api_orthodoxy_wardens | 🔴 Password esposta, no CORS, psycopg2 diretto | **P0** |
| api_graph | 🔴 IP prod, `"your_password"`, CORS hardcoded | **P0** |
| api_neural_engine | 🔴 CORS `*` | **P1** |
| api_mcp | ⚠️ No auth | **P1** |
| api_conclave | ⚠️ No CORS | **P2** |
| api_babel_gardens | ✅ CORS via env | **P2** |
| api_codex_hunters | ⚠️ `172.17.0.1` default | **P3** |
| api_memory_orders | ⚠️ No CORS | **P3** |
| api_pattern_weavers | ⚠️ No CORS | **P3** |
| api_vault_keepers | ⚠️ No CORS | **P3** |
| api_embedding | ✅ | **P3** |
| redis_streams_exporter | ⚠️ No auth metrics | **P3** |

---

## PROBLEMI ARCHITETTURALI

### Import rotti
| File | Problema |
|------|----------|
| [plasticity/observer.py](vitruvyan_core/core/synaptic_conclave/plasticity/observer.py) L37 | `from core.leo.postgres_agent` → path non esiste, va `core.agents` |
| [plasticity/outcome_tracker.py](vitruvyan_core/core/synaptic_conclave/plasticity/outcome_tracker.py) L21 | Stesso path stale `core.leo` |
| [governance/rite_of_validation.py](vitruvyan_core/core/synaptic_conclave/governance/rite_of_validation.py) | **Rotto** — importa 6 API rimosse (`get_heart`, `get_herald`, ecc.). Crash garantito. |

### Qualità codice
| Problema | Dove |
|----------|------|
| 21 `print()` di debug | graph_runner.py (7), graph_flow.py (14) |
| `import pickle` inutilizzato | [cache_manager.py](vitruvyan_core/core/llm/cache_manager.py) L11 |
| `logging.basicConfig()` in modulo libreria | [vault_node.py](vitruvyan_core/core/orchestration/langgraph/node/vault_node.py) L22 |
| `load_dotenv()` in 4+ nodi individuali | compose_node, can_node, params_extraction_node, cached_llm_node |
| `nest_asyncio.apply()` globale | [llm_mcp_node.py](vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py) L24 |
| Docstring `"Vitruvyan AI Trading Advisor"` | [langgraph/__init__.py](vitruvyan_core/core/orchestration/langgraph/__init__.py) L8 |
| Test file dentro `node/` | [test_route_node.py](vitruvyan_core/core/orchestration/langgraph/node/test_route_node.py) |
| Commenti italiano nel core | qdrant_agent.py |
| `@app.on_event("startup")` deprecato | api_conclave, api_graph, api_memory_orders, api_orthodoxy_wardens, api_vault_keepers |
| `foundation/` vuoto | 3 sottodirectory vuote (dead scaffolding) |
| `__all__` duplicato + phantom exports | [synaptic_conclave/__init__.py](vitruvyan_core/core/synaptic_conclave/__init__.py) L35-53 |
| Cross-service ref in docstring | [babel_to_neural.py](services/api_neural_engine/adapters/babel_to_neural.py) L268 (non runtime) |

---

## PIANO DI REMEDIATION

### FASE 0 — EMERGENZA SICUREZZA (ore)

| # | Azione | File | Effort |
|:---:|--------|------|:---:|
| 1 | Rimuovere password `@Caravaggio971_omni` | orthodoxy_db_manager.py | 5 min |
| 2 | Rimuovere IP `161.97.140.157` | api_graph, api_orthodoxy_wardens config.py | 5 min |
| 3 | CORS `"*"` → env var whitelist | api_neural_engine/config.py | 10 min |
| 4 | Default `"your_password"` → `""` | api_graph/config.py | 2 min |
| 5 | `psycopg2.connect()` → `PostgresAgent` | orthodoxy_db_manager.py | 30 min |
| 6 | Rimuovere `import pickle` inutilizzato | cache_manager.py | 2 min |

### FASE 2 — SACRED ORDERS CLEANUP (1 giorno)

| # | Azione | Effort |
|:---:|--------|:---:|
| 18 | Spostare `confessor_agent.py` (1006L) in `_legacy/` o `services/` | 30 min |
| 19 | Spostare `inquisitor_agent.py` (569L) in `_legacy/` | 15 min |
| 20 | Rimuovere stub re-export da `code_analyzer.py`, `penitent_agent.py` | 15 min |
| 21 | Spostare `test_memory_orders_cycle.py` (692L, imports rotti) in `_legacy/` | 5 min |
| 22 | Spostare `test_vault_cycle.py` in `_legacy/` | 5 min |
| 23 | Spostare `rite_of_validation.py` (rotto) in `_legacy/` | 5 min |
| 24 | Fix import `core.leo.postgres_agent` → `core.agents.postgres_agent` | 10 min |
| 25 | Definire `MetricNames` in vault_keepers/monitoring/ | 30 min |
| 26 | Rimuovere `__init__.py.bak` da memory_orders | 2 min |

### FASE 3 — SICUREZZA INFRASTRUTTURALE (1 giorno)

| # | Azione | Effort |
|:---:|--------|:---:|
| 27 | Supporto `REDIS_SSL` in StreamBus, WorkingMemory, LLMCacheManager | 2h |
| 28 | `REDIS_PASSWORD` in LLMCacheManager | 15 min |
| 29 | Middleware auth condiviso (API key header) | 4h |
| 30 | CORS middleware ai 5 servizi mancanti | 1h |
| 31 | Standardizzare hostname su `core_*` in tutti i servizi | 1h |
| 32 | Centralizzare hostname nodi in `config/api_config.py` | 1h |

### FASE 4 — SCALABILITÀ (2-3 giorni)

| # | Azione | Effort |
|:---:|--------|:---:|
| 33 | `PostgresAgent`: connection pooling | 4h |
| 34 | `PostgresAgent`: `fetch_paginated()` | 2h |
| 35 | `mnemosyne_cache.py`: `KEYS` → `SCAN` | 1h |
| 36 | Lazy init graph in `graph_runner.py` | 1h |
| 37 | Fix `qdrant_agent.py` timeout env var ignorato | 5 min |
| 38 | Configurare stream retention, rate limits, cache prefix via env | 2h |
| 39 | `LLMAgent`: `ILLMProvider` protocol per multi-provider | 4h |

### FASE 5 — QUALITÀ & POLISH (1 giorno)

| # | Azione | Effort |
|:---:|--------|:---:|
| 40 | `print()` → `logger` in graph_runner.py / graph_flow.py | 1h |
| 41 | Migrare 5 servizi da `@app.on_event()` a `lifespan` | 2h |
| 42 | `GraphState` → estendere `BaseGraphState` | 2h |
| 43 | Consolidare `os.getenv()` sparsi nei servizi | 2h |
| 44 | Fix cross-service ref docstring in babel_to_neural.py | 15 min |
| 45 | Tradurre commenti italiano → inglese (resta qdrant_agent.py) | 30 min |
| 46 | Spostare test da `node/` a `tests/` | 10 min |
| 48 | Creare `contracts/` + `ParserContract` | 1h |
| 49 | CI guardrail: scan import/branch verticali in core | 2h |

---

## SCORE PREVISTO

| Criterio | Attuale | Post-Fase 2-3 | Post-Tutte |
|:---|:---:|:---:|:---:|
| Domain-Agnostic | **95%** | 97% | **98%** |
| No Hard-Coded | **75%** | 93% | **96%** |
| Sicurezza | **55%** | 92% | **95%** |
| Scalabilità | **78%** | 90% | **93%** |
| Plugin-Ready | **92%** | 94% | **95%** |
| **Totale** | **79.0%** | **93.2%** | **95.4%** |

**Effort residuo: ~4-6 giorni lavorativi.** FASE 0 (sicurezza) da eseguire prima di qualsiasi push/deploy.
