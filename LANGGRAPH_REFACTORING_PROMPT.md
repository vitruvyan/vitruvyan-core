# LangGraph Agnostic Refactoring — Prompt per il Collega

> **Questo prompt contiene TUTTO il contesto necessario per eseguire il refactoring del grafo LangGraph in vitruvyan-core.**  
> Leggilo con il documento `LANGGRAPH_AGNOSTIC_REFACTORING_ANALYSIS.md` (652 righe, la spec tecnica dettagliata).  
> Creato: 10 Feb 2026 | Repository: vitruvyan-core | Branch: main | Commit: `54d68e0`

---

## 🎯 LA TUA MISSIONE

Trasformare il grafo LangGraph in vitruvyan-core da **copia sporca del monolite finance** a **motore di orchestrazione domain-agnostic** con architettura a plugin.

Questo lavoro si inserisce in un refactoring globale più ampio (Sacred Orders) portato avanti in parallelo da un'altra persona. **Devi mantenere piena coerenza architetturale** con quanto già fatto.

---

## 🧠 CONTESTO: IL REFACTORING GLOBALE

### Cosa esiste e cosa sta succedendo

vitruvyan-core è il framework agnostico estratto dal monolite `vitruvyan` (piattaforma AI di trading). L'obiettivo è rendere vitruvyan-core riusabile per **qualsiasi dominio** (logistica, healthcare, etc.), mantenendo vitruvyan come implementazione verticale finance.

**Il refactoring segue l'architettura a 2 livelli:**

| Livello | Dove | Cosa contiene | Regola |
|---------|------|---------------|--------|
| **LIVELLO 1** — Foundational | `vitruvyan_core/core/` | Python puro. No I/O. No infrastruttura. Testabile in isolamento. | `@dataclass(frozen=True)`, no import di Redis/PostgreSQL/FastAPI |
| **LIVELLO 2** — Service | `services/api_<ordine>/` | FastAPI, StreamBus, PostgreSQL, Docker. | Importa DA Livello 1, MAI il contrario |

### Stato attuale del refactoring (10 Feb 2026)

| Componente | Stato | Chi lo fa | Note |
|------------|-------|-----------|------|
| **Orthodoxy Wardens** (Truth) | ✅ COMPLETO | Altro dev | Template complesso (L1 + L2 + listener) |
| **Synaptic Conclave** (Bus) | ✅ COMPLETO | Altro dev | Redis Streams, NON TOCCARE |
| **Vault Keepers** (Memory) | ✅ L1 COMPLETO | Altro dev | Service L2 da splittare (prossimo) |
| **Conclave API** | ✅ COMPLETO | Altro dev | Template leggero (L2) |
| **Neural Engine** (Reason) | ✅ CORE OK, fix applicati | Altro dev | Contracts + mocks + engine allineati |
| **LangGraph** (Orchestration) | ❌ DA FARE | **TU** | Il tuo lavoro |
| **6 servizi Sacred Orders** | ❌ DA FARE | Altro dev | Vault, MCP, Codex, Pattern, Memory, Babel |

### Il tuo lavoro NON dipende dal refactoring dei 6 servizi

Tu lavori su `vitruvyan_core/core/orchestration/`, l'altro dev lavora su `services/` e `vitruvyan_core/core/governance/`. I due workstream sono **paralleli e indipendenti**, ma devono convergere sugli stessi principi architetturali.

---

## 📋 COSA DEVI LEGGERE (in ordine)

1. **`LANGGRAPH_AGNOSTIC_REFACTORING_ANALYSIS.md`** (652 righe) — La spec tecnica del TUO lavoro. Contiene: classificazione 35 nodi, 4 problemi architetturali, architettura target, piano a 5 fasi, decomposizione compose_node, strategia TypedDict.

2. **`vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md`** (303 righe) — Il pattern LIVELLO 1 canonico. Il tuo lavoro deve rispettare gli stessi principi.

3. **`services/SERVICE_PATTERN.md`** (258 righe) — Il pattern LIVELLO 2 canonico. Per capire come i servizi interagiscono con il core.

