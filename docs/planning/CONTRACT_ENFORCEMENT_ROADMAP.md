# Contract Enforcement End-to-End — Implementation Roadmap

> **Last updated**: Feb 28, 2026 17:15 UTC

## Executive Summary

L'analisi del codebase Vitruvyan Core rivela che la catena di garanzia contrattuale copre circa il **60%** del flusso dati. I contratti Pydantic sono forti ai bordi (servizi Babel Gardens / Pattern Weavers, output GraphResponseMin) ma **l'intero pipeline LangGraph interno (19+ nodi) opera senza alcuna validazione runtime**. Questa roadmap descrive 8 fasi per raggiungere il 100% di enforcement.

---

## Stato Attuale — Mappa dei Contratti

### Tipi di contratto esistenti

| Componente | Tipo contratto | File sorgente | Enforcement |
|------------|---------------|---------------|-------------|
| `BaseGraphState` | `TypedDict(total=False)` | `vitruvyan_core/core/orchestration/base_state.py` | ❌ Solo type hints, zero runtime |
| `NodeContract` | `@dataclass` con `required_fields`/`produced_fields` | `vitruvyan_core/core/orchestration/graph_engine.py:35` | ❌ Dichiarato, mai verificato |
| `GraphPlugin` | `ABC` | `vitruvyan_core/core/orchestration/graph_engine.py:60` | ⚠️ Solo ABC (metodi astratti) |
| `ComprehendRequest/Response` | Pydantic `BaseModel` `extra="forbid"` | `vitruvyan_core/contracts/comprehension.py` | ✅ Runtime, entry/exit |
| `OntologyPayload` | Pydantic `BaseModel` `extra="forbid"` | `vitruvyan_core/contracts/pattern_weavers.py:71` | ✅ Al servizio, ❌ nel grafo |
| `GraphResponseMin` | Pydantic `BaseModel` required fields | `vitruvyan_core/contracts/graph_response.py:93` | ✅ Runtime all'output |
| `SessionMin` | Pydantic `BaseModel` required fields | `vitruvyan_core/contracts/graph_response.py:51` | ✅ Runtime all'output |
| `OrthodoxyStatusType` | `Literal[5 valori]` | `vitruvyan_core/contracts/graph_response.py:33` | ✅ Validato da Pydantic all'output |
| `CollectionDeclaration` | `@dataclass(frozen=True)` con `__post_init__` | `vitruvyan_core/contracts/rag.py:126` | ⚠️ Warn-only (default) |
| `RAGPayload` | `@dataclass` con `__post_init__` | `vitruvyan_core/contracts/rag.py:200` | ⚠️ Warn-only |
| `TransportEvent` | `@dataclass(frozen=True)` | `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py:41` | ❌ Mai costruito da `emit()` |
| `CognitiveEvent` | `@dataclass` | `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py:111` | ❌ Nessuna validazione |

### Mappa visuale del flusso

```
INGESTION                   PIPELINE                           OUTPUT
─────────                   ────────                           ──────

ComprehendReq ──► Babel ──► [Pydantic ✅]
  (Pydantic ✅)   Service    ComprehensionResult
                    │
                    ▼ RAW DICT ─── contratto perso ❌
              ┌─────────────────────────────────────────┐
              │          LangGraph Pipeline              │
              │                                         │
              │  parse → intent → weaver → entity →     │
              │  babel → semantic → params → decide →   │
              │  [route] → exec/qdrant/llm →            │
              │  normalizer → orthodoxy → vault →       │
              │  compose → can → advisor → END          │
              │                                         │
              │  TUTTI I NODI: Dict[str, Any] ❌        │
              │  State = TypedDict(total=False) ❌      │
              │  NodeContract.required_fields ❌ UNUSED │
              │                                         │
              │  ⚠️ codex_hunters → END (skip ortho)   │
              └─────────────────────────────────────────┘
                    │
                    ▼ RAW DICT
              graph_adapter.py → GraphResponseMin ✅
                                  SessionMin ✅
                                  OrthodoxyStatus ✅
                                       │
                                       ▼
EVENT BUS                         HTTP Response
StreamBus.emit()                  al client
  payload: Any ❌
  no schema ❌

RAG / Qdrant
  upsert: warn-only ⚠️
```

