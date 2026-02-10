# LangGraph Agnostic Refactoring Analysis
**Date**: February 9, 2026  
**Author**: AI Copilot (based on deep audit of vitruvyan + vitruvyan-core)  
**Status**: STRATEGIC PROPOSAL  
**Scope**: Migrate LangGraph from finance-monolith to domain-agnostic orchestrator

---

## 1. Executive Summary

LangGraph in vitruvyan è un monolite da **16,499 righe** su **35+ nodi** interamente accoppiato alla finanza. L'obiettivo è isolarne il **motore di orchestrazione** (agnostico) dai **nodi di dominio** (finanza), applicando lo stesso pattern LIVELLO 1 / LIVELLO 2 usato con successo per Orthodoxy Wardens e Synaptic Conclave.

**Dimensione del problema**:
- `graph_flow.py`: 733 righe (vitruvyan) vs 501 righe (vitruvyan-core, parzialmente ripulito)
- `GraphState`: ~100 campi tipizzati, **85% finance-specific**
- 35 nodi: **~6 agnostici**, **~10 infrastruttura** (pattern agnostico, config di dominio), **~18 finanza pura**
- vitruvyan-core ha già `domains/base_domain.py` (242 righe) con `EntitySchema`, `SignalSchema`, `ScoringFactor` — **ma non è connesso a LangGraph**

**Approccio proposto**: **Plugin Architecture con GraphEngine + NodeRegistry**

---

## 2. Stato Attuale — Due Mondi Divergenti

### 2.1 vitruvyan (produzione, 733 righe graph_flow.py)
```
35+ nodi hardcoded → GraphState con ~100 campi finanza
→ Routing condizionale con 25+ destinazioni finance
→ Sacred Flow: normalizer → orthodoxy → vault → compose → can → advisor → proactive → END
```

### 2.2 vitruvyan-core (tentativo di pulizia, 501 righe graph_flow.py)
- Rename parziale: `ticker_resolver_node` → `entity_resolver_node`
- Rimossi: shadow_trading, allocation, comparison, fundamentals, autopilot, portfolio_guardian
- **MA**: ancora `screener`, `portfolio_node`, `portfolio_review`, `portfolio_complete`
- **MA**: `GraphState` ha ancora `sentinel_portfolio_value`, routing menziona "screening | collection | allocation"
- **Problema**: è un copia-incolla ripulito, non una vera architettura agnostica

### 2.3 Cosa esiste di buono in vitruvyan-core
- `domains/base_domain.py` (242 righe) — contratto `BaseDomain` con ABC
- `domains/example_domain.py` — placeholder dimostrativo
- `domains/risk_contract.py`, `explainability_contract.py`, `aggregation_contract.py`
- **Questi contratti sono la BASE giusta** ma non sono collegati a LangGraph

---

## 3. Classificazione Nodi (35 nodi, 16,499 righe)

### 🟢 AGNOSTICI PURI (~1,350 righe)
Possono andare in vitruvyan-core così come sono (o con pulizia minima).

| Nodo | Righe | Motivo |
|------|-------|--------|
| `base_node.py` | 50 | ABC puro, nessun import di dominio |
| `orthodoxy_node.py` | 325 | Sacred Orders, comunicazione via CognitiveEvent |
| `vault_node.py` | 333 | Sacred Orders (⚠️ ha "portfolio", "investment" nelle keywords — parametrizzare) |
| `output_normalizer_node.py` | 86 | Pattern agnostico (route → risultato normalizzato), route names parametrizzabili |

### 🟡 INFRASTRUTTURA AGNOSTICIZZABILE (~6,500 righe)
Pattern agnostico, ma configurazione attualmente finance-specific. **Richiedono decomposizione**.

