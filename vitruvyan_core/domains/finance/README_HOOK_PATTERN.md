# Finance Hook Pattern Reference

Last updated: 2026-02-23

## Scope

Reference guide for finance plugin registration in hook-based components.
This document is intentionally a pattern note, not a production runbook.

## Goal

Keep core modules domain-agnostic while letting the finance vertical inject
domain behavior through registries and domain packs.

## Main Hooks

| Hook | Finance Module | Typical Env |
|---|---|---|
| Entity resolver | `vitruvyan_core/domains/finance/entity_resolver_config.py` | `ENTITY_DOMAIN=finance` |
| Execution handler | `vitruvyan_core/domains/finance/execution_config.py` | `EXEC_DOMAIN=finance` |
| Intent registry | `vitruvyan_core/domains/finance/intent_config.py` | `INTENT_DOMAIN=finance` |

## Current Mercator Notes

- Finance domain packs are active for Sacred Orders and services through their
  dedicated domain env vars (for example `DOMAIN=finance`, `PATTERN_DOMAIN=finance`,
  `MCP_DOMAIN=finance`, `VAULT_DOMAIN=finance`).
- Hook registration points remain the same principle:
  core defines registries/contracts, domain modules provide concrete logic.

## Design Rules

- Core code must not hardcode finance assumptions.
- Domain modules can be enabled/disabled via environment without breaking core.
- Missing domain registration must degrade gracefully to generic behavior.
- Domain packs should keep I/O in adapters/services, not in core contracts.

## Example Startup Pattern

```python
import os

if os.getenv("INTENT_DOMAIN", "generic").lower() == "finance":
    from vitruvyan_core.domains.finance.intent_config import create_finance_registry
    registry = create_finance_registry()
```

```python
import os

if os.getenv("EXEC_DOMAIN", "generic").lower() == "finance":
    from vitruvyan_core.domains.finance.execution_config import (
        register_finance_execution_handler,
    )
    register_finance_execution_handler()
```

## Validation Checklist

- `INTENT_DOMAIN=finance` loads finance intents.
- `ENTITY_DOMAIN=finance` enables finance entity resolution hooks.
- `EXEC_DOMAIN=finance` enables finance execution handler registration.
- With generic env values, behavior falls back to agnostic defaults.
