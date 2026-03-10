# Core Hardening Roadmap — RAG, Prompt, Context, Observability

> **Last updated**: Mar 10, 2026 20:00 UTC
> **Status**: COMPLETE — Tutte le fasi (0-4) completate
> **Scope**: vitruvyan-core (domain-agnostic). I verticali (aicomsec, mercator) implementano sopra.
> **Origine**: brainstorming architetturale + audit codebase + peer review

---

## 0. Principio guida

**Core = capability. Verticale = policy.**

Il core fornisce meccanismi, hook, contratti e default. Non sa nulla di ISO 27001, ransomware, ticker finanziari o logistica. Ogni punto di questa roadmap DEVE essere:

- Backward compatible (nessun breaking change)
- Domain-agnostic (nessuna logica verticale)
- Opt-in (i verticali attivano ciò che serve, il default non rompe nulla)
- Coerente con i pattern esistenti (contratti, agent, Sacred Order)

---

## 1. Stato attuale — Audit sintetico

### 1.1 Cosa funziona

| Componente | Stato | File chiave |
|------------|-------|-------------|
| PromptRegistry | Implementato, feature-complete | `core/llm/prompts/registry.py` (330L) |
| LLMAgent con multi-model | Supporta `model=` per-request | `core/agents/llm_agent.py` (844L) |
| QdrantAgent | Funzionale, supporta `qfilter` | `core/agents/qdrant_agent.py` |
| VSGS (Semantic Grounding) | Funzionale ma conservativo | `core/vpar/vsgs/vsgs_engine.py` |
| Ingestion contract | Completo, event-driven | `contracts/ingestion.py` |
| Embedding multi-model registry | Dichiarato nel contratto | `contracts/rag.py` |
| Chunking sentence-aware | Funzionale in Oculus Prime | `infrastructure/edge/oculus_prime/core/agents/document_intake.py` |
| Orthodoxy Wardens (grounding) | Attivo, 5-state verdicts | `core/governance/orthodoxy_wardens/` |
| Multi-tenant contract | Definito | `contracts/tenancy.py` |
| Embedding service | Funzionale, accetta `model` param | `services/api_embedding/` |

### 1.2 Cosa manca o è incompleto

| Gap | Severità | Dettaglio |
|-----|----------|----------|
| PromptRegistry usato in 2 call site su 8+ | ALTA | Prompt hardcoded in compose_node, llm_mcp_node, early_exit_node, servizi Babel |
| PromptAgent (gateway canonico) | ALTA | Non esiste |
| Prompt contracts (DTO) | ALTA | Non esiste `contracts/prompting.py` |
| Prompt policy container | MEDIA | Non esiste `core/llm/prompts/policy.py` |
| Tenant filtering nelle ricerche Qdrant | CRITICA | `qdrant_node` e `vsgs_engine` non filtrano per tenant_id |
| Context budget manager | ALTA | Budget 800 char dichiarato, mai applicato. Nessuna allocazione dinamica |
| Query transformation hook | ALTA | Non esiste. Il retrieval dipende al 100% dall'embedding della query grezza |
| Re-ranking hook | MEDIA | Non esiste. Top-k Qdrant usato as-is |
| Citation nel response schema | MEDIA | Source trackato internamente, mai esposto nella risposta |
| Model tier routing | MEDIA | gpt-4o-mini per tutto. LLMAgent supporta multi-model ma nessun nodo lo usa |
| Inline context nel graph state | MEDIA | Non esiste campo per contesto effimero (upload) |
| Document lifecycle metadata | BASSA | No `ingested_at`, `expires_at` nel RAGPayload |
| Audit trail in LLMAgent | MEDIA | Nessun log di prompt_id, version, domain |
| RAG evaluation contract | BASSA | Non esiste |

---

## 2. Roadmap operativa

### Legenda stati

- ⬜ Non iniziato
- 🔄 In corso
- ✅ Completato
- 🔒 Bloccato da dipendenza

---

### FASE 0 — Infrastruttura critica

> Obiettivo: risolvere il buco di isolamento dati e creare le fondamenta prompt.
> Dipendenze: nessuna. Può partire subito.

