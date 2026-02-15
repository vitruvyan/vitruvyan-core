# Finance — Codex Hunters Domain Pack (Pilot)

This is the **pilot domain pack** for *finance*, showing how a vertical plugs into the **domain-agnostic** Codex Hunters core without contaminating it.

## What “domain pack” means

For Codex Hunters, a domain pack provides:

1) **Vocabulary binding** (what `entity_id` represents in the domain)  
2) **Configuration** (tables/collections, sources, stream namespace)  
3) **Normalization rules** (source payload → `normalized_data`)  
4) **Routing hooks** (when orchestration triggers Codex expeditions)

---

## 1) Vocabulary binding (finance)

| Core primitive | Finance meaning |
|---|---|
| `entity_id` | `ticker` (e.g. `AAPL`) |
| `source` | market data provider (e.g. `yfinance`) |
| `normalized_data` | canonical fundamentals/quotes/derived fields |

---

## 2) Configuration (YAML)

Finance binds Codex Hunters to finance-namespaced storage + streams.

- `examples/verticals/finance/config/codex_hunters_finance.yaml`

Key choices:

- `entity_table`: `finance.tickers`
- `embedding_collection`: `ticker_embeddings`
- `streams.prefix`: `codex.finance`
- `sources`: `yfinance` enabled (prototype), `alpha_vantage` disabled (placeholder)

> Note: the core remains unchanged — only `CodexConfig` changes.

---

## 3) Normalization rules (Restorer)

Codex Hunters normalizes data in LIVELLO 1 via `RestorerConsumer`.

Example “finance normalizer” + builder:

- `examples/verticals/finance/codex_hunters_domain_pack.py`

Pattern:

- register `normalizer(source_name, fn)` for each enabled source
- keep normalization deterministic and schema-friendly

---

## 4) Routing hook (when to trigger Codex expeditions)

Finance integrates with orchestration through the finance graph plugin:

- `vitruvyan_core/domains/finance/graph_plugin.py:478` (route `codex_expedition`)
- `vitruvyan_core/domains/finance/graph_plugin.py:515` (custom router)

Current rule (finance pilot):

- if no `tickers`/`entity_ids` in state
- and `screening_filters.mode == "discovery"`
- then route to `"codex_expedition"`

This is intentionally domain-specific and belongs in the **finance graph plugin**, not in Codex Hunters core.

---

## 5) Next hardening steps (to make it production-grade)

- Replace prototype source(s) with authenticated providers (still via LIVELLO 2 adapters).
- Define a canonical finance schema for `normalized_data` (minimal, versioned).
- Remove “ticker” language from shared event channels (keep it in domain pack + plugin only).
