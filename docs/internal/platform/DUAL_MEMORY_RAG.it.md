# Dual Memory Layer & RAG

<p class="kb-subtitle">Come Vitruvyan compone il RAG da due storage: Archivarium (PostgreSQL) + Mnemosyne (Qdrant), più migrazioni (Alembic) ed embedding services.</p>

## A cosa serve

- Fornisce **due memorie complementari**:
  - **Archivarium (PostgreSQL)**: record strutturati e interrogabili (fatti, log, audit, righe con lifecycle).
  - **Mnemosyne (Qdrant)**: memoria vettoriale semantica (embedding, similarità, retrieval).
- Definisce i **primitivi domain-agnostic** usati dai servizi:
  - `PostgresAgent` per read/write SQL (senza assunzioni sullo schema).
  - `QdrantAgent` per collezioni, upsert e ricerca per similarità.
  - `AlchemistAgent` per **migrazioni di schema** via Alembic (dove abilitato).
- Spiega dove vive il **RAG** nello stack:
  - gli embedding vengono prodotti da un servizio dedicato (`services/api_embedding/`) e/o dalle route embedding di Babel Gardens
  - persistenza e retrieval avvengono via agent + adapter del servizio
  - **coerenza** e **sync planning** sono governati da Memory Orders (non da script ad-hoc)

## Confine semantico (verificato)

- Nello stack attuale **non esiste un servizio `api_semantic` attivo** (servizio legacy rimosso).
- **Interpretazione intent e routing** vivono nell’orchestrazione LangGraph:
  - `intent_detection_node.py` classifica l’intent (LLM) e arricchisce i metadati lingua.
  - `route_node.py` decide il branch di esecuzione (`dispatcher_exec`, `llm_soft`, `semantic_fallback`, ecc.).
- **Babel Gardens** gestisce segnali linguistici/semantici (language detection, embedding, sentiment, emotion), ma **non sceglie la route**.
- Il grounding RAG è composto da `semantic_grounding_node.py` + engine VSGS con embedding + retrieval Qdrant.

In sintesi: l’orchestrazione decide **che percorso eseguire**; Babel Gardens fornisce **evidenza linguistica/semantica** usata da quel percorso.

## Primitivi core (codice)

### `PostgresAgent` — accesso Archivarium

- **Ruolo**: connettività PostgreSQL + CRUD generico.
- **Contratto**: l’SQL è del chiamante (verticale/servizio); PostgresAgent non incapsula logica di dominio.
- **Env**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Codice: `vitruvyan_core/core/agents/postgres_agent.py`

### `QdrantAgent` — accesso Mnemosyne

- **Ruolo**: connettività Qdrant + gestione collezioni + utility per search/upsert.
- **Contratto**: la logica chiamante resta del verticale, ma naming collezioni e metadati minimi sono governati da `docs/contracts/rag/RAG_GOVERNANCE_CONTRACT_V1.md`.
- **Env**: `QDRANT_HOST`, `QDRANT_PORT` *(oppure `QDRANT_URL`)*, `QDRANT_API_KEY`, `QDRANT_TIMEOUT`.

Codice: `vitruvyan_core/core/agents/qdrant_agent.py`

> Nota governance: `QdrantAgent` applica guardrail runtime (check collezioni dichiarate e warning su payload senza `source`) e metriche phase 4 (`RAG_METRICS`).

### `AlchemistAgent` — migrazioni schema (Alembic)

- **Ruolo**: rileva drift di versione vs Alembic “head”, applica migrazioni pendenti.
- **Event emission**: pubblica eventi di stato `alchemy.*` sul Cognitive Bus (via adapter).
- **Env**: `ALEMBIC_CONFIG` (default punta alle migrazioni di Memory Orders).

Codice: `vitruvyan_core/core/agents/alchemist_agent.py`

## Come si compone il RAG (vista di sistema)

Il RAG non è un singolo modulo: emerge da **(1) embedding**, **(2) persistenza dual**, **(3) retrieval**.

```mermaid
flowchart LR
  U[User / Request] --> S[Service / Sacred Order (LIVELLO 2)]
  S -->|text| E[Embedding Service]
  E -->|vector| Q[QdrantAgent (Mnemosyne)]
  S -->|facts/logs| P[PostgresAgent (Archivarium)]
  S -->|retrieve| Q
  S -->|retrieve| P
  MO[Memory Orders] -->|coherence + sync planning| P
  MO -->|coherence + sync planning| Q
```