4. **`NEURAL_ENGINE_REFACTORING_ANALYSIS.md`** (760 righe) — Come il Neural Engine (altro componente core) è stato allineato. Mostra il pattern contracts + domain_examples che DEVI replicare per il grafo.

5. **`vitruvyan_core/domains/base_domain.py`** (242 righe) — I contratti di dominio esistenti (`BaseDomain`, `EntitySchema`, `SignalSchema`, `ScoringFactor`). Il tuo `GraphPlugin` deve INTEGRARSI con questi, non duplicarli.

---

## 🏗️ L'ARCHITETTURA TARGET (dal documento di analisi)

### Schema sintetico

```
vitruvyan_core/core/orchestration/
├── base_state.py            ← NUOVO: BaseGraphState (~30 campi agnostici)
├── graph_engine.py          ← NUOVO: GraphEngine (builder) + GraphPlugin (ABC)
├── node_registry.py         ← NUOVO: NodeRegistry + BaseNodeContract
├── route_registry.py        ← NUOVO: RouteRegistry
├── sacred_flow.py           ← NUOVO: Pipeline normalizer→orthodoxy→vault→compose→can→advisor→proactive→END
└── langgraph/               ← ESISTENTE: Refactored
    ├── graph_flow.py        ← DA ~500 righe → ~150 righe (solo infrastruttura)
    ├── graph_runner.py      ← Refactored: entry point agnostico
    ├── node/                ← Solo nodi agnostici (~6-10 nodi)
    │   ├── base_node.py
    │   ├── orthodoxy_node.py
    │   ├── vault_node.py
    │   ├── output_normalizer_node.py
    │   ├── intent_detection_node.py  (intents da registry)
    │   ├── parse_node.py             (parser injected)
    │   ├── compose_node.py           (decomposed, ~200 righe)
    │   ├── can_node.py               (prompts template-based)
    │   └── ...
    └── shared/
```

Il dominio finance (vitruvyan) poi fa:
```python
from vitruvyan_core.core.orchestration.graph_engine import GraphEngine
engine = GraphEngine()
engine.register_plugin(FinanceGraphPlugin())
graph = engine.build()
```

---

## ⚠️ VINCOLI ARCHITETTURALI NON NEGOZIABILI

Questi vincoli vengono dal refactoring globale e sono già enforced in tutto il codice. **Violarli crea incoerenza.**

### 1. Direzione degli import: Service → Core, MAI il contrario
```python
# ✅ CORRETTO (il servizio importa dal core)
from vitruvyan_core.core.orchestration.base_state import BaseGraphState

# ❌ VIETATO (il core importa dal servizio)
from services.api_graph.finance_plugin import FinanceState
```

### 2. Nessun I/O in LIVELLO 1
```python
# ✅ CORRETTO: Pure Python, no side effects
class GraphPlugin(ABC):
    @abstractmethod
    def get_nodes(self) -> Dict[str, Callable]: ...

# ❌ VIETATO: Connessioni database nel core
import psycopg2
conn = psycopg2.connect(...)  # MAI nel core
```

### 3. PostgresAgent e QdrantAgent sono le UNICHE interfacce DB
```python
# ✅ CORRETTO
from core.agents.postgres_agent import PostgresAgent
pg = PostgresAgent()

# ❌ VIETATO
import psycopg2
conn = psycopg2.connect(host="161.97.140.157", ...)
```

### 4. Il Cognitive Bus (Synaptic Conclave) è CONGELATO
- NON modificare nulla in `vitruvyan_core/core/synaptic_conclave/`
- NON aggiungere eventi bus al grafo (il grafo è request-response, non event-driven)
- Il bus è per Sacred Orders (governance/truth/memory), NON per orchestrazione

### 5. Redis Streams è il trasporto canonico (NON Pub/Sub)
- `StreamBus` da `core/synaptic_conclave/transport/streams.py`
- Pub/Sub è deprecato (Jan 24, 2026)

