# domain/

> Frozen dataclasses representing the core concepts of the epistemic tribunal.

## Contents

| File | Description |
|------|-------------|
| `confession.py` | Audit request entering the tribunal |
| `finding.py` | Single observation from examination |
| `verdict.py` | Final judgment (5 statuses, factory methods) |
| `log_decision.py` | Meta-decision: whether/how to persist an event |

## Constraints

- **ALL objects are `@dataclass(frozen=True)`** — immutable after creation
- **NO I/O**: No database, no network, no file access
- **NO imports from other packages**: Only `dataclasses`, `typing`, standard lib
- **Collections use `tuple`**, not `list` — enforces immutability
- **Validation in `__post_init__`** — fail fast on invalid data
- **Factory methods** (e.g., `Verdict.blessed()`) — canonical creation patterns

## Design Decisions

1. **`tuple` for metadata, not `dict`**: Dicts are mutable. We store key-value pairs as
   `tuple[tuple[str, Any], ...]`. Consumers call `dict(obj.metadata)` when needed.

2. **`frozenset` for valid values**: Enum-like validation without import overhead.
   The valid values live as class attributes (`_VALID_STATUSES`).

3. **`LogDecision` as a domain object**: Logging is a *decision*, not a side effect.
   The Chronicler consumer produces LogDecisions; the service layer executes them.
