# Finance MCP Domain Pack

Last updated: 2026-02-23

## Scope

Finance helper package for `services/api_mcp`, enabled by `MCP_DOMAIN=finance`.
It keeps MCP core generic and adds compatibility transforms for legacy finance
tool contracts.

## What It Provides

- Tool alias mapping:
  - `screen_tickers -> screen_entities`
  - `compare_tickers -> compare_entities`
  - `query_sentiment -> query_signals`
- Argument normalization:
  - `ticker/tickers` -> canonical `entity_id/entity_ids`
  - `days` -> `time_window`
  - `include_phrases` -> `include_context`
- Finance profile and criteria normalization to canonical factors (`factor_1..factor_5`)
- Sentiment source fallback candidates:
  - primary: `sentiment_scores.ticker`
  - legacy: `entity_signals.entity_id`
- Deterministic phrase fallbacks when no context rows are available

## Activation

- `MCP_DOMAIN=finance`
- Optional service overrides:
  - `MCP_FINANCE_SIGNAL_TABLE`
  - `MCP_FINANCE_SIGNAL_ENTITY_COLUMN`
  - `MCP_FINANCE_EXPOSE_LEGACY_TOOLS`

## Contract Boundary

- Pure configuration/transforms only.
- No direct network or database I/O in this package.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/mcp_server/tests
```
