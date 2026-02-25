# Finance Vertical - Memory Orders Domain Pack

Last updated: 2026-02-23

## Scope

Finance helper package for Memory Orders adapters.
LIVELLO 1 Memory core stays domain-agnostic; this package only exposes finance
defaults and fallback candidates.

## What It Provides

- Canonical Mercator sources:
  - table: `entities`
  - collection: `entities_embeddings`
- Vitruvyan legacy fallbacks:
  - table: `phrases`
  - collection: `phrases_embeddings`
- Drift thresholds:
  - healthy: `5.0`
  - warning: `15.0`

## Activation

- `MEMORY_DOMAIN=finance`
- Optional overrides:
  - `MEMORY_FINANCE_TABLE`
  - `MEMORY_FINANCE_COLLECTION`

## Contract Boundary

- No I/O in this package.
- Source probing and persistence selection are handled by service adapters
  (`services/api_memory_orders/adapters/finance_adapter.py`).

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/memory_orders/tests
```
