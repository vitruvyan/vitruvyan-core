# Audit Architetturale: LangGraph Layer — Vitruvyan Core
> **Last updated**: Mar 06, 2026 — Principal Architect Review
> **Scope**: LangGraph orchestration layer, opzione A vs B, concorrenza, canali, Sacred Orders integration
> **Metodo**: Verifica puntuale nel codice (file:line), confronto dialettico con audit ChatGPT precedente

---

## 0. Nota Metodologica — Rapporto Dialettico con l'Audit Precedente

L'audit originale (ChatGPT) ha identificato 5 rilevanze architetturali corrette nella sostanza, ma con imprecisioni puntuali e una framing eccessivamente allarmistica. Questo documento:

1. **Conferma** ciò che è verificato nel codice
2. **Corregge** dove l'audit precedente ha esagerato o sbagliato i riferimenti
3. **Aggiunge** ciò che mancava (concurrency patterns reali, uvloop chain, execution guard)
4. **Propone** una decisione architetturale basata su evidenze, non su paura

---

## 1. Stato Attuale Verificato

### 1.1 api_graph: Orchestratore HTTP Sincrono ✅ CONFERMATO

| Aspetto | Stato | Riferimento |
|---------|-------|-------------|
| Pattern architetturale | HTTP request-response (sincrono dal punto di vista del client) | [services/api_graph/README.md](../services/api_graph/README.md) L1-2 |
| Framework | FastAPI + asyncio.to_thread() per offload | [graph_adapter.py](../services/api_graph/adapters/graph_adapter.py) L77-82 |
| Event bus | **Nessuna integrazione** (no StreamBus import/consume) | README L9: "no event bus integration" |
| Compliance SACRED_ORDER_PATTERN | ✅ main.py 89 linee (< 100) | [main.py](../services/api_graph/main.py) |

**Critica all'audit precedente**: Corretta la rilevanza. L'api_graph non è "descritto come" orchestratore HTTP — **lo è effettivamente**. Non c'è ambiguità.

### 1.2 Nodi del Grafo: Fire-and-Forget via StreamBus ✅ CONFERMATO (con precisazioni)

**L'audit precedente dice**: "nodi del grafo pubblicano eventi via shim legacy (redis_client.py)"

**Realtà verificata**: I nodi **NON** usano lo shim legacy. Usano StreamBus direttamente.

| Nodo | Usa Bus? | Import | Pattern | Riferimento |
|------|----------|--------|---------|-------------|
| orthodoxy_node | ✅ Sì | `from core.synaptic_conclave.transport.streams import get_stream_bus` | Fire-and-forget | [orthodoxy_node.py](../vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py) L23, L66-71 |
| vault_node | ✅ Sì | idem | Fire-and-forget | [vault_node.py](../vitruvyan_core/core/orchestration/langgraph/node/vault_node.py) L19, L149-155 |
| codex_hunters_node | ✅ Sì | idem | Fire-and-forget + HTTP polling | [codex_hunters_node.py](../vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py) L35, L294-310 |
| Tutti gli altri (15 nodi) | ❌ No | — | Pure compute | — |

**Lo shim** (`redis_client_shim.py`) esiste in `_legacy/` ma **non è importato da nessun nodo**. L'audit precedente ha confuso l'esistenza dello shim con il suo utilizzo. Questo è un errore significativo che potrebbe aver orientato valutazioni sul debito tecnico in modo fuorviante.

### 1.3 Round-Trip Disattivato ✅ CONFERMATO

Tutti e tre i nodi che emettono eventi:

1. **orthodoxy_node** — [L76-80](../vitruvyan_core/core/orchestration/langgraph/node/orthodoxy_node.py): TODO esplicito "Implement async verdict retrieval via Postgres polling". Verdict è SEMPRE `None` → fallback locale "locally_blessed" applicato al 100%.
2. **vault_node** — [L157-158](../vitruvyan_core/core/orchestration/langgraph/node/vault_node.py): `_create_fallback_protection()` chiamata IMMEDIATAMENTE dopo emit. Nessun polling per response.
3. **codex_hunters_node** — [L157-161](../vitruvyan_core/core/orchestration/langgraph/node/codex_hunters_node.py): Usa HTTP API polling verso il servizio Codex, NON il bus.