| Nodo | Righe | Pattern Agnostico | Dominio Hardcoded |
|------|-------|-------------------|-------------------|
| `parse_node.py` | 343 | Input parsing | `semantic_engine.parse_user_input()` estrae ticker, horizon |
| `intent_detection_node.py` | 880 | LLM intent classification | Intents: trend, momentum, risk, shadow_buy |
| `route_node.py` | 180 | Decision routing | Routes: shadow_buy, portfolio_review, allocation_exec |
| `params_extraction_node.py` | 339 | Parameter extraction | Estrae horizon (breve/medio/lungo), top_k |
| `semantic_grounding_node.py` | 524 | Vector search context | VSGS agnostico, ma schema collection potenzialmente finance |
| `babel_emotion_node.py` | 318 | Emotion detection | Agnostico (emozioni non sono domain-specific) |
| `weaver_node.py` | 166 | API bridge (httpx) | PatternWeaverClient agnostico nel pattern |
| `quality_check_node.py` | 575 | Validation pipeline | Pattern agnostico, checks finance-specific |
| `compose_node.py` | 2,332 | Narrative assembly (**IL MOSTRO**) | VEE, z-scores, tickers, fundamentals |
| `can_node.py` | 828 | Conversational advisor | LLM prompts finance-specific |

### 🔴 FINANZA PURA (~8,650 righe)
Restano in vitruvyan, NON migrano su vitruvyan-core.

| Nodo | Righe | Ragione |
|------|-------|---------|
| `ticker_resolver_node.py` | 405 | PostgreSQL ticker validation, LLM ticker extraction |
| `exec_node.py` | 110 | Chiama Neural Engine API (:8003) |
| `screener_node.py` | 199 | Neural Engine screener |
| `comparison_node.py` | 339 | Multi-ticker comparison |
| `sentiment_node.py` | 313 | Babel Gardens sentiment storage |
| `allocation_node.py` | 238 | Portfolio allocation optimization |
| `portfolio_analysis_node.py` | 510 | Portfolio quantitative analysis |
| `portfolio_guardian_node.py` | 460 | Portfolio risk monitoring |
| `portfolio_node.py` | 341 | Collection/portfolio analysis |
| `shadow_trading_node.py` | 223 | Shadow trading orders |
| `guardian_monitor_node.py` | 254 | Portfolio guardian agent |
| `autopilot_node.py` | 331 | Automated trading |
| `fundamentals_node.py` | 551 | yfinance fundamentals |
| `crew_node.py` | 680 | CrewAI strategic analysis |
| `codex_hunters_node.py` | 468 | Data collection orchestration |
| `llm_mcp_node.py` | 395 | MCP + OpenAI Function Calling |
| `llm_soft_node.py` | 194 | Soft LLM responses |
| `proactive_suggestions_node.py` | 276 | Domain-specific suggestions |
| `advisor_node.py` | 473 | Domain-specific decision advice |

---

## 4. I 4 Problemi Architetturali

### P1: GraphState Monolitico (~100 campi)
```python
# ATTUALE: Tutto in un TypedDict gigante
class GraphState(TypedDict, total=False):
    input_text: str                          # ← agnostico
    tickers: Optional[List[str]]             # ← FINANZA
    portfolio_data: Optional[Dict]           # ← FINANZA
    shadow_orders: Optional[Dict]            # ← FINANZA
    sentinel_portfolio_value: Optional[float] # ← FINANZA
    orthodoxy_status: Optional[str]          # ← agnostico
    # ... 90+ altri campi
```

**Solo ~15 campi sono agnostici**: input_text, route, result, error, response, user_id, intent, language_detected, emotion_detected, orthodoxy_*, vault_*, trace_id, vsgs_*, weaver_context, can_response.

### P2: Routing Hardcoded
```python
# ATTUALE: 25+ destinazioni finance nel dict
g.add_conditional_edges("decide", route_from_decide, {
    "dispatcher_exec": "sentiment_node",   # ← FINANZA
    "shadow_buy": "shadow_trading",        # ← FINANZA
    "portfolio_review": "collection",      # ← FINANZA
    "screener": "screener",                # ← FINANZA
    # ...
})
```

