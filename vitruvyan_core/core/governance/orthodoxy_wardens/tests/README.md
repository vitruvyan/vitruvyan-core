# tests/

> Unit and integration tests for Orthodoxy Wardens.

## Contents

| File | Description | Status |
|------|-------------|--------|
| `test_orthodoxy_bus.py` | Legacy Pub/Sub bus tests (345 lines) | ⚠️ Legacy — needs rewrite for Streams |

## Planned (FASE 2-3)

| File | Description |
|------|-------------|
| `test_domain_objects.py` | Confession, Finding, Verdict, LogDecision validation |
| `test_sacred_role.py` | SacredRole contract verification |
| `test_events.py` | OrthodoxyEvent serialization roundtrip |
| `test_governance.py` | RuleSet loading and classification |
| `test_consumers.py` | Pure consumer tests (no infra) |

## Testing Rules

- Domain objects: pure unit tests, zero infrastructure
- Consumers: pure tests (process() is deterministic, no mocks needed)
- Events: serialization roundtrip tests only
- Integration tests (bus, DB) live in the **service layer**, not here
