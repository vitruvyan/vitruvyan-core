# 🔬 Vitruvyan Core — Architecture Audit & Reorganization Proposal

**Date**: February 12, 2026  
**Scope**: Full tree audit from `vitruvyan-core/` to leaf files  
**Objective**: Agnostic, no-hardcoded, secure, scalable, portable core for domain spin-ups  

---

## 📊 Current State Summary

- **277 file Python attivi** (esclusi `_legacy/`, `_archived/`, `__pycache__/`)
- **14 servizi** in `services/`
- **6 Sacred Orders** al 100% SACRED_ORDER_PATTERN conformance
- **33 file .md** alla root del repo (work logs, audit, debug)
- **40+ file finance-leaky** nel core attivo → **CORRETTO dopo verifica codice: ~20 file reali** (molti falsi positivi da grep — docstring/commenti vs codice eseguibile)

### Riepilogo verifiche codice (Feb 12, 2026 — seconda passata)
| Area | File verificati | ✅ Agnostici | ⚠️ Misti | ❌ Finance-specific |
|------|----------------:|-------------:|---------:|-------------------:|
| orchestration/ (ABC) | 9 | **9** | 0 | 0 |
| orchestration/ (runners) | 2 | 0 | **2** | 0 |
| LangGraph nodes | 20 | **10** | **5** | **5** |
| synaptic_conclave/ | 6 | **1** | **2** | **3** |
| governance/ Sacred Orders | 7 | **5** | **2** | 0 |
| llm/ | 3 | **1** | **2** | 0 |
| cognitive/ | 1 | **1** | 0 | 0 |
| monitoring/ | 1 | 0 | 0 | **1** |
| foundation/ | 3 | 0 | 0 | 0 (morto) |
| domains/ contracts | 3 | **3** | 0 | 0 |
| **TOTALE** | **55** | **30** | **13** | **9** |

---

## 🗺️ Struttura Attuale (Annotata)