**Pattern emergente**: Il `correlation_id` viene generato e inserito nel payload, ma **nessun codice lo usa mai per recuperare risposte**. È un artefatto di un'architettura round-trip pianificata ma mai implementata.

**Critica all'audit precedente**: Corretto nella conclusione, ma mancava la distinzione cruciale: il round-trip non è "disattivato" (implicando che era attivo). **Non è mai stato implementato**. La differenza è importante: non c'è codice dormiente da riattivare, c'è un TODO da progettare.

### 1.4 Channel Drift ⚠️ PARZIALMENTE CONFERMATO

L'audit precedente parlava di drift generico. La realtà è più sfumata:

#### 1.4.1 `system.audit.requested` → RISOLTO (ma residui nei docs)

Il grafo **non** usa più `system.audit.requested`. È stato rinominato in `orthodoxy.audit.requested` ([releases.json](../releases.json) L8: "refactor: orthodoxy_node channel system.audit.requested -> orthodoxy.audit.requested"). Il vecchio nome persiste in:
- [api_orthodoxy_wardens/api/routes.py](../services/api_orthodoxy_wardens/api/routes.py) L188, L258, L266 (endpoint di trigger manuale — usa ancora il vecchio nome come event_type!)
- [test_orthodoxy_bus.py](../vitruvyan_core/core/governance/orthodoxy_wardens/tests/_legacy/test_orthodoxy_bus.py) L126, L163, L289 (test legacy)
- [RESUME_DEBUG_SESSION.md](../docs/prompts/RESUME_DEBUG_SESSION.md) L134, L141, L222 (docs stale)

**Verdict**: Il drift tra grafo e listener è RISOLTO. Ma c'è drift tra il servizio Orthodoxy (routes.py L188) e sé stesso: l'endpoint di trigger manuale pubblica `system.audit.requested` che IL SUO STESSO listener consuma come `orthodoxy.audit.requested`. Questo è un **bug silenzioso**: il trigger manuale non raggiunge mai il listener.

#### 1.4.2 `vault.integrity.requested` → DRIFT REALE 🔴

| Sorgente | Canale | Consumato? |
|----------|--------|------------|
| vault_node.py L167, L170, L172 | `vault.integrity.requested` | ❌ **NO** — assente da `SACRED_CHANNELS` in [vault_keepers/config.py](../services/api_vault_keepers/config.py) L42 |
| vault_node.py L168 | `vault.archive.requested` | ✅ Sì |
| vault_node.py L169 | `audit.vault.requested` | ✅ Sì |

Il vault_node emette `vault.integrity.requested` per i protection type `standard` e `integrity_check` (i più comuni), ma il listener Vault Keepers **non ascolta** su quel canale. Gli eventi vanno persi nel vuoto.

**Nota critica**: Questo è il drift più grave ma anche il meno impattante **oggi**, perché il vault_node usa fire-and-forget con fallback locale immediato. Il cliente HTTP non si accorge mai del drift. Ma è debito tecnico reale che impedisce l'evoluzione verso Option B.

#### 1.4.3 `integrity.check.requested` e `backup.create.requested` → DEFINITI MA MAI EMESSI

Definiti in:
- [event_schema.py](../vitruvyan_core/core/synaptic_conclave/events/event_schema.py) L53-54
- [vault_events.py](../vitruvyan_core/core/governance/vault_keepers/events/vault_events.py) L21-22

Ma **nessun codice nel grafo li emette mai**. Non sono drift — sono canali morti, probabilmente pianificati per un'architettura mai implementata.

#### 1.4.4 `langgraph.output.ready` vs `langgraph.response.completed` → NAMING MISMATCH

- [orthodoxy_events.py](../vitruvyan_core/core/governance/orthodoxy_wardens/events/orthodoxy_events.py): definisce `langgraph.output.ready`
- [orthodoxy config.py](../services/api_orthodoxy_wardens/config.py) L75: listener consuma `langgraph.response.completed`
- [conclave config.py](../services/api_conclave/config.py): registry usa `langgraph.response.completed`

