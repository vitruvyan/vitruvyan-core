# domain/

> **Immutable domain objects. No I/O. No infrastructure imports.**

## Constraints

- All classes use `@dataclass(frozen=True)` — immutable after creation
- Collections use `tuple`, not `list` — enforces immutability
- Metadata as `tuple[tuple[str, Any], ...]` — not `dict` (mutable)
- Validation in `__post_init__` — fail fast, explicit errors
- NO I/O, NO imports from other packages — only `dataclasses`, `typing`, stdlib

---

## Contents

| File | Description |
|------|-------------|
| `memory_objects.py` | Core domain objects (CoherenceInput, CoherenceReport, ComponentHealth, SystemHealth, SyncInput, SyncPlan, SyncOperation) |

---

**Sacred Order**: Memory & Coherence  
**Layer**: Foundational (LIVELLO 1)