```
vitruvyan-core/
├── vitruvyan_core/
│   ├── core/
│   │   ├── agents/                    ✅ CORE — PostgresAgent, QdrantAgent, LLMAgent
│   │   ├── cache/                     ✅ CORE — MnemosyneCache, CachedQdrantAgent
│   │   ├── cognitive/
│   │   │   ├── babel_gardens/         ✅ Sacred Order (10/10 dirs)
│   │   │   ├── pattern_weavers/       ✅ Sacred Order (10/10 dirs)
│   │   │   ├── vitruvyan_proprietary/ ⚠️ FUORI POSTO — 6 algoritmi finance-heavy
│   │   │   │   ├── vare/             6 engine files (VARE, attribution + risk)
│   │   │   │   ├── vee/              5 engine files (VEE, explainability)
│   │   │   │   ├── vhsw/            2 engine files (historical sliding window)
│   │   │   │   ├── vmfl/            2 engine files (multi-factor learning)
│   │   │   │   ├── vsgs/            1 __init__.py only (signal generation)
│   │   │   │   └── vwre/            2 engine files (weighted ranking)
│   │   │   └── semantic_engine.py     ✅ STUB AGNOSTICO — 110 righe, passthrough puro. Finance menzionato solo in docstring/commenti come esempio. Codice restituisce struttura generica.
│   │   ├── foundation/                ⚠️ CONFERMATO DUPLICATO MORTO
│   │   │   ├── cognitive_bus/         VUOTO (confermato: cartella vuota)
│   │   │   ├── persistence/           RE-EXPORT confermato: postgres_agent.py + qdrant_agent.py (re-import di core.agents)
│   │   │   └── semantic_sync/         VUOTO (confermato: cartella vuota)
│   │   ├── governance/
│   │   │   ├── codex_hunters/         ✅ Sacred Order (10/10 dirs) — Perception
│   │   │   ├── memory_orders/         ✅ Sacred Order (9/10 dirs, manca docs/) — Memory
│   │   │   ├── orthodoxy_wardens/     ✅ Sacred Order (10/10 dirs) — Truth
│   │   │   ├── vault_keepers/         ✅ Sacred Order (10/10 dirs) — Memory/Archival
│   │   │   └── semantic_sync/         ⚠️ 1 file: vsgs_sync.py (VSGS = finance-specific)
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── llm_interface.py       ✅ CORE — ABC per LLM
│   │   │   ├── conversational_llm.py  ⚠️ MISTO — Ha docstring che dichiara "LEGACY Finance-specific" (generate_portfolio_reasoning, generate_vee_narrative). Usa httpx→Babel, OpenAI. 734 righe.
│   │   │   ├── cache_api.py           ✅ CORE
│   │   │   ├── cache_manager.py       ✅ CORE — LLMCacheManager generico. Usa entity_ids/horizon come chiavi opache (nessuna logica finance). 445 righe.
│   │   │   ├── gemma_client.py        ✅ CORE — Wrapper Gemma
│   │   │   └── prompts/
│   │   │       ├── registry.py        ✅ CORE — Prompt registry
│   │   │       ├── version.py         ✅ CORE
│   │   │       └── _legacy/           3 files (base_prompts, scenario_prompts)
│   │   ├── monitoring/
│   │   │   └── vsgs_metrics.py        ⚠️ CONFERMATO FINANCE-SPECIFIC — 181 righe, Counter Prometheus per VSGS + VEE (vee_generation, entity_id labels). Dipende da prometheus_client.
│   │   ├── neural_engine/             ✅ CORE — Scoring generico con contracts
│   │   │   ├── engine.py             Engine principale
│   │   │   ├── scoring.py            Scoring framework
│   │   │   ├── composite.py          Composite scoring
│   │   │   ├── ranking.py            Ranking framework
│   │   │   └── domain_examples/      Mock implementations (ha ref finance)
│   │   ├── orchestration/             ✅ REFACTORED (Feb 10, 2026) — 9/11 files agnostic
│   │   │   ├── base_state.py          ✅ CORE — 196 righe, puro domain-agnostic (ZERO finance terms)
│   │   │   ├── graph_engine.py        ✅ CORE — GraphPlugin ABC + NodeContract (finance solo in docstring example)
│   │   │   ├── parser.py             ✅ CORE — Parser ABC generico (finance solo in docstring examples)
│   │   │   ├── intent_registry.py     ✅ CORE — IntentRegistry generico
│   │   │   ├── route_registry.py      ✅ CORE — RouteRegistry generico
│   │   │   ├── sacred_flow.py         ✅ CORE — Pure config + dataclass (ZERO finance terms)
│   │   │   ├── compose/
│   │   │   │   ├── base_composer.py       ✅ CORE — BaseComposer ABC
│   │   │   │   ├── response_formatter.py  ✅ CORE — ResponseFormatter ABC
│   │   │   │   └── slot_filler.py         ✅ CORE — SlotFiller ABC generico
│   │   │   └── langgraph/
│   │   │       ├── graph_flow.py      ⚠️ RUNNER CONCRETO — GraphState ha sentiment_label, sentinel_portfolio_value, crew_* fields; importa 20+ nodi concreti (by design)
│   │   │       ├── graph_runner.py    ⚠️ RUNNER CONCRETO — Propaga entity_ids, horizon, sentiment al response (by design)
│   │   │       └── node/             40+ nodi (dettaglio sotto)
│   │   └── synaptic_conclave/         ✅ CORE — Bus transport
│   │       ├── transport/
│   │       │   ├── streams.py         ✅ StreamBus (Redis Streams)
│   │       │   └── redis_client.py    ✅ Redis wrapper
│   │       ├── events/
│   │       │   ├── event_envelope.py  ✅ TransportEvent, CognitiveEvent
│   │       │   └── event_schema.py    ⚠️ MISTO — 797 righe. Enums EventDomain/Intents sono generici (audit, vault, orthodoxy, babel). Ma _create_default_schemas() ha payload: "ticker", "sentiment.requested", "sentiment.fused" nei template Babel. Struttura è schema-driven (potenzialmente refactorabile).
│   │       ├── consumers/
│   │       │   ├── risk_guardian.py    ⚠️ VERTICALE — Risk logic in bus layer
│   │       │   ├── narrative_engine.py ⚠️ VERTICALE — Narrative in bus layer
│   │       │   └── working_memory.py   ⚠️ Ha "sentiment"
│   │       ├── listeners/
│   │       │   └── langgraph.py       ❌ CONFERMATO FINANCE-SPECIFIC — 182 righe. Canali: "portfolio:snapshot_created", "portfolio:manual_check". Payload: "controlla il mio portfolio", validated_tickers. Import: core.leo.postgres_agent (path legacy).
│   │       ├── utils/
│   │       │   └── lexicon.py         ⚠️ MISTO — 439 righe. SacredLexicon con DomainSchema è struttura generica. Ma _create_default_schemas() ha payload templates con "ticker", "sentiment.requested" nei campi Babel. Caricabile da JSON (scroll_of_bonds.json), quindi potenzialmente config-driven.
│   │       ├── orthodoxy/             Validation layer
│   │       ├── governance/            Bus governance
│   │       └── philosophy/            charter.md
│   │
│   ├── contracts/                     ✅ CORE — Interfacce astratte
│   │   ├── data_provider.py           IDataProvider (ABC)
│   │   ├── scoring_strategy.py        IScoringStrategy (ABC)
│   │   ├── aggregation_contract.py    Aggregation ABC
│   │   ├── explainability_contract.py Explainability ABC
│   │   └── risk_contract.py           ✅ NON ESISTE QUI — audit errato. I 3 contracts (risk, aggregation, explainability) sono SOLO in vitruvyan_core/domains/
│   │
│   ├── domains/
│   │   ├── base_domain.py             ✅ CORE — Domain contract ABC
│   │   ├── example_domain.py          ✅ Placeholder
│   │   ├── finance_plugin.py          ✅ Finance plugin (giusto qui)
│   │   ├── finance/                   ✅ Finance vertical
│   │   │   ├── response_formatter.py  Finance-specific formatter
│   │   │   ├── slot_filler.py         Finance-specific slot filler
│   │   │   └── prompts/              Finance prompt templates
│   │   ├── aggregation_contract.py    ✅ ABC GENERICO — NON duplicato (contracts/ contiene solo data_provider.py e scoring_strategy.py). Fornisce AggregationProvider ABC per VWRE. 118 righe.
│   │   ├── explainability_contract.py ✅ ABC GENERICO — ExplainabilityProvider v2.0 per VEE. Puro domain-agnostic con NormalizationRule, AnalysisDimension, PatternRule. 195 righe.
│   │   └── risk_contract.py           ✅ ABC GENERICO — RiskProvider per VARE. RiskDimension + RiskProfile dataclasses. 136 righe.
│   │
│   ├── services/                      ⚠️ VUOTO — solo __init__.py
│   └── verticals/                     ⚠️ VUOTO — solo README.md
│
├── services/                          14 servizi LIVELLO 2
│   ├── api_babel_gardens/             ✅ 87 lines main.py
│   ├── api_codex_hunters/             ✅ 75 lines main.py
│   ├── api_conclave/                  ✅ Bus service
│   ├── api_embedding/                 ✅ Embedding service
│   ├── api_graph/                     ✅ LangGraph service
│   ├── api_mcp/                       ✅ MCP Gateway
│   ├── api_memory_orders/             ✅ 93 lines main.py
│   ├── api_neural_engine/             ✅ Scoring service
│   ├── api_orthodoxy_wardens/         ✅ 87 lines main.py
│   ├── api_pattern_weavers/           ✅ 62 lines main.py
│   ├── api_semantic/                  ✅ Semantic service
│   ├── api_vault_keepers/             ✅ 59 lines main.py
│   ├── adapters/                      ⚠️ 1 file solo (babel_to_neural.py)
│   ├── core/api_memory_orders/        ⚠️ PATH DUPLICATO (legacy symlink?)
│   ├── governance/api_orthodoxy.../   ⚠️ PATH DUPLICATO (legacy symlink?)
│   └── redis_streams_exporter/        ✅ Prometheus exporter
│
├── 33 file .md alla ROOT              ❌ DISORDINE — work logs, non documentazione
├── config/                            ✅ api_config.py
├── docs/                              ✅ Fondamentali + changelog
├── tests/                             ✅ Test suite
├── infrastructure/                    ✅ Docker + secrets
├── scripts/                           ✅ Utility scripts
└── .github/                           ✅ Appendix A-O + copilot-instructions
```

