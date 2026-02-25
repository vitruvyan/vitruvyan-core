# RAG Governance Contract V1

> **Last updated**: Feb 21, 2026 16:00 UTC

Status: **ACTIVE**
Version: 1.0.0
Owner: Vitruvyan Core Architecture

---

## 1. Purpose

This contract defines the **binding rules** for Retrieval-Augmented Generation (RAG) infrastructure in Vitruvyan.

RAG is the epistemic memory layer: it stores vectorized knowledge and retrieves it to augment reasoning.
Without governance, collections proliferate, orphan, and rot — becoming technical debt instead of cognitive asset.

**vitruvyan-core** defines the RULES. Deployments (mercator, verticals) IMPLEMENT the rules.

Normative terms use RFC 2119 semantics: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY.

---

## 2. Scope

This contract applies to:
- All Qdrant vector collections created or consumed by any Vitruvyan service
- The `QdrantAgent` (`core.agents.qdrant_agent`) as the ONLY access gateway
- The init script (`scripts/init_qdrant_collections.py`) as the ONLY bootstrap mechanism
- Any vertical or domain that introduces new collections

This contract does NOT govern:
- The internal embedding model choice (that is deployment-specific)
- The Qdrant cluster topology (infrastructure concern)

---

## 3. Core Principles

### 3.1 Single Gateway — QdrantAgent

All vector operations MUST go through `core.agents.qdrant_agent.QdrantAgent`.

- ❌ FORBIDDEN: `from qdrant_client import QdrantClient` in any service/node code
- ❌ FORBIDDEN: raw HTTP calls to Qdrant API from business logic
- ✅ REQUIRED: `from core.agents.qdrant_agent import QdrantAgent`

**Exception**: The init script (`init_qdrant_collections.py`) MAY use the Qdrant REST API directly for bootstrap operations.

### 3.2 Declared Collections Only

Every collection in production MUST be:
1. **Declared** in the init script (`scripts/init_qdrant_collections.py`)
2. **Owned** by exactly one Sacred Order or domain vertical
3. **Documented** with a description in the init script

Collections NOT declared in the init script are **rogue** and SHOULD be deleted.

### 3.3 No Hardcoded Defaults in Agent Methods

QdrantAgent methods MUST NOT have hardcoded collection name defaults.
Collection names MUST be passed explicitly by callers or resolved from configuration.

**Current violations** (to be remediated):
- `search_phrases(collection="phrases_embeddings")` — hardcoded default
- `upsert_semantic_state(collection="semantic_states")` — hardcoded default
- `upsert_point_from_grounding(collection="semantic_states")` — hardcoded default

**Target**: All methods accept `collection: str` as required parameter (no default).

---

## 4. Collection Taxonomy

### 4.1 Collection Tiers

| Tier | Scope | Lifecycle | Example |
|------|-------|-----------|---------|
| **CORE** | OS-level, domain-agnostic | Permanent — never deleted without contract change | `semantic_states`, `conversations_embeddings` |
| **ORDER** | Sacred Order operational data | Managed by owning Order | `entity_embeddings`, `weave_embeddings` |
| **DOMAIN** | Vertical/domain-specific | Created/destroyed with vertical lifecycle | `finance.templates`, `finance.ticker_embeddings` |
| **EPHEMERAL** | Testing, experiments, migrations | Auto-expire or manual cleanup | `test_*`, `migration_*` |

### 4.2 Naming Convention

```
<tier>.<purpose>
```

**Rules**:
- Core collections: `<purpose>` (no prefix — legacy names grandfathered)
- Order collections: `<order_short>.<purpose>` or legacy `<purpose>_embeddings`
- Domain collections: `<domain>.<purpose>` (e.g., `finance.templates`, `mercator.entities`)
- Ephemeral: `test_*` or `tmp_*` prefix (auto-eligible for cleanup)
- All names: lowercase, underscores, max 64 characters
- MUST NOT use dots in the purpose segment (dots separate tier/domain from purpose)

**Grandfathered names** (legacy, not subject to renaming until V2):
- `entity_embeddings` (Codex Hunters)
- `phrases_embeddings` (Embedding Service)
- `semantic_states` (VSGS)
- `conversations_embeddings` (LangGraph)
- `weave_embeddings` (Pattern Weavers)

### 4.3 Sacred Order Collection Ownership

