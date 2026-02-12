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
- **40+ file finance-leaky** nel core attivo (esclusi legacy/tests)

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
│   │   │   └── semantic_engine.py     ⚠️ STUB orfano (109 lines, passthrough)
│   │   ├── foundation/                ⚠️ DUPLICATO MORTO
│   │   │   ├── cognitive_bus/         VUOTO (0 files)
│   │   │   ├── persistence/           RE-EXPORT di core/agents/ (postgres_agent, qdrant_agent)
│   │   │   └── semantic_sync/         VUOTO
│   │   ├── governance/
│   │   │   ├── codex_hunters/         ✅ Sacred Order (10/10 dirs) — Perception
│   │   │   ├── memory_orders/         ✅ Sacred Order (9/10 dirs, manca docs/) — Memory
│   │   │   ├── orthodoxy_wardens/     ✅ Sacred Order (10/10 dirs) — Truth
│   │   │   ├── vault_keepers/         ✅ Sacred Order (10/10 dirs) — Memory/Archival
│   │   │   └── semantic_sync/         ⚠️ 1 file: vsgs_sync.py (VSGS = finance-specific)
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── llm_interface.py       ✅ CORE — ABC per LLM
│   │   │   ├── conversational_llm.py  ⚠️ Ha riferimenti "sentiment"
│   │   │   ├── cache_api.py           ✅ CORE
│   │   │   ├── cache_manager.py       ⚠️ Ha riferimenti "ticker/stock"
│   │   │   ├── gemma_client.py        ✅ CORE — Wrapper Gemma
│   │   │   └── prompts/
│   │   │       ├── registry.py        ✅ CORE — Prompt registry
│   │   │       ├── version.py         ✅ CORE
│   │   │       └── _legacy/           3 files (base_prompts, scenario_prompts)
│   │   ├── monitoring/
│   │   │   └── vsgs_metrics.py        ⚠️ FINANCE-SPECIFIC (VSGS = algoritmo proprietario)
│   │   ├── neural_engine/             ✅ CORE — Scoring generico con contracts
│   │   │   ├── engine.py             Engine principale
│   │   │   ├── scoring.py            Scoring framework
│   │   │   ├── composite.py          Composite scoring
│   │   │   ├── ranking.py            Ranking framework
│   │   │   └── domain_examples/      Mock implementations (ha ref finance)
│   │   ├── orchestration/             ⚠️ MISTO — core + finance-leaky
│   │   │   ├── base_state.py          ⚠️ Ha "ticker/portfolio/sentiment"
│   │   │   ├── graph_engine.py        ⚠️ Ha "ticker/stock"
│   │   │   ├── parser.py             ⚠️ Ha "ticker/trading"
│   │   │   ├── intent_registry.py     ✅ CORE
│   │   │   ├── route_registry.py      ✅ CORE
│   │   │   ├── sacred_flow.py         ⚠️ Ha "sentiment"
│   │   │   ├── compose/
│   │   │   │   ├── base_composer.py       ✅ CORE — ABC
│   │   │   │   ├── response_formatter.py  ✅ CORE — ABC
│   │   │   │   └── slot_filler.py         ✅ CORE — Generic slot filler
│   │   │   └── langgraph/
│   │   │       ├── graph_flow.py      ⚠️ Ha "sentiment/trading"
│   │   │       ├── graph_runner.py    ⚠️ Ha "sentiment"
│   │   │       └── node/             40+ nodi (dettaglio sotto)
│   │   └── synaptic_conclave/         ✅ CORE — Bus transport
│   │       ├── transport/
│   │       │   ├── streams.py         ✅ StreamBus (Redis Streams)
│   │       │   └── redis_client.py    ✅ Redis wrapper
│   │       ├── events/
│   │       │   ├── event_envelope.py  ✅ TransportEvent, CognitiveEvent
│   │       │   └── event_schema.py    ⚠️ Ha "sentiment/ticker"
│   │       ├── consumers/
│   │       │   ├── risk_guardian.py    ⚠️ VERTICALE — Risk logic in bus layer
│   │       │   ├── narrative_engine.py ⚠️ VERTICALE — Narrative in bus layer
│   │       │   └── working_memory.py   ⚠️ Ha "sentiment"
│   │       ├── listeners/
│   │       │   └── langgraph.py       ⚠️ Ha "sentiment/trading"
│   │       ├── utils/
│   │       │   └── lexicon.py         ⚠️ Ha "sentiment/stock"
│   │       ├── orthodoxy/             Validation layer
│   │       ├── governance/            Bus governance
│   │       └── philosophy/            charter.md
│   │
│   ├── contracts/                     ✅ CORE — Interfacce astratte
│   │   ├── data_provider.py           IDataProvider (ABC)
│   │   ├── scoring_strategy.py        IScoringStrategy (ABC)
│   │   ├── aggregation_contract.py    Aggregation ABC
│   │   ├── explainability_contract.py Explainability ABC
│   │   └── risk_contract.py           ⚠️ "risk" è finance-specifico?
│   │
│   ├── domains/
│   │   ├── base_domain.py             ✅ CORE — Domain contract ABC
│   │   ├── example_domain.py          ✅ Placeholder
│   │   ├── finance_plugin.py          ✅ Finance plugin (giusto qui)
│   │   ├── finance/                   ✅ Finance vertical
│   │   │   ├── response_formatter.py  Finance-specific formatter
│   │   │   ├── slot_filler.py         Finance-specific slot filler
│   │   │   └── prompts/              Finance prompt templates
│   │   ├── aggregation_contract.py    ⚠️ DUPLICATO di contracts/?
│   │   ├── explainability_contract.py ⚠️ DUPLICATO di contracts/?
│   │   └── risk_contract.py           ⚠️ DUPLICATO di contracts/?
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

