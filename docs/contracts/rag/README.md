# RAG Governance Contracts

> **Last updated**: Feb 21, 2026 16:00 UTC

This directory contains the binding contracts for RAG (Retrieval-Augmented Generation) infrastructure governance.

## Documents

| File | Description |
|------|-------------|
| `RAG_GOVERNANCE_CONTRACT_V1.md` | Full contract specification (naming, lifecycle, tiers, payload schema, compliance) |

## Python Interface

The programmatic contract interface lives at:
- `vitruvyan_core/contracts/rag.py`

Import via:
```python
from contracts.rag import CollectionDeclaration, CollectionTier, RAGPayload
# or
from vitruvyan_core.contracts import CollectionTier, RAGPayload, deterministic_point_id
```

## Quick Reference

### Collection Tiers
- **CORE**: OS-level, permanent (e.g., `semantic_states`, `conversations_embeddings`)
- **ORDER**: Sacred Order data (e.g., `entity_embeddings`, `weave_embeddings`)
- **DOMAIN**: Vertical-specific (e.g., `finance.templates`)
- **EPHEMERAL**: Test/tmp (`test_*`, `tmp_*`)

### Key Rules
1. All access through `QdrantAgent` — no raw Qdrant clients
2. All collections declared in `scripts/init_qdrant_collections.py`
3. All payloads include `source` + `created_at` metadata
4. One embedding model per deployment (currently 384-dim all-MiniLM-L6-v2)
