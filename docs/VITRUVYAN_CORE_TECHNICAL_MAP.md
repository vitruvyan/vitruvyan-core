# Vitruvyan Core — Mappa Tecnica dei Moduli

> **Versione**: 1.0 — February 15, 2026  
> **Destinatario**: Sviluppatore senior con esperienza architetturale  
> **Scopo**: Descrivere COSA fa ogni modulo, DOVE si trova, CHI lo chiama, COSA riceve e COSA produce

---

## Indice

1. [Cos'è Vitruvyan Core (in 60 secondi)](#1-cosè-vitruvyan-core-in-60-secondi)
2. [Mappa dei Moduli](#2-mappa-dei-moduli)
   - [2.1 Agents (Gateway Singleton)](#21-agents--gateway-singleton)
   - [2.2 LLM Subsystem](#22-llm-subsystem)
   - [2.3 Synaptic Conclave (Event Bus)](#23-synaptic-conclave--event-bus)
   - [2.4 Orchestrazione (LangGraph Pipeline)](#24-orchestrazione--langgraph-pipeline)
   - [2.5 Pipeline Nodes (Stadi Cognitivi)](#25-pipeline-nodes--stadi-cognitivi)
   - [2.6 Neural Engine (Batch Scoring)](#26-neural-engine--batch-scoring)
   - [2.7 VPAR (Risk, Explainability, Grounding)](#27-vpar--risk-explainability-grounding)
   - [2.8 Sacred Orders (Governance Modules)](#28-sacred-orders--governance-modules)
   - [2.9 Cache](#29-cache)
   - [2.10 Middleware & Logging](#210-middleware--logging)
3. [Diagramma dei Flussi](#3-diagramma-dei-flussi)
4. [Flusso End-to-End di una Richiesta](#4-flusso-end-to-end-di-una-richiesta)
5. [Dove e Quando Ha Senso Adottarlo](#5-dove-e-quando-ha-senso-adottarlo)
6. [Indice Variabili d'Ambiente](#6-indice-variabili-dambiente)

---

## 1. Cos'è Vitruvyan Core (in 60 secondi)

Vitruvyan Core è un **framework per costruire applicazioni AI conversazionali con governance**. Non è un chatbot: è l'infrastruttura che orchestra una pipeline cognitiva dove un input testuale attraversa ~15 stadi (comprensione linguistica → classificazione intent → ricerca semantica → generazione risposta → validazione → archiviazione) con audit trail, fault tolerance, e isolamento dei domini.

**Analogia tecnica**: se hai mai costruito un ETL pipeline con Apache Airflow dove ogni step ha un contratto I/O definito, Vitruvyan Core fa la stessa cosa ma per interazioni AI — con LLM al centro, vector DB per grounding semantico, e un event bus per disaccoppiamento.

**Stack tecnologico**:
- **Python 3.12** + **FastAPI** (12 microservizi)
- **LangGraph** (orchestrazione DAG a stati)
- **Redis Streams** (event bus durevole con consumer groups)
- **PostgreSQL** (persistence, con connection pooling)
- **Qdrant** (vector database per semantic search/RAG)
- **OpenAI API** (LLM, pluggabile via Protocol)

**Non è domain-specific**: il core non sa nulla di finanza, salute o logistica. I domini si inseriscono a runtime tramite variabili d'ambiente e plugin Python.

---

## 2. Mappa dei Moduli

### 2.1 Agents — Gateway Singleton

Gli Agents sono **wrapper singleton** che centralizzano l'accesso a sistemi esterni. Nessun modulo del core chiama direttamente `psycopg2`, `qdrant_client` o `openai` — passa sempre da qui.

---

#### PostgresAgent

| Campo | Valore |
|:---|:---|
| **Path** | `core/agents/postgres_agent.py` (315 righe) |
| **Come si ingaggia** | `from core.agents.postgres_agent import PostgresAgent` → `pg = PostgresAgent()` |
| **Chi lo ingaggia** | Tutti i servizi (adapters/persistence.py), AuditLogger, AlchemistAgent |
| **Input** | SQL + parametri (`str`, `Tuple`) |
| **Funzionalità** | CRUD su PostgreSQL con connection pooling thread-safe |
| **Output** | `List[Dict]` (righe), `bool` (esito), `Any` (scalare), `Generator` (paginato) |
| **Parametri env** | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_POOL_MIN` (2), `POSTGRES_POOL_MAX` (10) |
| **Utile fuori finanza?** | **Sì** — è un wrapper PostgreSQL generico con pooling e transazioni. Qualsiasi applicazione che usa Postgres ne beneficia. |
| **Prompt AI?** | No |

**Metodi principali**:
```python
pg.fetch("SELECT * FROM events WHERE type = %s", ("alert",))     # → List[Dict]
pg.execute("INSERT INTO logs (msg) VALUES (%s)", ("test",))       # → bool
pg.fetch_paginated("SELECT * FROM big_table", page_size=500)      # → Generator[List[Dict]]
with pg.transaction(): pg.execute(...)                             # Transazione atomica
```

---

#### QdrantAgent

| Campo | Valore |
|:---|:---|
| **Path** | `core/agents/qdrant_agent.py` (382 righe) |
| **Come si ingaggia** | `from core.agents.qdrant_agent import QdrantAgent` → `qa = QdrantAgent()` |
| **Chi lo ingaggia** | `qdrant_node`, `semantic_grounding_node` (via VSGSEngine), Memory Orders, Vault Keepers |
| **Input** | Vettori numerici (`List[float]`), filtri, metadati |
| **Funzionalità** | CRUD su Qdrant vector database: creazione collection, upsert punti, ricerca vettoriale (nearest-neighbor), conteggio |
| **Output** | `Dict` con risultati di ricerca (hits con score e payload) |
| **Parametri env** | `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_TIMEOUT` (30s) |
| **Utile fuori finanza?** | **Sì** — è l'interfaccia standard per qualsiasi operazione RAG, semantic search, o knowledge base vettoriale. |
| **Prompt AI?** | No |

**Metodi principali**:
```python
qa.ensure_collection("docs", vector_size=384)                     # Crea collection
qa.upsert("docs", [{"id": "1", "vector": [...], "payload": {}}]) # Inserisce
qa.search("docs", query_vector=[...], top_k=5)                    # Ricerca semantica
```

---

#### LLMAgent

| Campo | Valore |
|:---|:---|
| **Path** | `core/agents/llm_agent.py` (853 righe) |
| **Come si ingaggia** | `from core.agents.llm_agent import get_llm_agent` → `llm = get_llm_agent()` |
| **Chi lo ingaggia** | 7 nodi della pipeline (intent_detection, parse, compose, can, cached_llm, llm_mcp, params_extraction), servizi |
| **Input** | Prompt testuale (`str`) + system prompt opzionale + parametri (model, temperature, max_tokens) |
| **Funzionalità** | Gateway verso OpenAI (o qualsiasi provider che implementi `ILLMProvider`). Include: rate limiting (RPM/TPM), circuit breaker (5 fallimenti → open, 60s recovery), metriche, cache integrata |
| **Output** | `str` (testo) o `Dict` (JSON strutturato / tool calls) |
| **Parametri env** | `OPENAI_API_KEY`, `VITRUVYAN_LLM_MODEL` → `GRAPH_LLM_MODEL` → `OPENAI_MODEL` → `gpt-4o-mini`, `LLM_RATE_LIMIT_RPM` (500), `LLM_RATE_LIMIT_TPM` (30000) |
| **Utile fuori finanza?** | **Sì** — è il gateway centralizzato per qualsiasi applicazione che usi LLM. Rate limiting, circuit breaker, caching e metriche sono utili in ogni contesto. |
| **Prompt AI?** | No (i prompt li iniettano i chiamanti) |

**Metodi principali**:
```python
llm.complete("Riassumi questo testo: ...", system_prompt="Sei un assistente.")     # → str
llm.complete_json("Estrai entità: ...", system_prompt="Rispondi in JSON.")          # → Dict
llm.complete_with_tools(messages=[...], tools=[...])                                # → Dict (Function Calling)
llm.complete_with_messages([{"role": "user", "content": "..."}])                    # → str (multi-turn)
```

---

#### AlchemistAgent

| Campo | Valore |
|:---|:---|
| **Path** | `core/agents/alchemist_agent.py` (~110 righe) |
| **Come si ingaggia** | `AlchemistAgent(cognitive_bus=stream_bus)` |
| **Chi lo ingaggia** | Memory Orders service |
| **Input** | Nessun input esplicito — legge stato Alembic |
| **Funzionalità** | Verifica e applica migrazioni schema PostgreSQL via Alembic |
| **Output** | `Dict` con `status` ("up_to_date"/"inconsistent"), `db_revision`, `head_revision`. Emette eventi su Redis Streams. |
| **Parametri env** | `ALEMBIC_CONFIG` (path al file .ini) |
| **Utile fuori finanza?** | **Sì** — qualsiasi app con schema PostgreSQL migrabile. |
| **Prompt AI?** | No |

---

### 2.2 LLM Subsystem

---

#### PromptRegistry

| Campo | Valore |
|:---|:---|
| **Path** | `core/llm/prompts/registry.py` (331 righe) |
| **Come si ingaggia** | `from core.llm.prompts.registry import PromptRegistry` → metodi statici |
| **Chi lo ingaggia** | Plugin di dominio (al boot), `cached_llm_node`, `compose_node`, `can_node` |
| **Input** | Template con placeholder (`{assistant_name}`, `{domain_description}`) + parametri a runtime |
| **Funzionalità** | Registra e recupera prompt per dominio e lingua. Supporta scenari (analisi, raccomandazione, onboarding) e traduzioni. Il core registra prompt generici; ogni verticale registra i propri. |
| **Output** | `str` (prompt formattato con variabili sostituite) |
| **Parametri env** | Nessuno |
| **Utile fuori finanza?** | **Sì** — qualsiasi app multi-dominio che servire prompt LLM diversi per contesto/lingua. |
| **Prompt AI?** | Sì — contiene i **template** dei prompt (l'infrastruttura, non il contenuto di dominio) |

**Uso**:
```python
PromptRegistry.register_domain("healthcare", identity_template="Sei {name}...", ...)
prompt = PromptRegistry.get_identity("healthcare", language="it", name="MediBot")  # → str
```

---

#### LLMCacheManager

| Campo | Valore |
|:---|:---|
| **Path** | `core/llm/cache_manager.py` (449 righe) |
| **Come si ingaggia** | `from core.llm.cache_manager import get_cache_manager` (singleton) |
| **Chi lo ingaggia** | `LLMAgent` (internamente), `cached_llm_node`, `cache_api.py` |
| **Input** | State della pipeline + tipo di prompt → genera cache key |
| **Funzionalità** | Cache Redis delle risposte LLM. Evita chiamate duplicate all'API OpenAI. Include: ricerca di risposte simili, pulizia scadute, invalidazione per entità, statistiche di hit/miss. |
| **Output** | `Optional[CacheEntry]` (risposta cached) o `bool` (esito cache write) |
| **Parametri env** | `LLM_CACHE_TTL_HOURS` (24), `LLM_CACHE_MAX_SIZE` (10000), `LLM_CACHE_SIMILARITY_THRESHOLD` (0.85) |
| **Utile fuori finanza?** | **Sì** — riduzione costi LLM universale. Chiunque paghi per token OpenAI beneficia del caching. |
| **Prompt AI?** | No |

---

### 2.3 Synaptic Conclave — Event Bus

---

#### StreamBus

| Campo | Valore |
|:---|:---|
| **Path** | `core/synaptic_conclave/transport/streams.py` (656 righe) |
| **Come si ingaggia** | `from core.synaptic_conclave.transport.streams import StreamBus` → `bus = StreamBus()` |
| **Chi lo ingaggia** | `orthodoxy_node`, `vault_node`, `codex_hunters_node`, tutti i `bus_adapter.py` nei servizi, `streams_listener.py` |
| **Input** | `channel` (stringa dot-notation, es. `vault.archive.completed`), `payload` (dict), `emitter` (identificativo) |
| **Funzionalità** | Event bus durevole su Redis Streams. Supporta: consumer groups (fan-out), acknowledgment esplicito, replay, stream info. Payload-blind (non ispeziona il contenuto). Supporta TLS e password. |
| **Output** | `str` (event ID) per emit, `Generator[StreamEvent]` per consume |
| **Parametri env** | `REDIS_HOST/PORT/PASSWORD/SSL`, `STREAM_PREFIX` ("vitruvyan"), `STREAM_MAX_LEN` (100K), `STREAM_MAX_AGE_DAYS` (7) |
| **Utile fuori finanza?** | **Sì** — è un message bus generico comparabile a Kafka/RabbitMQ ma su Redis (più leggero, meno latenza). Utile per qualsiasi architettura event-driven. |
| **Prompt AI?** | No |

**Pattern tipico**:
```python
# Producer
bus.emit("alerts.created", {"severity": "high", "message": "..."})

# Consumer
bus.create_consumer_group("alerts.created", "notification_service")
for event in bus.consume("alerts.created", "notification_service", "worker_1"):
    process(event.payload)
    bus.ack(event, "notification_service")
```

---

#### DeadLetterQueue

| Campo | Valore |
|:---|:---|
| **Path** | `core/synaptic_conclave/transport/dlq.py` (360 righe) |
| **Come si ingaggia** | `bus.dlq.record_failure(stream, event_id, group, consumer, reason)` |
| **Chi lo ingaggia** | StreamBus (automaticamente), streams listener error handlers |
| **Input** | Metadati dell'evento fallito (stream, event_id, gruppo, motivo) |
| **Funzionalità** | Traccia i retry per ogni evento. Dopo N fallimenti (`DLQ_MAX_RETRIES`), sposta l'evento nel stream `vitruvyan:dlq`. Idempotenza via SHA256 (previene duplicati in DLQ). |
| **Output** | `bool` (True se spostato in DLQ, False se ancora in retry) |
| **Parametri env** | `DLQ_MAX_RETRIES` (3), `DLQ_STREAM_MAX_LEN` (50000) |
| **Utile fuori finanza?** | **Sì** — pattern DLQ standard per qualsiasi sistema event-driven che necessita di fault tolerance. |
| **Prompt AI?** | No |

---

#### Event Envelopes

| Campo | Valore |
|:---|:---|
| **Path** | `core/synaptic_conclave/events/event_envelope.py` (290 righe) |
| **Come si ingaggia** | Import diretto dei dataclass: `TransportEvent`, `CognitiveEvent`, `EventAdapter` |
| **Chi lo ingaggia** | StreamBus (internamente), tutti i consumer nei servizi |
| **Input** | Dati Redis raw (per deserializzazione) o campi strutturati (per creazione) |
| **Funzionalità** | Definisce la forma degli eventi a due livelli: **TransportEvent** (bus-level, frozen, payload opaco) e **CognitiveEvent** (consumer-level, con correlation/causation chain). **EventAdapter** converte tra i due. |
| **Output** | Dataclass istanziati |
| **Parametri env** | Nessuno |
| **Utile fuori finanza?** | **Sì** — pattern Envelope standard per event sourcing. |
| **Prompt AI?** | No |

---

### 2.4 Orchestrazione — LangGraph Pipeline

---

#### graph_flow.py (Assembla il DAG)

| Campo | Valore |
|:---|:---|
| **Path** | `core/orchestration/langgraph/graph_flow.py` (377 righe) |
| **Come si ingaggia** | Chiamato da `graph_runner.py` → `build_graph()` |
| **Chi lo ingaggia** | `graph_runner.py` (una sola volta, lazily) |
| **Input** | Variabili d'ambiente: `INTENT_DOMAIN`, `USE_MCP`, `ENABLE_MINIMAL_GRAPH` |
| **Funzionalità** | Assembla il grafo LangGraph collegando ~20 nodi in un DAG con branching condizionale. Carica il plugin di dominio dinamicamente (`importlib.import_module(f"domains.{domain}.intent_config")`). Configura il routing: quale intent va a quale nodo. |
| **Output** | `CompiledStateGraph` (grafo LangGraph compilato, pronto per `invoke()`) |
| **Parametri env** | `INTENT_DOMAIN` (generic), `ENTITY_DOMAIN`, `USE_MCP` (0), `ENABLE_MINIMAL_GRAPH` (false) |
| **Utile fuori finanza?** | **Sì** — è il "process orchestrator" domain-agnostic. Qualsiasi vertical si inserisce senza toccare questo codice. |
| **Prompt AI?** | No |

---

#### graph_runner.py (Punto di ingresso)

| Campo | Valore |
|:---|:---|
| **Path** | `core/orchestration/langgraph/graph_runner.py` (384 righe) |
| **Come si ingaggia** | `from core.orchestration.langgraph.graph_runner import run_graph_once` |
| **Chi lo ingaggia** | `api_graph` service (endpoint HTTP) |
| **Input** | `input_text: str`, `user_id: str`, `validated_entities: Optional[List]`, `language: Optional[str]` |
| **Funzionalità** | Entry point della pipeline: carica sessione precedente dell'utente, genera `trace_id` (UUID4), esegue il grafo con timeout globale (`GRAPH_EXEC_TIMEOUT_SECONDS`), salva stato sessione, emette audit event su timeout/errore. |
| **Output** | `Dict[str, Any]` con `response` (testo finale), `intent`, `emotion`, `route`, `trace_id`, ecc. |
| **Parametri env** | `ENABLE_MINIMAL_GRAPH` (false), `GRAPH_EXEC_TIMEOUT_SECONDS` (120) |
| **Utile fuori finanza?** | **Sì** — è il runtime generico per qualsiasi pipeline conversazionale. |
| **Prompt AI?** | No |

---

#### NodeExecutionGuard

| Campo | Valore |
|:---|:---|
| **Path** | `core/orchestration/execution_guard.py` (~195 righe) |
| **Come si ingaggia** | `from core.orchestration.execution_guard import get_execution_guard` |
| **Chi lo ingaggia** | `graph_runner.py` |
| **Input** | Handler function + state dict + timeout |
| **Funzionalità** | Wrappa l'esecuzione di ogni nodo in un `ThreadPoolExecutor` con timeout hard. Se un nodo non risponde entro N secondi, viene terminato e il risultato è `timed_out=True`. Previene hang della pipeline. |
| **Output** | `ExecutionResult(success, state, execution_time_ms, timed_out, error, node_name)` |
| **Parametri env** | `NODE_EXEC_TIMEOUT_SECONDS` (30), `NODE_EXEC_MAX_WORKERS` (4) |
| **Utile fuori finanza?** | **Sì** — qualsiasi pipeline con step non trusted (API esterne, LLM, scraping) beneficia di timeout enforcement. |
| **Prompt AI?** | No |

---

#### IntentRegistry

| Campo | Valore |
|:---|:---|
| **Path** | `core/orchestration/intent_registry.py` (388 righe) |
| **Come si ingaggia** | `from core.orchestration.intent_registry import IntentRegistry, IntentDefinition` |
| **Chi lo ingaggia** | Plugin di dominio (registrano intenti), `intent_detection_node` (usa il registry per classificare), `graph_flow.py` (configura routing basato sugli intenti) |
| **Input** | `IntentDefinition(name, description, examples, synonyms, requires_entities, route_type)` per registrazione; `user_input: str` per build prompt di classificazione |
| **Funzionalità** | Registro domain-agnostic degli intenti riconoscibili dalla pipeline. Il dominio registra i propri intenti; il core aggiunge `soft` e `unknown`. Genera il prompt per la classificazione LLM. Risolve sinonimi. Separa intenti "exec" (richiedono azione) da "soft" (conversazionali). |
| **Output** | `str` (prompt di classificazione), `List[str]` (labels), `Optional[IntentDefinition]` (lookup) |
| **Parametri env** | Nessuno (configurazione via codice) |
| **Utile fuori finanza?** | **Sì** — qualsiasi chatbot/assistente con intenti multipli. Equivalente domain-agnostic di Dialogflow/LUIS. |
| **Prompt AI?** | Sì — genera il prompt di classificazione per l'LLM (template, non contenuto hardcoded) |

---

#### BaseGraphState

| Campo | Valore |
|:---|:---|
| **Path** | `core/orchestration/base_state.py` (196 righe) |
| **Come si ingaggia** | Ereditato da `GraphState` in `graph_flow.py`. I domini estendono con campi propri. |
| **Chi lo ingaggia** | Tutti i nodi della pipeline leggono/scrivono campi di questo stato |
| **Input** | N/A (è un TypedDict, non una funzione) |
| **Funzionalità** | Definisce i ~37 campi standard che attraversano la pipeline: `input_text`, `intent`, `route`, `language_detected`, `emotion_detected`, `orthodoxy_verdict`, `vault_status`, `trace_id`, `final_response`, ecc. I domini aggiungono i propri campi. |
| **Output** | N/A |
| **Parametri env** | Nessuno |
| **Utile fuori finanza?** | **Sì** — è il contratto base di qualsiasi pipeline LangGraph con governance. |
| **Prompt AI?** | No |

---

### 2.5 Pipeline Nodes — Stadi Cognitivi

Ogni nodo è una funzione `node_name(state: dict) → dict` che legge campi dallo stato, li elabora, e restituisce i campi aggiornati. Tutti vivono in `core/orchestration/langgraph/node/`.

#### Tabella riassuntiva

| # | Nodo | File (righe) | Legge | Scrive | Chiama | LLM? |
|:---:|:---|:---|:---|:---|:---|:---:|
| 1 | **parse** | `parse_node.py` (303) | `input_text` | `entity_ids`, `intent` (fallback) | `get_llm_agent()`, semantic_engine | Sì |
| 2 | **intent_detection** | `intent_detection_node.py` (316) | `input_text`, `language` | `intent`, `proposed_exec` | `get_llm_agent()` (GPT classifica), Babel API | **Sì** |
| 3 | **weaver** | `pattern_weavers_node.py` (143) | `input_text`, `user_id` | `weaver_context`, `matched_concepts` | HTTP → Pattern Weavers API | No |
| 4 | **entity_resolver** | `entity_resolver_node.py` (66) | `entity_ids`, `input_text` | entità risolte | `EntityResolverRegistry` | No |
| 5 | **babel_emotion** | `emotion_detector.py` (125) | `input_text` | `emotion_detected`, `emotion_confidence` | HTTP → Babel Gardens API | No |
| 6 | **semantic_grounding** | `semantic_grounding_node.py` (99) | `input_text`, `user_id`, `intent` | `semantic_matches`, `vsgs_status` | VSGSEngine → Qdrant + Embedding API | No |
| 7 | **params_extraction** | `params_extraction_node.py` (324) | `input_text`, `horizon`, `top_k` | `horizon`, `top_k`, `route` | `get_llm_agent()` (fallback) | Sì |
| 8 | **decide** | `route_node.py` (96) | `intent`, `proposed_exec` | `route` | — | No |
| 9 | **exec** | `exec_node.py` (64) | stato completo | `raw_output`, `route` | `ExecutionRegistry` (hook dominio) | No |
| 10 | **qdrant** | `qdrant_node.py` (86) | `input_text` | `result.hits` | QdrantAgent + Embedding API | No |
| 11 | **cached_llm** | `cached_llm_node.py` (378) | `input_text`, `intent`, emozione, VSGS | `result.response_text` | `get_llm_agent()`, LLMCacheManager | **Sì** |
| 12 | **output_normalizer** | `output_normalizer_node.py` (79) | `route`, `raw_output`, `result` | `result` (normalizzato) | — | No |
| 13 | **orthodoxy** | `orthodoxy_node.py` (328) | stato completo | `orthodoxy_status`, `orthodoxy_verdict`, `orthodoxy_findings` | StreamBus (emette evento) | No |
| 14 | **vault** | `vault_node.py` (364) | `input_text`, `_domain_config` | `vault_status`, `vault_protection`, `vault_blessing` | StreamBus (emette evento) | No |
| 15 | **compose** | `compose_node.py` (243) | `intent`, `route`, `input_text`, `raw_output` | `narrative`, `response` | `get_llm_agent()` | **Sì** |
| 16 | **can** | `can_node.py` (309) | `intent`, `conversation_type`, `input_text`, `language` | `final_response`, `follow_ups` | `get_llm_agent()` | **Sì** |
| 17 | **advisor** | `advisor_node.py` (140) | `user_requests_action`, panel/matrix data | `advisor_recommendation` | — (STUB) | No |
| 18 | **codex_hunters** | `codex_hunters_node.py` (470) | stato | risultati expedizione | HTTP → Codex API + StreamBus | No |
| 19 | **llm_mcp** | `llm_mcp_node.py` (315) | `input_text`, `intent`, `entity_ids` | `raw_output`, MCP tool results | `get_llm_agent()` (Function Calling) + MCP Server | **Sì** |
| 20 | **audit** | `audit_node_simple.py` (234) | stato completo | `audit_findings`, `audit_critical_count` | — | No |

**Tutti i nodi sono domain-agnostic.** Nessun nodo contiene logica di finanza o altri domini.

---

### 2.6 Neural Engine — Batch Scoring

| Campo | Valore |
|:---|:---|
| **Path** | `core/neural_engine/` — 4 file: `engine.py` (304), `scoring.py` (204), `composite.py` (180), `ranking.py` (205) |
| **Come si ingaggia** | `NeuralEngine(data_provider, scoring_strategy)` → `engine.run(profile, top_k)` |
| **Chi lo ingaggia** | `api_neural_engine` service via `EngineOrchestrator`, `exec_node` (via hook dominio) |
| **Input** | Un **dataframe** di entità con feature numeriche, un profilo di pesi (es. "balanced"), top_k risultati |
| **Funzionalità** | Pipeline 4 fasi: **(1)** Recupero universo entità → **(2)** Calcolo z-score per feature → **(3)** Composito pesato (Σ z_i × w_i) → **(4)** Ranking con percentile bucketing |
| **Output** | `Dict` con `ranked_entities` (DataFrame ordinato), `metadata`, `statistics`, `diagnostics` |
| **Parametri env** | Nessuno nel core (configurazione via dependency injection) |
| **Utile fuori finanza?** | **Sì** — è un ranking engine generico. Funziona per qualsiasi scenario di scoring multi-fattore: valutazione candidati HR, ranking prodotti e-commerce, prioritizzazione bug/ticket, scoring lead CRM. Basta implementare `IDataProvider` (da dove leggi i dati) e `IScoringStrategy` (come li pesi). |
| **Prompt AI?** | No |

**Componenti interni**:

| Classe | Cosa fa | Input → Output |
|:---|:---|:---|
| `ZScoreCalculator` | Normalizza features in z-score | DataFrame con N feature → DataFrame con N colonne `{feature}_z` |
| `CompositeScorer` | Pesa e aggrega z-score | DataFrame z-scored + profilo pesi → `composite_score` per riga |
| `RankingEngine` | Ordina e buckettizza | DataFrame scored → DataFrame con `rank`, `percentile`, `bucket` |

---

### 2.7 VPAR — Risk, Explainability, Grounding

4 sub-engine indipendenti, tutti contract-driven (richiedono un provider di dominio).

| Sub-Engine | Path | Classe | Input → Output | Scopo |
|:---|:---|:---|:---|:---|
| **VSGS** (Grounding) | `core/vpar/vsgs/vsgs_engine.py` (184) | `VSGSEngine` | testo → `GroundingResult` (matches semantici da Qdrant) | Ancora le risposte LLM a fatti verificabili dal vector DB (anti-hallucination) |
| **VEE** (Explainability) | `core/vpar/vee/vee_engine.py` (204) | `VEEEngine` | entity_id + metriche → spiegazione testuale | Genera narrative "perché questo score?" |
| **VARE** (Risk) | `core/vpar/vare/vare_engine.py` (329) | `VAREEngine` | entity_id + dati raw → `RiskResult` (score + categorizzazione) | Valutazione rischio multi-dimensionale |
| **VWRE** (Attribution) | `core/vpar/vwre/vwre_engine.py` (387) | `VWREEngine` | composite_score + factors → `AttributionResult` | Reverse engineering: "quale fattore ha pesato di più?" |

**Utili fuori finanza?** **Sì**:
- VSGS → qualsiasi RAG (Retrieval-Augmented Generation) per grounding
- VEE → qualsiasi sistema che deve spiegare un punteggio (credito, assicurazione, HR)
- VARE → qualsiasi scoring con componente rischio (supply chain, compliance)
- VWRE → trasparenza algoritmica, auditing ML

**Prompt AI?** No (VEE genera testo tramite template del provider, non LLM)

---

### 2.8 Sacred Orders — Governance Modules

I Sacred Orders sono moduli di governance organizzati in **due livelli**:
- **LIVELLO 1** (`core/cognitive/` o `core/governance/`): logica pura Python, zero I/O, testabile senza Docker
- **LIVELLO 2** (`services/api_*/`): microservizio FastAPI che orchestra LIVELLO 1 + infrastruttura

| Sacred Order | LIVELLO 1 Path | LIVELLO 2 Path | Funzionalità |
|:---|:---|:---|:---|
| **Babel Gardens** | `core/cognitive/babel_gardens/` | `services/api_babel_gardens/` | Percezione linguistica: language detection, emotion detection, sentiment fusion, topic classification |
| **Pattern Weavers** | `core/cognitive/pattern_weavers/` | `services/api_pattern_weavers/` | Contestualizzazione semantica: matching concetti da tassonomia configurabile, weaving di contesto |
| **Codex Hunters** | `core/governance/codex_hunters/` | `services/api_codex_hunters/` | Discovery e manutenzione: consistenza cross-store (PG ↔ Qdrant), expedizioni di verifica |
| **Memory Orders** | `core/governance/memory_orders/` | `services/api_memory_orders/` | Coerenza della memoria: drift detection (PG vs Qdrant), pianificazione sync, RAG state management |
| **Vault Keepers** | `core/governance/vault_keepers/` | `services/api_vault_keepers/` | Archiviazione e protezione: backup, snapshot, archival, monitoraggio sicurezza |
| **Orthodoxy Wardens** | `core/governance/orthodoxy_wardens/` | `services/api_orthodoxy_wardens/` | Governance e validazione: audit compliance, pattern matching su output, enforcement invarianti |

**Consumer LIVELLO 1 chiave per ordine**:

| Ordine | Consumer | Input → Output |
|:---|:---|:---|
| Memory Orders | `CoherenceAnalyzer` | `CoherenceInput(pg_count, qdrant_count, thresholds)` → `CoherenceReport(drift%, recommendation)` |
| Vault Keepers | `Archivist` | `{"operation": "backup"}` → `VaultSnapshot` |
| Orthodoxy Wardens | `Inquisitor` | `Confession(text)` → `InquisitorResult(findings: Tuple[Finding], rules_applied)` |
| Codex Hunters | `InspectorConsumer` | count/ID from two stores → `InspectionReport(consistency_scores, orphan_lists)` |
| Babel Gardens | `TopicClassifierConsumer` | testo → topic labels con confidence |
| Pattern Weavers | `KeywordMatcher` | testo + tassonomia → concetti matchati |

**Utili fuori finanza?** **Sì** — sono moduli di governance generici:
- Babel Gardens → qualsiasi piattaforma multilingua
- Orthodoxy Wardens → compliance in healthcare, legal, financial regulation
- Vault Keepers → audit trail, data protection (GDPR-relevant)
- Memory Orders → data integrity per sistemi con dual-store (SQL + Vector)
- Codex Hunters → health monitoring per infrastrutture complesse

**Prompt AI?** No (la logica di governance è rule-based, l'LLM è usato solo nei nodi di pipeline)

---

### 2.9 Cache

#### MnemosyneCache

| Campo | Valore |
|:---|:---|
| **Path** | `core/cache/mnemosyne_cache.py` (393 righe) |
| **Come si ingaggia** | Usato internamente dal layer di ricerca semantica |
| **Chi lo ingaggia** | Operazioni Qdrant search (evita ricerche duplicate) |
| **Input** | `query_vector` + `collection` + `top_k` |
| **Funzionalità** | Cache intelligente per risultati di ricerca vettoriale. Genera hash del vettore query, cerca cache hit. Se il vettore è sufficientemente simile (threshold 0.95), ritorna risultato cached senza interrogare Qdrant. |
| **Output** | `Optional[SemanticCacheEntry]` (risultati cached con metadati: hit_count, similarity) |
| **Parametri env** | `MNEMOSYNE_CACHE_TTL_HOURS` (6), `MNEMOSYNE_CACHE_SIMILARITY_THRESHOLD` (0.95), `MNEMOSYNE_CACHE_PREFIX` |
| **Utile fuori finanza?** | **Sì** — riduzione latenza e costi per qualsiasi app con ricerche vettoriali ripetitive. |
| **Prompt AI?** | No |

---

### 2.10 Middleware & Logging

#### AuthMiddleware

| Campo | Valore |
|:---|:---|
| **Path** | `core/middleware/auth.py` (133 righe) |
| **Come si ingaggia** | `app.add_middleware(AuthMiddleware)` in ogni service `main.py` |
| **Chi lo ingaggia** | Tutti gli 11 servizi FastAPI |
| **Input** | Header HTTP `Authorization: Bearer <token>` |
| **Funzionalità** | Middleware opt-in (default disabilitato). Valida token JWT. Path pubblici configurabili. Supporta validator custom iniettabile e Keycloak. Passthrough per CORS preflight. |
| **Output** | Passa la request o ritorna 401/403 |
| **Parametri env** | `VITRUVYAN_AUTH_ENABLED` (false), `VITRUVYAN_AUTH_SECRET`, `VITRUVYAN_KEYCLOAK_URL`, `AUTH_PUBLIC_PATHS` |
| **Utile fuori finanza?** | **Sì** — middleware auth standard per qualsiasi FastAPI app. |
| **Prompt AI?** | No |

#### AuditLogger

| Campo | Valore |
|:---|:---|
| **Path** | `core/logging/audit.py` (226 righe) |
| **Come si ingaggia** | `from core.logging.audit import get_audit_logger` |
| **Chi lo ingaggia** | `graph_runner.py`, service adapters |
| **Input** | `event_id`, `correlation_id`, `node_id`, `status`, `execution_time_ms`, `error_code`, `**metadata` |
| **Funzionalità** | Logger strutturato multi-backend: (1) Python logger (sempre), (2) Redis Stream `vitruvyan:audit` (default), (3) PostgreSQL (opt-in). Schema `AuditEvent` con campi obbligatori. |
| **Output** | Scrive su Redis Stream e/o PostgreSQL. Non ritorna nulla al chiamante. |
| **Parametri env** | `AUDIT_ENABLED` (true), `AUDIT_STREAM`, `AUDIT_STREAM_MAX_LEN` (200K), `AUDIT_POSTGRES_ENABLED` (false) |
| **Utile fuori finanza?** | **Sì** — audit logging è requisito per qualsiasi sistema in produzione (GDPR, SOC2, ISO 27001). |
| **Prompt AI?** | No |

---

## 3. Diagramma dei Flussi

### 3.1 Pipeline Principale (LangGraph)

```
                          ┌──────────────────────────────────────────────┐
                          │              api_graph (HTTP)                │
                          │         POST /v1/graph/invoke               │
                          │  input: { text, user_id, entities, lang }   │
                          └──────────────┬───────────────────────────────┘
                                         │
                                         ▼
               ┌─────────────────────────────────────────────────┐
               │              graph_runner.py                     │
               │  • Carica sessione utente                       │
               │  • Genera trace_id (UUID4)                      │
               │  • Esegue pipeline con timeout (120s)           │
               │  • Emette audit su errore/timeout               │
               └──────────────────┬──────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────────────────┐
          │                       │ graph_flow.py (DAG)               │
          │                       ▼                                   │
          │  ┌────────┐    ┌──────────────┐    ┌─────────┐           │
          │  │ parse   │───▶│intent_detect │───▶│ weaver  │           │
          │  │ (LLM)   │    │  (LLM+GPT)  │    │ (HTTP)  │           │
          │  └────────┘    └──────────────┘    └────┬────┘           │
          │                                         │                 │
          │  ┌──────────────┐    ┌──────────┐    ┌──┴──────────┐     │
          │  │entity_resolver│◀──│babel_emot│◀───│semantic_gnd │     │
          │  │  (Registry)   │    │  (HTTP)  │    │(Qdrant+Emb)│     │
          │  └──────┬───────┘    └──────────┘    └─────────────┘     │
          │         │                                                 │
          │         ▼                                                 │
          │  ┌──────────────┐    ┌──────────────────────────────┐    │
          │  │params_extract│───▶│          decide (router)      │    │
          │  │   (LLM)      │    │  intent → route mapping       │    │
          │  └──────────────┘    └──────┬───────────────────────┘    │
          │                             │                             │
          │            ┌────────────────┼────────────────────┐       │
          │            ▼                ▼                    ▼       │
          │     ┌────────────┐  ┌──────────────┐  ┌──────────────┐  │
          │     │    exec    │  │  cached_llm  │  │    qdrant    │  │
          │     │(Dominio)   │  │(LLM+Cache)   │  │  (VectorDB) │  │
          │     └────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
          │          │                 │                  │          │
          │          └─────────┬───────┴──────────────────┘          │
          │                    ▼                                      │
          │  ┌──────────────────────────────────────────────────┐    │
          │  │              output_normalizer                    │    │
          │  └──────────────────┬───────────────────────────────┘    │
          │                     │                                     │
          │         ┌───────────┼───────────┐                        │
          │         ▼           ▼           ▼                        │
          │  ┌───────────┐ ┌─────────┐ ┌─────────┐                  │
          │  │ orthodoxy │ │  vault  │ │ compose │                  │
          │  │(StreamBus)│ │(Stream) │ │ (LLM)   │                  │
          │  └───────────┘ └─────────┘ └────┬────┘                  │
          │                                  │                       │
          │                     ┌────────────┼────────────┐          │
          │                     ▼            ▼            ▼          │
          │              ┌───────────┐ ┌──────────┐ ┌────────┐      │
          │              │    can    │ │ advisor  │ │  END   │      │
          │              │  (LLM)   │ │ (stub)   │ │        │      │
          │              └──────────┘ └──────────┘ └────────┘      │
          └──────────────────────────────────────────────────────────┘
```

### 3.2 Architettura Infrastrutturale

```
                    ┌─────────────────────────────────────────┐
                    │            CLIENT (HTTP)                 │
                    └────────────────┬────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
  ┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
  │  api_graph   │        │ api_babel_gardens │        │api_neural_eng│
  │  (Pipeline)  │        │  (NLU/Emotion)   │        │  (Scoring)   │
  │  Port 8000   │        │   Port 8009      │        │  Port 8003   │
  └──────┬───────┘        └──────────────────┘        └──────┬───────┘
         │                                                    │
    ┌────┴────────────────────────────────────────────────────┴────┐
    │                    SHARED AGENTS (Singleton)                  │
    │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
    │  │PostgresAgent│  │ QdrantAgent │  │      LLMAgent       │ │
    │  │ (Pool 2-10) │  │ (Qdrant SDK)│  │(Rate+Circuit+Cache) │ │
    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
    └─────────┼────────────────┼─────────────────────┼────────────┘
              │                │                     │
              ▼                ▼                     ▼
       ┌────────────┐  ┌────────────┐        ┌────────────┐
       │ PostgreSQL  │  │   Qdrant   │        │ OpenAI API │
       │  (RDBMS)    │  │ (VectorDB) │        │   (LLM)    │
       └────────────┘  └────────────┘        └────────────┘

    ┌────────────────────────────────────────────────────────────┐
    │                     Redis                                   │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
    │  │ Streams      │  │ LLM Cache    │  │ Mnemosyne Cache │ │
    │  │ (Event Bus)  │  │ (Risposte)   │  │ (Vector Results)│ │
    │  │ + DLQ        │  │              │  │                 │ │
    │  └──────────────┘  └──────────────┘  └──────────────────┘ │
    └────────────────────────────────────────────────────────────┘
```

### 3.3 Flusso Inter-Servizi

```
  ┌───────────┐  emit()   ┌────────────┐  consume()  ┌─────────────┐
  │ Qualsiasi │─────────▶│   Redis    │────────────▶│  Qualsiasi  │
  │ Servizio  │           │  Streams   │             │  Listener   │
  │ (produttore)          │            │             │ (consumatore)│
  └───────────┘           │  ┌──────┐  │             └──────┬──────┘
                          │  │ DLQ  │  │                    │
                          │  └──────┘  │              ack() │
                          └────────────┘◀───────────────────┘
```

---

## 4. Flusso End-to-End di una Richiesta

**Scenario**: l'utente invia `"Quali sono i rischi principali?"` con `INTENT_DOMAIN=healthcare`.

```
1. HTTP POST → api_graph/v1/graph/invoke
   body: { "text": "Quali sono i rischi principali?", "user_id": "u123" }

2. graph_runner.py:
   - Carica session state per "u123" (in-memory dict)
   - Genera trace_id: "a1b2c3d4-e5f6-..."
   - Invoca graph_flow.build_graph() (lazy, cached dopo 1ˢᵗ call)
   - Esegue graph.invoke(state) con timeout 120s

3. parse_node: 
   - Legge input_text → estrae entità generiche
   - Scrive: entity_ids=[], intent=None

4. intent_detection_node:
   - Carica IntentRegistry del dominio "healthcare" (3 intenti + soft + unknown)
   - Genera prompt: "Classifica: 'Quali sono...' tra [symptom_check, medication_info, ...]"  
   - Chiama LLMAgent.complete_json() → {"intent": "symptom_check"}
   - Scrive: intent="symptom_check", proposed_exec="symptom_check"

5. pattern_weavers_node:
   - HTTP GET → api_pattern_weavers → concetti matchati dalla tassonomia
   - Scrive: weaver_context={...}

6. entity_resolver_node:
   - Hook healthcare non definito → no-op

7. emotion_detector:
   - HTTP POST → api_babel_gardens/v1/emotion/detect
   - Scrive: emotion_detected="neutral", emotion_confidence=0.72

8. semantic_grounding_node:
   - VSGSEngine → embedding API → Qdrant search
   - Scrive: semantic_matches=[{doc1, score 0.87}, ...], vsgs_status="grounded"

9. params_extraction_node:
   - Estrae parametri (nessun parametro specifico per questo intent)
   - Scrive: route=None

10. route_node (decide):
    - intent="symptom_check" è exec → route="dispatcher_exec"

11. exec_node:
    - Chiama ExecutionRegistry hook del dominio healthcare
    - Esegue logica triage → raw_output={urgency: "routine", ...}

12. output_normalizer_node:
    - Normalizza raw_output in struct uniforme

13. orthodoxy_node:
    - Genera summary dello stato, emette evento su StreamBus "orthodoxy.review.requested"
    - Scrive: orthodoxy_verdict="approved", orthodoxy_status="completed"

14. vault_node:
    - Emette evento "vault.archive.requested" su StreamBus
    - Scrive: vault_status="archived"

15. compose_node:
    - Chiama LLMAgent.complete() con prompt contestualizzato
    - Genera narrativa dalla raw_output + semantic_matches
    - Scrive: response="Basandomi sulle informazioni disponibili, i rischi..."

16. can_node:
    - Arricchisce risposta con follow-ups, conversation_type
    - Scrive: final_response="...", follow_ups=["Vuoi approfondire..."]

17. graph_runner.py:
    - Salva session state
    - Ritorna: { response, intent, emotion, trace_id, ... }
```

**Tempo tipico**: 2-5 secondi (dipende da latenza LLM e Qdrant).

---

## 5. Dove e Quando Ha Senso Adottarlo

### Quando SÌ

| Scenario | Perché |
|:---|:---|
| **Assistente AI enterprise con audit trail** | Pipeline governata: ogni output passa da validazione (Orthodoxy), archiviazione (Vault), audit logging. Requisito per compliance GDPR/SOC2. |
| **Piattaforma multi-dominio** | Il sistema di plugin permette di servire domini diversi (legal, HR, healthcare) dalla stessa infrastruttura, cambiando una env var. |
| **RAG (Retrieval-Augmented Generation)** | Grounding semantico integrato (VSGS + Qdrant). L'LLM risponde ancorato a documenti vettorializzati, non hallucina. |
| **Decisioni basate su scoring multi-fattore** | Neural Engine: normalizzazione → pesatura → ranking. Generico: candidati HR, priorità ticket, lead scoring. |
| **Sistema event-driven con retry e DLQ** | StreamBus + DeadLetterQueue: event sourcing production-grade su Redis (più leggero di Kafka). |
| **Applicazione che chiama LLM intensivamente** | LLMAgent con rate limiting, circuit breaker, caching risposte. Riduce costi OpenAI del 30-70% (cache hit). |
| **Multilingual conversational AI** | Babel Gardens per language/emotion detection, PromptRegistry per gestione prompt per lingua. |

### Quando NO

| Scenario | Perché |
|:---|:---|
| **Chatbot semplice (FAQ bot)** | Troppa infrastruttura. Usa Langchain + Qdrant direttamente. |
| **Batch processing senza interazione utente** | La pipeline è ottimizzata per interazioni conversazionali una-alla-volta, non per processing di milioni di record. |
| **Single-purpose tool (es. solo embedding)** | Puoi estrarre il singolo agente (`LLMAgent`, `QdrantAgent`) senza adottare l'intero framework. |
| **Team < 3 persone senza esperienza Docker/Redis** | L'infrastruttura richiede PostgreSQL, Redis, Qdrant. Il setup ha una curva di apprendimento. |

### Componenti Utilizzabili Standalone (senza l'intera pipeline)

| Componente | Uso standalone | Dipendenze |
|:---|:---|:---|
| `PostgresAgent` | Wrapper PostgreSQL con pooling | Solo `psycopg2` + PostgreSQL |
| `LLMAgent` | Gateway LLM con rate limiting e cache | `openai` + Redis (per cache) |
| `StreamBus` + `DLQ` | Event bus production-grade | Solo Redis |
| `NeuralEngine` | Ranking engine multi-fattore | Solo `pandas` + `numpy` |
| `AuthMiddleware` | Auth per FastAPI | Solo `pyjwt` |
| `AuditLogger` | Structured audit logging | Solo Redis (PG opzionale) |
| `NodeExecutionGuard` | Timeout enforcement generico | Solo Python stdlib |

---

## 6. Indice Variabili d'Ambiente

| Categoria | Variabile | Default | Modulo |
|:---|:---|:---|:---|
| **PostgreSQL** | `POSTGRES_HOST` / `PORT` / `DB` / `USER` / `PASSWORD` | localhost/5432/vitruvyan/—/— | PostgresAgent |
| | `POSTGRES_POOL_MIN` / `POOL_MAX` | 2 / 10 | PostgresAgent |
| **Qdrant** | `QDRANT_HOST` / `PORT` / `URL` / `API_KEY` / `TIMEOUT` | localhost/6333/—/—/30 | QdrantAgent |
| **Redis** | `REDIS_HOST` / `PORT` / `PASSWORD` / `SSL` | localhost/6379/—/false | StreamBus, Cache* |
| **LLM** | `OPENAI_API_KEY` | — (obbligatorio) | LLMAgent |
| | `VITRUVYAN_LLM_MODEL` → `GRAPH_LLM_MODEL` → `OPENAI_MODEL` | gpt-4o-mini | LLMAgent |
| | `LLM_RATE_LIMIT_RPM` / `TPM` | 500 / 30000 | LLMAgent |
| | `LLM_CACHE_TTL_HOURS` / `MAX_SIZE` | 24 / 10000 | LLMCacheManager |
| **Streams** | `STREAM_PREFIX` / `MAX_LEN` / `MAX_AGE_DAYS` | vitruvyan/100K/7 | StreamBus |
| | `DLQ_MAX_RETRIES` / `STREAM_MAX_LEN` | 3 / 50000 | DeadLetterQueue |
| **Dominio** | `INTENT_DOMAIN` | generic | graph_flow |
| | `ENTITY_DOMAIN` | = INTENT_DOMAIN | graph_flow |
| | `EXEC_DOMAIN` | — | graph_flow |
| **Pipeline** | `ENABLE_MINIMAL_GRAPH` | false | graph_runner |
| | `GRAPH_EXEC_TIMEOUT_SECONDS` | 120 | graph_runner |
| | `NODE_EXEC_TIMEOUT_SECONDS` / `MAX_WORKERS` | 30 / 4 | ExecutionGuard |
| **Grounding** | `VSGS_ENABLED` / `GROUNDING_TOPK` / `COLLECTION_NAME` | 0/3/semantic_states | semantic_grounding |
| **MCP** | `USE_MCP` / `MCP_SERVER_URL` | 0/http://mcp:8020 | llm_mcp_node |
| **Service URLs** | `BABEL_GARDENS_URL` / `EMBEDDING_API_URL` / `CODEX_API_BASE` | http://babel:8009 / ... | vari nodi |
| **Auth** | `VITRUVYAN_AUTH_ENABLED` / `AUTH_SECRET` / `KEYCLOAK_URL` | false/—/— | AuthMiddleware |
| **Audit** | `AUDIT_ENABLED` / `STREAM` / `POSTGRES_ENABLED` | true/vitruvyan:audit/false | AuditLogger |
| **Cache Vettoriale** | `MNEMOSYNE_CACHE_TTL_HOURS` / `SIMILARITY_THRESHOLD` | 6 / 0.95 | MnemosyneCache |
| **CORS** | `CORS_ORIGINS` | http://localhost:3000 | Tutti i servizi |