### 6. Naming conventions uniformi
- Prefisso `core_` per Docker (non `omni_`, non `vitruvyan_`)
- Canali bus: dot notation `<servizio>.<dominio>.<azione>` (es. `codex.discovery.mapped`)
- `entity_id` (non `ticker`), `entity_name` (non `company_name`) nel core agnostico

### 7. Il Neural Engine è request-response, NON bus
Decisione architetturale (commit `b86d02f`): Il NE viene chiamato via HTTP (`:8003/screen`), non tramite eventi bus. Questo vale anche per il grafo: i nodi chiamano servizi via REST, non emettono eventi.

---

## 📊 LO STATO ATTUALE DI graph_flow.py (502 righe)

### Il problema in sintesi
`graph_flow.py` in vitruvyan-core è una **copia parzialmente ripulita** del monolite finance. Ha subito rename superficiali (`ticker` → `entity_id` in alcuni punti) ma:

- **GraphState ha ~100 campi** di cui ~85 sono finance-specific (sentinel_portfolio_value, shadow, allocation, crew, etc.)
- **35 nodi importati** di cui ~18 sono finanza pura (screener, portfolio, shadow_trading, etc.)
- **25+ route hardcoded** nel conditional routing (shadow_buy, portfolio_review, allocation_exec, etc.)
- **Nodi come compose_node.py (2,332 righe!)** sono monoliti accoppiati alla finanza

### Campi GraphState da RIMUOVERE (portare in FinanceState)
Tutto ciò che NON è in questa lista va spostato nel dominio:

**Campi agnostici da TENERE in BaseGraphState (~30):**
```
input_text, route, result, error, response, user_id, budget
intent, needs_clarification, clarification_reason
orthodoxy_*, vault_* (Sacred Orders)
sentinel_* → VALUTARE: il pattern Sentinel è agnostico (risk monitoring), ma i campi attuali sono finance
babel_status, sentiment_label, sentiment_score, language_detected, language_confidence, cultural_context
emotion_detected, emotion_confidence, emotion_intensity, emotion_secondary, emotion_reasoning
trace_id, semantic_matches, vsgs_status
weaver_context
can_response, can_mode, can_route, follow_ups, conversation_type
final_response, proactive_suggestions
_ux_metadata
```

**Campi finance da SPOSTARE (~70+):**
```
entity_ids (→ nel dominio come "tickers"), horizon, top_k, sentiment (legacy Dict)
raw_output, crew_*, sentinel_portfolio_value, conclave_event
advisor_recommendation, user_requests_action
babel_analysis_summary, babel_metrics, babel_timestamp
emotion_sentiment_label, emotion_sentiment_score, emotion_metadata
vsgs_elapsed_ms, vsgs_error
```

### Nodi da RIMUOVERE da graph_flow.py (restano in vitruvyan)
```python
# Questi import E nodi vanno ELIMINATI dal core:
screener_node          # Neural Engine screener (finanza)
portfolio_node         # Collection analysis (finanza)
codex_hunters_node     # Data collection (Codex è un Sacred Order, ma il nodo è finance-specific)
crew_node              # CrewAI strategic (finanza)
llm_mcp_node           # MCP + OpenAI (infrastructure, ma config è finance)
advisor_node           # Decision advice (finanza)
proactive_suggestions_node  # Suggerimenti proattivi (finanza)
sentinel_node          # Portfolio risk (finanza)
```

### Nodi che RESTANO nel core (agnostic puri + infrastruttura parametrizzabile)
```python
# AGNOSTICI PURI:
base_node              # ABC puro
orthodoxy_node         # Sacred Orders
vault_node             # Sacred Orders (parametrizzare keywords)
output_normalizer_node # Pattern agnostico

# INFRASTRUTTURA (da parametrizzare):
parse_node             # Parser ABC → il dominio inietta il proprio
intent_detection_node  # Intents da plugin.get_intents()
route_node             # Routes da plugin.get_route_map()
params_extraction_node # ParamsExtractor ABC
babel_emotion_node     # Già quasi agnostico
semantic_grounding_node # VSGS, già quasi agnostico
weaver_node            # API bridge, già quasi agnostico
quality_check_node     # QualityChecker ABC
compose_node           # DECOMPORRE (vedi sotto)
can_node               # Separare framework generico da prompts finance
cached_llm_node        # Agnostico (LLM caching)
```