---

## I 5 Buchi Critici

### BUCO 1 — Pipeline LangGraph senza validazione (CRITICO)

- **Dove**: tra tutti i 20 nodi in `graph_flow.py` (linee 272-500)
- **Causa**: `BaseGraphState` è `TypedDict(total=False)` — tutti i campi opzionali, nessun enforcement runtime. `TypedDict` è un costrutto esclusivamente per type checker statici (mypy/pyright), Python non lo valida mai a runtime.
- **Conseguenza**: un nodo può scrivere `state["intent"] = 42` (tipo sbagliato) o omettere `input_text`, e nulla lo intercetta.
- **Evidenza**: `NodeContract.required_fields` e `produced_fields` sono dichiarati nella dataclass (`graph_engine.py:35-45`) ma `GraphEngine.get_all_nodes()` (`graph_engine.py:257`) non li verifica mai. Inoltre, `graph_flow.py` NON usa `GraphEngine` per il pipeline principale — assembla il grafo direttamente.

### BUCO 2 — Boundary servizio→grafo perde Pydantic (ALTO)

- **Dove**: `pw_compile_node.py:89`, `pattern_weavers_node.py`, `emotion_detector.py`
- **Causa**: i nodi fanno `state["ontology_payload"] = result.get("payload", {})` — raw dict. `OntologyPayload.model_validate()` non viene mai chiamato nonostante il modello Pydantic con `extra="forbid"` esista.
- **Conseguenza**: la validazione forte del servizio Pattern Weavers (via FastAPI) viene persa quando il dato entra nel grafo.

### BUCO 3 — Orthodoxy saltata su codex_hunters (ALTO)

- **Dove**: `graph_flow.py:440` — conditional edge `codex_hunters → END` (success path)
- **Causa**: il path di successo bypassa `orthodoxy_node`, `vault_node`, `compose_node`, `can_node`.
- **Conseguenza**: nessun `orthodoxy_status` settato. Il contratto `GraphResponseMin` lo richiede come campo obbligatorio — `graph_adapter.py:183` mappa qualsiasi valore sconosciuto a `"blessed"` (default silenzioso).
- **Confronto**: `early_exit_node.py:85-93` setta correttamente tutti i campi orthodoxy.

### BUCO 4 — Event Bus accetta qualsiasi payload (MEDIO)

- **Dove**: `streams.py:209-260` — metodo `StreamBus.emit()`
- **Causa**: `emit()` accetta `payload: Dict[str, Any]` e fa `json.dumps(payload)` + `XADD`. `TransportEvent` e `CognitiveEvent` esistono come dataclass ma non vengono mai costruiti da `emit()`.
- **Conseguenza**: payload arbitrari circolano nel bus senza contratto.

### BUCO 5 — RAG warn-only di default (MEDIO)

- **Dove**: `qdrant_agent.py:62` — `_check_collection_registered()` e `_check_payload_contract()` (linea 77)
- **Causa**: `RAG_ENFORCE_REGISTRY` default = `"warn"`. Collezioni non dichiarate e payload senza `source` → warning nei log, dato che passa.
- **Conseguenza**: violazioni contrattuali invisibili in produzione.

---

## Decisione Architetturale: Decorator `@enforced` (Non Agent)

### Opzione scartata: ContractAgent

Un `ContractAgent` centralizzato sarebbe un anti-pattern perché:
1. Gli Agent in Vitruvyan wrappano I/O esterno (PostgreSQL/Qdrant/OpenAI). La validazione contrattuale è logica interna pura.
2. Richiederebbe chiamate esplicite `contract_agent.validate()` in ogni nodo — opt-in, dimenticabile.
3. Creerebbe un god object con accoppiamento universale.

### Opzione scelta: decorator `@enforced` + wrapping centralizzato in `build_graph()`

- **Cross-cutting concern** implementato come middleware/decorator
- **Applicato una volta sola** nel `build_graph()`, non in ogni file nodo
- **Non bypassabile** — il wrapping avviene all'assemblaggio del grafo
- **Configurabile** — ENV var `CONTRACT_ENFORCE_MODE` (warn/strict/off)

---

## Fasi di Implementazione