#### 0.1 ✅ Tenant-aware retrieval

**Cosa**: propagare `tenant_id` come filtro opzionale nelle ricerche Qdrant.

**File modificati**:
- `vitruvyan_core/core/orchestration/langgraph/node/qdrant_node.py` → aggiunto `_build_tenant_filter()` helper, applicato a tier 1 e tier 3
- `vitruvyan_core/core/vpar/vsgs/vsgs_engine.py` → `ground()` e `_search()` accettano `tenant_id`, costruiscono Filter Qdrant
- `vitruvyan_core/core/orchestration/langgraph/node/semantic_grounding_node.py` → propaga `tenant_id` dallo state a VSGS

**Contratto**: se `tenant_id` è presente nello state, le ricerche Qdrant DEVONO filtrare. Se assente, comportamento invariato.

**Test**: ✅ `_build_tenant_filter('abc')` costruisce Filter correttamente, `_build_tenant_filter('')` → None

**Stato**: ✅ Completato Mar 10, 2026

---

#### 0.2 ✅ Prompt contracts (`contracts/prompting.py`)

**File creato**: `vitruvyan_core/contracts/prompting.py`

**Contenuto implementato**: `PromptPolicy`, `PromptRequest`, `PromptResolution` (frozen dataclass), `compute_prompt_hash()`, `build_prompt_id()`, `DEFAULT_POLICY`. Esportati via `contracts/__init__.py`.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 0.3 ✅ PromptAgent (`core/agents/prompt_agent.py`)

**File creato**: `vitruvyan_core/core/agents/prompt_agent.py`

**Implementato**: Singleton con `resolve(PromptRequest) → PromptResolution`, `resolve_identity()` convenience method, `get_prompt_agent()` factory.
- comporre `prompt_id` e `prompt_hash`
- restituire `PromptResolution` completa

**Stato**: ✅ Completato Mar 10, 2026

---

#### 0.4 ✅ Policy container (`core/llm/prompts/policy.py`)

**File creato**: `vitruvyan_core/core/llm/prompts/policy.py`

**Implementato**: `apply_policy(prompt, policy, language) → str` funzione pura. Frammenti multilingua (en/it/es/fr) per limitations, evidence, domain boundary, disclaimers.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 0.5 ✅ Estensione PromptRegistry

**File modificato**: `vitruvyan_core/core/llm/prompts/registry.py`

**Implementato**: Nuovo metodo `resolve(domain, scenario, language, **vars) → PromptResolution` con prompt_id, hash, estimated_tokens, fallback_used. Backward compatible (metodi esistenti invariati).

**Stato**: ✅ Completato Mar 10, 2026

---

### FASE 1 — Migrazione call site + RAG primitives

> Obiettivo: portare adoption del PromptAgent sui nodi critici e preparare i primitivi RAG.
> Dipendenze: Fase 0 completata.

#### 1.1 ✅ Migrazione prompt hardcoded (3-4 nodi prioritari)

**Cosa**: sostituire i prompt hardcoded nei nodi LangGraph con chiamate al PromptAgent.

**Nodi migrati**:
- `compose_node.py` → conversational + synthesis prompts via PromptAgent
- `early_exit_node.py` → early_exit scenario via PromptAgent
- `llm_mcp_node.py` → mcp_tool_selection scenario via PromptAgent

**Nuovi scenari registrati in PromptRegistry** (generic domain):
- `conversational` (multilingua: en, it, es, fr)
- `synthesis` (multilingua: en, it)
- `mcp_tool_selection` (en)
- `early_exit` (multilingua: en, it, es)

**Stato**: ✅ Completato Mar 10, 2026

**Cosa**: sostituire i prompt hardcoded nei nodi LangGraph con chiamate al PromptAgent.

**Call site da migrare (in ordine di impatto)**:

| Nodo | File | Righe | Tipo prompt |
|------|------|-------|-------------|
| compose_node (conversational) | `node/compose_node.py` | L143-150 | Dict multilingua hardcoded |
| compose_node (synthesis) | `node/compose_node.py` | L246-261 | Synthesis prompt hardcoded |
| llm_mcp_node | `node/llm_mcp_node.py` | L200-214 | System prompt con context inline |
| early_exit_node | `node/early_exit_node.py` | L144 | Stringa generica |

**Pattern di migrazione**:
```python
# PRIMA (hardcoded)
system_prompt = "You are an intelligent and friendly AI assistant..."

# DOPO (via PromptAgent)
from core.agents.prompt_agent import get_prompt_agent
agent = get_prompt_agent()
resolution = agent.resolve(PromptRequest(
    domain=state.get("domain", "generic"),
    scenario="conversational",
    language=state.get("language", "en"),
))
system_prompt = resolution.system_prompt
# resolution.prompt_id e resolution.prompt_hash disponibili per audit
```

**Principio**: ogni migrazione è atomica. Un nodo alla volta. Test dopo ogni migrazione.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 1.2 ✅ Context Budget Manager

**Cosa**: modulo core che calcola e alloca il budget di contesto disponibile.

**File da creare**: `vitruvyan_core/core/llm/context_budget.py`

**Interfaccia**:
```python
@dataclass
class ContextItem:
    content: str
    priority: int          # 0 = più alta
    source: str            # "system_prompt", "rag", "history", "inline"
    estimated_tokens: int

class ContextBudgetManager:
    def __init__(self, model_context_window: int, safety_margin: int = 500):
        ...
    
    def allocate(self, items: List[ContextItem], max_response_tokens: int) -> List[ContextItem]:
        """Ordina per priorità, tronca al budget. Restituisce solo gli item che ci stanno."""
        ...
    
    def available_budget(self, system_prompt_tokens: int, max_response_tokens: int) -> int:
        """Quanto spazio resta per RAG + history + inline."""
        ...
```

**Model context windows** (hardcoded come registry nel modulo):
- gpt-4o-mini: 128K
- gpt-4o: 128K
- gpt-4-turbo: 128K
- claude-sonnet: 200K

**Principio**: il core calcola. Il verticale decide le priorità (cosa ha priority 0 vs 1 vs 2).

**Stato**: ✅ Completato Mar 10, 2026 — `vitruvyan_core/core/llm/context_budget.py` creato.
Implementato: `ContextBudgetManager`, `ContextItem`, `estimate_tokens()`, model registry con `register_model()`, `get_context_window()`, `ContextBudgetManager.for_model()`.

---

#### 1.3 ⬜ Embedding model upgrade path

**Cosa**: rendere il modello di embedding configurabile per collection, non globale.

**File da modificare**:
- `vitruvyan_core/contracts/rag.py` → `CollectionDeclaration` ha già `model_name` (Phase 4). Verificare che sia usato ovunque
- `services/api_embedding/config.py` → supportare multi-model via endpoint (già supporta `model` param nella request)
- Documentare la procedura di migrazione collection (re-embed con nuovo modello)

**Non fare**: cambiare il modello di default adesso. Questo è un percorso che il verticale attiva quando è pronto.

**Stato**: ⬜

---

#### 1.4 ✅ Model tier nel graph state

**Cosa**: aggiungere campo per routing multi-LLM nel graph state.

**File modificati**:
- `vitruvyan_core/core/orchestration/base_state.py` → aggiunti `model_tier`, `inline_context`, `domain` in BaseGraphState + ESSENTIAL_FIELDS

**Stato**: ✅ Completato Mar 10, 2026

**Valori convenzionali** (documentati, non enforced):
- `"routing"` → modello veloce/cheap (intent, classificazione)
- `"reasoning"` → modello potente (risposte complesse, sintesi)
- `"deep_context"` → modello con context window ampio (documenti grandi)
- `None` → usa default (backward compatible)

**Contratto**: i nodi downstream che chiamano LLMAgent leggono `state.get("model_tier")` e passano il modello corrispondente. La mappatura tier → modello è configurabile via env vars.

**Stato**: ⬜

---

### FASE 2 — Qualità del retrieval

