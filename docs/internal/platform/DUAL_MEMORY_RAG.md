# Dual Memory Layer & RAG

<p class="kb-subtitle">How Vitruvyan composes RAG from two storages: Archivarium (PostgreSQL) + Mnemosyne (Qdrant), plus migrations (Alembic) and embedding services.</p>

## What it does

- Provides **two complementary memories**:
  - **Archivarium (PostgreSQL)**: structured, queryable records (facts, logs, audits, rows with lifecycle).
  - **Mnemosyne (Qdrant)**: semantic vector memory (embeddings, similarity search, retrieval).
- Defines the **domain-agnostic access primitives** used by services:
  - `PostgresAgent` for SQL read/write (no schema assumptions).
  - `QdrantAgent` for collections, upsert, and similarity search.
  - `AlchemistAgent` for **schema migrations** via Alembic (where enabled).
- Explains where **RAG** lives in the stack:
  - embeddings are produced by a dedicated service (`services/api_embedding/`) and/or by Babel Gardens embedding routes
  - persistence and retrieval are performed via the agents + service adapters
  - **coherence** and **sync planning** are governed by Memory Orders (not by ad-hoc scripts)

## Semantic responsibility split (verified)

- There is **no active `api_semantic` service** in the current stack (legacy service removed).
- **Intent interpretation and routing** are handled in LangGraph orchestration:
  - `intent_detection_node.py` classifies intent (LLM) and enriches language metadata.
  - `route_node.py` decides the execution branch (`dispatcher_exec`, `llm_soft`, `semantic_fallback`, etc.).
- **Babel Gardens** handles linguistic/semantic signals (language detection, embeddings, sentiment, emotion), but it **does not choose routes**.
- RAG grounding is assembled by `semantic_grounding_node.py` + VSGS engine using embedding + Qdrant retrieval.

In short: orchestration decides **what path to execute**; Babel Gardens provides **language/semantic evidence** used by that path.

## Core primitives (code)

### `PostgresAgent` — Archivarium access

- **Role**: generic PostgreSQL connectivity + CRUD.
- **Contract**: SQL is owned by the caller (vertical/service); PostgresAgent does not encode domain logic.
- **Env**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Code: `vitruvyan_core/core/agents/postgres_agent.py`

### `QdrantAgent` — Mnemosyne access

- **Role**: Qdrant connectivity + collection management + search/upsert utilities.
- **Contract**: collection naming and payload schema are owned by the caller (vertical/service).
- **Env**: `QDRANT_HOST`, `QDRANT_PORT` *(or `QDRANT_URL`)*, `QDRANT_API_KEY`, `QDRANT_TIMEOUT`.

Code: `vitruvyan_core/core/agents/qdrant_agent.py`

> Note: Appendix E describes a stricter “language-first” validation policy. In the current `QdrantAgent.upsert()` implementation, payload language validation is **not enforced** yet; services must enforce invariants at the adapter level if required.

### `AlchemistAgent` — schema migrations (Alembic)

- **Role**: detect schema drift vs Alembic “head”, apply pending migrations.
- **Event emission**: publishes `alchemy.*` status events on the Cognitive Bus (via an adapter).
- **Env**: `ALEMBIC_CONFIG` (default points to Memory Orders migrations).

Code: `vitruvyan_core/core/agents/alchemist_agent.py`

## How RAG is assembled (system view)

RAG is not a single module: it emerges from **(1) embedding**, **(2) dual persistence**, and **(3) retrieval**.

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

## Runtime flow (today)

1. A service/node asks the embedding layer for vectors (today, often `api_embedding`).
2. Vectors are persisted/retrieved through `QdrantAgent` (Mnemosyne), while structured context remains in PostgreSQL via `PostgresAgent` (Archivarium).
3. Retrieval combines semantic hits from Qdrant with structured records from PostgreSQL.
4. Memory Orders monitors drift and plans synchronization when PG↔Qdrant coherence degrades.

This is why the RAG behavior is dual: **semantic recall + structured truth**.

### Embedding layer

Common patterns in the codebase:

- **Dedicated embedding service** exposes `/v1/embeddings/*`: `services/api_embedding/`
- **Babel Gardens** exposes embedding routes (including multilingual) and can cooperate with the embedding service: `services/api_babel_gardens/`

Appendix reference: `.github/Vitruvyan_Appendix_E_RAG_System.md`

Internal KB:

- Sacred Order: `docs/internal/orders/BABEL_GARDENS.md`
- Service: `docs/internal/services/BABEL_GARDENS_API.md`

### Coherence, drift, and healing

The dual-memory system needs constant monitoring because “row count” and “point count” can diverge.

- **Coherence checks**: drift calculation between Postgres (expected coverage) and Qdrant (actual vectors).
- **Health aggregation**: unified snapshot of dependencies (datastores + embedding service + bus).
- **Sync planning**: produces a plan to restore alignment (planning-only in LIVELLO 1).

Order reference: `docs/internal/orders/MEMORY_ORDERS.md`

## Evolution roadmap (toward Babel Gardens as embedding front layer)

Target direction: Babel Gardens becomes the main semantic-embedding front layer, while orchestration/routing stays in LangGraph.

### What must be implemented

1. **Unify embedding contract**
   - Standard request/response schema for Graph, Pattern Weavers, Memory Orders, Babel.
   - Freeze mandatory metadata: `language`, `model_type`, `dimension`, correlation/trace ids.
2. **Migrate callers incrementally**
   - Switch one consumer at a time from legacy embedding endpoints to Babel endpoints.
   - Keep compatibility adapters during transition.
3. **Centralize vector-write semantics**
   - Single owner for id strategy, payload schema, collection naming conventions.
   - Enforce this at adapter boundary, not inside business nodes.
4. **Guard coherence during migration**
   - Add PG↔Qdrant reconciliation checks after each migration step.
   - Use Memory Orders drift metrics as release gate.
5. **Deprecate legacy path**
   - Mark old embedding endpoints deprecated.
   - Remove only after all consumers are migrated and stable in production.

### Important boundary

- Even after migration, Babel Gardens should **not** own routing decisions.
- Routing remains in LangGraph (`intent_detection_node` + `route_node`).

## Verticalization (finance pilot)

The core is domain-agnostic; the finance vertical owns:

- **PostgreSQL schema**: tables, indexes, constraints (e.g., market entities, logs, audits, phrase stores).
- **Qdrant collections**: naming, vector dimensions, payload schema (e.g., `phrases_embeddings`, `sentiment_embeddings`).
- **Adapters**: what gets embedded, stored, retrieved, filtered, and how scores/thresholds are applied.

Example (finance pack): `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## References (deep dive)

- Agents: `vitruvyan_core/core/agents/__init__.py`
- RAG Appendix: `.github/Vitruvyan_Appendix_E_RAG_System.md`
- Architectural map (agents + integration): `docs/architecture/MAPPA_ARCHITETTURALE_MODULI.md`
