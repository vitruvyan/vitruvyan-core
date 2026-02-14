# Sacred Orders — Documentation Index

> **Last Updated**: February 14, 2026

These pages document the **Sacred Orders** of Vitruvyan OS as production components:

- **What the Order does** (mandate) and **what it must not do** (hard boundaries)
- **Interfaces** (events, API surfaces) and integration contracts
- **Code map** (LIVELLO 1 vs LIVELLO 2) for fast onboarding
- **Verticalization** guidance: how a domain (e.g. finance) plugs in without contaminating the core

Start with: [Sacred Orders — Introduction](../foundational/SACRED_ORDERS_INTRO.md)

## Orders

1. [Memory Orders](MEMORY_ORDERS.md) — Dual-memory coherence & sync planning (PostgreSQL ↔ Qdrant)
2. [Vault Keepers](VAULT_KEEPERS.md) — Integrity, backup/recovery, archival
3. [Orthodoxy Wardens](ORTHODOXY_WARDENS.md) — Epistemic tribunal (validation, verdicts, audit)
4. [Babel Gardens](BABEL_GARDENS.md) — Semantic signal extraction (YAML-driven)
5. [Codex Hunters](CODEX_HUNTERS.md) — Data acquisition & canonicalization (domain-agnostic)
6. [Pattern Weavers](PATTERN_WEAVERS.md) — Ontology resolution / semantic contextualization (YAML-driven)

## Reading path (recommended)

1) Babel Gardens → 2) Pattern Weavers → 3) Codex Hunters → 4) Memory Orders → 5) Vault Keepers → 6) Orthodoxy Wardens