---

## 🔑 IL PATTERN CHIAVE: GraphPlugin

Questo è il contratto che unifica tutto. Ogni dominio implementa un `GraphPlugin` per registrare i propri nodi, route, state extensions e intents.

```python
# vitruvyan_core/core/orchestration/graph_engine.py

class GraphPlugin(ABC):
    @abstractmethod
    def get_domain_name(self) -> str: ...
    
    @abstractmethod
    def get_state_extensions(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    def get_nodes(self) -> Dict[str, Callable]: ...
    
    @abstractmethod
    def get_route_map(self) -> Dict[str, str]: ...
    
    @abstractmethod
    def get_intents(self) -> List[str]: ...
    
    @abstractmethod
    def get_entry_pipeline(self) -> List[str]: ...
    
    @abstractmethod
    def get_post_routing_edges(self) -> List[Tuple[str, str]]: ...
```

**Collegamento con `domains/base_domain.py`**: Il contratto `BaseDomain` esistente deve produrre un `GraphPlugin`:
```python
class BaseDomain(ABC):
    @abstractmethod
    def get_graph_plugin(self) -> GraphPlugin: ...
```

Questo unifica: **Un dominio = Un plugin = Tutto il necessario per funzionare nel grafo**.

---

## 🎯 PIANO DI ESECUZIONE (5 Fasi, ~25h)

### Fase 0: Fondazioni (2h)
- Creare `base_state.py` con `BaseGraphState` (~30 campi)
- Creare `graph_engine.py` con `GraphPlugin` ABC + `GraphEngine` builder
- Collegare `BaseDomain.get_graph_plugin()`
- **Test**: `GraphEngine().build()` compila senza errori

### Fase 1: Sacred Flow Extraction (3h)
- Estrarre `sacred_flow.py`: normalizer → orthodoxy → vault → compose → can → advisor → proactive → END
- È il cuore agnostico: QUALSIASI dominio passa da qui
- Parametrizzare keywords in orthodoxy_node e vault_node (rimuovere "portfolio", "investment")
- **Test**: Sacred Flow funziona con stato vuoto

### Fase 2: Decomposizione Nodi Infrastruttura (8h) — IL GROSSO
Decomporre i nodi 🟡 in pattern agnostico + config di dominio. **Priorità critica: compose_node.py (2,332 righe!)**.

Decomposizione compose_node:
```
compose_node.py (2,332 righe) →
├── slot_filler.py (~200)        ← AGNOSTICO: ABC + domain slots
├── explainability_engine.py     ← AGNOSTICO: ABC ExplainabilityEngine
├── result_formatter.py (~150)   ← AGNOSTICO: Generic result → narrative
├── compose_node.py (~200)       ← AGNOSTICO: Orchestrates above modules
└── (in vitruvyan, NON in core):
    ├── finance_slot_filler.py   ← FINANZA: tickers, horizon, budget
    ├── vee_adapter.py           ← FINANZA: VEE Engine wrapper
    └── finance_formatter.py     ← FINANZA: numerical_panel, comparison
```

### Fase 3: GraphEngine Assembly (4h)
- Implementare `GraphEngine.build()` (merge state, registra nodi, costruisci pipeline)
- `graph_runner.py` diventa `run_graph_once(engine, input_text, user_id)`
- **Test**: ExamplePlugin (nessun nodo di dominio, solo Sacred Flow)

### Fase 4: Finance Plugin Migration (6h)
- Creare `FinanceGraphPlugin` **in vitruvyan** (NON in vitruvyan-core)
- Registrare 18 nodi finance, 15+ route, 85 campi estensione
- E2E test: stessa funzionalità con architettura nuova