---

## 🔴 Dettaglio: Nodi LangGraph (20 files verificati — codice letto)

**Path**: `vitruvyan_core/core/orchestration/langgraph/node/`

### ✅ Nodi AGNOSTICI (confermati dal codice — possono restare nel core)
| File | Righe | Verdetto | Ruolo |
|------|------:|----------|-------|
| `base_node.py` | - | ✅ CORE | ABC base per tutti i nodi |
| `entity_resolver_node.py` | 50 | ✅ AGNOSTIC | Stub passthrough. `flow = "direct"`. Finance solo in docstring. |
| `semantic_grounding_node.py` | 433 | ✅ AGNOSTIC | Genera embedding, query Qdrant. Pura infrastruttura. |
| `babel_gardens_node.py` | 140 | ✅ AGNOSTIC | HTTP adapter v2.0 verso Babel Gardens API. Zero business logic. |
| `pattern_weavers_node.py` | 127 | ✅ AGNOSTIC | HTTP adapter v2.0 verso Pattern Weavers API. Zero finance. |
| `codex_hunters_node.py` | 470 | ✅ AGNOSTIC | API calls, Redis events, expedition polling. Pura infrastruttura. |
| `archivarium_node.py` | 376 | ✅ AGNOSTIC | Processa memory.read/write events. Formatta narrative memoria. |
| `exec_node.py` | 25 | ✅ AGNOSTIC | Stub neutralizzato PHASE 1D: `domain_neutral: True`, ranking vuoto. |
| `gemma_node.py` | 34 | ✅ AGNOSTIC | Thin wrapper su `gemma_predict()`. Estrae intent/entity_ids generici. |
| `emotion_detector.py` | 128 | ✅ AGNOSTIC | HTTP adapter verso Babel Gardens emotion endpoint. |
| `compose_node.py` | - | ✅ CORE | Response composition |
| `output_normalizer_node.py` | - | ✅ CORE | Output normalization |
| `orthodoxy_node.py` | - | ✅ CORE | Governance validation |
| `audit_node_simple.py` | - | ✅ CORE | Audit logging |
| `quality_check_node.py` | - | ✅ CORE | Quality validation |
| `can_node.py` | - | ✅ CORE | CAN (Conversational Analysis) |
| `llm_mcp_node.py` | - | ✅ CORE | MCP tool calling |

