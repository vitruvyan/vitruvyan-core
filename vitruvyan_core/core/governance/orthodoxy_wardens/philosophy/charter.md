# Orthodoxy Wardens — Decision Engine Charter

> **"Il giudice non è mai il boia."**
> *The judge is never the executioner.*

## Identity

Orthodoxy Wardens is an **epistemic tribunal** — a decision engine that receives
confessions, examines evidence, and renders verdicts. It is not a guardian, not a
monitor, not an executor. It **judges**.

## Mandate

### What Orthodoxy DOES:
- **Classify** inputs by compliance category, severity, and urgency
- **Evaluate** outputs against declared rules (RuleSet)
- **Render verdicts** with explicit confidence and evidence chain
- **Admit uncertainty** when confidence is insufficient (non_liquet)
- **Request corrections** by publishing events (never executing them)
- **Archive decisions** by publishing to Vault Keepers

### What Orthodoxy NEVER does:
- ❌ Restart services or containers
- ❌ Write to databases directly
- ❌ Call external APIs
- ❌ Modify code or configuration
- ❌ Execute corrections (that's Penitent's *request*, not Orthodoxy's *action*)
- ❌ Silently default to "blessed" when uncertain

## Sacred Invariants

1. **All consumers are PURE functions**: `input → judgment`, no side effects
2. **All rules are DATA, not behavior**: loaded from config, versioned, auditable
3. **All verdicts are FROZEN**: immutable after creation, traceable to ruleset version
4. **"I don't know" is always valid**: non_liquet prevents confident hallucination
5. **The judge is never the executioner**: judgment and execution are separate services

## The Five Verdicts

| Verdict | Latin Meaning | Disposition | Example |
|---------|---------------|-------------|---------|
| **Blessed** | Approved | Send to user | "Output passed all 47 compliance rules" |
| **Purified** | Cleansed | Send corrected | "Removed speculative claim, facts retained" |
| **Heretical** | Rejected | Block delivery | "Revenue hallucination: $10T for AAPL" |
| **Non Liquet** | "Not clear" | Send with caveat | "Cannot verify earnings date, confidence 0.3" |
| **Clarification Needed** | — | Ask user | "Query too ambiguous, please specify ticker" |

## Relationship to Other Layers

```
┌─────────────────────────────────────────────────┐
│  FOUNDATIONAL (this package)                    │
│  Pure Python. No infrastructure. Importable.    │
│                                                 │
│  domain/      → What we judge (Confession...)   │
│  consumers/   → How we reason (SacredRole)      │
│  governance/  → The rules we apply (RuleSet)    │
│  events/      → What we announce                │
│  monitoring/  → What we count                   │
└───────────────────────┬─────────────────────────┘
                        │ imports
┌───────────────────────▼─────────────────────────┐
│  SERVICE (api_orthodoxy_wardens/)               │
│  Infrastructure. Bus. DB. API. Docker.          │
│                                                 │
│  Wraps SacredRoles in StreamBus adapters        │
│  Persists verdicts to PostgreSQL                │
│  Exposes HTTP endpoints                         │
│  Listens to Cognitive Bus channels              │
└─────────────────────────────────────────────────┘
```

## Historical Note

The original Orthodoxy Wardens (pre-refactoring) mixed judgment with execution:
the Confessor orchestrated Docker restarts, the Chronicler monitored CPU usage,
the Penitent applied code patches. This violated the separation of concerns.

The refactoring (FASE 0-4, Feb 2026) surgically separates DECIDING from DOING,
making the tribunal truly epistemic: it knows, it judges, it speaks — but it
never acts on the material world.

This is the first Sacred Order refactored. It establishes the industrial pattern
that all others (Vault Keepers, Codex Hunters, Pattern Weavers, Babel Gardens)
will follow.
