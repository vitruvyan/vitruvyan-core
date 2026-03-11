---
tags:
  - web-ui
  - plasticity
  - governance
  - learning
  - system-core
---

# Plasticity — Adaptive Learning Loop

> **Last updated**: Mar 11, 2026 11:30 UTC  
> **Status**: ✅ Active  
> **Location**: UI `ui/components/chat/` · Backend `vitruvyan_core/core/synaptic_conclave/plasticity/` · Service `services/api_graph/`

---

## What is Plasticity?

Plasticity is Vitruvyan's **bounded, auditable learning system**. It allows the system to adapt its governance parameters based on real user feedback — without black-box neural tuning. Every adjustment is:

- **Bounded** by explicit min/max ranges
- **Reversible** via full rollback history
- **Auditable** through CognitiveEvent trails
- **Governed** by Orthodoxy Wardens (Truth layer validation)

!!! quote "Design Principle"
    *"No parameter escapes its declared bounds. No adjustment happens without a recorded reason. No change survives without governance approval."*

---

## User-Facing Feature: Thumbs Up / Down

Every AI response includes feedback buttons (👍 / 👎) that feed directly into the Plasticity learning loop.

```mermaid
flowchart LR
    U[User clicks 👍 or 👎] --> MF[MessageFeedback.jsx]
    MF --> UF[useFeedback.js hook]
    UF -->|POST /api/feedback| BE[Backend Endpoint]
    BE --> OT[OutcomeTracker]
    BE -->|plasticity.feedback.received| BUS[StreamBus]
    OT --> LL[LearningLoop<br/>24h cycle]
    LL --> PM[PlasticityManager]
    PM -->|propose_adjustment| SE[ShadowEvaluator]
    SE -->|approved?| ADJ[Apply / Reject]
    
    style U fill:#1e293b,stroke:#94a3b8,color:#fff
    style MF fill:#0f172a,stroke:#3b82f6,color:#fff
    style BE fill:#172554,stroke:#60a5fa,color:#fff
    style OT fill:#1e3a8a,stroke:#93c5fd,color:#fff
    style LL fill:#312e81,stroke:#a78bfa,color:#fff
    style SE fill:#581c87,stroke:#c084fc,color:#fff
```

### UI Components

| Component | File | Purpose |
|-----------|------|---------|
| `MessageFeedback.jsx` | `ui/components/chat/MessageFeedback.jsx` | Thumbs up/down buttons under AI messages |
| `useFeedback.js` | `ui/components/chat/hooks/useFeedback.js` | Hook: sends feedback signal to backend, optimistic local update |

### Feedback Signal Contract

```typescript
interface FeedbackSignal {
  message_id: string      // The AI message being rated
  trace_id?: string       // Links to CognitiveEvent chain (from finalState)
  feedback: 'positive' | 'negative'
  comment?: string        // Optional free-text correction
  timestamp: string       // ISO 8601
}
```

Defined in `ui/contracts/ChatContract.ts`.

---

## Backend Architecture

### Feedback Endpoint

**`POST /api/feedback`** (in `services/api_graph/api/routes.py`)

1. Converts feedback to outcome value: `positive → 1.0`, `negative → 0.0`
2. Records in `OutcomeTracker` via `PlasticityService`
3. Emits to StreamBus channel `plasticity.feedback.received`
4. Returns `200` (fire-and-forget from UI; failures are non-fatal)

### Core Components (LIVELLO 1 — Pure Domain)

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **OutcomeTracker** | `synaptic_conclave/plasticity/outcome_tracker.py` | Records outcomes to PostgreSQL, computes success rates (7-day lookback) |
| **PlasticityManager** | `synaptic_conclave/plasticity/manager.py` | Proposes/applies bounded adjustments, rollback, history tracking |
| **LearningLoop** | `synaptic_conclave/plasticity/learning_loop.py` | Periodic (24h) analysis: low success → relax, high success → tighten |
| **ShadowEvaluator** | `services/api_graph/adapters/plasticity_adapter.py` | Anti-oscillation: simulates proposed adjustment on 7 days of history before approving |

### Adjustment Algorithm

Every 24 hours (configurable via `PLASTICITY_INTERVAL_HOURS`):

1. For each consumer with plasticity enabled:
2. For each adjustable parameter:
    - Fetch 7-day `success_rate` from OutcomeTracker
    - If `success_rate < 0.4` → parameter is too strict → **relax** (delta +)
    - If `success_rate > 0.9` → parameter is too permissive → **tighten** (delta -)
    - Validate via ShadowEvaluator (compare simulated vs current rate)
    - Apply only if `simulated_rate >= current_rate`

### Parameter Bounds (Example)

```python
ParameterBounds(
    name="confidence_threshold",
    min_value=0.4,
    max_value=0.9,
    step_size=0.05,
    default_value=0.6,
    description="Minimum confidence for automated classification"
)
```

All adjustments snap to `step_size` and are rejected if they exceed `[min, max]`.

---

## StreamBus Channels

| Channel | Producer | Consumer | Purpose |
|---------|----------|----------|---------|
| `plasticity.feedback.received` | `api_graph` | `plasticity` | User feedback signal |
| `plasticity.outcome.recorded` | `plasticity` | `orthodoxy_wardens` | Outcome recorded, ready for learning |

Internal CognitiveEvent types:

- `plasticity.adjustment` — Parameter adjustment applied (delta, reason, bounds)
- `plasticity.rollback` — Adjustment reversed (causation_id → original event)

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PLASTICITY_ENABLED` | `true` | Enable/disable the learning loop |
| `PLASTICITY_INTERVAL_HOURS` | `24` | Learning cycle interval |

---

## Governance Safeguards

1. **Bounded parameters**: Each parameter has explicit `[min, max]` — values cannot escape declared ranges
2. **Shadow validation**: Before applying, the system simulates the adjustment on 7 days of historical data
3. **Rollback stack**: Full adjustment history; `rollback(steps=N)` reverses the last N changes
4. **Orthodoxy audit**: Adjustment events flow to Orthodoxy Wardens for governance validation
5. **Disable per-parameter**: `disable_plasticity(param)` freezes a specific parameter while others continue learning

!!! info "No Black Box"
    Unlike neural fine-tuning, Plasticity operates on named, bounded, interpretable parameters. Every change is traceable from user feedback to parameter adjustment via CognitiveEvent chains.
