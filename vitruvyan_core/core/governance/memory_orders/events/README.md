# events/

> **Event type definitions and channel constants.**

## Constraints

- Dot notation: `<order>.<domain>.<action>`
- String constants, not enums — Redis Streams compatibility
- Event envelope is `frozen=True` — immutable
- `to_dict()` / `from_dict()` — bus serialization
- Define PUBLISH and CONSUME channel groups — explicit contract

---

## Contents

| File | Description |
|------|-------------|
| `memory_events.py` | Channel constants + event envelope for Memory Orders |

---

## Channel Naming Convention

All Memory Orders events follow:
```
memory.<domain>.<action>
```

Examples:
- `memory.coherence.requested` — Request coherence check
- `memory.coherence.checked` — Coherence check completed
- `memory.health.requested` — Request health check
- `memory.health.checked` — Health check completed
- `memory.sync.requested` — Request synchronization
- `memory.sync.completed` — Synchronization completed

---

**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1 — events)