### P3: Import Monolitici
```python
# ATTUALE: 35+ import hardcoded in graph_flow.py
from core.langgraph.node.ticker_resolver_node import ticker_resolver_node
from core.langgraph.node.shadow_trading_node import shadow_trading_node
from core.langgraph.node.portfolio_analysis_node import portfolio_analysis_node
# ... 32 altri import
```

### P4: compose_node.py — Il Mostro (2,332 righe)
Il compose_node è il collo di bottiglia perché:
- Contiene VEE Engine integration (1,200+ righe)
- Slot-filling logic per finanza (tickers, horizon, budget)
- Narrative generation con z-scores, fundamentals, sentiment
- È il nodo più grande E il più accoppiato

---

## 5. Approccio Proposto: Plugin Architecture

### 5.1 Filosofia (Stessa di Orthodoxy/Conclave)

```
LIVELLO 1 (vitruvyan-core)     LIVELLO 2 (vitruvyan o altro vertical)
─────────────────────────      ─────────────────────────────────────
GraphEngine (builder)     ←──  FinanceGraphPlugin (registra nodi)
BaseGraphState (~15 campi) ←──  FinanceState (+85 campi)
NodeRegistry (ABC)        ←──  ticker_resolver, screener, etc.
RouteRegistry (ABC)       ←──  "shadow_buy"→shadow_trading, etc.
Sacred Flow (pipeline)    ←──  (usa direttamente quello di core)
```

### 5.2 Architettura Target

```
vitruvyan_core/
├── core/
│   ├── orchestration/
│   │   ├── graph_engine.py          ← NEW: Builder pattern domain-agnostic
│   │   ├── base_state.py            ← NEW: BaseGraphState (~15 campi)
│   │   ├── node_registry.py         ← NEW: NodeRegistry + BaseNodeContract
│   │   ├── route_registry.py        ← NEW: RouteRegistry
│   │   ├── sacred_flow.py           ← NEW: Reusable Sacred Flow pipeline
│   │   └── langgraph/               ← KEEP: LangGraph-specific implementation
│   │       ├── graph_flow.py        ← REFACTOR: Solo infrastruttura agnostica
│   │       ├── graph_runner.py      ← REFACTOR: Solo entry point agnostico
│   │       ├── node/
│   │       │   ├── base_node.py     ← KEEP as-is
│   │       │   ├── orthodoxy_node.py ← KEEP (Sacred Order)
│   │       │   ├── vault_node.py    ← KEEP (Sacred Order, parametrizzare keywords)
│   │       │   ├── output_normalizer_node.py ← KEEP (route names da registry)
│   │       │   ├── intent_detection_node.py  ← REFACTOR (intents da registry)
│   │       │   ├── parse_node.py    ← REFACTOR (parser injected dal dominio)
│   │       │   └── ...              ← Solo nodi agnostici
│   │       └── shared/
│   │           └── state_preserv.py ← KEEP as-is
│   └── governance/                  ← Invariato (oggi è ok)
└── domains/
    ├── base_domain.py               ← KEEP + ESTENDERE con GraphPlugin contract
    └── example_domain.py            ← KEEP

vitruvyan/                           (PRODUZIONE — FINANCE VERTICAL)
├── core/
│   └── langgraph/
│       ├── finance_plugin.py        ← NEW: FinanceGraphPlugin
│       ├── finance_state.py         ← NEW: FinanceState extension (+85 campi)
│       └── node/
│           ├── ticker_resolver_node.py  ← STAY (finanza pura)
│           ├── exec_node.py             ← STAY
│           ├── screener_node.py         ← STAY
│           ├── comparison_node.py       ← STAY
│           ├── shadow_trading_node.py   ← STAY
│           ├── allocation_node.py       ← STAY
│           ├── portfolio_*.py           ← STAY
│           ├── fundamentals_node.py     ← STAY
│           ├── compose_node.py          ← STAY (ma decomporlo)
│           └── ...                      ← 18 nodi finance
```