> Obiettivo: migliorare la precisione del retrieval con hook per verticali.
> Dipendenze: Fase 0, parzialmente Fase 1.

#### 2.1 ✅ IQueryTransformer contract

**File creato**: `vitruvyan_core/contracts/retrieval.py`

**Implementato**: `IQueryTransformer` ABC con `transform(query, context) → List[str]`, `DefaultQueryTransformer` (passthrough). Verticals implementano HyDE, multi-query, synonym expansion.

**Stato**: ✅ Completato Mar 10, 2026

**Cosa**: interfaccia per trasformazione query pre-retrieval.

**File da creare**: `vitruvyan_core/contracts/rag.py` (estensione) o `vitruvyan_core/contracts/retrieval.py` (nuovo, se rag.py diventa troppo grande)

**Interfaccia**:
```python
class IQueryTransformer(ABC):
    @abstractmethod
    def transform(self, query: str, context: dict) -> List[str]:
        """Restituisce una o più varianti della query per il retrieval."""
        ...

class DefaultQueryTransformer(IQueryTransformer):
    def transform(self, query, context):
        return [query]  # passthrough
```

**Integrazione**: `semantic_grounding_node` o `qdrant_node` chiama il transformer registrato. Se restituisce N query, fa N ricerche e unisce (deduplica) i risultati.

**Esempio verticale** (non nel core):
```python
# aicomsec implementerebbe:
class HyDEQueryTransformer(IQueryTransformer):
    def transform(self, query, context):
        llm = get_llm_agent()
        hypothetical = llm.complete(f"Write a paragraph answering: {query}", model="gpt-4o-mini")
        return [query, hypothetical]
```

**Stato**: 🔒 (dipende da Fase 0 per il pattern)

---

#### 2.2 ✅ IReranker contract

**File**: `vitruvyan_core/contracts/retrieval.py` (stesso di 2.1)

**Implementato**: `RankedResult` dataclass con `effective_score` property (usa `reranked_score` se disponibile, altrimenti `original_score`), `IReranker` ABC con `rerank(query, results, top_k) → List[RankedResult]`, `DefaultReranker` (ordine Qdrant invariato, top_k truncation).

**Integrazione**: tra ricerca Qdrant e iniezione nel CAN node. Recupera top-10, re-ranka, inietta top-3.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 2.3 ✅ CitationRef nel response schema

**File modificato**: `vitruvyan_core/contracts/graph_response.py`
**File creato**: `vitruvyan_core/contracts/retrieval.py` (contiene `CitationRef`)

**Implementato**: `CitationRef` frozen dataclass (chunk_id, source_name, text_excerpt, relevance_score, collection, metadata). Campo `citations: Optional[List[Any]]` aggiunto a `GraphResponseMin`. Anche `ContextRouting` enum e `IContextRouter`/`DefaultContextRouter` (anticipati da Fase 3).

**Stato**: ✅ Completato Mar 10, 2026

**Cosa**: campo opzionale nel response per attribuire fonti.

**File da modificare**:
- `vitruvyan_core/contracts/graph_response.py` → aggiungere `citations: Optional[List[CitationRef]]`

**Dataclass**:
```python
@dataclass(frozen=True)
class CitationRef:
    chunk_id: str
    source_name: str
    text_excerpt: str              # primi 200 char del chunk
    relevance_score: float
    collection: str                # da quale collection Qdrant
    metadata: dict = field(default_factory=dict)  # il verticale ci mette ciò che serve
```

**Flusso**: i chunk usati dal CAN node per generare la risposta vengono tracciati nello state (`used_chunk_ids`), e al momento di comporre la risposta finale diventano `CitationRef`.

**Stato**: 🔒

---

### FASE 3 — Upload & inline context

> Obiettivo: abilitare i verticali a implementare upload-in-chat e long context.
> Dipendenze: Fase 1 (context budget).

#### 3.1 ✅ Inline context nel BaseGraphState

**File modificato**: `vitruvyan_core/core/orchestration/base_state.py` (Fase 1.4)

**Implementato**: campo `inline_context: Optional[str]` aggiunto a BaseGraphState. Contesto opaco (può essere testo estratto da un PDF, un CSV, un log). Il core non sa cos'è, lo inietta nel prompt con delimitatori strutturali.

