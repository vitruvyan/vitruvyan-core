# Vitruvyan Core — Architecture (Current State)

> **Last updated**: February 14, 2026  
> **Scope**: Complete tree of the domain-agnostic epistemic OS core  

---

## Summary

| Metric | Value |
|--------|-------|
| Active Python files | **~278** (excludes `_legacy/`, `__pycache__/`) |
| Services (LIVELLO 2) | **12** |
| Sacred Orders (100% conformant) | **6** |
| LangGraph nodes (active) | **22** (19 wired in graph) |
| VPAR algorithms | **4** (VEE, VARE, VWRE, VSGS) |
| Domain registries | **3** (Intent, EntityResolver, Execution) |
| Domain-agnostic files | **59/65 core** (91%) |
| Finance-specific files in core | **0** |

---

## Complete Tree

```
vitruvyan-core/
│
├── vitruvyan_core/                         ── OS CORE PACKAGE ──
│   ├── core/
│   │   ├── agents/                         4 gateway agents (singleton pattern)
│   │   │   ├── llm_agent.py               853L — LLM gateway (get_llm_agent())
│   │   │   ├── postgres_agent.py          PostgresAgent
│   │   │   ├── qdrant_agent.py            QdrantAgent
│   │   │   └── alchemist_agent.py         AlchemistAgent
│   │   │
│   │   ├── cache/
│   │   │   ├── mnemosyne_cache.py         MnemosyneCache
│   │   │   └── _legacy/
│   │   │       └── cached_qdrant_agent.py Deprecated CachedQdrantAgent
│   │   │
│   │   ├── cognitive/                      Perception Sacred Orders + engine stub
│   │   │   ├── babel_gardens/             Sacred Order — Perception (10/10 dirs)
│   │   │   │   ├── consumers/             Pure process() functions
│   │   │   │   ├── domain/                Frozen dataclasses
│   │   │   │   ├── events/                Channel constants
│   │   │   │   ├── governance/            Rules, classifiers
│   │   │   │   ├── monitoring/            Metric constants
│   │   │   │   ├── philosophy/            charter.md
│   │   │   │   ├── docs/                  Design notes
│   │   │   │   ├── examples/              Usage examples
│   │   │   │   └── tests/                 Unit tests
│   │   │   │
│   │   │   ├── pattern_weavers/           Sacred Order — Reason (10/10 dirs)
│   │   │   │   └── (same 10-dir structure as babel_gardens)
│   │   │   │
│   │   │   └── semantic_engine.py         108L — Stub/passthrough
│   │   │
│   │   ├── governance/                     Governance Sacred Orders
│   │   │   ├── SACRED_ORDER_PATTERN.md    Canonical pattern spec
│   │   │   │
│   │   │   ├── codex_hunters/             Sacred Order — Perception (10/10 dirs)
│   │   │   │   ├── _legacy/               Archived code
│   │   │   │   └── (same 10-dir structure)
│   │   │   │
│   │   │   ├── memory_orders/             Sacred Order — Memory/Coherence (10/10)
│   │   │   │   ├── _legacy/               Archived code
│   │   │   │   ├── scripts/               (empty)
│   │   │   │   └── (same 10-dir structure)
│   │   │   │
│   │   │   ├── orthodoxy_wardens/         Sacred Order — Truth/Governance (10/10)
│   │   │   │   ├── _legacy/               code_analyzer.py, penitent_agent.py
│   │   │   │   ├── scripts/               start_orthodoxy_listener.sh
│   │   │   │   └── (same 10-dir structure)
│   │   │   │
│   │   │   └── vault_keepers/             Sacred Order — Memory/Archival (10/10)
│   │   │       ├── _legacy/               Archived code
│   │   │       ├── scripts/               test scripts
│   │   │       └── (same 10-dir structure)
│   │   ├── llm/                            LLM infrastructure
│   │   │   ├── cache_api.py               269L — Cache API
│   │   │   ├── cache_manager.py           444L — LLMCacheManager
│   │   │   ├── gemma_client.py            24L — Thin Gemma wrapper
│   │   │   └── prompts/
│   │   │       ├── registry.py            330L — PromptRegistry (domain-aware)
│   │   │       └── version.py             Prompt versioning
│   │   │
│   │   │
│   │   ├── neural_engine/                  Scoring framework (contract-driven)
│   │   │   ├── engine.py                  Engine principale
│   │   │   ├── scoring.py                 Scoring framework
│   │   │   ├── composite.py              Composite scoring
│   │   │   ├── ranking.py                Ranking framework
│   │   │   ├── domain_examples/           Mock providers (IDataProvider, IScoringStrategy)
│   │   │   └── docs/                      8 design/architecture docs
│   │   │
│   │   ├── orchestration/                  LangGraph + ABC + registries
│   │   │   ├── base_state.py              196L — Domain-agnostic base state
│   │   │   ├── graph_engine.py            GraphPlugin ABC + NodeContract
│   │   │   ├── parser.py                 Parser ABC
│   │   │   ├── intent_registry.py         380L — IntentRegistry (hook pattern)
│   │   │   ├── entity_resolver_registry.py 218L — EntityResolverRegistry
│   │   │   ├── execution_registry.py      242L — ExecutionRegistry
│   │   │   ├── route_registry.py          RouteRegistry
│   │   │   ├── sacred_flow.py             Pure config + dataclass
│   │   │   │
│   │   │   ├── compose/                   Response composition ABCs
│   │   │   │   ├── base_composer.py       BaseComposer ABC
│   │   │   │   ├── response_formatter.py  ResponseFormatter ABC
│   │   │   │   └── slot_filler.py         SlotFiller ABC
│   │   │   │
│   │   │   └── langgraph/                 Graph engine runtime
│   │   │       ├── graph_flow.py          431L — StateGraph + GraphState TypedDict
│   │   │       ├── graph_runner.py        332L — Pipeline runner
│   │   │       ├── memory/
│   │   │       │   └── conversation_context.py  146L — DomainContextProvider
│   │   │       ├── shared/
│   │   │       │   └── state_preserv.py   112L — UX field preservation
│   │   │       │
│   │   │       └── node/                  22 active nodes + _legacy/
│   │   │           ├── base_node.py       ABC base
│   │   │           ├── parse_node.py      292L — Input parser v3.0
│   │   │           ├── intent_detection_node.py  315L — IntentRegistry-driven
│   │   │           ├── pattern_weavers_node.py   142L — HTTP adapter
│   │   │           ├── entity_resolver_node.py   65L — Stub passthrough
│   │   │           ├── emotion_detector.py       124L — Babel Gardens HTTP
│   │   │           ├── semantic_grounding_node.py 98L — Qdrant embedding
│   │   │           ├── params_extraction_node.py  323L — Domain-agnostic params
│   │   │           ├── route_node.py      95L — IntentRegistry routing v3.0
│   │   │           ├── exec_node.py       63L — Stub (domain_neutral: True)
│   │   │           ├── qdrant_node.py     85L — Semantic search fallback
│   │   │           ├── cached_llm_node.py 377L — Cached LLM orchestrator
│   │   │           ├── output_normalizer_node.py  79L — Output normalization
│   │   │           ├── compose_node.py    242L — Response composition
│   │   │           ├── orthodoxy_node.py  328L — Governance validation
│   │   │           ├── vault_node.py      363L — Archival protection
│   │   │           ├── can_node.py        310L — Conversational Navigator
│   │   │           ├── advisor_node.py    140L — Recommendation (domain_neutral)
│   │   │           ├── llm_mcp_node.py    331L — MCP tool calling
│   │   │           ├── codex_hunters_node.py  469L — Expedition polling
│   │   │           ├── audit_node_simple.py   233L — Audit logging
│   │   │           ├── test_route_node.py     Test utility
│   │   │           │
│   │   │           └── _legacy/           4 archived nodes
│   │   │               ├── archivarium_node.py
│   │   │               ├── babel_gardens_node.py
│   │   │               ├── codex_node.py
│   │   │               └── mnemosyne_node.py
│   │   │
│   │   ├── synaptic_conclave/              Cognitive Bus (Redis Streams)
│   │   │   ├── event_schema.py            Compatibility shim → events/
│   │   │   ├── redis_client.py            Compatibility shim → transport/
│   │   │   │
│   │   │   ├── transport/
│   │   │   │   ├── streams.py             StreamBus (canonical transport)
│   │   │   │   └── redis_client.py        Redis wrapper
│   │   │   │
│   │   │   ├── events/
│   │   │   │   ├── event_envelope.py      TransportEvent, CognitiveEvent
│   │   │   │   └── event_schema.py        Event domain/intent enums
│   │   │   │
│   │   │   ├── consumers/
│   │   │   │   ├── base_consumer.py       ABC base
│   │   │   │   ├── listener_adapter.py    Adapter pattern
│   │   │   │   ├── registry.py            Consumer registry
│   │   │   │   ├── working_memory.py      Redis working memory
│   │   │   │   └── MIGRATION_GUIDE.md
│   │   │   │
│   │   │   ├── plasticity/                Synaptic learning (2,325L total)
│   │   │   │   ├── manager.py             506L — Plasticity manager
│   │   │   │   ├── observer.py            922L — Event observer
│   │   │   │   ├── outcome_tracker.py     311L — Outcome tracking
│   │   │   │   ├── metrics.py             282L — Plasticity metrics
│   │   │   │   └── learning_loop.py       242L — Learning loop
│   │   │   │
│   │   │   ├── orthodoxy/                 Bus validation layer
│   │   │   │   ├── formatter.py           225L
│   │   │   │   └── verdicts.py            189L
│   │   │   │
│   │   │   ├── governance/
│   │   │   │   └── rite_of_validation.py  Bus governance
│   │   │   │
│   │   │   ├── monitoring/
│   │   │   │   ├── metrics.py             338L — Bus metrics
│   │   │   │   └── metrics_server.py      45L — Prometheus server
│   │   │   │
│   │   │   ├── utils/
│   │   │   │   ├── lexicon.py             438L — Schema templates
│   │   │   │   └── scroll_of_bonds.json   Channel config
│   │   │   │
│   │   │   ├── philosophy/                4 architecture manifestos
│   │   │   └── docs/                      27 docs (16 active + 8 history/ + README)
│   │   │
│   │   └── vpar/                           Proprietary algorithms
│   │       ├── vee/                       VEE — Explainability Engine (5 files)
│   │       ├── vare/                      VARE — Attribution & Risk (3 files)
│   │       ├── vwre/                      VWRE — Weighted Ranking (3 files)
│   │       └── vsgs/                      VSGS — Signal Generation (3 files)
│   │
│   ├── contracts/                          Core ABC interfaces
│   │   ├── data_provider.py               IDataProvider
│   │   └── scoring_strategy.py            IScoringStrategy
│   │
│   └── domains/                            Domain plugin system
│       ├── base_domain.py                 Domain contract ABC
│       ├── example_domain.py              Template/placeholder
│       ├── finance_plugin.py              Finance plugin loader
│       ├── aggregation_contract.py        AggregationProvider (VWRE)
│       ├── explainability_contract.py     ExplainabilityProvider (VEE)
│       ├── risk_contract.py               RiskProvider (VARE)
│       └── finance/                       Finance vertical plugin
│           ├── intent_config.py           265L — create_finance_registry()
│           ├── entity_resolver_config.py
│           ├── execution_config.py
│           ├── governance_rules.py
│           ├── response_formatter.py
│           ├── slot_filler.py
│           ├── prompts/                   Finance prompt templates
│           └── README_HOOK_PATTERN.md
│
├── services/                               12 microservices (LIVELLO 2)
│   ├── api_babel_gardens/                 87L main.py
│   ├── api_codex_hunters/                 75L main.py
│   ├── api_conclave/                      Bus service
│   ├── api_embedding/                     Embedding service
│   ├── api_graph/                         LangGraph service
│   ├── api_mcp/                           MCP Gateway
│   ├── api_memory_orders/                 93L main.py
│   ├── api_neural_engine/                 Scoring service
│   ├── api_orthodoxy_wardens/             87L main.py
│   ├── api_pattern_weavers/               62L main.py
│   ├── api_vault_keepers/                 59L main.py
│   └── redis_streams_exporter/            Prometheus exporter
│
├── config/                                 api_config.py
├── docs/                                   MkDocs documentation
│   ├── architecture/                      Design docs
│   ├── changelog/                         Version history
│   ├── foundational/                      Core philosophy
│   ├── installation/                      Setup guides
│   ├── internal/                          orders/, platform/, services/
│   ├── knowledge_base/                    governance/
│   ├── orders/                            Sacred Orders docs
│   ├── planning/                          Architecture plans
│   ├── prompts/                           Prompt templates
│   ├── public/                            Public docs
│   ├── services/                          Service docs
│   └── testing/                           Test strategies
│
├── tests/                                  Test suite
│   ├── unit/                              Unit tests
│   ├── integration/                       Integration tests
│   ├── e2e/                               End-to-end tests
│   ├── graph/                             LangGraph tests
│   ├── architectural/                     Architecture conformance
│   ├── conversational/                    Dialogue tests
│   └── explainability/                    Explainability tests
│
├── infrastructure/                         Deployment
│   ├── docker/                            Docker Compose + Dockerfiles
│   ├── monitoring/                        Grafana dashboards
│   └── secrets/                           Secrets templates
│
├── scripts/                                Utility scripts
├── examples/                               Demo scripts + MCP examples
│   ├── mercator_demo/                     Demo vertical
│   └── verticals/                         Vertical examples
│
├── .github/                                Appendix A-O + copilot-instructions
│
├── README.md
├── CREWAI_DEPRECATION_NOTICE.md
├── SYNAPTIC_CONCLAVE_VERIFICATION_REPORT.md
├── TEST_ESTENSIVI_REPORT.md
├── index.md                                MkDocs entry
└── index.it.md                             MkDocs entry (IT)
```