### Fase 5: Cleanup graph_flow.py (2h)
- Rimuovere TUTTI i nodi/campi/import finance da vitruvyan-core
- `graph_flow.py` scende da 501 → ~150 righe
- **Test**: vitruvyan-core compila con ExampleDomain, zero import finance

---

## ⚡ QUICK WINS (se non hai 25h)

Le 3 azioni che danno il massimo ROI in 5h:

1. **[2h] Creare `base_state.py`** — Isola i ~30 campi agnostici. Definisce il confine.
2. **[2h] Creare `GraphPlugin` ABC** — Il contratto. Chiarisce cosa "agnostico" significa.
3. **[1h] Pulire graph_flow.py** — Rimuovere i 18 nodi finance rimasti. 501 → ~150 righe.

---

## 🔴 ERRORI DA EVITARE

### 1. NON fare rename superficiali
```python
# ❌ SBAGLIATO: rename cosmetico senza vera decomposizione
entity_ids = state.get("tickers")  # Rename ma logica identica
```

Il problema attuale di graph_flow.py è ESATTAMENTE questo: rename parziali senza vera architettura. Servono **contratti ABC** e **iniezione di dipendenze**, non ricerca-e-sostituisci.

### 2. NON decomporre compose_node con import circolari
```python
# ❌ SBAGLIATO: compose_node importa da finance
from vitruvyan.core.langgraph.node.vee_adapter import VEEAdapter  # circolare!

# ✅ CORRETTO: ExplainabilityEngine ABC in core, VEE implementa in vitruvyan
class ExplainabilityEngine(ABC):
    @abstractmethod
    def explain(self, result: Dict, level: str) -> str: ...
```

### 3. NON creare file di contratto senza test
Ogni nuova ABC deve avere almeno un test con mock implementation. Il pattern di riferimento è `vitruvyan_core/core/neural_engine/domain_examples/` che ha `mock_data_provider.py` e `mock_scoring_strategy.py`.

### 4. NON modificare il Cognitive Bus
`vitruvyan_core/core/synaptic_conclave/` è **congelato**. Se pensi che serve un evento bus nel grafo, FERMATI: il grafo è request-response, il bus è per Sacred Orders. Decisione architetturale confermata (commit `b86d02f`).

### 5. NON modificare Sacred Orders già completati
- `services/api_orthodoxy_wardens/` → ✅ FROZEN (template)
- `services/api_conclave/` → ✅ FROZEN (template)
- `vitruvyan_core/core/governance/orthodoxy_wardens/` → ✅ FROZEN
- `vitruvyan_core/core/governance/vault_keepers/` → ✅ FROZEN (L1 completo)

### 6. NON lasciare `os.getenv()` sparsi
Se crei config per il grafo, centralizza in un unico `config.py` (vedi `services/SERVICE_PATTERN.md`).

### 7. NON rompere `invoke_with_propagation()`
Il wrapper `invoke_with_propagation()` in fondo a `build_graph()` preserva campi UX durante la pipeline Sacred Orders. Questo pattern è agnostico e va mantenuto, ma i campi specifici vanno parametrizzati (non hardcoded emotion/sentiment).

---

## 📐 PATTERN DI RIFERIMENTO: Neural Engine

Il Neural Engine è il componente che più assomiglia architetturalmente a ciò che devi fare con LangGraph. Ecco il parallelismo:

| Neural Engine | LangGraph (target) |
|---------------|-------------------|
| `IDataProvider` (ABC) | `GraphPlugin.get_nodes()` |
| `IScoringStrategy` (ABC) | `GraphPlugin.get_route_map()` |
| `NeuralEngine.run()` orchestra il pipeline | `GraphEngine.build()` assembla il grafo |
| `domain_examples/mock_*.py` | Example plugin con nodi dummy |
| `engine.py` legge `metadata_columns` dal provider | `graph_flow.py` legge intents/routes dal plugin |

**Commit di riferimento**: `54d68e0` — fix allineamento contracts, mocks e metadata detection. Mostra il livello di pulizia atteso.

---

## 🧪 STRATEGIA DI TEST

