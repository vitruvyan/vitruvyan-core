# consumers/

> Decision engines that process events and render judgments.

## Contents

| File | Description |
|------|-------------|
| `base.py` | `SacredRole` ABC — the contract all consumers implement |

### Planned (FASE 3)

| File | Description | Migrated From |
|------|-------------|---------------|
| `confessor.py` | Audit orchestrator — routes confessions to specialists | `confessor_agent.py` |
| `inquisitor.py` | Classification engine — categorizes findings by rules | `inquisitor_agent.py` |
| `penitent.py` | Strategy selector — recommends corrections (never executes) | `penitent_agent.py` |
| `chronicler.py` | LogDecision engine — decides what to remember | `chronicler_agent.py` (reborn) |

## SacredRole Contract

```python
class SacredRole(ABC):
    role_name: str       # Unique identifier
    description: str     # English description
    can_handle(event)    # Should this role process this event?
    process(event)       # Pure judgment: event → Verdict/Finding/LogDecision
```

## Constraints

- `process()` is **PURE**: no side effects, no I/O, no network
- Consumers **never** import StreamBus, Redis, or PostgreSQL
- Type enforcement at **concrete** level (ABC uses `Any`)
- Same input → same output (deterministic, testable)
- The service layer wraps consumers in bus adapters for production use