### 5.3 Contratti Chiave (Codice)

#### A) BaseGraphState — Lo Stato Agnostico
```python
# vitruvyan_core/core/orchestration/base_state.py

from typing import TypedDict, Optional, Dict, Any, List

class BaseGraphState(TypedDict, total=False):
    """Campi agnostici che QUALSIASI dominio ha."""
    
    # === Essenziali ===
    input_text: str
    route: str
    result: Dict[str, Any]
    error: Optional[str]
    response: Dict[str, Any]
    user_id: Optional[str]
    
    # === Intent & Language ===
    intent: Optional[str]
    language_detected: Optional[str]
    language_confidence: Optional[float]
    needs_clarification: Optional[bool]
    clarification_reason: Optional[str]
    
    # === Emotion (domain-agnostic) ===
    emotion_detected: Optional[str]
    emotion_confidence: Optional[float]
    emotion_intensity: Optional[str]
    _ux_metadata: Optional[Dict[str, Any]]
    
    # === Sacred Orders (domain-agnostic) ===
    orthodoxy_status: Optional[str]
    orthodoxy_verdict: Optional[str]
    orthodoxy_confidence: Optional[float]
    vault_status: Optional[str]
    vault_protection: Optional[str]
    
    # === Tracing ===
    trace_id: Optional[str]
    
    # === VSGS / Semantic Grounding ===
    semantic_matches: Optional[List[Dict[str, Any]]]
    vsgs_status: Optional[str]
    
    # === Weaver Context ===
    weaver_context: Optional[Dict[str, Any]]
    
    # === CAN / Compose Output ===
    can_response: Optional[Dict[str, Any]]
    conversation_type: Optional[str]
    follow_ups: Optional[List[str]]
    final_response: Optional[str]
    proactive_suggestions: Optional[List[Dict[str, Any]]]
```

**~30 campi vs ~100 attuali**. Il dominio aggiunge il resto.

#### B) GraphPlugin — Contratto di Estensione
```python
# vitruvyan_core/core/orchestration/graph_engine.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Tuple

class GraphPlugin(ABC):
    """Contratto che ogni dominio implementa per registrare i propri nodi."""
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Es: 'finance', 'logistics', 'healthcare'"""
        pass
    
    @abstractmethod
    def get_state_extensions(self) -> Dict[str, Any]:
        """Campi aggiuntivi per GraphState (es: tickers, portfolio, etc.)"""
        pass
    
    @abstractmethod
    def get_nodes(self) -> Dict[str, Callable]:
        """
        Mappa nome_nodo → handler function.
        Es: {"ticker_resolver": ticker_resolver_node, "screener": screener_node}
        """
        pass
    
    @abstractmethod
    def get_route_map(self) -> Dict[str, str]:
        """
        Mappa route_value → node_name.
        Es: {"dispatcher_exec": "sentiment_node", "shadow_buy": "shadow_trading"}
        """
        pass
    
    @abstractmethod
    def get_intents(self) -> List[str]:
        """
        Intents riconosciuti dal dominio.
        Es: ["trend", "momentum", "risk", "shadow_buy", "portfolio_review"]
        """
        pass
    
    @abstractmethod
    def get_entry_pipeline(self) -> List[str]:
        """
        Pipeline pre-routing specifica del dominio.
        Es: ["ticker_resolver"] (dopo entity_resolver, prima di babel_emotion)
        """
        pass
    
    @abstractmethod
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        """
        Edge aggiuntive post-routing.
        Es: [("sentiment_node", "exec"), ("exec", "quality_check")]
        """
        pass

class GraphEngine:
    """Domain-agnostic graph builder. Il cuore di vitruvyan-core."""
    
    def __init__(self):
        self._plugins: List[GraphPlugin] = []
    
    def register_plugin(self, plugin: GraphPlugin):
        self._plugins.append(plugin)
    
    def build(self) -> CompiledGraph:
        """
        Assembla il grafo:
        1. Crea GraphState mergiando BaseGraphState + estensioni dei plugin
        2. Registra nodi agnostici (parse, intent, orthodoxy, vault, compose, can, etc.)
        3. Registra nodi dei plugin
        4. Costruisce pipeline: parse → intent → [domain pipeline] → decide → [domain routing] → Sacred Flow → END
        5. Compila e restituisce
        """
        # ... implementazione ...
```

