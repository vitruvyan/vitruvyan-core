# Finance Vertical - Vault Keepers Domain Pack

Last updated: 2026-02-23

## Scope

Finance runtime defaults for Vault Keepers adapters.
Core Vault logic remains domain-agnostic.

## What It Provides

- Backup defaults:
  - `mode=full`
  - `include_vectors=true`
- Retention defaults:
  - archives: `1825` days
  - signal timeseries: `1825` days
- Archive content normalization:
  - channel to content-type mapping
  - fallback classification (`audit_result`, `eval_result`, `system_state`, `agent_log`, `generic`)
- Source-order normalization aliases:
  - `memory -> memory_orders`
  - `pattern -> pattern_weavers`
  - `babel -> babel_gardens`
  - `orthodoxy -> orthodoxy_wardens`
  - `engine -> neural_engine`

## Activation

- `VAULT_DOMAIN=finance`
- Optional service overrides:
  - `VAULT_FINANCE_DEFAULT_BACKUP_MODE`
  - `VAULT_FINANCE_INCLUDE_VECTORS`
  - `VAULT_FINANCE_ARCHIVE_RETENTION_DAYS`
  - `VAULT_FINANCE_SIGNAL_RETENTION_DAYS`

## Contract Boundary

- No I/O in this package.
- Applied by `services/api_vault_keepers/adapters/finance_adapter.py`.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/vault_keepers/tests
```
