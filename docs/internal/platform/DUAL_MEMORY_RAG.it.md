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

## Primitivi core (codice)

### `PostgresAgent` — accesso Archivarium

- **Ruolo**: connettività PostgreSQL + CRUD generico.
- **Contratto**: l’SQL è del chiamante (verticale/servizio); PostgresAgent non incapsula logica di dominio.
- **Env**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Codice: `vitruvyan_core/core/agents/postgres_agent.py`

### `QdrantAgent` — accesso Mnemosyne

- **Ruolo**: connettività Qdrant + gestione collezioni + utility per search/upsert.
- **Contratto**: naming collezioni e schema payload sono del chiamante (verticale/servizio).
- **Env**: `QDRANT_HOST`, `QDRANT_PORT` *(oppure `QDRANT_URL`)*, `QDRANT_API_KEY`, `QDRANT_TIMEOUT`.

Codice: `vitruvyan_core/core/agents/qdrant_agent.py`

> Nota: l’Appendix E descrive una policy “language-first” più restrittiva. Nell’implementazione attuale di `QdrantAgent.upsert()` la validazione della lingua nel payload **non è ancora applicata**; se serve, gli invarianti vanno enforceati a livello adapter.

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

## Verticalizzazione (dominio pilota: finanza)

Il core è domain-agnostic; il verticale finance possiede:

- **Schema PostgreSQL**: tabelle, indici, vincoli (es. entità di mercato, log, audit, phrase store).
- **Collezioni Qdrant**: naming, dimensioni vettore, schema payload (es. `phrases_embeddings`, `sentiment_embeddings`).
- **Adapter**: cosa viene embedded, salvato, recuperato e filtrato (e come applicare scoring/thresholds).

Esempio (finance pack): `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## Riferimenti (approfondimento)

- Agents: `vitruvyan_core/core/agents/__init__.py`
- RAG Appendix: `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Mappa architetturale (agent + integrazione): `docs/architecture/MAPPA_ARCHITETTURALE_MODULI.md`