#### C) FinanceGraphPlugin (in vitruvyan, NON in vitruvyan-core)
```python
# vitruvyan/core/langgraph/finance_plugin.py

from vitruvyan_core.core.orchestration.graph_engine import GraphPlugin

class FinanceGraphPlugin(GraphPlugin):
    
    def get_domain_name(self) -> str:
        return "finance"
    
    def get_state_extensions(self) -> Dict[str, Any]:
        return {
            "tickers": Optional[List[str]],
            "validated_tickers": Optional[List[str]],
            "portfolio_data": Optional[Dict],
            "shadow_orders": Optional[Dict],
            "allocation_data": Optional[Dict],
            "comparison_matrix": Optional[Dict],
            "numerical_panel": Optional[List[Dict]],
            "vee_explanations": Optional[Dict],
            # ... 70+ campi finanza
        }
    
    def get_nodes(self) -> Dict[str, Callable]:
        return {
            "ticker_resolver": ticker_resolver_node,
            "sentiment_node": run_sentiment_node,
            "exec": exec_node,
            "screener": screener_node,
            "comparison": comparison_node,
            "shadow_trading": shadow_trading_node,
            "allocation": allocation_node,
            "portfolio_analysis": portfolio_analysis_node,
            "portfolio_guardian": portfolio_guardian_node,
            "guardian_monitor": guardian_monitor_node,
            "autopilot": autopilot_node,
            "fundamentals": fundamentals_node,
            "crew": crew_node,
            "codex_hunters": codex_hunters_node,
            "collection": portfolio_node,
        }
    
    def get_route_map(self) -> Dict[str, str]:
        return {
            "dispatcher_exec": "sentiment_node",
            "screener": "screener",
            "shadow_buy": "shadow_trading",
            "shadow_sell": "shadow_trading",
            "portfolio_review": "collection",
            "portfolio_analysis": "portfolio_analysis",
            "allocation_exec": "allocation",
            "comparison_exec": "comparison",
            "crew_strategy": "crew",
            "codex_expedition": "codex_hunters",
            "sentinel_monitoring": "sentinel",
        }
    
    def get_intents(self) -> List[str]:
        return [
            "trend", "momentum", "volatility", "risk",
            "sentiment", "allocate", "portfolio", "portfolio_review",
            "shadow_buy", "shadow_sell", "comparison",
        ]
    
    def get_entry_pipeline(self) -> List[str]:
        return ["ticker_resolver"]  # dopo entity_resolver generico
    
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        return [
            ("sentiment_node", "exec"),
            ("exec", "quality_check"),
        ]
```

---

## 6. Piano di Esecuzione (5 Fasi)

### Fase 0: Preparazione (2h)
- [ ] Creare `vitruvyan_core/core/orchestration/base_state.py` con BaseGraphState (~30 campi)
- [ ] Creare `vitruvyan_core/core/orchestration/graph_engine.py` con GraphPlugin ABC + GraphEngine builder
- [ ] Aggiornare `domains/base_domain.py` per collegare BaseDomain → GraphPlugin
- [ ] Test: `GraphEngine().build()` compila grafo vuoto senza errori

