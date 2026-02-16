---
tags:
  - sacred-orders
  - governance
  - admin
---

# Sacred Orders (Admin)

> **Last Updated**: February 14, 2026

This section is the **internal** (admin) view of the Sacred Orders: deeper implementation notes, code map, agent-level responsibilities, and operational behavior.

!!! note "Public vs admin"
    The public documentation exposes the concept-level overview.  
    The admin documentation explains *how it works in code*.

Start with: [Sacred Orders — Introduction](../../foundational/SACRED_ORDERS_INTRO.md)

## Orders

- **Codex Hunters** — discovery → normalization → binding (sources → canonical entities)
- **Orthodoxy Wardens** — epistemic governance pipeline (confession → findings → verdict)
- **Vault Keepers** — archival, integrity, backup/restore planning and audit trail
- **Memory Orders** — coherence integrity across Postgres ↔ Qdrant (drift, health, sync planning)
- **Babel Gardens** — text → structured semantic signals (embeddings, sentiment/signals, explainability)
- **Pattern Weavers** — ontology/taxonomy resolution (semantic weave + keyword fallback)

Some pages may still be expanding (especially Babel Gardens during refactor), but the summary at the top of each page is the stable starting point.