| Sacred Order | Domain | Owned Collections | Purpose |
|--------------|--------|-------------------|---------|
| **Codex Hunters** | Perception | `entity_embeddings` | Ingested entity semantic vectors |
| **Embedding Service** | Perception | `phrases_embeddings` | NLP phrase embeddings (general-purpose) |
| **Pattern Weavers** | Reason | `weave_embeddings` | Ontological pattern results |
| **VSGS Engine** | Reason | `semantic_states` | Semantic grounding context |
| **LangGraph** | Discourse | `conversations_embeddings` | Conversational memory for RAG retrieval |
| **Memory Orders** | Memory | *(no owned collection)* | Reads `entity_embeddings` for coherence |
| **Vault Keepers** | Memory | *(no owned collection)* | Reads `entity_embeddings` for archival |
| **Orthodoxy Wardens** | Truth | *(no owned collection)* | MAY read any collection for audit |

**Cross-Order access rules**:
- Read access: Any Order MAY read any collection
- Write access: ONLY the owning Order writes to its collection
- Exception: `entity_embeddings` is the **shared ingestion target** — Codex Hunters (primary writer) and Pattern Weavers (secondary writer via search+enrich) both write

---

## 5. Vector Standards

### 5.1 Dimensions and Distance

| Parameter | Requirement | Current Standard |
|-----------|-------------|-----------------|
| Vector dimensions | MUST be consistent within a deployment | 384 (all-MiniLM-L6-v2) |
| Distance metric | MUST be `Cosine` unless domain justifies otherwise | Cosine |
| Embedding model | MUST be centralized (single model per deployment) | Configurable via `EMBEDDING_MODEL` |

**Invariant**: All collections in a deployment MUST use the same embedding model and dimension.
A deployment that changes models MUST re-embed all collections (no mixed dimensions).

### 5.2 Payload Schema

Every point upserted to any collection MUST include these metadata fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `str` | MUST | Origin identifier (e.g., `codex_hunters`, `babel_gardens`, `vsgs`) |
| `created_at` | `str` (ISO 8601) | MUST | Timestamp of vector creation |
| `text` | `str` | SHOULD | Original text that was embedded (for debugging/display) |
| `version` | `str` | SHOULD | Schema version of the payload (e.g., `"1.0"`) |
| `domain` | `str` | SHOULD | Domain tag (e.g., `"finance"`, `"generic"`) |

Additional payload fields are domain-specific and MAY be included freely.

### 5.3 Point ID Convention

- Point IDs MUST be deterministic UUIDs (UUID v5 from namespace + content hash) OR sequential integers
- Point IDs SHOULD be UUIDs for deduplication (upsert idempotency)
- Point IDs MUST NOT be random UUIDs (prevents dedup on re-ingestion)

---

## 6. Lifecycle Management

### 6.1 Collection Creation

1. New collections MUST be proposed via code change to `init_qdrant_collections.py`
2. The init script entry MUST include: `name`, `vector_size`, `distance`, `description`
3. New collections MUST specify their **tier** and **owner** in the description
4. The init script MUST be idempotent (safe to run multiple times)

### 6.2 Collection Deletion

1. Collections MUST NOT be deleted from production without:
   - Removing all code references (writers AND readers)
   - Removing from init script
   - A migration period of at least 1 release cycle
2. EPHEMERAL (`test_*`, `tmp_*`) collections MAY be deleted at any time
3. Deletion of CORE/ORDER collections requires a contract amendment

### 6.3 Collection Health Monitoring

Each deployment SHOULD implement periodic checks:
- **Ghost detection**: Collections with no writer in codebase
- **Orphan detection**: Collections not in init script but present in Qdrant
- **Stale detection**: Collections with no writes in > 30 days (configurable)
- **Zero-point detection**: Collections with 0 points (dead or failed bootstrap)

### 6.4 Migration Protocol

When renaming or restructuring collections:
1. Create new collection with new name
2. Migrate data (re-embed or copy vectors)
3. Update all readers to use new collection
4. Update all writers to use new collection
5. Keep old collection for 1 release cycle
6. Delete old collection

---

## 7. RAG Pipeline Integration

### 7.1 Write Pipeline (Ingestion → Embedding → Store)

```
Source → Provider → Codex Hunters → Embedding Service → Qdrant (entity_embeddings)
                                  → Babel Gardens → Qdrant (sentiment_embeddings)
                                  → Pattern Weavers → Qdrant (weave_embeddings)
```

**Rules**:
- Embedding MUST happen via the centralized Embedding Service (api_embedding) or the embedding API endpoint
- Services MUST NOT load embedding models locally (memory/consistency risk)
- The embedding vector MUST be generated from the same model across all collections

### 7.2 Read Pipeline (Query → Embed → Search → Augment)

```
User Query → Embedding → Qdrant Search (conversations → phrases → entity) → LLM Context
```