### FASE 1 — Decorator `@enforced` + `ContractViolation` (2 file nuovi)

**Obiettivo**: creare il meccanismo di enforcement senza toccare nessun nodo esistente.

**File da creare**:
1. `vitruvyan_core/core/orchestration/contract_enforcement.py` (~120 righe)
2. `vitruvyan_core/core/orchestration/tests/test_contract_enforcement.py` (~80 righe)

**Specifiche del decorator**:

```python
@enforced(
    requires=["input_text"],
    produces=["intent", "needs_clarification"],
    validate_types={                          # opzionale
        "input_text": str,
        "intent": str,
    }
)
def intent_detection_node(state: dict) -> dict:
    ...
```

**Comportamento**:
- **PRE**: verifica che ogni campo in `requires` esista in `state` e non sia `None`
- **POST**: verifica che ogni campo in `produces` esista nel dict restituito
- **TYPE** (opzionale): verifica `isinstance()` sui campi dichiarati
- **Modalità** controllata da env `CONTRACT_ENFORCE_MODE` (letta UNA VOLTA a import-time per zero overhead):
  - `warn` (default): log `WARNING` + incremento contatore interno (nome metric string only)
  - `strict`: raise `ContractViolationError` (per test/staging)
  - `off`: restituisce la funzione originale non wrappata — **zero overhead reale** (nessun wrapper)

**LIVELLO 1 compliance**: il file espone SOLO costanti con i nomi delle metriche (es. `METRIC_CONTRACT_VIOLATIONS = "contract_violations_total"`). Nessun `from prometheus_client import ...`. L'istanziazione delle metriche Prometheus avviene in LIVELLO 2 (servizio), seguendo il pattern di `vault_keepers/monitoring/metrics.py` e `codex_hunters/monitoring/__init__.py`.

**Performance `off` mode**:
```python
_MODE = os.getenv("CONTRACT_ENFORCE_MODE", "warn")  # letto UNA VOLTA

def enforced(requires, produces):
    def decorator(fn):
        if _MODE == "off":
            return fn  # restituisce funzione originale — zero wrapping
        @functools.wraps(fn)
        def wrapper(state):
            ...
        return wrapper
    return decorator
```

**Dipendenze**: nessuna esterna (pure Python + `logging`). NO `prometheus_client` in LIVELLO 1.

**Verifica**:
```bash
python3 -c "from core.orchestration.contract_enforcement import enforced; print('✅')"
pytest vitruvyan_core/core/orchestration/tests/test_contract_enforcement.py -v
```

---

### FASE 2 — Registry contratti per tutti i 20 nodi (1 file nuovo)

**Obiettivo**: definire `requires`/`produces` per ogni nodo in un registro centralizzato.

**File da creare**: `vitruvyan_core/core/orchestration/node_contracts_registry.py` (~150 righe)

**Contenuto — dizionario `NODE_CONTRACTS`**:

| Nodo | `requires` | `produces` |
|------|-----------|-----------|
| `parse` | `["input_text"]` | `["input_text", "language"]` |
| `intent_detection` | `["input_text"]` | `["intent"]` |
| `weaver` | `["input_text"]` | `["weaver_context"]` |
| `entity_resolver` | `["input_text"]` | `["entity_ids"]` |
| `babel_emotion` | `["input_text"]` | `["emotion_detected"]` |
| `semantic_grounding` | `["input_text"]` | `["vsgs_status"]` |
| `params_extraction` | `["input_text"]` | `[]` |
| `decide` (route_node) | `["intent"]` | `["route"]` |
| `exec` | `["route"]` | `["result"]` |
| `qdrant` | `["input_text"]` | `["result"]` |
| `llm_soft` (cached_llm) | `["input_text"]` | `["result"]` |
| `llm_mcp` | `["input_text"]` | `["result"]` |
| `output_normalizer` | `["result"]` | `["response"]` |
| `orthodoxy` | `["response"]` | `["orthodoxy_status"]` |
| `vault` | `["response"]` | `["vault_status"]` |
| `compose` | `["response"]` | `["narrative"]` |
| `can` | `["narrative"]` | `["final_response"]` |
| `advisor` | `["narrative"]` | `[]` |
| `codex_hunters` | `["input_text"]` | `["route"]` |
| `early_exit` | `["intent"]` | `["orthodoxy_status", "narrative", "final_response"]` |