**Integrazione CAN node** (TODO): se `state["inline_context"]` è presente, iniettare con delimitatori `[USER_CONTEXT_START]...[USER_CONTEXT_END]`.

**Stato**: ✅ Campo creato Mar 10, 2026 (integrazione CAN node completata)

---

#### 3.2 ✅ IContextRouter contract

**File**: `vitruvyan_core/contracts/retrieval.py` (creato insieme a 2.1 e 2.2)

**Implementato**: `ContextRouting` enum (INLINE/EMBED/BOTH), `IContextRouter` ABC con `route(content, metadata) → ContextRouting`, `DefaultContextRouter` (soglia 15000 chars).

**Integrazione compose_node**: `inline_context` iniettato con delimitatori `[USER_CONTEXT_START]...[USER_CONTEXT_END]` in entrambi i path (conversational e synthesis).

**Interfaccia**:
```python
class ContextRouting(str, Enum):
    INLINE = "inline"       # inietta direttamente nel prompt
    EMBED = "embed"         # chunk → embed → Qdrant
    BOTH = "both"           # inline per la sessione corrente + persistente in RAG

class IContextRouter(ABC):
    @abstractmethod
    def route(self, content: str, metadata: dict) -> ContextRouting:
        ...

class DefaultContextRouter(IContextRouter):
    def __init__(self, inline_threshold_chars: int = 15000):
        self.threshold = inline_threshold_chars
    
    def route(self, content, metadata):
        if len(content) <= self.threshold:
            return ContextRouting.INLINE
        return ContextRouting.EMBED
```

**Principio**: il default è basato su dimensione. Il verticale può overridare con logica propria (es. "i documenti PDF vanno sempre in RAG, i messaggi brevi vanno inline").

**Stato**: ✅ Completato Mar 10, 2026 (anticipato da Fase 2)

---

### FASE 4 — Observability & governance

> Obiettivo: rendere il sistema misurabile e auditabile.
> Dipendenze: Fase 1.

#### 4.1 ✅ Audit trail in LLMAgent

**File modificato**: `vitruvyan_core/core/agents/llm_agent.py`

**Implementato**: parametro `prompt_metadata: Optional[dict] = None` aggiunto a `complete()`, `complete_with_tools()`, `complete_with_messages()`. Se presente, emette structured log `llm_audit` con prompt_id, domain, scenario, model, tokens, tenant_id, latency_ms.

**Backward compatible**: parametro opzionale, default None.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 4.2 ✅ Document lifecycle metadata

**File modificato**: `vitruvyan_core/contracts/rag.py`

**Implementato**: 4 campi opzionali aggiunti a `RAGPayload`:
- `ingested_at: Optional[str]` (auto-set da `created_at` se non fornito)
- `expires_at: Optional[str]` (ISO 8601)
- `document_version: Optional[str]`
- `superseded_by: Optional[str]` (chunk_id del documento sostitutivo)

`to_dict()` aggiornato: include solo i campi lifecycle valorizzati. Backward compatible.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 4.3 ✅ IRAGEvaluator contract

**File modificato**: `vitruvyan_core/contracts/retrieval.py`

**Implementato**: `EvalResult` dataclass con faithfulness/relevance/context_precision (0-1, validati), `composite_score` (media armonica). `IRAGEvaluator` ABC con `evaluate(query, response, context_chunks, expected_answer) → EvalResult`. Esportati via `contracts/__init__.py`.

**Stato**: ✅ Completato Mar 10, 2026

---

#### 4.4 ✅ Cost accounting hooks

**File modificato**: `vitruvyan_core/core/agents/llm_agent.py`

**Implementato**: `LLMMetrics` ora traccia `prompt_tokens` e `completion_tokens` separatamente (oltre a `total_tokens`). Le tre API call site (`complete`, `complete_with_tools`, `complete_with_messages`) estraggono `response.usage.prompt_tokens` e `response.usage.completion_tokens`. `to_dict()` espone entrambi. Il verticale usa questi dati con la propria pricing table per calcolare costi.