Due nomi diversi per lo stesso concetto, usati in punti diversi. Drift reale, ma mitigato dal fatto che nessun nodo del grafo emette su nessuno dei due canali.

### 1.5 Concorrenza e Performance ⚠️ CONFERMATO (con gravità diversa)

#### 1.5.1 Uvicorn Single Worker ✅

[Dockerfile.api_graph](../infrastructure/docker/dockerfiles/Dockerfile.api_graph) L43:
```dockerfile
CMD ["uvicorn", "api_graph.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

Nessun `--workers`. Worker singolo. Ma:

**Critica all'audit precedente**: Presentarlo come bug è riduttivo. Con `asyncio.to_thread()` in [graph_adapter.py](../services/api_graph/adapters/graph_adapter.py) L77-82 e l'`ExecutionGuard` con ThreadPoolExecutor (4 worker, [execution_guard.py](../vitruvyan_core/core/orchestration/execution_guard.py) L33-40), il sistema gestisce **concorrenza reale** anche con 1 processo uvicorn. Il collo di bottiglia non è il worker uvicorn, è il **thread pool dell'ExecutionGuard** (max 4 esecuzioni parallele di nodi).

Detto ciò, aggiungere `--workers 2-4` è un **no-regret fix** per resilienza (crash recovery, memory leak isolation).

#### 1.5.2 Sync/Async Mixing — IL PROBLEMA REALE 🔴

Questo è l'issue architetturale più grave, e l'audit precedente lo ha sottovalutato:

**Chain of contamination:**
```
uvicorn (usa uvloop di default)
  → llm_mcp_node.py L63: nest_asyncio.apply() rileva uvloop, marca _nest_applied=True senza effetto
  → intent_detection_node.py L262: crea SelectorEventLoop() ad ogni invocazione (workaround per nest_asyncio)
  → Ogni chiamata: nuovo loop + close (inefficiente, ~30 allocazioni/sec sotto carico)
