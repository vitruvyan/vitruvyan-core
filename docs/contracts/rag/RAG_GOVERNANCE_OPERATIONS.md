# RAG Governance Operations

Last updated: February 26, 2026

Operational runbook for RAG governance workflows.

## 1. Bootstrap Collections

```bash
python scripts/init_qdrant_collections.py
```

Expected behavior:

- creates missing declared collections
- keeps existing collections untouched
- returns non-zero on bootstrap errors

## 2. Audit Registry vs Live Qdrant

```bash
python scripts/audit_rag_collections.py
python scripts/audit_rag_collections.py --json
python scripts/audit_rag_collections.py --strict
```

Audit states:

- `OK`
- `MISSING`
- `MISMATCH`
- `ORPHAN`

## 3. Runtime Guard Controls

Environment flags:

- `RAG_ENFORCE_REGISTRY=warn|strict|off`
- `RAG_METRICS=1|0`
- `RAG_METRICS_HISTORY=<N>`
- `RAG_STALE_THRESHOLD_DAYS=<days>`

## 4. Retrieval Metrics Snapshot

Via QdrantAgent CLI:

```bash
python -m vitruvyan_core.core.agents.qdrant_agent --mode metrics
```

Programmatic access:

```python
from contracts.rag import get_rag_metrics

summary = get_rag_metrics().summary()
print(summary)
```

## 5. Stale Detection Check

```python
from core.agents.qdrant_agent import QdrantAgent
from contracts.rag import check_stale_collection

agent = QdrantAgent()
report = check_stale_collection(agent, "phrases_embeddings")
print(report.status, report.age_days)
```

## 6. Migration Planning (Model/Version)

```python
from contracts.rag import get_collection_declaration, plan_collection_migration

decl = get_collection_declaration("phrases_embeddings")
plan = plan_collection_migration(decl, target_model="all-mpnet-base-v2", target_version=2)
print(plan.to_dict())
```

Notes:

- planning does not execute migration
- execution still requires controlled dual-write/cutover workflow

## 7. Recommended CI Gate Sequence

1. `scripts/audit_rag_collections.py --strict`
2. contract tests/import checks for `contracts/rag.py`
3. smoke query against key collections (`conversations`, `phrases`, `weave`)
4. fail release on MISSING/MISMATCH