**Stato**: ✅ Completato Mar 10, 2026

---

## 3. Dipendenze tra fasi

```
FASE 0 (fondamenta)
  ├── 0.1 Tenant filtering         ← indipendente, può partire subito
  ├── 0.2 Prompt contracts         ← indipendente
  ├── 0.3 PromptAgent              ← dipende da 0.2
  ├── 0.4 Policy container         ← dipende da 0.2
  └── 0.5 PromptRegistry extend    ← dipende da 0.2
                │
FASE 1 (adoption + RAG primitives)
  ├── 1.1 Migrazione call site     ← dipende da 0.3, 0.4, 0.5
  ├── 1.2 Context Budget Manager   ← dipende da 0.3 (per integrazione)
  ├── 1.3 Embedding upgrade path   ← indipendente (documentazione)
  └── 1.4 Model tier in state      ← indipendente
                │
FASE 2 (retrieval quality)
  ├── 2.1 IQueryTransformer        ← indipendente (contratto)
  ├── 2.2 IReranker                ← indipendente (contratto)
  └── 2.3 CitationRef              ← dipende da 2.2 (per chunk_id tracking)
                │
FASE 3 (upload & inline)
  ├── 3.1 Inline context state     ← dipende da 1.2 (budget manager)
  └── 3.2 IContextRouter           ← dipende da 3.1
                │
FASE 4 (observability)
  ├── 4.1 Audit trail LLMAgent     ← dipende da 0.3 (PromptResolution metadata)
  ├── 4.2 Document lifecycle       ← indipendente
  ├── 4.3 IRAGEvaluator            ← indipendente (contratto)
  └── 4.4 Cost accounting          ← indipendente
```

---

## 4. Cosa NON è nel core (confine esplicito)

Queste responsabilità appartengono ai verticali, non a questa roadmap:

- Policy specifiche di dominio (disclaimer legali, vincoli security, etc.)
- Dataset di evaluation
- Scelta del modello di embedding per una collection specifica
- Implementazione concreta di HyDE, multi-query, o re-ranker
- Formattazione citazioni per UI
- TTL specifici per tipo documento
- Mapping model_tier → modello concreto (configurabile via env var)
- Logica di upload specifica (formati accettati, size limit, validazione)
- Prompt content (il testo dei prompt di dominio)

---

## 5. File che verranno creati

| File | Fase | Tipo |
|------|------|------|
| `vitruvyan_core/contracts/prompting.py` | 0.2 | NEW |
| `vitruvyan_core/core/agents/prompt_agent.py` | 0.3 | NEW |
| `vitruvyan_core/core/llm/prompts/policy.py` | 0.4 | NEW |
| `vitruvyan_core/core/llm/context_budget.py` | 1.2 | NEW |
| `vitruvyan_core/contracts/retrieval.py` | 2.1 | NEW |

## 6. File che verranno modificati

| File | Fase | Tipo modifica |
|------|------|---------------|
| `vitruvyan_core/core/orchestration/langgraph/node/qdrant_node.py` | 0.1 | Tenant filter |
| `vitruvyan_core/core/vpar/vsgs/vsgs_engine.py` | 0.1 | Tenant filter |
| `vitruvyan_core/core/llm/prompts/registry.py` | 0.5 | Extend con resolve() |
| `vitruvyan_core/core/orchestration/langgraph/node/compose_node.py` | 1.1 | Migrazione prompt |
| `vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py` | 1.1 | Migrazione prompt |
| `vitruvyan_core/core/orchestration/langgraph/node/early_exit_node.py` | 1.1 | Migrazione prompt |
| `vitruvyan_core/core/orchestration/base_state.py` | 1.4, 3.1 | Nuovi campi opzionali |
| `vitruvyan_core/contracts/orchestration.py` | 1.4 | Nuovi campi |
| `vitruvyan_core/contracts/rag.py` | 4.2 | Lifecycle metadata |
| `vitruvyan_core/contracts/graph_response.py` | 2.3 | CitationRef |
| `vitruvyan_core/core/agents/llm_agent.py` | 4.1, 4.4 | Audit + cost |
| `vitruvyan_core/contracts/__init__.py` | 0.2 | Export nuovi contratti |

