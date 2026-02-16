---
tags:
  - architecture
  - memory
  - governance
  - sacred-orders
---

# 🧠 Dual Memory Layer in Vitruvyan

**PostgreSQL + Qdrant coordinated by governance orders**

## 🧭 1) What it is

The Dual Memory Layer is the memory substrate of Vitruvyan:

- 🧱 **Archivarium (PostgreSQL)** stores canonical, structured truth
- 🌐 **Mnemosyne (Qdrant)** stores semantic/vector representations
- ⚖️ **Memory Orders** keeps the two layers coherent over time
- 🏛️ **Vault Keepers** records audit evidence for traceability
- 🛡️ **Orthodoxy Wardens** records epistemic verdicts for governance

In short: one memory for deterministic structure, one memory for semantic retrieval, and a governance layer that keeps them aligned.

---

## 🧱 2) What each layer does

### Archivarium — structured memory

PostgreSQL is the authoritative source for entities, versions, and relational state.
It supports deterministic queries, consistency checks, and governance-grade audit linkage.

### Mnemosyne — semantic memory

Qdrant stores vectors and semantic payloads used by retrieval and pattern correlation.
It enables similarity search and context expansion across multilingual and unstructured inputs.

---

## ⚖️ 3) Role of Memory Orders

Memory Orders is the coordination and integrity order between the two memories.
It performs three core functions:

1. **Drift calculation**: detects divergence between canonical and semantic state
2. **Health aggregation**: computes a unified health view across memory dependencies
3. **Sync/reconciliation planning**: produces and, when allowed, executes repair operations

Memory Orders does not define business truth. It protects alignment between truth and representation.

---

## 🛡️ 4) Reconciliation and enforcement model

Reconciliation follows a controlled policy model:

- `dry_run`: generate plan only, no data mutation
- `assisted` / `autonomous`: allow execution when requested

Execution safety is enforced by:

- **Idempotency key** (`idempotency_key`) to avoid duplicate runs
- **Run lock** per source pair (`table` + `collection`) to avoid concurrent collisions
- **Mass-delete guardrail** (threshold policy, explicit override required)
- **Retry + dead-letter** for failed operations (`memory.reconciliation.dead_letter`)

The design keeps PostgreSQL authoritative and reconciles derived Qdrant state.

---

## 🔗 5) Governance coupling

The orders are connected but not merged:

```text
Memory Orders
  ├─ computes coherence/health/reconciliation
  └─ emits audit.vault.requested

Vault Keepers
  └─ persists audit evidence in vault_audit_log

Orthodoxy Wardens
  └─ persists epistemic verdicts in audit_findings
```

This separation preserves clear responsibilities:
- Memory integrity (Memory Orders)
- Accountability (Vault Keepers)
- Epistemic discipline (Orthodoxy Wardens)

---

## 🚀 6) Why this is important

The Dual Memory Layer is not “just Postgres + vectors.”  
Its value is architectural:

- It keeps semantic retrieval tied to canonical truth
- It makes drift visible and governable
- It enforces safe reconciliation instead of ad-hoc repairs
- It provides auditability and epistemic accountability for regulated contexts

This is what makes Vitruvyan memory **governed cognitive infrastructure**, not a generic RAG storage stack.