```

**Specificamente:**

| File:Line | Problema | Severità |
|-----------|----------|----------|
| [intent_detection_node.py](../vitruvyan_core/core/orchestration/langgraph/node/intent_detection_node.py) L262-264 | Nuovo `asyncio.SelectorEventLoop()` per ogni invocazione | MEDIUM (funziona ma inefficiente) |
| [llm_mcp_node.py](../vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py) L212-230 | Nuovo `ThreadPoolExecutor()` per ogni chiamata (2x per esecuzione grafo) | HIGH (thread pool thrashing) |
| [llm_mcp_node.py](../vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py) L35-68 | `nest_asyncio.apply()` contamina asyncio internals globalmente | HIGH (side effect globale) |
| [intent_detection_node.py](../vitruvyan_core/core/orchestration/langgraph/node/intent_detection_node.py) L137-140 | `asyncio.get_event_loop()` deprecated pattern | LOW (funziona in practice) |

#### 1.5.3 "Doppia Inizializzazione" del Grafo → NON CONFERMATO ❌

L'audit precedente parlava di "doppia inizializzazione grafo (graph_adapter e graph_runner)". Verificato:

- [graph_runner.py](../vitruvyan_core/core/orchestration/langgraph/graph_runner.py) L124-132: `_get_graph()` con lazy singleton (prima compilazione)
- [graph_adapter.py](../services/api_graph/adapters/graph_adapter.py) L59-66: `build_graph()` nel costruttore

Questi **sono lo stesso path**: `graph_adapter.__init__()` → `build_graph()` → compilazione. `graph_runner._get_graph()` è un singleton che cachea il risultato. Non c'è doppia compilazione — c'è un singleton con due entry point, il che è un design discutibile ma non una doppia inizializzazione.

**Possibile race**: Due thread potrebbero chiamare `_get_graph()` contemporaneamente prima che `_GRAPH` sia settato. Python GIL lo protegge per semplici check-and-set, ma sarebbe più pulito con un lock esplicito.

---

## 2. Gap Architetturali

### 2.1 Gap Critici (impatto operativo immediato)

| # | Gap | Impatto | Effort Fix |
|---|-----|---------|------------|
| G1 | `vault.integrity.requested` non consumato dal listener | Eventi standard/integrity_check persi nel vuoto | 0.5 giorni |
| G2 | `system.audit.requested` in routes.py Orthodoxy (L188) vs `orthodoxy.audit.requested` nel listener | Trigger manuale non raggiunge listener | 0.5 giorni |
| G3 | Thread pool thrashing in llm_mcp_node (nuovo executor ogni call) | GC pressure, overhead allocazione sotto carico | 1 giorno |
| G4 | correlation_id generato ovunque, usato da nessuno | Dead code + falsa aspettativa di round-trip | 0.5 giorni (documentativo) |

### 2.2 Gap Strutturali (impatto architetturale)

| # | Gap | Impatto | Effort Fix |
|---|-----|---------|------------|
| G5 | Nessun canale centralizzato definisce il contratto producer→consumer | Channel drift ripetibile ad ogni evoluzione | 2 giorni |
| G6 | nest_asyncio + uvloop contamination chain | Workaround fragile, rompe a upgrades uvicorn/uvloop | 3 giorni |
| G7 | Nessun budget di latenza esplicito per nodo | Impossible fare SLO p95 senza decomposizione | 1 giorno (misurativo) |
| G8 | Nessun test di concorrenza multi-utente | Regressioni concurrency invisibili | 2 giorni |

### 2.3 Gap Evolutivi (bloccanti per Option B)

| # | Gap | Impatto |
|---|-----|---------|
| G9 | Nessun meccanismo response channel nel bus | Round-trip impossibile senza redesign StreamBus |
| G10 | Nessun correlation store (Redis/PG) per match request→response | Anche con response channel, nessun modo di correlare |
| G11 | Listener Sacred Orders non emettono su canali di "risposta" consumabili dal grafo | Comunicazione unidirezionale (grafo → listener) |

---

## 3. Decisione Raccomandata: A, con Evoluzione Selettiva verso A+

### 3.1 Perché NON Option B (oggi)

L'Option B (grafo ibrido event-driven con round-trip via Redis Streams) richiede:

1. **Response channels**: Ogni Sacred Order deve emettere su `<order>.audit.completed` (o equivalente) con il `correlation_id` nel payload
2. **Correlation store**: Un meccanismo per il grafo di attendere la risposta (polling PG? subscribe Redis? timeout?)
3. **Timeout & fallback**: Cosa succede se il listener non risponde in N secondi?
4. **Ordering guarantee**: Redis Streams non garantisce che la risposta arrivi sullo stesso consumer se ci sono più istanze del grafo

**Il codebase attuale non ha NESSUNO di questi building block.** Implementare B significa riscrivere: StreamBus (aggiungere response pattern), tutti i listener (aggiungere emit di risposta), tutti i nodi del grafo (aggiungere polling/await), execution guard (aggiungere timeout per risposta bus), più un correlation store.

**Effort stimato per B completa**: 15-20 giorni/uomo, con rischio significativo di regressione.

### 3.2 Perché Option A (oggi) è già la realtà

Il sistema **è già** Option A. I nodi del grafo:
- Eseguono logica locale (pure compute o LLM call)
- Emettono eventi fire-and-forget per post-processing asincrono
- Non attendono mai risposte dal bus
- Applicano fallback locali immediati

L'unica cosa che manca è **dichiararlo esplicitamente** e ripulire i residui di un'architettura round-trip mai implementata (correlation_id, TODO comments, canali morti).

### 3.3 Cos'è A+ (evoluzione selettiva)

A+ = Option A con **estensioni event-driven selettive** dove il valore è dimostrabile:

| Scenario | Pattern | Motivazione |
|----------|---------|-------------|
| Audit ortodossia (già oggi) | Fire-and-forget → async post-processing | Il verdict non serve al client HTTP, serve alla governance |
| Archiviazione vault (già oggi) | Fire-and-forget → async archival | La persistenza è un side-effect, non fa parte della risposta |
| Codex expedition (futuro) | HTTP call → polling → webhook callback | Operazione pesante, minuti non millisecondi |
| Memory coherence (futuro) | Scheduled job, non evento del grafo | La coherence è un check periodico, non per-request |

**Regola decisionale**: Se un'operazione cambia la risposta al client → sincrono nel grafo. Se è un side-effect → fire-and-forget al bus. Se richiede minuti → HTTP callback/webhook.

---

## 4. Tabella Comparativa A vs B vs A+

| Dimensione | A (Status Quo pulito) | B (Round-Trip Event-Driven) | A+ (Raccomandato) |
|------------|----------------------|----------------------------|-------------------|
| **Complessità implementativa** | Bassa (cleanup, no new code) | Alta (correlation store, response channels, timeout logic) | Media (cleanup + contratti espliciti) |
| **Latenza p50** | ~800ms (LLM-bound) | ~1200ms (+polling/correlation overhead) | ~800ms (invariata) |
| **Latenza p95** | ~2500ms (LLM variance) | ~4000ms (+bus roundtrip + timeout budget) | ~2500ms (invariata) |
| **Throughput multi-utente** | 4 concurrent (ExecutionGuard pool) | 4 concurrent (identico, bus non cambia il bottleneck) | 8-16 concurrent (con tuning workers + pool) |
| **Failure modes** | Timeout LLM, PG down → graceful fallback | Tutto A + listener down → timeout cascade, correlation store corruption, event ordering issues | Come A, più resiliente con contratti espliciti |
| **Osservabilità** | Prometheus per HTTP, nessun tracing bus | Richiede distributed tracing (correlation_id → Jaeger/Zipkin) | Prometheus + channel health metrics |
| **Effort stimato** | 3 giorni/uomo (Fase 0-1) | 15-20 giorni/uomo + 5 test | 8-10 giorni/uomo (tutte le fasi) |
| **Rischio regressione** | Basso | Alto (nuovi failure modes) | Medio-basso |
| **Semplicità evolutiva Sacred Orders** | Alta (listener indipendenti, fire-and-forget) | Bassa (ogni Sacred Order deve implementare response protocol) | Alta (contratti espliciti mantengono indipendenza) |

---

## 5. Roadmap Operativa

### Fase 0: No-Regret Fixes (3 giorni/uomo)

| Fix | Dettaglio | File | Effort |
|-----|----------|------|--------|
| F0.1 | Aggiungere `vault.integrity.requested` a SACRED_CHANNELS di Vault Keepers | [services/api_vault_keepers/config.py](../services/api_vault_keepers/config.py) L42 | 0.25 giorni |
| F0.2 | Correggere `system.audit.requested` → `orthodoxy.audit.requested` in routes.py Orthodoxy | [services/api_orthodoxy_wardens/api/routes.py](../services/api_orthodoxy_wardens/api/routes.py) L188 | 0.25 giorni |
| F0.3 | Unificare naming `langgraph.output.ready` / `langgraph.response.completed` | [orthodoxy_events.py](../vitruvyan_core/core/governance/orthodoxy_wardens/events/orthodoxy_events.py) + config | 0.5 giorni |
| F0.4 | Aggiungere `--workers 2` al CMD di Dockerfile.api_graph | [Dockerfile.api_graph](../infrastructure/docker/dockerfiles/Dockerfile.api_graph) L43 | 0.25 giorni |
| F0.5 | Pool ThreadPoolExecutor singolo in llm_mcp_node (invece di uno per call) | [llm_mcp_node.py](../vitruvyan_core/core/orchestration/langgraph/node/llm_mcp_node.py) L212-230 | 0.5 giorni |
| F0.6 | Rimuovere docs stale (`system.audit.requested` in RESUME_DEBUG_SESSION.md, test_integration_orthodoxy.py) | Vari | 0.25 giorni |
| F0.7 | Aggiungere lock esplicito a `_get_graph()` in graph_runner.py | [graph_runner.py](../vitruvyan_core/core/orchestration/langgraph/graph_runner.py) L124-132 | 0.25 giorni |

### Fase 1: Contract Cleanup (3 giorni/uomo)

| Fix | Dettaglio | Effort |
|-----|----------|--------|
| F1.1 | Creare `vitruvyan_core/core/synaptic_conclave/channels/channel_registry.py` — fonte di verità unica per tutti i canali, usata da producer E consumer | 1 giorno |
| F1.2 | Documentare il correlation_id come "trace_id for observability" (non round-trip), rimuovere TODO "implement async verdict retrieval" da orthodoxy_node e vault_node, sostituire con commento architetturale chiaro | 0.5 giorni |
| F1.3 | Definire `EventContract` (dataclass) per ogni canale: nome, schema payload, producer, consumer, SLA di processing | 1 giorno |
| F1.4 | Aggiungere health check per channel alignment: test che verifica che ogni canale emesso da un nodo sia in almeno un SACRED_CHANNELS di un listener | 0.5 giorni |

### Fase 2: Performance Tuning (3 giorni/uomo)

| Fix | Dettaglio | Effort |
|-----|----------|--------|
| F2.1 | Risolvere uvloop/nest_asyncio chain: forzare `--loop asyncio` in uvicorn CMD (disabilita uvloop), eliminare nest_asyncio workaround | 1 giorno |
| F2.2 | Convertire SelectorEventLoop in intent_detection_node a design pulito: thread-based executor condiviso (no loop creation per call) | 1 giorno |
| F2.3 | Aumentare ExecutionGuard max_workers da 4 a 8 (misurare prima con benchmark) | 0.5 giorni |
| F2.4 | Aggiungere latency budget per nodo: middleware che logga tempo per nodo, genera percentile metrics | 0.5 giorni |

### Fase 3: Evoluzione Event-Driven Selettiva (opzionale, 3 giorni/uomo)

| Fix | Dettaglio | Effort |
|-----|----------|--------|
| F3.1 | Implementare `orthodoxy.audit.completed` emission nel listener Orthodoxy | 1 giorno |
| F3.2 | Implementare `vault.archive.completed` emission nel listener Vault | 0.5 giorni |
| F3.3 | Aggiungere observability dashboard: channel throughput, consumer lag, dead letters | 1 giorno |
| F3.4 | Valutare se orthodoxy_node dovrebbe attendere il verdict (solo se latenza < 200ms aggiuntivi) | 0.5 giorni (spike) |

---

## 6. Piano Test e Metriche

### 6.1 SLO Target

| Metrica | Target | Attuale Stimato | Note |
|---------|--------|-----------------|------|
| Latenza p50 (POST /run) | < 1000ms | ~800ms | LLM-bound |
| Latenza p95 (POST /run) | < 3000ms | ~2500ms | LLM variance + PG |
| Latenza p99 (POST /run) | < 5000ms | ~4500ms | Cold start + cache miss |
| Error rate (5xx) | < 1% | Sconosciuto | Da misurare |
| Throughput (concurrent users) | > 8 req/s sustained | ~4 req/s | ExecutionGuard-limited |
| Channel delivery rate | 100% (no lost events) | < 100% (vault.integrity.requested perso) | Gap G1 |

### 6.2 Test E2E Minimi (da implementare)

| Test | Descrizione | Priorità |
|------|-------------|----------|
| T1 | POST /run con input valido → response in < 5s con tutti i campi GraphResponseMin | P0 |
| T2 | POST /run con validated_entities=[] → risposta conversational (no entity extraction) | P0 |
| T3 | POST /run → verificare che evento emesso su orthodoxy.audit.requested arrivi al listener | P1 |
| T4 | POST /run → verificare che evento emesso su vault.*.requested arrivi al listener corretto | P1 |
| T5 | 10 POST /run concorrenti con user_id diversi → tutte completate in < 10s, no race condition | P0 |
| T6 | 5 POST /run concorrenti con STESSO user_id → serializzate (per-user lock), no corruption | P0 |
| T7 | POST /run durante PG down → fallback graceful (session cache RAM) | P1 |
| T8 | POST /run durante Redis down → graph execution completata (bus emit fallisce silenziosamente) | P1 |

### 6.3 Test Multi-Utente / Concorrenza

```python
# Pseudocodice test di carico
# Tool: locust o k6
# Scenario: ramp-up 1→20 utenti in 60s, sustained 60s, ramp-down 60s