### Fase 1: Sacred Flow Extraction (3h)
- [ ] Estrarre `sacred_flow.py` — la pipeline normalizer → orthodoxy → vault → compose → can → advisor → proactive → END
- [ ] Questo è il **cuore agnostico**: qualsiasi dominio deve passare da qui
- [ ] Rimuovere da orthodoxy_node: keywords "portfolio", "investment" → parametrizzare
- [ ] Rimuovere da vault_node: keywords "portfolio", "investment" → parametrizzare
- [ ] Test: Sacred Flow funziona con stato vuoto (nessun campo finance)

### Fase 2: Infrastructure Nodes Decomposition (8h) — **IL GROSSO DEL LAVORO**
Decomporre i 10 nodi 🟡 in pattern agnostico + config di dominio:

| Nodo | Strategia |
|------|-----------|
| `parse_node.py` | Extract `Parser` ABC → Il dominio inietta il proprio parser (FinanceParser con semantic_engine) |
| `intent_detection_node.py` | Intents da `plugin.get_intents()` anziché hardcoded. LLM prompt template iniettato dal dominio |
| `route_node.py` | Routes da `plugin.get_route_map()`. Logica di routing generica (validated_entities, comparison detection, etc. parametrizzati) |
| `params_extraction_node.py` | `ParamsExtractor` ABC → FinanceParamsExtractor (horizon, top_k) |
| `compose_node.py` (2,332!) | **DECOMPOSIZIONE CRITICA**: Separare (a) slot-filling generico, (b) ExplainabilityEngine ABC (→VEE in finanza), (c) narrative assembly generico. Minimo 3 moduli. |
| `can_node.py` (828) | Separare (a) conversational framework generico, (b) domain-specific prompts (finanza). Prompt template strategy. |
| `quality_check_node.py` | `QualityChecker` ABC → FinanceQualityChecker |
| `babel_emotion_node.py` | **Già quasi agnostico**. Parametrizzare solo URL API. |
| `semantic_grounding_node.py` | **Già quasi agnostico (VSGS)**. Parametrizzare collection name. |
| `weaver_node.py` | **Già quasi agnostico**. Parametrizzare URL API. |

**Priorità**: compose_node.py è il bottleneck — decomporre PER PRIMO.

### Fase 3: GraphEngine Assembly (4h)
- [ ] Implementare `GraphEngine.build()` che:
  1. Merge BaseGraphState + plugin extensions in un TypedDict dinamico
  2. Registra nodi agnostici (parse, intent_detection, orthodoxy, vault, etc.)
  3. Registra nodi del plugin
  4. Costruisce pipeline: parse → intent → [domain nodes] → decide → [conditional routing] → Sacred Flow → END
  5. Applica `invoke_with_propagation()` wrapper
- [ ] `graph_runner.py` diventa `run_graph_once(engine: GraphEngine, input_text, user_id)`
- [ ] Test con ExamplePlugin (nessun nodo di dominio, solo Sacred Flow)

### Fase 4: Finance Plugin Migration (6h)
- [ ] Creare `FinanceGraphPlugin` in vitruvyan
- [ ] Registrare 18 nodi finance
- [ ] Registrare 15+ route finance
- [ ] Estendere stato con 85 campi finance
- [ ] `api_graph/main.py` → `engine.register_plugin(FinanceGraphPlugin())`
- [ ] E2E test: stessa funzionalità di prima con architettura nuova

### Fase 5: Cleanup vitruvyan-core graph_flow.py (2h)
- [ ] Rimuovere TUTTI i nodi finance dal graph_flow.py di vitruvyan-core
- [ ] Rimuovere TUTTI i campi finance da GraphState → usare BaseGraphState
- [ ] Rimuovere import `entity_resolver_node`, `screener_node`, `portfolio_node`
- [ ] `graph_flow.py` scende da 501 → ~150 righe (solo infrastruttura)
- [ ] Test: vitruvyan-core compila con ExampleDomain

**Tempo stimato totale**: ~25h

---

## 7. compose_node.py — Piano di Decomposizione Speciale

Il compose_node è **2,332 righe** — il nodo più grande e il più accoppiato. Merita un piano dedicato.