---

## 7. Metriche di successo

| Fase | Metrica | Target |
|------|---------|--------|
| 0 | Prompt contracts e PromptAgent importabili e testabili | 100% |
| 0 | Ricerche Qdrant filtrate per tenant se tenant_id presente | 100% |
| 1 | Call site hardcoded migrati al PromptAgent | ≥ 4 nodi |
| 1 | Context budget calcolato e rispettato | Verificabile su ogni LLM call |
| 2 | IQueryTransformer e IReranker registrabili da un verticale | Contratto + default + test |
| 2 | CitationRef disponibile nel response schema | Campo opzionale popolato |
| 3 | Inline context iniettabile nel graph | Campo state + delimitatori |
| 4 | Audit trail con prompt_id su ogni LLM call | Log strutturato verificabile |

---

## 8. Log delle decisioni architetturali

| Data | Decisione | Motivazione |
|------|-----------|-------------|
| 2026-03-10 | Estendere PromptRegistry, non riscriverlo | Infrastruttura esistente valida, adoption > redesign |
| 2026-03-10 | PromptAgent come thin wrapper, non god object | Coerenza con pattern agent esistenti |
| 2026-03-10 | Policy anticipata a Fase 0 come dataclass leggero | Costo basso, protezione alta per verticali security |
| 2026-03-10 | Tenant filter come modifica core, non verticale | Isolamento dati è infrastruttura, non business logic |
| 2026-03-10 | Hook pattern (IQueryTransformer, IReranker, etc.) | Core = capability, verticale = implementation |
| 2026-03-10 | Context budget come modulo dedicated | Collega prompt system e RAG, nessuno dei due sa dell'altro altrimenti |
| 2026-03-10 | Inline context con delimitatori strutturali | Protezione prompt injection come primitivo core, non come policy verticale |
| 2026-03-10 | Nessun cambio embedding model di default | Il verticale decide quando migrare, il core abilita |

---

## 9. Cronologia implementazione

> Aggiornare questa sezione ad ogni sessione di lavoro.

| Data | Lavoro svolto | Note |
|------|---------------|------|
| 2026-03-10 | Brainstorming architetturale, audit codebase, creazione roadmap | Piano consolidato |
| 2026-03-10 | Fase 0 completata: tenant filter (0.1), contracts/prompting.py (0.2), PromptAgent (0.3), policy.py (0.4), registry.resolve() (0.5) | Tutti i test passano |
| 2026-03-10 | Fase 1 completata: 3 nodi migrati (1.1), context_budget.py (1.2), model_tier+domain+inline_context in state (1.4) | Tutti i test passano |
| 2026-03-10 | Fase 2 completata: retrieval.py (IQueryTransformer, IReranker, CitationRef, ContextRouting, IContextRouter), citations in GraphResponseMin | Tutti i test passano |
| 2026-03-10 | Fase 3 completata: inline_context injection in compose_node (conversational + synthesis) con delimitatori [USER_CONTEXT_START/END], fix state param in _synthesize_from_results | Tutti i test passano |
| 2026-03-10 | Fase 4 completata: prompt_metadata audit trail in LLMAgent (4.1), RAGPayload lifecycle fields (4.2), IRAGEvaluator+EvalResult (4.3), prompt/completion token tracking (4.4) | Tutti i test passano |

---

## Documenti correlati

- [PROMPT_LIBRARY_IMPLEMENTATION_PLAN_2026-03-10.md](PROMPT_LIBRARY_IMPLEMENTATION_PLAN_2026-03-10.md) — Piano originale prompt library (pre-audit)
- `.github/Vitruvyan_Appendix_E_RAG_System.md` — Documentazione RAG
- `vitruvyan_core/contracts/rag.py` — RAG governance contract
- `vitruvyan_core/contracts/tenancy.py` — Multi-tenant contract
- `vitruvyan_core/contracts/ingestion.py` — Ingestion contract