**Dipendenze**: FASE 1 completata.

**Verifica**:
```bash
python3 -c "from core.orchestration.node_contracts_registry import NODE_CONTRACTS; print(f'✅ {len(NODE_CONTRACTS)} contratti')"
```

---

### FASE 3 — Applicazione a `build_graph()` (1 file modificato)

**Obiettivo**: wrappare ogni nodo al momento della registrazione nel grafo.

**File da modificare**: `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`

**Cambiamento** (~25 righe aggiunte, zero modifiche ai file dei singoli nodi):

```python
from core.orchestration.contract_enforcement import enforced
from core.orchestration.node_contracts_registry import NODE_CONTRACTS

def _wrap(name, fn):
    """Wrap node function with contract enforcement if registered."""
    c = NODE_CONTRACTS.get(name)
    if c:
        return enforced(requires=c.requires, produces=c.produces)(fn)
    return fn

# Nel build_graph():
g.add_node("parse", _wrap("parse", parse_node))
g.add_node("intent_detection", _wrap("intent_detection", intent_detection_node))
g.add_node("weaver", _wrap("weaver", weaver_node))
# ... per tutti i 20 nodi
```

**Impatto**: il wrapping è centralizzato in un solo punto. I nodi non sanno di essere wrappati.

**Dipendenze**: FASE 1 + FASE 2 completate.

**Verifica**:
```bash
# Compilazione del grafo con enforcement attivo
CONTRACT_ENFORCE_MODE=warn python3 -c "
from core.orchestration.langgraph.graph_flow import build_graph
g = build_graph()
print('✅ Graph compiled with contract enforcement')
"

# Pipeline end-to-end con enforcement
CONTRACT_ENFORCE_MODE=warn python3 -c "
from core.orchestration.langgraph.graph_runner import run_graph_once
result = run_graph_once('hello', user_id='test_contracts')
print(f'✅ Pipeline completa, route={result.get(\"route\")}')
"
```

---

### FASE 4 — Fix `codex_hunters → END` senza orthodoxy (1 file modificato)

**Obiettivo**: garantire che `orthodoxy_status` sia SEMPRE presente in output.

**File da modificare**: `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py`

**Cambiamento**: nel branch di successo (prima del return), aggiungere:
```python
from contracts.graph_response import ORTHODOXY_BLESSED  # costante canonica

state["orthodoxy_status"] = ORTHODOXY_BLESSED
state["orthodoxy_verdict"] = ORTHODOXY_BLESSED
state["orthodoxy_confidence"] = 0.99
state["orthodoxy_findings"] = 0
state["orthodoxy_message"] = "Codex expedition: maintenance system response"
state["orthodoxy_timestamp"] = datetime.utcnow().isoformat()
```

Pattern identico a `early_exit_node.py:85-93`.

**Prerequisito (FASE 4a)**: aggiungere costanti canoniche in `contracts/graph_response.py`:
```python
# Canonical orthodoxy status constants (avoid hardcoded strings)
ORTHODOXY_BLESSED = "blessed"
ORTHODOXY_PURIFIED = "purified"
ORTHODOXY_HERETICAL = "heretical"
ORTHODOXY_NON_LIQUET = "non_liquet"
ORTHODOXY_CLARIFICATION_NEEDED = "clarification_needed"
```
Tutti i nodi che settano `orthodoxy_status` (early_exit, codex_hunters, orthodoxy_node, graph_adapter) devono importare queste costanti anziché usare stringhe letterali.

**Alternativa** (modifica topologica): cambiare l'edge in `graph_flow.py` per far passare anche Codex per `output_normalizer → orthodoxy → vault → compose → can → END`. 

Pro: enforcement strutturale. Contro: aggiunge latenza al path di manutenzione.

**Dipendenze**: nessuna (parallelizzabile con FASE 1-3).