### Responsabilità attuali (miscelate):
1. **Slot-filling** (~300 righe): Controlla se mancano tickers, horizon, budget → genera domande
2. **VEE Engine integration** (~600 righe): Chiama VEEEngine per narrative 3-livello
3. **Result formatting** (~400 righe): Formatta numerical_panel, comparison_matrix, vee_explanations
4. **LLM narrative generation** (~500 righe): ConversationalLLM per arricchire risposte
5. **State management** (~500 righe): Merge states, preserve UX fields, handle edge cases

### Decomposizione proposta:
```
compose_node.py (2,332 righe)
├── slot_filler.py (~200 righe)            ← AGNOSTICO: ABC + domain slots
├── explainability_engine.py (~100 righe)  ← AGNOSTICO: ABC ExplainabilityEngine
├── result_formatter.py (~150 righe)       ← AGNOSTICO: Generic result → narrative
├── compose_node.py (~200 righe)           ← AGNOSTICO: Orchestrates above
├── finance_slot_filler.py (~200 righe)    ← FINANZA: tickers, horizon, budget
├── vee_adapter.py (~600 righe)            ← FINANZA: VEE Engine wrapper
└── finance_formatter.py (~400 righe)      ← FINANZA: numerical_panel, comparison
```

Risultato: compose_node.py agnostico scende a **~200 righe** (da 2,332).

---

## 8. GraphState Evolution — Strategia TypedDict Dinamica

### Problema
Python `TypedDict` è statico. Non puoi fare `GraphState.extend({"tickers": List[str]})` a runtime.

### Soluzioni (in ordine di praticabilità):

#### A) TypedDict Union (Consigliata ✅)
```python
# vitruvyan_core
class BaseGraphState(TypedDict, total=False):
    input_text: str
    route: str
    # ... 30 campi agnostici

# vitruvyan (finanza)
class FinanceGraphState(BaseGraphState, total=False):
    tickers: Optional[List[str]]
    portfolio_data: Optional[Dict]
    # ... 85 campi finanza

# graph_flow.py in vitruvyan usa FinanceGraphState
g = StateGraph(FinanceGraphState)
```
**Pro**: Semplice, type-safe, zero overhead runtime.  
**Contro**: Serve un import dal dominio in graph_flow.py (ma è in vitruvyan, non in core).

#### B) Dict[str, Any] con Schema Validation
```python
# Nessun TypedDict, validazione runtime
g = StateGraph(dict)
# Plugin valida i campi al runtime
```
**Pro**: Massimo disaccoppiamento.  
**Contro**: Zero type safety, debug più difficile.

#### C) TypedDict Factory
```python
# build_state_class(base_fields, extension_fields) → TypedDict class
def build_state_class(extensions: Dict) -> type:
    all_fields = {**BASE_FIELDS, **extensions}
    return TypedDict("GraphState", all_fields, total=False)
```
**Pro**: Dinamico E tipizzato.  
**Contro**: Complessità, tooling support incerto.

**Raccomandazione**: Opzione A (TypedDict Union). Semplice, pythonica, e il type checker funziona.

---

## 9. Differenza con il Refactoring di Oggi (Orthodoxy/Conclave)

| Aspetto | Orthodoxy/Conclave | LangGraph |
|---------|-------------------|-----------|
| Dimensione | ~300 righe/servizio | 16,499 righe totali |
| Accoppiamento | Basso (Redis events) | Alto (import diretti, shared state) |
| Livelli | 2 clean (L1 puro, L2 wrapper) | Tutto mescolato |
| Pattern | main.py snello + adapters | graph_flow.py monolitico |
| Difficoltà | 🟢 Bassa (4h/servizio) | 🔴 Alta (~25h totali) |
| Rischio | 🟢 Basso (servizi indipendenti) | 🔴 Alto (tutto dipende da graph_flow.py) |

