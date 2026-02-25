# Finance Vertical - Babel Gardens Domain Pack

Last updated: 2026-02-23

## Scope

Finance domain pack used by `api_babel_gardens` when `BABEL_DOMAIN=finance`.
It keeps core Babel logic domain-agnostic and provides finance-specific
configuration and helper logic.

## Activation

- `BABEL_DOMAIN=finance`
- Optional runtime integration in Mercator stack: `babel_gardens` + `babel_listener`

## Package Content

| File | Role |
|---|---|
| `sentiment_config.py` | Multi-model fusion weights and finance-aware boosts |
| `financial_context.py` | Finance context detector (language-aware keyword model) |
| `sector_resolver.py` | Sector alias resolution from `sector_mappings` (DB access injected) |
| `volatility_lexicon.py` | Deterministic `volatility_perception` extractor |
| `signals_finance.yaml` | Finance signal catalog for Babel extraction pipeline |

## Runtime Notes

- `SectorResolver` does not open DB connections directly: it receives a `db_fetcher`
  callable from the service adapter.
- `volatility_perception` is heuristic and normalized to `[0, 1]`.
- Default fusion weights:
  - `llm=0.45`
  - `finbert=0.35`
  - `multilingual=0.20`

## Contract Boundary

- Core remains in `vitruvyan_core/core/cognitive/babel_gardens`.
- This package is finance-only and consumed by LIVELLO 2 adapters.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/babel_gardens/tests
```