### ⚠️ Nodi MISTI (meccanismo generico, ma con residui finance configurabili)
| File | Righe | Problema Reale | Fix Stimato |
|------|------:|----------------|-------------|
| `advisor_node.py` | 118 | State keys `portfolio_data`, `allocation_data`. MA tutto stubbed a `NO_ACTION`/`domain_neutral: True`. | Facile: rinominare chiavi a generiche |
| `params_extraction_node.py` | 340 | Regex ha `titoli\|acciones\|etfs`. LLM prompt: "financial horizon classifier". Core logic è generica. | Medio: estrarre prompt/regex in config |
| `llm_soft_node.py` | 174 | Guardrails: "NEVER output BUY/SELL", "investment risk disclaimer". Persona "Leonardo" finance advisor. | Medio: parametrizzare guardrails |
| `route_node.py` | 77 | `TECHNICAL_INTENTS = ["trend","momentum","volatility","risk","backtest","allocate","collection","sentiment"]` hardcoded. | Facile: rendere lista configurabile da state/config |
| `vault_node.py` | 356 | Un singolo `"financial_guardian"` string literal. Resto usa domain-plugin pattern. | Banale: rimuovere 1 stringa |
| `codex_node.py` | 511 | `__main__` test block ha `"yfinance","reddit"`. Core logic generica. | Banale: pulire test fixtures |

### ❌ Nodi FINANCE-SPECIFIC (hardcoded, da spostare in domains/finance/nodes/)
| File | Righe | Problema Reale |
|------|------:|----------------|
| `intent_detection_node.py` | 603 | **Peggiore.** INTENT_LABELS: trend/momentum/volatility/risk/allocate/sentiment. INTENT_SYNONYMS: "buy"→"allocate", "comprare"→"allocate". GPT prompt: "financial query". Screening filters: risk_tolerance, momentum_breakout. |
| `parse_node.py` | 327 | **Company→ticker map hardcoded**: "nvidia":"EXAMPLE_ENTITY_2", "amazon":"AMZN". Budget extraction: €/$/eur/usd. Fallback intent: "portafoglio"→"collection". |
| `proactive_suggestions_node.py` | 214 | **Dict correlazione ticker hardcoded**: "JPM":["BAC","WFC","C"]. Calendario earnings. Smart money detection. Hedging italiano: "put protettive, stop loss". |
| `cached_llm_node.py` | 540 | **Prompt BUY/HOLD/SELL**: "consulente finanziario AI istituzionale", "RACCOMANDAZIONE: [BUY/HOLD/SELL]", composite_score/momentum_score/risk_score. |
| `enhanced_llm_node.py` | 181 | **Persona hardcoded**: "senior financial advisor 20+ years", "former sell-side analyst". Keywords: "bullish/rialzista/alcista". Market context baked in. |

### Nodi ARCHIVED (legacy, non attivi)
| File | Stato |
|------|-------|
| `_archived_can_node_v1.py` | Frozen |
| `_archived_compose_node_v1.py` | Frozen |
| `_archived_emotion_detector_v1.py` | Frozen |
| `_legacy_babel_emotion_node_v1.py` | Frozen |
| `_legacy_mnemosyne_node_v1.py` | Frozen |

---

## 🔴 Dettaglio: Finance Leakage nel Core

**40 file nel core attivo** (esclusi _legacy/ _archived/ tests/ examples/ domain_examples/) contengono terminologia finance-specific:

### Area: orchestration/ (2 file runner concreti + nodi)
- `langgraph/graph_flow.py` — Runner concreto: `sentiment_label`, `sentinel_portfolio_value`, `crew_*` fields in GraphState
- `langgraph/graph_runner.py` — Runner concreto: propaga `entity_ids`, `horizon`, `sentiment` 
- ~~`base_state.py`~~ ✅ REFACTORED (puro agnostico, ZERO finance)
- ~~`graph_engine.py`~~ ✅ REFACTORED (ABC, finance solo in docstring example)
- ~~`parser.py`~~ ✅ REFACTORED (ABC, finance solo in docstring examples)
- ~~`sacred_flow.py`~~ ✅ REFACTORED (puro agnostico, ZERO finance)
- `langgraph/node/`: intent_detection, proactive_suggestions, advisor, params_extraction, cached_llm, entity_resolver, enhanced_llm, parse, semantic_grounding

### Area: synaptic_conclave/ (6 files)
- `listeners/langgraph.py`, `events/event_schema.py`, `utils/lexicon.py`
- `consumers/risk_guardian.py`, `consumers/narrative_engine.py`, `consumers/working_memory.py`