## Flusso runtime (oggi)

1. Un servizio/nodo richiede i vettori al layer embedding (oggi spesso `api_embedding`).
2. I vettori vengono persistiti/recuperati via `QdrantAgent` (Mnemosyne), mentre il contesto strutturato resta in PostgreSQL via `PostgresAgent` (Archivarium).
3. Il retrieval combina hit semantiche da Qdrant con record strutturati da PostgreSQL.
4. Memory Orders monitora il drift e pianifica la sincronizzazione quando la coerenza PG↔Qdrant degrada.

Per questo il comportamento RAG è duale: **richiamo semantico + verità strutturata**.

### Embedding layer

Pattern tipici nella codebase:

- **Embedding service dedicato** espone `/v1/embeddings/*`: `services/api_embedding/`
- **Babel Gardens** espone route embedding (anche multilingua) e può cooperare con l’embedding service: `services/api_babel_gardens/`

Appendix di riferimento: `.github/Vitruvyan_Appendix_E_RAG_System.md`

KB interna:

- Sacred Order: `docs/internal/orders/BABEL_GARDENS.md`
- Service: `docs/internal/services/BABEL_GARDENS_API.md`

### Coerenza, drift e healing

Il dual-memory richiede monitoraggio perché “row count” e “point count” possono divergere.

- **Coherence check**: drift tra Postgres (copertura attesa) e Qdrant (vettori effettivi).
- **Health aggregation**: snapshot unico delle dipendenze (datastore + embedding service + bus).
- **Sync planning**: genera un piano per riallineare (planning-only in LIVELLO 1).

Ordine di riferimento: `docs/internal/orders/MEMORY_ORDERS.md`

## Roadmap evolutiva (verso Babel Gardens come front layer embedding)

Direzione target: Babel Gardens diventa il front layer principale per embedding semantici, mentre orchestrazione/routing restano in LangGraph.

### Cosa va implementato

1. **Unificare il contratto embedding**
   - Schema request/response standard per Graph, Pattern Weavers, Memory Orders e Babel.
   - Metadati obbligatori congelati: `language`, `model_type`, `dimension`, correlation/trace ids.
2. **Migrare i chiamanti in modo incrementale**
   - Spostare un consumer alla volta dagli endpoint embedding legacy a quelli Babel.
   - Mantenere adapter di compatibilità durante la transizione.
3. **Centralizzare la semantica di scrittura vettori**
   - Un solo owner per strategia id, schema payload, naming collezioni.
   - Enforcement al boundary adapter, non nei nodi business.
4. **Proteggere la coerenza durante la migrazione**
   - Aggiungere check di riconciliazione PG↔Qdrant a ogni step.
   - Usare le metriche di drift di Memory Orders come gate di rilascio.
5. **Deprecare il path legacy**
   - Marcare deprecated i vecchi endpoint embedding.
   - Rimuovere solo dopo migrazione completa e stabilità in produzione.

### Confine importante

- Anche dopo la migrazione, Babel Gardens **non** deve decidere il routing.
- Il routing rimane in LangGraph (`intent_detection_node` + `route_node`).

## Verticalizzazione (dominio pilota: finanza)

Il core è domain-agnostic; il verticale finance possiede:

- **Schema PostgreSQL**: tabelle, indici, vincoli (es. entità di mercato, log, audit, phrase store).
- **Estensioni Qdrant di dominio**: collezioni e adapter nel rispetto dei vincoli RAG (es. `<domain>.<purpose>`, ownership dichiarata, metadati payload).
- **Adapter**: cosa viene embedded, salvato, recuperato e filtrato (e come applicare scoring/thresholds).

Esempio (finance pack): `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## Riferimenti (approfondimento)

- Agents: `vitruvyan_core/core/agents/__init__.py`
- Contratto RAG: `docs/contracts/rag/RAG_GOVERNANCE_CONTRACT_V1.md`
- Runbook operativo RAG: `docs/contracts/rag/RAG_GOVERNANCE_OPERATIONS.md`
- RAG Appendix: `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Mappa architetturale (agent + integrazione): `docs/architecture/MAPPA_ARCHITETTURALE_MODULI.md`