---

## LangGraph Pipeline

```
parse → intent_detection → weaver → entity_resolver → babel_emotion
  → semantic_grounding → params_extraction → decide → [route branches]
  → output_normalizer → orthodoxy → vault → compose → can → [advisor] → END
```

### Route branches (from `decide`)

| Route | Node | Description |
|-------|------|-------------|
| `dispatcher_exec` | `exec` | Direct execution |
| `semantic_fallback` | `qdrant` | Semantic search |
| `llm_soft` | `cached_llm` | Conversational LLM |
| `slot_filler` | `compose` | Missing params |
| `codex_expedition` | `codex_hunters` | System maintenance |
| `llm_mcp` | `llm_mcp` | MCP tools (when `USE_MCP=1`) |

---

## Architecture Layers

```
LAYER 0 — Infrastructure
├── agents/              PostgresAgent, QdrantAgent, LLMAgent, AlchemistAgent
├── cache/               MnemosyneCache
├── llm/                 Cache, PromptRegistry, Gemma client
├── synaptic_conclave/   StreamBus, events, consumers, plasticity, monitoring

LAYER 1 — Cognitive Engines
├── neural_engine/       Scoring, ranking, composite (contract-driven)
├── orchestration/       LangGraph (19 nodes), 3 registries, compose/
├── vpar/                VEE, VARE, VWRE, VSGS (proprietary algorithms)
└── cognitive/           semantic_engine.py (stub)

LAYER 2 — Sacred Orders
├── cognitive/babel_gardens/        Perception — Semantic signals
├── cognitive/pattern_weavers/      Reason — Ontology
├── governance/codex_hunters/       Perception — Data acquisition
├── governance/memory_orders/       Memory — Coherence
├── governance/orthodoxy_wardens/   Truth — Governance
└── governance/vault_keepers/       Memory — Archival

LAYER 3 — Contracts & Domain Plugins
├── contracts/           IDataProvider, IScoringStrategy (ABC)
├── domains/             base_domain, VPAR contracts
└── domains/finance/     Intent, entity resolver, execution, prompts

LAYER 4 — Services
└── 12 microservices     LIVELLO 2 (FastAPI, Docker, adapters)
```