### Area: cognitive/ (7 files — algoritmi proprietari)
- `vitruvyan_proprietary/vare/vare_engine.py`
- `vitruvyan_proprietary/vee/` (4 files)
- `vitruvyan_proprietary/vhsw/vhsw_engine.py`
- `vitruvyan_proprietary/vmfl/vmfl_engine.py`
- `vitruvyan_proprietary/vwre/vwre_engine.py`

### Area: governance/ (7 files — Sacred Orders) — VERIFICATI DAL CODICE
- `vault_keepers/domain/signal_archive.py` — ✅ AGNOSTICO. Domain-agnostic dataclass con `vertical` campo configurabile ("finance", "cybersecurity", "healthcare"). Usa tuple frozen per immutabilità.
- `vault_keepers/consumers/signal_archivist.py` — ✅ AGNOSTICO. VaultRole ABC, pianifica archiviazione timeseries da Babel Gardens. entity_id è generico.
- `orthodoxy_wardens/governance/verdict_engine.py` — ✅ AGNOSTICO. Pure scoring: (findings, ruleset) → Verdict. Zero domini, zero I/O. 299 righe.
- `orthodoxy_wardens/governance/rule.py` — ✅ AGNOSTICO. Dataclass Rule + RuleSet. Pattern matching generico (compliance, security, quality, hallucination). 337 righe.
- `orthodoxy_wardens/governance/classifier.py` — ✅ AGNOSTICO. PatternClassifier: (text, ruleset) → Findings. Regex puro, stateless. 308 righe.
- `orthodoxy_wardens/consumers/penitent_agent.py` — ⚠️ MISTO. AutoCorrector generico (container restart, disk cleanup, config updates). Ha 1 esempio finance in docstring: "Buy AAPL now!" → "AAPL shows buy signal". Codice eseguibile è domain-agnostic. 823 righe.
- `orthodoxy_wardens/consumers/inquisitor_agent.py` — ⚠️ MISTO. ComplianceValidator con regex patterns + LLM semantic check. Ha categorie `prescriptive_language` e esempi finance in docstring ("NVDA shows strong momentum"). Pattern stage è generico, ma prompts LLM stage referenziano "financial advice". 618 righe.

### Area: altri (6 files) — VERIFICATI DAL CODICE
- `monitoring/vsgs_metrics.py` — ❌ CONFERMATO FINANCE: Counter Prometheus VSGS + VEE (entity_id labels). 181 righe.
- `llm/conversational_llm.py` — ⚠️ MISTO: La classe stessa dichiara "LEGACY Finance-specific" per generate_portfolio_reasoning, generate_vee_narrative. 734 righe.
- `llm/cache_manager.py` — ✅ CORRETTO A AGNOSTICO: Usa entity_ids/horizon come chiavi opache per hash, nessuna logica finance. 445 righe.
- `agents/llm_agent.py` — ⚠️ MISTO: 1 esempio "Analyze AAPL stock" in docstring. Codice è pattern generico. 666 righe.
- `agents/qdrant_agent.py` — DA VERIFICARE
- `cognitive/semantic_engine.py` — ✅ CORRETTO A AGNOSTICO: Stub puro 110 righe. Finance solo in commenti come esempio verticale.

---

## 🏗️ Proposta: Architettura Target