**Rules**:
- Search SHOULD follow a cascade: most-specific collection first, then fallback
- Search results MUST be scored and filtered (top_k + minimum score threshold)
- Retrieved context MUST be budget-limited (max chars/tokens) before injection into LLM prompt

### 7.3 Grounding Pipeline (VSGS)

```
Conversation State → Embedding → Qdrant Search (semantic_states) → Grounding Context
```

**Rules**:
- VSGS grounds the conversation in historical semantic context
- Grounding is optional (controlled by `VSGS_ENABLED` env var)
- Grounding data MUST NOT be exposed to end users (internal augmentation only)

---

## 8. Domain/Vertical Extension Rules

### 8.1 Domain Collections

Verticals MAY create domain-specific collections following these rules:

1. Collection name MUST follow: `<domain>.<purpose>` (e.g., `finance.templates`)
2. Collection MUST be declared in a domain-specific init section of the init script
3. Domain collections MUST use the same vector dimensions as core
4. Domain collections MUST include the standard payload fields (Section 5.2)
5. Domain collections SHOULD be listed in `vertical_manifest.yaml`

### 8.2 Domain Collection Registration

```yaml
# In vertical_manifest.yaml
rag:
  collections:
    - name: "finance.templates"
      tier: domain
      purpose: "Financial template embeddings for pattern matching"
      owner: "shadow_traders"
    - name: "finance.ticker_embeddings"
      tier: domain
      purpose: "Ticker entity semantic embeddings"
      owner: "codex_hunters"
```

### 8.3 Domain Cleanup

When a vertical is deactivated or removed:
1. Its domain collections MUST be marked for archival
2. Archival = snapshot + delete (not silent deletion)
3. Snapshot MUST be stored in Vault Keepers or external storage

---

## 9. Configuration Standards

### 9.1 Environment Variables

| Variable | Scope | Default | Description |
|----------|-------|---------|-------------|
| `QDRANT_HOST` | Global | `localhost` | Qdrant server host |
| `QDRANT_PORT` | Global | `6333` | Qdrant server port |
| `QDRANT_URL` | Global | `http://localhost:6333` | Full Qdrant URL (alternative to HOST+PORT) |
| `QDRANT_API_KEY` | Global | *(none)* | API key for authenticated clusters |
| `QDRANT_TIMEOUT` | Global | `30.0` | Client timeout in seconds |
| `QDRANT_COLLECTION` | Per-service | *(varies)* | Default collection for the service |
| `EMBEDDING_MODEL` | Global | `all-MiniLM-L6-v2` | Embedding model name |
| `EMBEDDING_API_URL` | Global | `http://embedding:8010/v1/embeddings/batch` | Centralized embedding endpoint |
| `VSGS_COLLECTION_NAME` | VSGS | `semantic_states` | VSGS grounding collection |
| `VSGS_ENABLED` | VSGS | `0` | Enable/disable semantic grounding |

### 9.2 Per-Service Collection Config

Each service MUST declare its collection(s) in its `config.py`:

```python
# services/api_<service>/config.py
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "<default_collection>")
```

Collection names MUST NOT be hardcoded in business logic. They MUST flow from config.

---

## 10. Audit & Compliance

### 10.1 Init Script as Source of Truth

The init script (`scripts/init_qdrant_collections.py`) is the **single source of truth** for declared collections.

Each entry MUST include:

```python
{
    "name": "<collection_name>",
    "vector_size": 384,
    "distance": "Cosine",
    "description": "<tier>: <owner> — <purpose>",
}
```

The description field MUST follow the format: `"<TIER>: <Owner> — <Purpose>"`.

Example:
```python
{"name": "entity_embeddings", "vector_size": 384, "distance": "Cosine",
 "description": "ORDER: Codex Hunters — Ingested entity semantic embeddings"},
```

### 10.2 Collection Audit Script

Deployments SHOULD implement an audit script that:
1. Lists all Qdrant collections
2. Compares against init script declarations
3. Reports: rogue (in Qdrant, not in script), missing (in script, not in Qdrant), empty (0 points)
4. Optionally reports stale collections (no writes in N days)

### 10.3 Compliance Check

A deployment is RAG-compliant when:
1. All live collections are declared in init script (**no rogues**)
2. All declared collections exist in Qdrant (**no missing**)
3. All collections use the same vector dimensions (**no mixed**)
4. All core/order collections have at least one writer and one reader in codebase
5. No `test_*` or `tmp_*` collections exist in production
6. QdrantAgent is the only Qdrant access path

---

## 11. Current State Assessment (Feb 25, 2026)