---

## 6 Mixed Files (not finance-specific, just not 100% pure)

| File | Residual | Impact |
|------|----------|--------|
| `parse_node.py` | imports `semantic_engine` stub, `state["companies"]` key | LOW — stub is passthrough |
| `test_route_node.py` | test utility | NONE |
| `event_schema.py` | `sentiment.requested/fused` enums | NONE — sentiment is domain-agnostic Perception |
| `lexicon.py` | `sentiment.*` schema templates | NONE — config-driven via scroll_of_bonds.json |
| `graph_flow.py` | Domain plugin loading via env vars | BY DESIGN — runner loads domain at boot |
| `graph_runner.py` | Propagates `entity_ids`, `horizon` | BY DESIGN — structural params for any vertical |

---

## Proposed Cleanup (Minor — No Structural Redesign Needed)

L'architettura attuale è solida. Non serve una ristrutturazione. Servono solo pulizie puntuali:

### ~~Directories vuote~~ — ELIMINATE (commit ef28808+)

Tutte le 5 directory vuote identificate sono state eliminate:
`client/`, `listeners/`, `utilities/`, `monitoring/`, `memory_orders/scripts/`

### Compatibility shims da valutare

| File | Purpose | Action |
|------|---------|--------|
| `synaptic_conclave/event_schema.py` | Re-export da `events/event_schema.py` | **KEEP** — backward compat per import legacy |
| `synaptic_conclave/redis_client.py` | Re-export da `transport/redis_client.py` | **KEEP** — backward compat per import legacy |

Se un giorno si fa un major version bump si possono rimuovere (breaking change).

### Documentazione embedded eccessiva

| Location | Files | Action |
|----------|------:|--------|
| `synaptic_conclave/docs/` | 27 | Considerare consolidamento: spostare `history/` (8 file) in `docs/archive/` |
| `neural_engine/docs/` | 8 | OK — design docs legittimi, mantenerli |

### `cache/_legacy/cached_qdrant_agent.py`

Valutare rimozione — se nessun import lo usa, eliminare.

---

## How to Extend

| Action | Steps |
|--------|-------|
| **Nuovo vertical** | 1. Crea `domains/<vertical>/` con intent_config, entity_resolver_config, execution_config. 2. Imposta `INTENT_DOMAIN=<vertical>`. 3. Zero modifiche al core. |
| **Nuovo Sacred Order** | 1. Crea 10-dir structure sotto `cognitive/` o `governance/`. 2. Crea servizio LIVELLO 2 in `services/api_<order>/`. |
| **Nuovo nodo LangGraph** | 1. Aggiungi file in `node/`. 2. Registra in `graph_flow.py`. |
| **Nuovo algoritmo VPAR** | 1. Aggiungi sotto `core/vpar/<name>/` con types.py + engine.py. |
