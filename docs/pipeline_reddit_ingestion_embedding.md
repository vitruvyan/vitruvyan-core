# Pipeline Completa: Ingestion → Embedding → Linguistica → Ontologia

> **Last updated**: Feb 25, 2026 22:00 UTC

Ecco come funziona la pipeline end-to-end, passo per passo, con riferimenti esatti al codice.
La pipeline è composta da 6 step asincroni collegati via Redis Streams.

---

## Pipeline Reddit (identica strutturalmente a FRED e GNews)

### STEP 1 — Acquisizione (Oculus Prime Edge)

**Sacred Order**: Perception | **Componente**: `infrastructure/edge/oculus_prime/core/agents/`

Il `RedditIntakeAgent` in `reddit_intake.py` usa PRAW per scaricare post e commenti da un subreddit. Per ogni post:

1. **Estrae il testo letterale** (titolo + selftext + top 10 commenti) — senza alcuna interpretazione semantica
2. **Costruisce l'Evidence Pack** — un JSON immutabile con:
   - `evidence_id`: `EVD-<UUID>` 
   - `normalized_text`: testo concatenato ("Title: ... Author: ... Score: ...")
   - `source_ref`: `reddit://r/<subreddit>/comments/<id>` + SHA-256 hash
   - `technical_metadata`: metadati Reddit (score, upvote_ratio, flair, commenti)
   - `integrity.evidence_hash`: SHA-256 dell'intero pacchetto
3. **Guardrails** — `IntakeGuardrails.validate_no_semantics()` verifica che il testo non contenga interpretazioni (`guardrails.py`)
4. **Persiste** l'Evidence Pack in PostgreSQL (`oculus_evidence_packs`)
5. **Emette** l'evento `oculus_prime.evidence.created` su Redis Streams via `event_emitter.py`

**Varianti per sorgente** (solo lo Step 1 cambia):
- **Reddit** (`reddit_intake.py`): PRAW → post/commenti → tag `["reddit", "subreddit:technology"]`
- **FRED** (`fred_intake.py`): API REST `api.stlouisfed.org` → serie temporali → tag `["fred", "series:GDP", "frequency:quarterly"]`
- **GNews** (`gnews_intake.py`): GNews.io API + RSS fallback → articoli → tag `["gnews", "topic:technology"]`

Dal Step 2 in poi, la pipeline è identica — Codex, embedding, BG e PW non sanno e non si interessano della sorgente.

---

### STEP 2 — Discovery (Codex Hunters Listener → API)

**Sacred Order**: Perception | **Componente**: `services/api_codex_hunters/`

Il `streams_listener.py` di Codex consuma `oculus_prime.evidence.created`:

```
xreadgroup → TransportEvent → _dispatch_spec_for_channel() → POST /discover
```

L'evento viene trasformato in una richiesta HTTP verso Codex API `/discover` con `entity_id = evidence_id`, `raw_data = { evidence payload }`. Codex risponde con `status: "discovered"`.

Internamente il `bus_adapter.py` `process_discovery()` chiama il `TrackerConsumer` (puro, LIVELLO 1) → emette `codex.entity.discovered` su Redis Streams.

---

### STEP 3 — Restore (Codex)

**Sacred Order**: Perception | **Consumer**: `RestorerConsumer`

Il listener fa poi `POST /restore` con `entity_id` + `raw_data`. Il `RestorerConsumer` normalizza i dati → emette `codex.entity.restored`.

---

### STEP 4 — Bind + Auto-Embed (Codex → Embedding → Qdrant)

**Sacred Order**: Perception + Memory | **Consumer**: `BinderConsumer`

`POST /bind` con `normalized_data` (i dati normalizzati). In `bus_adapter.py`:

1. `BinderConsumer.process()` (puro) → produce `normalized_data_out`, `quality_score`, `dedupe_key`
2. **Auto-embed**: se nessun embedding è fornito e `CODEX_AUTO_EMBED=true` (default):
   - `_build_embed_text()` estrae il testo dai campi prioritari (`title`, `normalized_text`, `description`, ecc.)
   - `persistence.py` `generate_embedding()` chiama `POST http://embedding:8010/v1/embeddings/create` con il modello `all-MiniLM-L6-v2` → ottiene un vettore a 384 dimensioni
3. **PostgreSQL**: `store_entity()` → salva in tabella `codex_entities` (JSONB)
4. **Qdrant**: `store_embedding()` → salva il punto vettoriale in `entity_embeddings` (384-dim, Cosine)
5. **Emette** `codex.entity.bound` su Redis Streams con `{entity_id, postgres_stored: true, qdrant_stored: true}`

> **Nota**: Il vettore in Qdrant è il "ponte" tra la pipeline di ingestion e quella conversazionale. Quando un utente fa una query, il nodo `weaver` nel grafo LangGraph cerca in Qdrant embedding simili — restituendo le entità ingerite dai provider come contesto semantico.

---

### STEP 5 — Analisi Linguistica (Babel Gardens Listener)

**Sacred Order**: Perception (Linguistic) | **Componente**: `services/api_babel_gardens/streams_listener.py`

Il `streams_listener.py` di BG consuma `codex.entity.bound`:

1. `_extract_text_from_payload()` estrae il testo dall'evento (cerca `text`, `data.normalized_text`, `data.title`, ecc.)
2. **Emotion detection**: `POST /v1/emotion/detect` → risultato tipo `{emotion: "neutral", confidence: 0.90}`
3. **Sentiment analysis**: `POST /analyze` → risultato tipo `{label: "positive", score: 0.75}`
4. **Emette** `babel.linguistic.completed` con emotion + sentiment aggregati
5. **Bridge → PW**: emette `pattern.weave.request` con il testo + contesto emotion/sentiment per l'analisi ontologica

---

### STEP 6 — Classificazione Ontologica (Pattern Weavers Listener)

**Sacred Order**: Reason | **Componente**: `services/api_pattern_weavers/streams_listener.py`

Il `streams_listener.py` di PW consuma `pattern.weave.request` (emesso da BG nel Step 5):

1. **`_build_weave_request(payload)`** — estrae `query` (= il testo dell'entità) + parametri (limit, threshold)
2. **`run_weave_pipeline(request)`** — esegue la pipeline di weaving:
   a. **Embedding della query**: `embedding_adapter.get_embedding(text)` → api_embedding:8010 → vettore 384-dim
   b. **Ricerca Qdrant**: `persistence.search_similar(collection="entity_embeddings", query_vector, threshold=0.35)` — cerca entità semanticamente simili **tra quelle già ingerite**
   c. **Consumer puro**: `WeaverConsumer.process({mode: "process_results", similarity_results: [...]})` — applica taxonomy matching sui risultati Qdrant
   d. **Output**: lista di `PatternMatch` con `name`, `category`, `score`, `match_type`
3. **Emette** `pattern_weavers.weave.completed` con i match ontologici + metadata
4. **Emette** `pattern_weavers.context.extracted` con i concetti estratti separatamente

---

### Come il Grafo LangGraph usa questi dati (Pipeline Conversazionale)

Quando un utente fa una query (es. "What's happening with inflation?"), il grafo LangGraph esegue il nodo `weaver` **sincronamente**:

```
parse → intent_detection → weaver (PW) → entity_resolver → babel_emotion → ...
```

Il nodo `weaver` (v2, default):
1. Embeds la query utente → vettore 384-dim
2. **Cerca in Qdrant `entity_embeddings`** — troverà le entità FRED (CPI, GDP) o Reddit ingerite
3. WeaverConsumer processa i risultati → `matched_concepts`, `semantic_context`, `weave_confidence`
4. I nodi downstream (`compose`, `CAN`) usano `weaver_context` per costruire la risposta

Con `PATTERN_WEAVERS_V3=1`, il nodo usa `/compile` (LLM-based semantic compilation) invece di `/weave`.
Con `BABEL_COMPREHENSION_V3=1`, un singolo nodo `comprehension_node` sostituisce sia PW che emotion detection chiamando `/v2/comprehend`.

---

### Schema riassuntivo completo

```
RedditIntakeAgent / FREDIntakeAgent / GNewsIntakeAgent
  │
  ├─ Evidence Pack → PostgreSQL (oculus_evidence_packs)
  │
  └─ emit: oculus_prime.evidence.created ─────────────────┐
                                                          │
                    Codex Listener (xreadgroup)  ◄────────┘
                        │
                        ├─ POST /discover  → TrackerConsumer → emit: codex.entity.discovered
                        ├─ POST /restore   → RestorerConsumer → emit: codex.entity.restored
                        └─ POST /bind      → BinderConsumer
                                               │
                                               ├─ AUTO-EMBED → POST embedding:8010 → [384-dim vector]
                                               ├─ PostgreSQL (codex_entities)
                                               ├─ Qdrant (entity_embeddings)
                                               └─ emit: codex.entity.bound ──────────┐
                                                                                      │
                    BG Listener (xreadgroup) ◄────────────────────────────────────────┘
                        │
                        ├─ POST /v1/emotion/detect → {emotion: neutral, confidence: 0.90}
                        ├─ POST /analyze           → {label: positive, score: 0.75}
                        ├─ emit: babel.linguistic.completed
                        └─ emit: pattern.weave.request ──────────────────┐
                                                                         │
                    PW Listener (xreadgroup)  ◄──────────────────────────┘
                        │
                        ├─ Embed text → POST embedding:8010 → [384-dim vector]
                        ├─ Qdrant search (entity_embeddings) → similar entities
                        ├─ WeaverConsumer → taxonomy matching → PatternMatch[]
                        ├─ emit: pattern_weavers.weave.completed
                        └─ emit: pattern_weavers.context.extracted
```

### Due Pipeline Parallele

Il sistema ha **due modalità** per usare gli embedding in Qdrant:

| Pipeline | Tipo | Trigger | Come usa Qdrant |
|----------|------|---------|-----------------|
| **Ingestion** (asincrona) | Redis Streams | Provider → Codex → BG → PW | Scrivi embedding (Step 4), poi PW cerca simili (Step 6) per classificazione batch |
| **Conversazionale** (sincrona) | LangGraph HTTP | Query utente → nodo `weaver` | Legge embedding per arricchire la risposta con contesto semantico |

Le due pipeline sono collegate **indirettamente** tramite Qdrant: l'ingestion scrive i vettori, il grafo conversazionale li legge per fornire risposte informate sulla knowledge base ingerita.