**Verifica**:
```bash
python3 -c "
from contracts.graph_response import GraphResponseMin, SessionMin
from datetime import datetime, timezone
# Simula output codex senza orthodoxy → deve fallire
try:
    GraphResponseMin(
        human='test', follow_ups=[], orthodoxy_status=None,
        route_taken='codex', correlation_id='x',
        as_of=datetime.now(timezone.utc),
        session_min=SessionMin(user_id='a', session_id='a', turn_id='a')
    )
    print('❌ Doveva fallire')
except Exception as e:
    print(f'✅ Pydantic ha bloccato input invalido')
"
```

---

### FASE 5 — Validazione payload lato emittente (0 file nel bus modificati)

**Obiettivo**: validazione dei payload emessi sul bus **PRIMA** della chiamata a `emit()`, mantenendo il bus 100% payload-blind.

**Principio architetturale**: il sacro invariante dice:
> *"Sacred invariant: the bus is payload-blind (no semantic routing/correlation/synthesis in transport)"*

Aggiungere validazione **dentro** `StreamBus.emit()` violerebbe questo principio — il trasporto "guarderebbe" il payload. La soluzione corretta è validare **lato emittente**, prima di chiamare `emit()`.

**Approccio (caller-side validation)**:

Ogni servizio che emette eventi valida il payload prima dell'invio:
```python
# Nell'emittente (es. bus_adapter.py di un Sacred Order):
from contracts.comprehension import ComprehensionResult

result = ComprehensionResult.model_validate(payload)  # emittente valida
bus.emit("babel.comprehension.completed", result.model_dump())  # bus riceve dato già validato
```

**File da modificare**: i singoli `adapters/bus_adapter.py` dei servizi che emettono eventi (Pattern Weavers, Babel Gardens, Orthodoxy Wardens, Vault Keepers, Codex Hunters).

**File NON modificato**: `vitruvyan_core/core/synaptic_conclave/transport/streams.py` — il bus resta intatto e payload-blind.

