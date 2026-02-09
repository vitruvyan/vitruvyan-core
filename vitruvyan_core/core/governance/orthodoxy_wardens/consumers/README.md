# consumers/

> Decision engines that process events and render judgments.

## Status: ✅ COMPLETE (FASE 3)

## Contents

| File | Description | Migrated From |
|------|-------------|---------------|
| `base.py` | `SacredRole` ABC — the contract all consumers implement | — |
| `confessor.py` | Intake officer — raw events → `Confession` | `confessor_agent.py` |
| `inquisitor.py` | Examiner — Confession + text/code → `InquisitorResult` (Findings) | `inquisitor_agent.py` |
| `penitent.py` | Correction advisor — Verdict → `CorrectionPlan` (never executes) | `penitent_agent.py` |
| `chronicler.py` | Log strategist — Verdict → `ChronicleDecision` (never persists) | `chronicler_agent.py` (reborn) |

## Pipeline Flow

```
Raw Event
  → Confessor.process(event)         → Confession
  → Inquisitor.process({confession, text, code})  → InquisitorResult (Findings)
  → VerdictEngine.render(findings)   → Verdict        [governance/]
  → Penitent.process(verdict)        → CorrectionPlan
  → Chronicler.process(verdict)      → ChronicleDecision
```

## SacredRole Contract

```python
class SacredRole(ABC):
    role_name: str       # Unique identifier
    description: str     # English description
    can_handle(event)    # Should this role process this event?
    process(event)       # Pure judgment: event → result
```

## Result Types

| Consumer | Input | Output |
|----------|-------|--------|
| Confessor | `OrthodoxyEvent` / `dict` | `Confession` |
| Inquisitor | `dict{confession, text, code}` | `InquisitorResult` (tuple[Finding]) |
| Penitent | `Verdict` | `CorrectionPlan` (tuple[CorrectionRequest]) |
| Chronicler | `Verdict` | `ChronicleDecision` (LogDecision + ArchiveDirectives) |

## Constraints

- `process()` is **PURE**: no side effects, no I/O, no network
- Consumers **never** import StreamBus, Redis, or PostgreSQL
- Type enforcement at **concrete** level (ABC uses `Any`)
- Same input → same output (deterministic, testable)
- The service layer wraps consumers in bus adapters for production use