```
vitruvyan-core/
│
├── vitruvyan_core/                    # PACCHETTO PYTHON INSTALLABILE
│   │
│   ├── core/                          # LAYER 0: INFRASTRUTTURA PURA
│   │   ├── agents/                    # PostgresAgent, QdrantAgent, LLMAgent
│   │   ├── cache/                     # MnemosyneCache, CachedQdrantAgent
│   │   ├── llm/                       # LLM interface, conversational (purificato)
│   │   ├── transport/                 # ← RINOMINARE synaptic_conclave/transport/
│   │   │   ├── streams.py            #   StreamBus (Redis Streams)
│   │   │   └── events/               #   TransportEvent, CognitiveEvent, EventAdapter
│   │   └── monitoring/                # Metriche GENERICHE (no vsgs_metrics)
│   │
│   ├── engine/                        # LAYER 1: MOTORI COGNITIVI GENERICI
│   │   ├── neural_engine/             # Scoring, ranking, composite (con contracts)
│   │   ├── orchestration/             # LangGraph flow, nodi GENERICI
│   │   │   ├── nodes/               #   base, parse, intent, route, compose, output
│   │   │   ├── state/               #   GraphState (generico)
│   │   │   └── compose/             #   slot_filler, response_formatter (ABC)
│   │   └── semantic/                  # Semantic engine (stub → override da dominio)
│   │
│   ├── orders/                        # LAYER 2: SACRED ORDERS (namespace unificato)
│   │   ├── babel_gardens/             # Segnali semantici (attuale: cognitive/)
│   │   ├── codex_hunters/             # Data acquisition (attuale: governance/)
│   │   ├── memory_orders/             # Coherence (attuale: governance/)
│   │   ├── orthodoxy_wardens/         # Governance (attuale: governance/)
│   │   ├── pattern_weavers/           # Ontology (attuale: cognitive/)
│   │   └── vault_keepers/             # Archival (attuale: governance/)
│   │
│   ├── contracts/                     # LAYER 3: INTERFACCE ASTRATTE
│   │   ├── data_provider.py           # IDataProvider (ABC)
│   │   ├── scoring_strategy.py        # IScoringStrategy (ABC)
│   │   ├── response_formatter.py      # ABC per output formatting
│   │   └── domain_plugin.py           # DomainPlugin interface (NUOVO)
│   │
│   └── algorithms/                    # LAYER 4: ALGORITMI PROPRIETARI (opzionali)
│       ├── __init__.py                # Registry: load_algorithm("vee") → VEEEngine
│       ├── vee/                       # Vitruvyan Explainability Engine
│       ├── vare/                      # Vitruvyan Attribution & Risk Engine
│       ├── vwre/                      # Vitruvyan Weighted Ranking Engine
│       ├── vhsw/                      # Vitruvyan Historical Sliding Window
│       ├── vmfl/                      # Vitruvyan Multi-Factor Learning
│       └── vsgs/                      # Vitruvyan Signal Generation System
│
├── domains/                           # FUORI DAL CORE → plugin packages
│   ├── finance/                       # Domain: Finance
│   │   ├── prompts/                  #   Prompt templates finance-specific
│   │   ├── nodes/                    #   Nodi LangGraph finance-specific
│   │   ├── config/                   #   YAML config (tickers, sectors, etc.)
│   │   └── algorithms.yaml          #   Quali algoritmi abilitare
│   ├── healthcare/                    # Domain: Healthcare (futuro)
│   ├── legal/                         # Domain: Legal (futuro)
│   └── template/                      # Domain: Template per nuovi verticali
│
├── services/                          # LIVELLO 2: Microservizi
│   ├── api_babel_gardens/             87 lines main.py
│   ├── api_codex_hunters/             75 lines main.py
│   ├── api_conclave/                  Bus service
│   ├── api_embedding/                 Embedding service
│   ├── api_graph/                     LangGraph service
│   ├── api_mcp/                       MCP Gateway
│   ├── api_memory_orders/             93 lines main.py
│   ├── api_neural_engine/             Scoring service
│   ├── api_orthodoxy_wardens/         87 lines main.py
│   ├── api_pattern_weavers/           62 lines main.py
│   ├── api_semantic/                  Semantic service
│   ├── api_vault_keepers/             59 lines main.py
│   └── monitoring/                    Prometheus exporter + Grafana
│
├── docs/                              # Documentazione strutturata
│   ├── architecture/                 #   ← SPOSTARE i 33 .md dalla root
│   ├── foundational/                 #   Charter, Bus Invariants, etc.
│   └── changelog/                    #   Changelogs per fase
│
├── tests/
├── infrastructure/
├── config/
└── .github/
```

---

## 🎯 7 Problemi Critici

### 1. `vitruvyan_proprietary/` nel posto SBAGLIATO (P1)

**Attuale**: `core/cognitive/vitruvyan_proprietary/` (dentro il core)