### Per ogni fase, servono test che verificano:

1. **Compilazione**: `GraphEngine().build()` non crasha senza plugin
2. **Plugin vuoto**: Un `ExamplePlugin` con zero nodi produce un grafo che esegue solo Sacred Flow
3. **State isolation**: `BaseGraphState` non contiene campi finance
4. **Import isolation**: Nessun file in `core/orchestration/` importa da `services/` o da moduli finance
5. **Backward compatibility**: (Solo Fase 4) Il `FinanceGraphPlugin` produce lo stesso output del monolite attuale

### Struttura test consigliata
```
tests/
├── test_base_state.py           # BaseGraphState ha solo campi agnostici
├── test_graph_engine.py         # GraphEngine.build() con ExamplePlugin
├── test_graph_plugin_contract.py # GraphPlugin ABC enforcement
├── test_sacred_flow.py          # Sacred Flow pipeline execution
└── test_import_isolation.py     # Nessun import finance in core/orchestration/
```

---

## 📂 FILE CRITICI DA CONOSCERE

### Core Orchestration (IL TUO PERIMETRO)
| File | Righe | Stato | Azione |
|------|-------|-------|--------|
| `core/orchestration/langgraph/graph_flow.py` | 502 | ❌ Mescolato | Ridurre a ~150 (solo infrastruttura) |
| `core/orchestration/langgraph/graph_runner.py` | ~200 | ❌ Mescolato | Agnosticizzare entry point |
| `core/orchestration/langgraph/node/compose_node.py` | 2,332 | ❌ Monolite | Decomporre in 3-4 moduli agnostici |
| `core/orchestration/langgraph/node/can_node.py` | 828 | ❌ Finance prompts | Separare framework da prompts |
| `core/orchestration/langgraph/node/intent_detection_node.py` | 880 | ❌ Finance intents | Intents da registry |
| `core/orchestration/langgraph/node/quality_check_node.py` | 575 | ❌ Finance checks | QualityChecker ABC |
| `core/orchestration/langgraph/node/route_node.py` | 180 | ❌ Finance routes | Routes da registry |
| `core/orchestration/langgraph/node/parse_node.py` | 343 | ❌ Finance parsing | Parser ABC |
| `core/orchestration/langgraph/node/params_extraction_node.py` | 339 | ❌ Finance params | ParamsExtractor ABC |
| `core/orchestration/langgraph/node/orthodoxy_node.py` | 325 | ✅ Quasi agnostico | Parametrizzare keywords |
| `core/orchestration/langgraph/node/vault_node.py` | 333 | ✅ Quasi agnostico | Parametrizzare keywords |
| `core/orchestration/langgraph/node/base_node.py` | 50 | ✅ Agnostico puro | Tenere |
| `core/orchestration/langgraph/node/output_normalizer_node.py` | 86 | ✅ Agnostico | Tenere |
| `core/orchestration/langgraph/node/babel_emotion_node.py` | 318 | ✅ Quasi agnostico | Parametrizzare URL |
| `core/orchestration/langgraph/node/semantic_grounding_node.py` | 524 | ✅ VSGS agnostico | Parametrizzare collection |
| `core/orchestration/langgraph/node/weaver_node.py` | 166 | ✅ Quasi agnostico | Parametrizzare URL |

### Contratti & Domini (DEVI CONOSCERLI)
| File | Righe | Rilevanza |
|------|-------|-----------|
| `contracts/data_provider.py` | 165 | Pattern IDataProvider (riferimento per GraphPlugin) |
| `contracts/scoring_strategy.py` | 199 | Pattern IScoringStrategy (riferimento) |
| `domains/base_domain.py` | 242 | BaseDomain dove aggiungere `get_graph_plugin()` |
| `domains/example_domain.py` | ~100 | Dove creare ExampleGraphPlugin |

### Governance (NON TOCCARE, solo leggere per capire il pattern)
| File | Righe | Note |
|------|-------|------|
| `core/governance/SACRED_ORDER_PATTERN.md` | 303 | Pattern L1 canonico |
| `core/governance/orthodoxy_wardens/` | ~40 file | Template complesso |
| `core/governance/vault_keepers/` | ~20 file | Template L1 completato |