**Trade-off**: la validazione è opt-in per ogni emittente (stessa natura del decorator `@enforced` — l'enforcement è al confine del componente, non nel trasporto).

**Dipendenze**: nessuna (parallelizzabile).

**Verifica**:
```bash
python3 -c "
from pydantic import BaseModel

class AuditEvent(BaseModel):
    source: str
    entity_id: str

# Emittente valida PRIMA di emit()
try:
    AuditEvent.model_validate({'source': 'test', 'entity_id': 'E1'})
    print('✅ Payload valido — pronto per emit()')
except: pass

try:
    AuditEvent.model_validate({'wrong': 'data'})
    print('❌ Doveva fallire')
except Exception as e:
    print(f'✅ Validazione ha bloccato prima di emit(): {type(e).__name__}')
"
```

---

### FASE 6 — RAG enforce `strict` mode (1 env var + audit preventivo)

**Obiettivo**: passare da warn-only a strict per QdrantAgent.

**File da modificare**: `vitruvyan_core/core/agents/qdrant_agent.py`

**Prerequisito**: eseguire audit preventivo:
```bash
python3 scripts/audit_rag_collections.py
# Deve restituire 0 collezioni non dichiarate
```

**Cambiamento**: il default resta `warn` (zero breaking changes). La modalità `strict` viene attivata esplicitamente:
- **CI/staging**: `RAG_ENFORCE_REGISTRY=strict` nel docker-compose di staging
- **Produzione**: si attiva manualmente SOLO dopo audit a zero violazioni

```python
# Il codice NON cambia default — resta warn:
self.enforce_mode = os.getenv("RAG_ENFORCE_REGISTRY", "warn")
# ^
# Il default warn è intenzionale per backward-compat.
# Il valore strict viene settato via env var nei deploy di staging/CI.
```

**Dipendenze**: audit preventivo con `audit_rag_collections.py` per verificare che tutte le collezioni in Qdrant siano dichiarate in `ALL_DECLARED_COLLECTIONS`. Solo dopo audit a zero violazioni si può abilitare strict.

**Verifica**:
```bash
# Step 1: Audit (prerequisito)
python3 scripts/audit_rag_collections.py
# Deve restituire 0 collezioni non-dichiarate

# Step 2: Test strict mode
RAG_ENFORCE_REGISTRY=strict python3 -c "
from core.agents.qdrant_agent import QdrantAgent
print('✅ QdrantAgent in strict mode')
"
```

---

### FASE 7 — Pydantic re-validation ai boundary servizio→grafo (2-3 file modificati)

**Obiettivo**: quando un nodo LangGraph riceve JSON da servizi esterni, rivalidare con il contratto Pydantic.

**File da modificare**:

1. **`vitruvyan_core/core/orchestration/langgraph/node/pw_compile_node.py`** (~linea 89):
```python
# Da:
state["ontology_payload"] = result.get("payload", {})
# A:
from contracts.pattern_weavers import OntologyPayload
raw = result.get("payload", {})
try:
    OntologyPayload.model_validate(raw)
except Exception as e:
    logger.warning(f"[PW_COMPILE] OntologyPayload validation failed: {e}")
state["ontology_payload"] = raw
```

2. **`vitruvyan_core/core/orchestration/langgraph/node/pattern_weavers_node.py`**: stesso pattern per `weaver_context`.

3. **`vitruvyan_core/core/orchestration/langgraph/node/emotion_detector.py`**: stesso pattern per i campi emotion.

**Dipendenze**: nessuna (parallelizzabile).

---

### FASE 8 — Test E2E di conformità contrattuale (1 file nuovo)

**Obiettivo**: test automatizzato che verifica l'intera catena contrattuale.

**File da creare**: `tests/architectural/test_pipeline_contract_enforcement.py` (~100 righe)

**Casi di test**:

1. `run_graph_once("hello")` → risultato contiene `orthodoxy_status` (non None, non vuoto)
2. `run_graph_once("hello")` → risultato serializzabile in `GraphResponseMin` senza errori Pydantic
3. `run_graph_once("analyze this data")` → risultato contiene `route`, `intent`, `narrative`
4. Con `CONTRACT_ENFORCE_MODE=strict`, nessun `ContractViolationError` durante esecuzione
5. Path `early_exit` → tutti i campi orthodoxy presenti e con valori canonici
6. Path `codex_hunters` → `orthodoxy_status` presente
7. `orthodoxy_status` del risultato finale è tra i 5 valori canonici: `blessed|purified|heretical|non_liquet|clarification_needed`

**Dipendenze**: FASI 1-4 completate.

**Verifica**:
```bash
CONTRACT_ENFORCE_MODE=strict pytest tests/architectural/test_pipeline_contract_enforcement.py -v
```

---

## Grafo delle Dipendenze

```
FASE 1 ─────────────────────┐
  (decorator @enforced)      │
                              ├──► FASE 3 (applicazione a graph_flow.py)
FASE 2 ─────────────────────┘              │
  (registry contratti)                      │
                                            ├──► FASE 8 (test E2E)
FASE 4 ────────────────────────────────────┘
  (codex orthodoxy fix)

FASE 5 ──── indipendente (StreamBus schema)
FASE 6 ──── indipendente (RAG strict, dopo audit)
FASE 7 ──── indipendente (Pydantic boundary)
```

**Parallelizzazione possibile**: FASI 4, 5, 6, 7 possono partire tutte in parallelo con FASE 1.

---

## Stima Effort

| Fase | File | Righe nuove/mod | Rischio | Tempo stimato |
|------|------|----------------|---------|---------------|
| 1 | 2 nuovi | ~200 | Basso — pure Python, zero dipendenze | 1h |
| 2 | 1 nuovo | ~150 | Basso — solo dati dichiarativi | 45m |
| 3 | 1 mod | ~30 | **Medio** — potenziali warning da nodi non conformi oggi | 1h |
| 4 | 1 mod | ~10 | Basso | 15m |
| 5 | 1 mod | ~15 | Basso | 30m |
| 6 | 1 mod + audit | ~5 | **Medio** — richiede audit collezioni pre-deploy | 30m |
| 7 | 2-3 mod | ~10 | Basso | 30m |
| 8 | 1 nuovo | ~100 | Basso | 45m |
| **Totale** | **~10 file** | **~520 righe** | | **~5h** |

---

## Matrice di Copertura Pre/Post

| Punto pipeline | Prima (stato attuale) | Dopo (tutte le fasi) |
|----------------|----------------------|---------------------|
| Ingestion (servizi Babel/Pattern Weavers) | ✅ Pydantic `extra="forbid"` | ✅ Invariato |
| Boundary servizio → grafo | ❌ Raw dict, contratto perso | ✅ Re-validation Pydantic (FASE 7) |
| Tra nodi pipeline (19+ transizioni) | ❌ Zero validazione | ✅ `@enforced` pre/post (FASE 1-3) |
| Path `codex_hunters → END` | ❌ Skip orthodoxy | ✅ Orthodoxy settata (FASE 4) |
| Path `early_exit → END` | ✅ Già conforme | ✅ Invariato |
| Output `GraphResponseMin` | ✅ Pydantic required fields | ✅ Invariato |
| Event bus `StreamBus.emit()` | ❌ `Dict[str, Any]` senza schema | ⚠️ Opt-in schema (FASE 5) |
| RAG `QdrantAgent.upsert()` | ⚠️ Warn-only di default | ✅ Strict mode (FASE 6) |

---

## Architettura Target

```
       @enforced decorator (LIVELLO 1 — pure Python, zero I/O)
              │
              ▼
┌──────────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline                         │
│                                                              │
│  parse ──► intent ──► weaver ──► entity ──► babel ──►       │
│  semantic ──► params ──► decide ──► [route] ──►             │
│  exec/qdrant/llm ──► normalizer ──► orthodoxy ──►           │
│  vault ──► compose ──► can ──► advisor ──► END              │
│                                                              │
│  OGNI NODO: @enforced(requires=[...], produces=[...])        │
│  Validazione automatica PRE (input) e POST (output)          │
│  Violazione → log WARNING + Prometheus metric                │
│  CONTRACT_ENFORCE_MODE=strict → raise (staging/test)         │
│  CONTRACT_ENFORCE_MODE=off → no-op (escape hatch)            │
└──────────────────────────────────────────────────────────────┘
              │
              ▼
       GraphResponseMin (Pydantic — checkpoint finale)
```

---

## Vincoli Non-Negoziabili

1. **Zero breaking changes**: modalità `warn` di default. Nessun nodo esistente smette di funzionare.
2. **Zero modifiche ai file dei nodi**: il wrapping avviene solo in `build_graph()`.
3. **LIVELLO 1 compliance**: `contract_enforcement.py` è pure Python — no I/O, no Redis, no Postgres, NO `prometheus_client`. Solo nomi metriche come stringhe costanti.
4. **Bus payload-blind**: `StreamBus.emit()` NON viene modificato. La validazione avviene lato emittente.
5. **Nessun god object**: no `ContractAgent`, no singleton globale. Il decorator è funzionale e stateless.
6. **No hardcoded strings**: i valori orthodoxy (`blessed`, `purified`, etc.) sono costanti importate da `contracts/graph_response.py`, non stringhe letterali sparse.
7. **Core agnostic**: nessuna logica domain-specific introdotta in `vitruvyan_core/core/`. I contratti sono domain-agnostic.
8. **Performance `off` mode**: quando `CONTRACT_ENFORCE_MODE=off`, il decorator restituisce la funzione originale — zero wrapping, zero overhead.
9. **RAG backward-compat**: il default `RAG_ENFORCE_REGISTRY` resta `warn`. `strict` si attiva via env var solo dopo audit.

---

## Riferimenti al Codice

| File | Righe chiave | Ruolo |
|------|-------------|-------|
| `vitruvyan_core/core/orchestration/base_state.py` | L26 (`TypedDict, total=False`) | State del grafo — nessun enforcement runtime |
| `vitruvyan_core/core/orchestration/graph_engine.py` | L35-45 (`NodeContract`) | required/produced fields — mai verificati |
| `vitruvyan_core/core/orchestration/langgraph/graph_flow.py` | L200 (`GraphState`), L272-500 (`build_graph`) | Assemblaggio del grafo — punto di wrapping |
| `vitruvyan_core/core/orchestration/langgraph/graph_runner.py` | L120 (`run_graph_once`) | Entry point — restituisce raw dict |
| `services/api_graph/adapters/graph_adapter.py` | L183 (`_CANONICAL_MAP`), L235 (`GraphResponseMin`) | Ultimo checkpoint Pydantic |
| `vitruvyan_core/contracts/__init__.py` | L1-200 | Namespace canonico contratti |
| `vitruvyan_core/contracts/graph_response.py` | L33, L93 | `OrthodoxyStatusType`, `GraphResponseMin` |
| `vitruvyan_core/contracts/comprehension.py` | Pydantic `extra="forbid"` | Contratti Babel Gardens |
| `vitruvyan_core/contracts/pattern_weavers.py` | L71, L103-117 | Contratti Pattern Weavers |
| `vitruvyan_core/contracts/rag.py` | L126, L200 | `CollectionDeclaration`, `RAGPayload` |
| `vitruvyan_core/core/synaptic_conclave/transport/streams.py` | L209 (`emit`) | Bus — zero schema |
| `vitruvyan_core/core/synaptic_conclave/events/event_envelope.py` | L41, L111 | `TransportEvent`, `CognitiveEvent` — mai usati da emit |
| `vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py` | L30, L262-285 | Valori non-canonici, local blessing |
| `vitruvyan_core/core/orchestration/langgraph/node/early_exit_node.py` | L85-93 | Pattern corretto di orthodoxy |
| `vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py` | processo → END | Bypassa orthodoxy |
| `vitruvyan_core/core/orchestration/langgraph/node/pw_compile_node.py` | L89 | Raw dict nello state |

---

## Compliance Audit — Verifica Principi Architetturali

Questa sezione documenta la verifica del roadmap contro tutti i principi architetturali di Vitruvyan Core.

| Principio | Stato | Note |
|-----------|-------|------|
| **Core stays generic** — no domain logic in `vitruvyan_core/core/` | ✅ Conforme | Nessuna logica domain nei file toccati. Il decorator è agnostico. |
| **No cross-service imports** | ✅ Conforme | Tutto interno a `core/` o a singoli servizi |
| **Agents for external access** — no raw clients | ✅ Conforme | Nessun agent spurio introdotto. No raw DB/vector/OpenAI clients |
| **No secrets in repo** | ✅ Conforme | Solo nomi env var, zero valori |
| **LIVELLO 1 / LIVELLO 2 separation** | ✅ Corretto dopo review | `contract_enforcement.py` espone SOLO nomi metriche (stringhe). NO `prometheus_client` in LIVELLO 1 |
| **Bus payload-blind** | ✅ Corretto dopo review | `StreamBus.emit()` NON viene modificato. Validazione lato emittente |
| **Validated lists authoritative** | ✅ Non impattato | Non tocca entity validation |
| **Import conventions (`core.*`)** | ✅ Conforme | Segue pattern esistente |
| **Edge architecture** | ✅ Non impattato | Non tocca edge services |
| **Zero breaking changes** | ✅ Corretto dopo review | RAG default resta `warn`. Decorator default `warn`. Nessun nodo si rompe |
| **Scalability (stateless)** | ✅ Conforme | Decorator stateless, no locks, no shared mutable state |
| **Performance** | ✅ Corretto dopo review | `off` mode = funzione originale non wrappata (zero overhead). `_MODE` letto una volta a import-time |
| **LLM-first** | N/A | Non tocca NLU |
| **No hardcoded strings** | ✅ Corretto dopo review | Costanti canoniche in `contracts/graph_response.py`. Import ovunque. |
| **Bias-aware tests** | ✅ Conforme | FASE 8 test usa input diversificati, non fixtures ripetitive |

### Violazioni trovate e corrette durante review

| # | Violazione | Severità | Fix applicato |
|---|-----------|----------|---------------|
| 1 | `prometheus_client` in LIVELLO 1 (`contract_enforcement.py`) | Alta | Solo nomi metriche come stringhe. Istanziazione Prometheus in LIVELLO 2 |
| 2 | `StreamBus.emit()` con parametro `schema` violava payload-blind | Media | Validazione spostata lato emittente. Bus non toccato |
| 3 | RAG default cambiato a `strict` = breaking change | Media | Default resta `warn`. `strict` attivato via env var dopo audit |
| 4 | Stringhe `"blessed"` hardcoded nei nodi | Bassa | Costanti canoniche `ORTHODOXY_*` in `contracts/graph_response.py` |
| 5 | `CONTRACT_ENFORCE_MODE` letto ad ogni invocazione = overhead | Bassa | Letto UNA VOLTA a import-time. `off` → funzione originale restituita |