**Lezione chiave**: Con Orthodoxy/Conclave il refactoring era "spostare e pulire". Con LangGraph è "decomporre e ricostruire".

---

## 10. Rischi e Mitigazioni

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| compose_node.py decomposition breaks narratives | 🔴 Alto | Mantenere compose_node intatto in vitruvyan fino a E2E green |
| TypedDict extension non funziona con LangGraph | 🟡 Medio | Test Fase 0 con TypedDict Union prima di commit |
| Plugin overhead degrada performance | 🟢 Basso | Plugin registra funzioni, zero overhead a runtime |
| Dual-repo sync complexity | 🟡 Medio | vitruvyan-core pubblica package, vitruvyan lo consuma come dependency |
| Regressione su routing condizionale | 🔴 Alto | Route map E2E test prima e dopo |

---

## 11. Metriche di Successo

### Pre-refactoring (oggi)
- `graph_flow.py` vitruvyan-core: 501 righe (ancora pieno di finanza)
- GraphState: 100+ campi (85% finance)
- Nodi in core: 35 (tutti copiati brutalmente, molti broken)
- Domain coupling: 95% (quasi tutto dipende da ticker, portfolio, etc.)

### Post-refactoring (target)
- `graph_flow.py` vitruvyan-core: **~150 righe** (solo infrastruttura)
- BaseGraphState: **~30 campi** (0% finance)
- Nodi in core: **~10** (solo agnostici: parse, intent, orthodoxy, vault, compose_skeleton, can_skeleton, etc.)
- Domain coupling: **0%** (nessun import finance in core)
- FinanceGraphPlugin in vitruvyan: **~200 righe** (registra 18 nodi + 85 campi)
- **Qualsiasi nuovo dominio** (logistics, healthcare) può usare lo stesso GraphEngine

---

## 12. Quick Wins — Cosa Fare Subito

Se non hai 25h disponibili, ecco le azioni che danno il massimo ROI:

1. **[2h] Creare `base_state.py`** — Isola i 30 campi agnostici. Impatto: definisce il confine.
2. **[2h] Creare `GraphPlugin` ABC** — Il contratto. Impatto: chiarisce a tutti cosa "agnostico" significa.
3. **[1h] Pulire graph_flow.py di vitruvyan-core** — Rimuovere i 18 nodi finance rimasti (screener, portfolio, etc.)

Queste 5h creano la **fondazione** su cui costruire tutto il resto.

---

## 13. Connessione con Domain Contracts Esistenti

vitruvyan-core ha già `domains/base_domain.py` con:
- `EntitySchema` (→ corrisponde a "tickers" in finanza, "routes" in logistics)
- `SignalSchema` (→ corrisponde a "momentum_z", "trend_z" in finanza)
- `ScoringFactor` (→ corrisponde ai pesi Neural Engine)
- `DomainPolicy` (→ corrisponde ai professional boundaries)

**Il collegamento mancante**: `BaseDomain` dovrebbe produrre un `GraphPlugin`:

```python
class BaseDomain(ABC):
    # ... existing methods ...
    
    @abstractmethod
    def get_graph_plugin(self) -> GraphPlugin:
        """Return the LangGraph plugin for this domain."""
        pass
```

Questo unifica l'architettura: **Un dominio = Un plugin = Tutto il necessario per funzionare in LangGraph**.

---

## Conclusione

L'approccio è chiaro: **Plugin Architecture** che separa il motore di orchestrazione (vitruvyan-core) dai nodi di dominio (vitruvyan/finance). Lo stesso pattern LIVELLO 1/LIVELLO 2 funziona, ma la complessità è 5x superiore rispetto a Orthodoxy/Conclave a causa dell'accoppiamento monolitico di graph_flow.py e del compose_node.py da 2,332 righe.

Il quick win è creare `base_state.py` + `GraphPlugin` ABC (5h) per definire il confine. Il resto segue naturalmente come con Sacred Orders.