---

## 🔄 WORKFLOW DI COMMIT

Segui lo stesso pattern usato nel resto del refactoring:

```bash
# Dopo ogni fase completata:
git add vitruvyan_core/core/orchestration/
git commit -m "refactor(orchestration): Fase N — <descrizione>

- [cosa hai fatto punto 1]
- [cosa hai fatto punto 2]
- Test: [cosa hai verificato]"
git push origin main
```

**Convenzione commit**: `refactor(orchestration): ...` per distinzione dai commit `refactor(vault_keepers): ...` dell'altro dev.

---

## 🤝 SINCRONIZZAZIONE CON L'ALTRO DEV

### Aree di possibile conflitto
1. **`vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py`** — Tu parametrizzi le keywords, l'altro dev potrebbe toccare il nodo per aggiornare la governance. **Coordinatevi prima di modificarlo.**

2. **`vitruvyan_core/core/orchestration/langgraph/node/vault_node.py`** — Stessa situazione.

3. **`vitruvyan_core/domains/base_domain.py`** — Tu aggiungi `get_graph_plugin()`. L'altro dev potrebbe estenderlo per altri scopi. **Comunica la modifica prima.**

4. **`vitruvyan_core/core/orchestration/langgraph/graph_flow.py`** — Solo tu lo tocchi. L'altro dev NON dovrebbe modificarlo.

### Regola d'oro
> **Se devi modificare un file FUORI da `core/orchestration/`, parlane prima con l'altro dev.**  
> Se resti DENTRO `core/orchestration/`, hai carta bianca.

---

## ✅ CHECKLIST DI COMPLETAMENTO

Quando hai finito, verifica:

- [ ] `graph_flow.py` < 150 righe, zero import finance
- [ ] `BaseGraphState` ha ~30 campi, zero campi finance
- [ ] `GraphPlugin` ABC implementato e testato con ExamplePlugin
- [ ] `GraphEngine.build()` compila e produce grafo funzionante
- [ ] Sacred Flow (normalizer→orthodoxy→vault→compose→can→advisor→proactive→END) estratto e testato
- [ ] compose_node.py decomposto in 3+ moduli agnostici
- [ ] `domains/base_domain.py` ha `get_graph_plugin()` method
- [ ] Zero `os.getenv()` sparsi (tutto in config)
- [ ] Zero import circolari core → service
- [ ] Tutti i test passano
- [ ] Commit atomici per fase con messaggi descrittivi

---

## 📚 GLOSSARIO RAPIDO

| Termine | Significato |
|---------|-------------|
| **Sacred Orders** | Subsistemi cognitivi (Perception, Memory, Reason, Discourse, Truth) |
| **LIVELLO 1** | Python puro, no infrastructure, testabile in isolamento |
| **LIVELLO 2** | FastAPI + Redis + PostgreSQL + Docker |
| **Sacred Flow** | Pipeline post-routing: normalizer→orthodoxy→vault→compose→can→advisor→proactive→END |
| **GraphPlugin** | Contratto ABC che un dominio implementa per registrare nodi/route/state |
| **BaseGraphState** | TypedDict con ~30 campi agnostici (il dominio estende con ereditarietà) |
| **VSGS** | Vitruvyan Semantic Grounding System (vector search per contesto conversazionale) |
| **VEE** | Vitruvyan Explainability Engine (narrativa 3 livelli — in vitruvyan, NON in core) |
| **CAN** | Conversational Advisor Node (framework conversazionale) |
| **Cognitive Bus** | Redis Streams event backbone (Synaptic Conclave) |
| **Orthodoxy Wardens** | Audit e validazione output (Sacred Order: Truth) |
| **Vault Keepers** | Archiviazione e versionamento (Sacred Order: Memory) |

---

*Generato il 10 Feb 2026, commit `54d68e0`. Buon lavoro! 🏛️*