# Acceptance criteria:
# - p50 < 1500ms under 10 concurrent
# - p95 < 5000ms under 20 concurrent
# - 0% 5xx errors
# - No thread deadlock (monitor via /metrics)
# - No memory leak (RSS stable over 5 min)
```

---

## 7. Rischi Top-10 e Dipendenze Bloccanti

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---------|-------------|---------|-------------|
| R1 | nest_asyncio contamination rompe con upgrade uvicorn/uvloop | Alta | Alto | F2.1: forzare `--loop asyncio`, rimuovere nest_asyncio |
| R2 | Channel drift non rilevato causa eventi persi in produzione | Media | Alto | F1.1: channel_registry.py + F1.4: alignment test |
| R3 | Thread pool thrashing in llm_mcp_node causa OOM sotto carico | Media | Alto | F0.5: pool condiviso singleton |
| R4 | Single uvicorn worker crash = downtime totale api_graph | Bassa | Critico | F0.4: `--workers 2` |
| R5 | Evoluzione verso Option B forzata senza preparazione | Media | Alto | Decidere A+ ora, documentare perché B è prematura |
| R6 | Per-user lock LRU eviction sotto carico alto → lock perse | Bassa | Medio | Monitorare `_USER_LOCKS` size via /metrics |
| R7 | Graph compilation race (due thread, nessun lock) | Molto bassa | Basso | F0.7: lock esplicito |
| R8 | Nessuna osservabilità su channel lag/dead letters | Media | Medio | F3.3: dashboard dedicated |
| R9 | SelectorEventLoop creato/distrutto ~30x/sec sotto carico | Media | Medio | F2.2: executor condiviso |
| R10 | correlation_id creato ovunque crea falsa aspettativa di tracing | Bassa | Basso | F1.2: documentare come trace_id |

**Dipendenze bloccanti:**
- F0.5 e F2.1 devono essere testati insieme (entrambi toccano async patterns)
- F1.1 (channel registry) deve precedere F1.4 (alignment test)
- F2.3 (workers aumento) richiede benchmark prima dell'implementazione

---

## 8. Open Questions per Workshop Tecnico

### Domande Decisive (da discutere prima di implementare)

1. **Ortodossia sincrona o asincrona?**
   - Oggi: il verdict è sempre "locally_blessed" (fallback). Il listener processa async ma il risultato non torna al client.
   - Domanda: il client **ha bisogno** del verdict dell'Orthodoxy Wardens nella response HTTP? Se sì, serve un micro-roundtrip (200ms budget). Se no, il fire-and-forget attuale è corretto e il TODO va rimosso.

2. **uvloop: tenere o rimuovere?**
   - uvloop dà ~20% speedup su I/O bound workloads, ma crea cascata di workaround con nest_asyncio.
   - Domanda: il grafo è I/O bound (LLM calls, PG, Redis) o CPU bound (parsing, logic)? Se I/O bound, `--loop asyncio` costa 20% latenza. Se CPU bound, non cambia nulla.

3. **Quanti utenti concorrenti in produzione?**
   - Il dimensionamento (workers, pool size) dipende dal carico reale.
   - Con 4 thread pool + 1 worker: ~4-8 req/s. Con 8 pool + 2 workers: ~12-20 req/s.
   - Domanda: qual è il target di utenti concorrenti per i prossimi 6 mesi?

4. **Channel registry: LIVELLO 1 o LIVELLO 2?**
   - I canali sono un contratto condiviso tra Sacred Orders.
   - Domanda: il registry va nel core (LIVELLO 1, `vitruvyan_core/core/synaptic_conclave/channels/`) o in un file di configurazione condiviso a LIVELLO 2?
   - Raccomandazione: LIVELLO 1 (è un contratto architetturale, non un dettaglio operativo).

5. **Codex Hunters: fire-and-forget o callback?**
   - Oggi il codex_hunters_node usa HTTP polling verso l'API Codex (non il bus).
   - Le expedition possono durare minuti.
   - Domanda: il pattern attuale (polling) è accettabile o serve un webhook callback?

6. **Quanto a lungo mantenere `_legacy/`?**
   - `redis_client_shim.py` non è usato da nessuno. I test legacy usano `system.audit.requested`.
   - Domanda: fissare una deadline per la rimozione (suggerimento: Q2 2026)?

7. **Monitoring: Prometheus sufficiente o serve distributed tracing?**
   - Con A+ (fire-and-forget), Prometheus + channel lag metrics bastano.
   - Con B (round-trip), serve Jaeger/Zipkin con correlation_id.
   - Domanda: la decisione A+ elimina la necessità di distributed tracing?

---

## 9. Critica Costruttiva all'Audit Precedente

### Cosa ha fatto bene l'audit ChatGPT:
1. **Identificazione corretta dei 5 temi** (sync vs async, bus publishing, round-trip, channel drift, concurrency)
2. **Framing della decisione A vs B** come domanda architetturale centrale
3. **Rilevazione del channel drift vault.integrity.requested** — confermata

### Dove l'audit era impreciso o fuorviante:
1. **"shim legacy" usato dai nodi** → Falso. I nodi usano StreamBus direttamente. Lo shim esiste ma non è mai importato dai nodi. Questo errore potrebbe portare a sprecare effort su una migrazione non necessaria.
2. **"doppia inizializzazione grafo"** → Non confermato. Due entry point per lo stesso singleton.
3. **"round-trip disattivato nei nodi"** → Framing errato. Il round-trip non è mai stato attivato. Non c'è codice dormiente, c'è un TODO.
4. **Mancanza di contesto quantitativo** → L'audit non ha misurato/stimato latenze, non ha esaminato l'ExecutionGuard (4 thread pool), non ha compreso che asyncio.to_thread() mitiga il single-worker issue.
5. **Gravità undifferenziata** → Tutto presentato come "possibile problema" senza separare bug reali (channel drift vault, L188 routes.py) da design deliberato (fire-and-forget, single worker con async).

### Dove l'audit avrebbe dovuto scavare di più:
1. **uvloop + nest_asyncio chain** — Il problema di concurrency più grave non è il single worker, è la contaminazione asincrona. L'audit precedente lo ha sfiorato senza entrare nel dettaglio tecnico.
2. **ExecutionGuard** — Non menzionato. È il vero meccanismo di concurrency del sistema (ThreadPoolExecutor con hard timeout).
3. **Session cache RAM + PG fallback** — Non menzionato. È un pattern architetturale sofisticato (Feb 23, 2026) che dimostra che il team ha già affrontato problemi di resilienza.

---

## 10. Conclusione

**Il sistema è già Option A.** Non per default, ma per scelta evolutiva: i nodi emettono eventi per post-processing, applicano fallback locali, e il client HTTP riceve una risposta sincrona. I residui di un'architettura round-trip mai implementata (correlation_id, TODO comments, canali morti) vanno puliti, non completati.

**Option B non è giustificata oggi** perché:
- Nessun Sacred Order ha bisogno che il suo output rientri nella response HTTP
- Il costo di implementazione (15-20 gg/u) non è proporzionato al beneficio
- Introduce failure modes nuovi (correlation store, ordering, timeout cascade) senza eliminarne di esistenti

**A+ è il path consigliato**: ripulire A, contrattualizzare i canali, risolvere i problemi di concurrency reali (nest_asyncio, thread pool thrashing), e abilitare evoluzione event-driven selettiva solo dove il valore è dimostrabile.

**Effort totale Fase 0-2**: 9 giorni/uomo  
**Effort Fase 3 (opzionale)**: 3 giorni/uomo  
**Decision checkpoint**: dopo Fase 1, rivalutare se Fase 3 serve.

---

*Fine documento. Preparato per workshop tecnico di allineamento.*
