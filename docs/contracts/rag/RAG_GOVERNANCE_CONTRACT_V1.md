# RAG Governance Contract V1

Last updated: February 26, 2026  
Status: ACTIVE  
Version: 1.1.0  
Owner: Vitruvyan Core Architecture

---

## 1. Purpose

This contract defines binding governance rules for RAG infrastructure in Vitruvyan.

RAG is a managed memory substrate. The objective is to prevent collection sprawl, hidden coupling, and silent quality decay.

Normative keywords follow RFC 2119 semantics: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY.

---

## 2. Scope

This contract applies to:

- all Qdrant collections used by Vitruvyan services
- `QdrantAgent` as the canonical runtime gateway
- collection declarations and bootstrap via `scripts/init_qdrant_collections.py`
- registry contracts in `vitruvyan_core/contracts/rag.py`
- audit and compliance tooling (`scripts/audit_rag_collections.py`)

This contract does not define Qdrant cluster topology (infra concern).

---

## 3. Core Principles

### 3.1 Single Gateway

Service runtime code MUST use `QdrantAgent`.

- forbidden: direct `QdrantClient` usage in business logic
- forbidden: raw Qdrant REST calls in business logic
- exception: bootstrap/ops scripts MAY use direct calls when needed

### 3.2 Declared Collections Only

Production collections MUST be declared and owned.

- declaration authority: `scripts/init_qdrant_collections.py`
- programmatic registry: `vitruvyan_core/contracts/rag.py`
- undeclared live collections are ORPHAN and SHOULD be remediated

### 3.3 No Hardcoded Collection Defaults

Collection names MUST be explicit at call sites.

Current implementation status:

- `search_phrases(..., collection=...)` -> enforced
- `upsert_semantic_state(..., collection=...)` -> enforced
- `upsert_point_from_grounding(..., collection=...)` -> enforced

### 3.4 Soft Runtime Guards

`QdrantAgent` includes non-blocking governance guards:

- undeclared collection usage warning (`RAG_ENFORCE_REGISTRY=warn|strict|off`)
- payload warning when `payload.source` is missing (MUST metadata)

---

## 4. Collection Taxonomy

### 4.1 Tiers

| Tier | Scope | Lifecycle | Example |
|---|---|---|---|
| CORE | OS-level, domain-agnostic | long-lived | `semantic_states`, `conversations_embeddings` |
| ORDER | Sacred Order operational | managed by owner order | `entity_embeddings`, `weave_embeddings` |
| DOMAIN | vertical-specific | vertical lifecycle | `finance.templates` |
| EPHEMERAL | tests/migration/temp | disposable | `test_*`, `tmp_*`, `migration_*` |

### 4.2 Naming

- lowercase, 3-64 chars
- allowed chars: `[a-z0-9_.]`
- domain collections SHOULD use `<domain>.<purpose>`
- EPHEMERAL collections MUST use approved prefixes

Grandfathered active names:

- `semantic_states`
- `phrases_embeddings`
- `conversations_embeddings`
- `entity_embeddings`
- `weave_embeddings`

### 4.3 Ownership

- write path: owner-first responsibility
- read path: cross-order reads allowed when contract-compliant

---

## 5. Vector and Model Standards

### 5.1 Collection Declaration Fields

`CollectionDeclaration` supports:

- `name`
- `vector_size`
- `distance`
- `tier`
- `owner`
- `purpose`
- `domain`
- `model_name` (phase 4)
- `version` (phase 4)

### 5.2 Multi-Model Rules (Phase 4)

Multi-model deployments are supported with explicit declaration.

- `model_name` MUST be declared per collection
- `vector_size` MUST match declared model dimension
- model registry lives in `contracts/rag.py` (`EMBEDDING_MODELS`)
- cross-collection mixed dimensions are allowed only when each collection is internally consistent

### 5.3 Versioning Rules (Phase 4)

Collection schema versioning is supported.

- `version` MUST be integer >= 1
- v1 uses canonical collection name
- v2+ MAY use suffix strategy (`<name>_vN`) during migration
- migrations SHOULD use explicit migration planning (see Section 9)

---

## 6. Payload Contract

Every upserted point MUST include:

- `source`
- `created_at`

Recommended metadata:

- `text`
- `version`
- `domain`

`RAGPayload` in `contracts/rag.py` is the canonical helper for payload normalization.

---

## 7. Runtime Integration

### 7.1 Write Path (Current)

Representative active flows:

- Codex Hunters -> `entity_embeddings`
- Embedding service -> `phrases_embeddings`
- Pattern Weavers -> `weave_embeddings`
- VSGS / semantic grounding sync -> `semantic_states`
- CAN conversational memory -> `conversations_embeddings`

Note: legacy `sentiment_embeddings` is not part of the active declared registry.

### 7.2 Read Path

LangGraph retrieval follows tiered cascade behavior in current code:

- conversations memory
- phrase memory
- ontological fallback

All retrieval calls should pass explicit collection names.

---

## 8. Audit and Compliance

### 8.1 Canonical Audit Tool

`scripts/audit_rag_collections.py` reports:

- OK
- MISSING
- MISMATCH
- ORPHAN

### 8.2 Stale Detection Utilities (Phase 4)

`contracts/rag.py` provides stale analysis helpers:

- `StaleReport`
- `check_stale_collection(...)`
- `RAG_STALE_THRESHOLD_DAYS`

### 8.3 Effectiveness Metrics Utilities (Phase 4)

`contracts/rag.py` provides retrieval quality instrumentation:

- `SearchMetrics`
- `RAGMetricsCollector`
- global collector via `get_rag_metrics()`

`QdrantAgent.search()` can auto-record metrics when `RAG_METRICS != 0`.

### 8.4 Compliance Checklist

A deployment is compliant when:

1. no undeclared live collections
2. no missing declared collections
3. declared vector/distance values match live config
4. Qdrant access path is contract-compliant
5. required payload metadata is enforced at adapter boundaries

---

## 9. Migration Planning (Phase 4)

`contracts/rag.py` includes migration planning primitives:

- `MigrationPlan`
- `plan_collection_migration(...)`

Use these for controlled v1 -> v2 and/or model migrations.

---

## 10. Current State (Feb 26, 2026)

### 10.1 Completed

- Phase 1 cleanup: orphan collection purge
- Phase 2 wiring: explicit collection params and missing reader/writer paths
- Phase 3 enforcement: audit script + runtime soft guards
- Phase 4 core primitives:
  - model registry (`EmbeddingModel`, `EMBEDDING_MODELS`)
  - per-collection model/version fields
  - stale detection utilities
  - retrieval effectiveness metrics collector
  - `QdrantAgent` CLI metrics mode

### 10.2 Remaining Operational Work

- stale alerting integration (automated scheduling + alert channel)
- long-term metrics persistence/observability dashboards
- migration playbook automation for large collections

---

## 11. Change Control

1. CORE/ORDER contract changes require contract amendment in this document.
2. DOMAIN collection additions follow vertical governance and manifest policy.
3. Breaking changes require V2 contract.

---

## 12. References

- `vitruvyan_core/contracts/rag.py`
- `vitruvyan_core/core/agents/qdrant_agent.py`
- `scripts/init_qdrant_collections.py`
- `scripts/audit_rag_collections.py`
- `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`