**Problema**:
- 6 algoritmi proprietari (VEE, VARE, VWRE, VHSW, VMFL, VSGS) sono **finance-heavy**
- Contengono terminologia "ticker", "stock", "sentiment", "portfolio"
- Un dominio healthcare/legal NON dovrebbe caricare questi algoritmi
- Sono **dentro cognitive/** che dovrebbe contenere solo Sacred Orders

**Target**: `vitruvyan_core/algorithms/` (pacchetto separato, caricabile on-demand)

**Beneficio**: `pip install vitruvyan-core` non include bagaglio finance. Domini specifici attivano algoritmi via `algorithms.yaml`.

### 2. `foundation/` è un DUPLICATO morto (P1)

**Attuale**:
- `foundation/cognitive_bus/` → VUOTO (0 files)
- `foundation/persistence/` → Re-export di `core/agents/` (2 righe ciascuno)
- `foundation/semantic_sync/` → VUOTO

**Problema**:
- Confonde i path di import (`core.foundation.persistence.PostgresAgent` vs `core.agents.PostgresAgent`)
- Nessuna funzionalità propria

**Target**: ELIMINARE completamente, redirect import in `__init__.py` se necessario

### 3. `monitoring/vsgs_metrics.py` è FINANCE-SPECIFIC (P2)

**Attuale**: Metriche VSGS (Vitruvyan Signal Generation System) nel core

**Problema**: VSGS è un algoritmo proprietario finance-first

**Target**: `algorithms/vsgs/metrics.py`

### 4. `governance/semantic_sync/vsgs_sync.py` è FINANCE-SPECIFIC (P2)

**Attuale**: Sync logic per segnali VSGS nella governance layer

**Problema**: Logica verticale nel namespace generico

**Target**: `algorithms/vsgs/sync.py`

### 5. 40+ nodi LangGraph mescolano core e finance (P3) — CORRETTO: 5 nodi finance-specific

**Attuale**: 20 nodi verificati in `orchestration/langgraph/node/`, di cui 10 agnostici, 5 misti (fix facile), 5 finance-hardcoded

**5 nodi ❌ FINANCE-SPECIFIC** (da spostare in `domains/finance/nodes/`):
- `intent_detection_node.py` (603 righe) — intent taxonomy, GPT prompt, synonym dict, screening filters
- `parse_node.py` (327 righe) — company→ticker map, budget €/$, intent fallback "portafoglio"
- `proactive_suggestions_node.py` (214 righe) — ticker correlation dict, earnings calendar, hedging
- `cached_llm_node.py` (540 righe) — BUY/HOLD/SELL prompts, composite scores, financial advisor persona
- `enhanced_llm_node.py` (181 righe) — "senior financial advisor", bullish/bearish keywords

**5 nodi ⚠️ MISTI** (meccanismo generico, residui configurabili):
- `route_node.py` — lista intenti hardcoded (fix: rendere configurabile)
- `params_extraction_node.py` — prompt "financial horizon" (fix: estrarre in config)
- `llm_soft_node.py` — guardrails BUY/SELL (fix: parametrizzare)
- `advisor_node.py` — stubbed ma con chiavi portfolio_data (fix: rinominare)
- `vault_node.py` — 1 stringa "financial_guardian" (fix: rimuovere)

**Target**: Nodi finance-specific → `domains/finance/nodes/`; nodi misti → configurazione

### 6. `synaptic_conclave/consumers/` ha logica VERTICALE (P3) — CONFERMATO + DETTAGLIO

**Attuale**:
- `risk_guardian.py` (613 righe) → ❌ FINANCE: Portfolio volatility, VARE integration, concentration risk >40%. **Ha già docstring "⚠️ DOMAIN MIGRATION NOTICE"** verso domains/finance/.
- `narrative_engine.py` (571 righe) → ❌ FINANCE: VEEEngine integration, ticker analysis narratives. **Ha già docstring "⚠️ DOMAIN MIGRATION NOTICE"** verso domains/finance/. Import path legacy: `core.vpar.vee.vee_engine`.
- `working_memory.py` (428 righe) → ✅ AGNOSTICO (corretto da audit precedente): Redis working memory generico con remember/recall/forget. ZERO finance nel codice.

**Anche nel bus**:
- `listeners/langgraph.py` (182 righe) → ❌ FINANCE: Canali "portfolio:snapshot_created", "portfolio:manual_check". Import path legacy: `core.leo.postgres_agent`.
- `events/event_schema.py` (797 righe) → ⚠️ MISTO: Enums generici, ma default schemas hanno "ticker", "sentiment.requested" nei template Babel.
- `utils/lexicon.py` (439 righe) → ⚠️ MISTO: SacredLexicon struttura generica, ma default schemas hanno "ticker" nei payload.

**Problema**: Business logic in un layer che dovrebbe essere **payload-blind** (violazione Bus Invariants). risk_guardian e narrative_engine hanno GIÀ la migrazione documentata nel codice stesso.

**Target**: Spostare risk_guardian e narrative_engine in Sacred Orders appropriati o in `domains/finance/`. Esternalizzare default schemas in config JSON caricabile.

### 7. 33 file .md alla root = disordine (P4)

**Attuale**: Work logs, audit reports, prompts, debug sessions alla root

**Problema**: Confonde la navigazione, non è documentazione strutturata

**Target**: `docs/architecture/` per documenti architetturali, `docs/changelog/` per log

---

## 📊 Matrice di Migrazione Dettagliata

### Priorità P1 — Bloccanti per agnosticità

| Modulo Attuale | Dove Va | Tipo | File Coinvolti | Rischio |
|---------------|---------|------|----------------|---------|
| `core/cognitive/vitruvyan_proprietary/` | `vitruvyan_core/algorithms/` | Spostamento | 18 .py | MEDIO — update import paths |
| `core/foundation/` | **ELIMINARE** | Rimozione | 5 .py (re-export) | BASSO — solo redirect |
| `vitruvyan_core/services/` (vuoto) | **ELIMINARE** | Rimozione | 1 __init__.py | NULLO |
| `vitruvyan_core/verticals/` (vuoto) | **ELIMINARE** | Rimozione | 1 README | NULLO |

### Priorità P2 — Finance leakage isolation

| Modulo Attuale | Dove Va | Tipo | File Coinvolti | Rischio |
|---------------|---------|------|----------------|---------|
| `core/monitoring/vsgs_metrics.py` | `algorithms/vsgs/metrics.py` | Spostamento | 1 | BASSO |
| `core/governance/semantic_sync/` | `algorithms/vsgs/sync.py` | Spostamento | 1 | BASSO |
| `core/cognitive/` Orders → `orders/` | Unificazione namespace | Rinominamento | ~60 | ALTO — import chain |
| `core/governance/` Orders → `orders/` | Unificazione namespace | Rinominamento | ~100 | ALTO — import chain |

### Priorità P3 — Purificazione nodi e consumers (NUMERI CORRETTI dopo verifica codice)

| Modulo Attuale | Dove Va | Tipo | File Coinvolti | Rischio |
|---------------|---------|------|----------------|---------|
| Nodi finance-specific (5, non 15) | `domains/finance/nodes/` | Spostamento | 5 (1,865 righe) | ALTO |
| Nodi misti (5, fix facile) | Stessa posizione, parametrizzati | Config refactor | 5 | MEDIO |
| `synaptic_conclave/consumers/` (2 verticali, non 3) | Sacred Orders / domains/ | Spostamento | 2 (1,184 righe) | MEDIO |
| `synaptic_conclave/listeners/langgraph.py` | `domains/finance/listeners/` | Spostamento | 1 (182 righe) | MEDIO |
| `domains/` → fuori dal core | Top-level `/domains/` | Spostamento | 11 | MEDIO |

### Priorità P4 — Pulizia

| Modulo Attuale | Dove Va | Tipo | File Coinvolti | Rischio |
|---------------|---------|------|----------------|---------|
| 33 .md alla root | `docs/architecture/` | Spostamento | 33 | NULLO |
| `services/core/`, `services/governance/` | **ELIMINARE** (legacy paths) | Rimozione | - | BASSO |
| `services/adapters/` (1 file) | `services/api_neural_engine/adapters/` | Spostamento | 1 | BASSO |

---

## 💡 Benefici Attesi

| Principio | Stato Attuale | Dopo Riorganizzazione |
|-----------|---------------|----------------------|
| **Agnosticità domini** | ⚠️ 40+ file finance nel core | ✅ Zero terminologia domain nel core |
| **Scalabilità funzionale** | ⚠️ Algoritmi hardcoded nel core | ✅ Plugin registry, config-driven |
| **Portabilità** | ⚠️ VSGS/VEE ovunque | ✅ `pip install vitruvyan-core` = core puro |
| **Sicurezza IP** | ⚠️ Proprietari esposti nel core | ✅ `algorithms/` = pacchetto separabile/licensable |
| **Leggibilità** | ⚠️ cognitive/ vs governance/ split | ✅ `orders/` namespace unico per Sacred Orders |
| **Spin-up domini** | ⚠️ Copia + rimuovi finance | ✅ `domains/template/` + YAML config |
| **Performance** | ⚠️ Carica tutto sempre | ✅ Lazy loading algoritmi configurati |
| **Documentazione** | ⚠️ 33 .md disordinati alla root | ✅ `docs/` strutturato |

---

## 🚀 Execution Plan (Suggerito)

### Fase 1: Quick Wins (2-4h)
1. Eliminare `foundation/` (duplicato morto)
2. Eliminare `vitruvyan_core/services/` e `vitruvyan_core/verticals/` (vuoti)
3. Spostare 33 .md → `docs/architecture/`
4. Eliminare `services/core/` e `services/governance/` (legacy paths)

### Fase 2: Algoritmi Proprietari (4-6h)
1. Creare `vitruvyan_core/algorithms/`
2. Spostare `vitruvyan_proprietary/` → `algorithms/`
3. Spostare `vsgs_metrics.py` → `algorithms/vsgs/`
4. Spostare `semantic_sync/vsgs_sync.py` → `algorithms/vsgs/`
5. Aggiornare import paths in services che usano algoritmi

### Fase 3: Unificazione Sacred Orders (6-8h)
1. Valutare se unificare `cognitive/` + `governance/` → `orders/`
2. Creare redirect imports per backward compatibility
3. Aggiornare services e tests

### Fase 4: Purificazione Nodi (8-12h)
1. Classificare nodi: generici vs finance-specific
2. Estrarre terminologia finance → config YAML
3. Spostare nodi finance-specific → `domains/finance/nodes/`

### Fase 5: Domains Isolation (4-6h)
1. Spostare `vitruvyan_core/domains/` → top-level `/domains/`
2. Creare `domains/template/` per nuovi verticali
3. Deduplicare contracts (domains/ vs contracts/)

---

## ⚠️ Rischi e Mitigazioni

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| Import path breakage | ALTO | Redirect `__init__.py` + deprecation warnings |
| Docker compose failure | ALTO | Update `PYTHONPATH` in Dockerfile |
| Test suite breakage | MEDIO | Run full suite dopo ogni fase |
| Service downtime | BASSO | Non toccare `services/api_*/main.py` |

---

**Ultimo aggiornamento**: February 12, 2026  
**Autore**: Architecture Audit (Copilot-assisted)  
**Stato**: PROPOSTA — In attesa di review