## 🔴 Dettaglio: Nodi LangGraph (40+ files)

**Path**: `vitruvyan_core/core/orchestration/langgraph/node/`

### Nodi GENERICI (possono restare nel core)
| File | Righe | Ruolo |
|------|-------|-------|
| `base_node.py` | - | ABC base per tutti i nodi |
| `parse_node.py` | - | Input parsing |
| `intent_detection_node.py` | - | Intent detection (ma ha "sentiment") |
| `route_node.py` | - | Routing (ma ha "ticker") |
| `compose_node.py` | - | Response composition |
| `output_normalizer_node.py` | - | Output normalization |
| `mnemosyne_node.py` | - | Memory recall |
| `orthodoxy_node.py` | - | Governance validation |
| `audit_node_simple.py` | - | Audit logging |
| `quality_check_node.py` | - | Quality validation |
| `can_node.py` | - | CAN (Conversational Analysis) |
| `llm_mcp_node.py` | - | MCP tool calling |

### Nodi FINANCE-LEAKY (contengono "ticker/portfolio/sentiment/trading")
| File | Problema |
|------|----------|
| `advisor_node.py` | Ha "portfolio/sentiment/trading" |
| `proactive_suggestions_node.py` | Ha "sentiment/trading" |
| `entity_resolver_node.py` | Ha "ticker/stock" |
| `params_extraction_node.py` | Ha "ticker/portfolio" |
| `semantic_grounding_node.py` | Ha "ticker/sentiment" |
| `enhanced_llm_node.py` | Ha "ticker/sentiment" |
| `cached_llm_node.py` | Ha "ticker/sentiment" |
| `llm_soft_node.py` | Ha "sentiment" |
| `babel_gardens_node.py` | Signal extraction |
| `pattern_weavers_node.py` | Ontology resolution |
| `codex_hunters_node.py` | Data acquisition |
| `codex_node.py` | Data acquisition |
| `vault_node.py` | Archival |
| `archivarium_node.py` | Archival |
| `exec_node.py` | Execution |
| `gemma_node.py` | Gemma LLM |
| `emotion_detector.py` | Emotion detection |

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

### Area: orchestration/ (14 files)
- `base_state.py`, `graph_engine.py`, `parser.py`, `sacred_flow.py`
- `langgraph/graph_flow.py`, `graph_runner.py`
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

### Area: governance/ (7 files — Sacred Orders)
- `vault_keepers/domain/signal_archive.py`, `consumers/signal_archivist.py`
- `orthodoxy_wardens/governance/verdict_engine.py`, `governance/rule.py`, `governance/classifier.py`
- `orthodoxy_wardens/consumers/penitent_agent.py`, `consumers/inquisitor_agent.py`

### Area: altri (6 files)
- `monitoring/vsgs_metrics.py`, `llm/conversational_llm.py`, `llm/cache_manager.py`
- `agents/llm_agent.py`, `agents/qdrant_agent.py`
- `cognitive/semantic_engine.py` (stub con commenti finance)

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

### 5. 40+ nodi LangGraph mescolano core e finance (P3)

**Attuale**: 40 file in `orchestration/langgraph/node/`, 15+ con hardcoded finance terms

**Problema**:
- Nodi generici (parse, route, compose) mescolati con nodi domain-specific (advisor, proactive_suggestions)
- Difficile capire quali nodi servono per un dominio healthcare

**Target**:
- Nodi generici → `engine/orchestration/nodes/`
- Nodi finance-specific → `domains/finance/nodes/`

### 6. `synaptic_conclave/consumers/` ha logica VERTICALE (P3)

**Attuale**:
- `risk_guardian.py` → Logica risk assessment nel layer di trasporto
- `narrative_engine.py` → Generazione narrative nel bus
- `working_memory.py` → Ha riferimenti "sentiment"

**Problema**: Business logic in un layer che dovrebbe essere **payload-blind** (violazione Bus Invariants)

**Target**: Spostare in Sacred Orders appropriati o in `domains/finance/`

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
| `contracts/` duplicati in `domains/` | Deduplicazione | Rimozione | 3 | BASSO |

### Priorità P3 — Purificazione nodi e consumers

| Modulo Attuale | Dove Va | Tipo | File Coinvolti | Rischio |
|---------------|---------|------|----------------|---------|
| Nodi finance-specific (15+) | `domains/finance/nodes/` | Spostamento | 15 | ALTO |
| `synaptic_conclave/consumers/` (3 verticali) | Sacred Orders / domains/ | Spostamento | 3 | MEDIO |
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