### 11.1 Live Collections (5 total — all 384-dim Cosine)

| Collection | Tier | Points | Owner | Writer | Reader | Status |
|---|---|---|---|---|---|---|
| `semantic_states` | CORE | 3,538 | VSGS Engine | `upsert_semantic_state` | `semantic_grounding_node` | ✅ Healthy |
| `phrases_embeddings` | CORE | 38,238 | Embedding Service | `api_embedding` | `qdrant_node` (fallback) | ✅ Healthy |
| `conversations_embeddings` | CORE | 4,752 | LangGraph | *(upstream import)* | `qdrant_node` (primary) | ⚠️ Ghost writer |
| `entity_embeddings` | ORDER | 4 | Codex Hunters | `codex bus_adapter` | Memory Orders, PW, Vault | ✅ Healthy |
| `weave_embeddings` | ORDER | 97 | Pattern Weavers | `PW streams_listener` | *(none yet)* | ⚠️ Write-only |

### 11.2 Open Items

| Item | Priority | Description |
|---|---|---|
| `conversations_embeddings` writer | Medium | Reader active in qdrant_node; writer was upstream vitruvyan. Need to implement write path (e.g., from compose_node or CAN) |
| `weave_embeddings` reader | Low | PW writes ontological patterns; wire a reader in LangGraph or Memory Orders for ontological retrieval |
| QdrantAgent hardcoded defaults | Medium | `search_phrases()` and `upsert_semantic_state()` have hardcoded collection defaults — should be explicit |

### 11.3 Cleanup Completed (Feb 25, 2026)

Deleted 10 orphaned collections (~1.83M vectors freed):

| Collection | Points | Reason |
|---|---|---|
| `financial_templates` | 1,777,364 | Kaggle import, no code reference |
| `market_data` | 3,214 | Upstream import, no code reference |
| `ticker_embeddings` | 519 | Upstream import, yaml config only |
| `momentum_vectors` | 519 | Upstream import, no code reference |
| `volatility_vectors` | 519 | Upstream import, no code reference |
| `trend_vectors` | 517 | Upstream import, no code reference |
| `vare_embeddings` | 27 | Upstream import, no code reference |
| `sentiment_embeddings` | 1,048 | BG dead code (store_embedding never called) |
| `test_collection` | 0 | Development artifact |
| `vitruvyan_notes` | 1 | CLI default only |

---

## 12. Remediation Roadmap

### Phase 1: Cleanup ✅ COMPLETED (Feb 25, 2026)
- [x] Delete 10 orphaned/ghost collections from Qdrant
- [x] Remove from init script
- [x] Update init script descriptions to follow `"<TIER>: <Owner> — <Purpose>"` format
- [x] Clean contract registry (rag.py) to match live state

### Phase 2: Wire Missing Paths (Short-term)
- [ ] Implement `conversations_embeddings` writer (compose_node or CAN → embed user exchanges)
- [ ] Wire `weave_embeddings` reader (ontological retrieval in LangGraph or Memory Orders)
- [ ] Remove hardcoded collection defaults from QdrantAgent methods

### Phase 3: Contract Enforcement (Medium-term)
- [ ] Implement collection audit script (compare Qdrant vs init script)
- [ ] Add payload schema validation to QdrantAgent.upsert()
- [ ] Add collection name validation (reject names not in registry)
- [ ] Add vertical_manifest.yaml RAG section for domain collections

### Phase 4: Growth (Long-term)
- [ ] Multi-model support (different dimensions per collection tier)
- [ ] Collection versioning (v1, v2 with migration)
- [ ] Automatic stale collection detection and alerting
- [ ] RAG effectiveness metrics (retrieval relevance scoring)

---

## 13. Change Control

1. Changes to CORE/ORDER collection definitions require a contract amendment (new version)
2. Adding DOMAIN collections follows Section 8 (no contract change needed)
3. Changes to vector standards (Section 5) require re-embedding of all affected collections
4. This contract is versioned; breaking changes require V2

---

## 14. References

- QdrantAgent: `vitruvyan_core/core/agents/qdrant_agent.py`
- Init script: `scripts/init_qdrant_collections.py`
- Python contract interface: `vitruvyan_core/contracts/rag.py`
- Vertical contract: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`
- VSGS engine: `vitruvyan_core/core/vpar/vsgs/`
- Qdrant node (LangGraph): `vitruvyan_core/core/orchestration/langgraph/node/qdrant_node.py`
- Semantic grounding node: `vitruvyan_core/core/orchestration/langgraph/node/semantic_grounding_node.py`
