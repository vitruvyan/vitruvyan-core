# Finance Vertical - Orthodoxy Wardens Domain Pack

Last updated: 2026-02-23

## Scope

Finance governance defaults for Orthodoxy Wardens adapters.
This package is configuration-only and keeps core wardens domain-agnostic.

## What It Provides

- Ruleset metadata:
  - `domain_name=finance`
  - `ruleset_version=v1.1-finance`
- Default event fields:
  - `trigger_type=output_validation`
  - `scope=single_output`
  - `source=orthodoxy.finance`
- Strictness defaults:
  - `strict_mode=true`
  - `confidence_floor=0.75`

## Activation

- `ORTHODOXY_DOMAIN=finance`
- Optional override in service layer:
  - `ORTHODOXY_RULESET_VERSION`

## Contract Boundary

- No I/O in this package.
- Finance rules are loaded by adapters in
  `services/api_orthodoxy_wardens/adapters/finance_adapter.py`.
- Governance rule definitions remain in
  `vitruvyan_core/domains/finance/governance_rules.py`.

## Tests

```bash
pytest -q vitruvyan_core/domains/finance/orthodoxy_wardens/tests
```
