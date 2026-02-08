# Vitruvyan Cognitive Bus — Architectural Invariants
Version: 2.0 (Hardening Refactor)  
Date: 2026-01-18  
Status: Foundational (Non-Negotiable)


**MAJOR UPDATE (Jan 24, 2026):**
- Redis Streams is the ONLY canonical bus (Pub/Sub archived)
- Event envelope standardized (TransportEvent / CognitiveEvent)
- BaseConsumer functional on real Redis Streams
- Bus invariants enforced structurally in code
---

## 0. Purpose

This document defines the non-negotiable architectural invariants of the Vitruvyan Cognitive Bus (“the Bus”).  
These are not guidelines or policies. They are structural constraints that must hold for all current and future implementations.

The Bus is designed to **enable temporal coherence**, not to implement cognition.

---

## 1. Core Separation of Responsibilities

Temporal coherence involves three layers:

1) **Correlation** — linking events and reconstructing causal chains  
2) **Interpretation** — assigning meaning to relationships  
3) **Action** — deciding and executing based on meaning

**Invariant:**  
- The Bus may enable **(1) Correlation**  
- The Bus must never perform **(2) Interpretation** or **(3) Action**

All interpretation and action live exclusively in explicit consumers (orchestration, governance, validation, explainability).

---

## 2. The Bus Primitives (Allowed Capabilities)

The Bus is allowed to provide only the following primitives:

### 2.1 Causal Ordering
Events must carry metadata sufficient to reconstruct “happened-before” relationships.
- globally unique `event.id`
- human-friendly `timestamp`
- causal ancestry via `causation_id` and/or `parent_ids`

### 2.2 Correlation Identifiers
Events must be groupable by **opaque** identifiers:
- `trace_id` (root causal tree)
- `correlation_id` (logical flow/session/decision chain)
- `causation_id` (immediate parent)

The Bus provides the namespace and storage for these identifiers, but never their semantics.

### 2.3 Durable, Ordered Storage
The Bus must support:
- append-only persistence
- ordered retrieval within a partition
- replay from any point in time (subject to retention)

### 2.4 Subscription with Temporal Filters
Consumers must be able to retrieve events by “coordinates”, not by meaning:
- time ranges
- event types (opaque string)
- correlation identifiers
- causal ancestry
- offsets / sequence numbers

### 2.5 Schema Envelope Integrity
The Bus transports events with a strict envelope schema:
- envelope is validated structurally
- payload is treated as opaque data

---

## 3. Hard Invariants (Prohibited Behaviors)

Violations must be impossible by construction.

### 3.1 No Payload Inspection
The Bus must never inspect payload contents to make routing, prioritization, or correlation decisions.

Routing and partitioning decisions may only use:
- envelope fields (id, timestamp, event_type, trace_id, correlation_id, causation_id, version, etc.)

### 3.2 No Event Synthesis
The Bus must never create events on its own.
- It only stores and transports events emitted by producers.
- System-generated “housekeeping” events are permitted only if emitted by a dedicated producer service, not by the Bus itself.

### 3.3 No Correlation Inference
The Bus must never infer relationships between events.
- `correlation_id`, `trace_id`, and ancestry links are provided by producers.
- The Bus does not “discover” or “learn” correlations.

### 3.4 No Semantic Aggregation
The Bus must not compute:
- rolling windows
- summaries
- derived metrics
- semantic clusters
- trend/insight streams

All aggregation is a consumer responsibility.

### 3.5 No Conditional Routing or Smart Policies
The Bus must not implement logic such as:
- “if event X happened, route Y differently”
- “promote this stream when pattern P occurs”
- “throttle based on inferred meaning”

Any such logic must be implemented by explicit consumers that:
- read events
- decide
- emit new events

### 3.6 Violation Examples (Anti-Patterns)

The following are concrete examples of invariant violations:

| Anti-Pattern | Violation | Why It's Wrong |
|--------------|-----------|----------------|
| "Route high-sentiment events to a priority queue" | 3.1 (Payload Inspection) | Routing decisions based on semantic content |
| "Auto-generate `session_started` when first event arrives" | 3.2 (Event Synthesis) | Bus creating events, not just transporting |
| "Link events that mention the same ticker symbol" | 3.3 (Correlation Inference) | Bus inferring relationships from content |
| "Compute rolling average of sentiment scores" | 3.4 (Semantic Aggregation) | Bus performing analytics on payloads |
| "Throttle events when anomaly pattern detected" | 3.5 (Conditional Routing) | Bus implementing semantic policies |
| "Cluster events by embedding similarity" | 3.4 (Semantic Aggregation) | Bus performing meaning-based grouping |
| "Promote urgent events based on keyword detection" | 3.1 + 3.5 | Payload inspection + conditional routing |

**Correct Alternative:** All of the above must be implemented as consumers that subscribe to events, perform their logic, and emit new events (e.g., `priority_flagged`, `session_boundary_detected`, `anomaly_alert`).

---

## 4. Observability and Auditability Requirements

### 4.1 Append-Only Truth
Events must be immutable once written.
- corrections are modeled as new events (e.g., `correction_event`)
- deletes are not allowed (except retention expiry)

### 4.2 Deterministic Replay
Given the same event history, consumer logic must be able to reproduce:
- decision chains
- governance verdicts
- explainability provenance

This is the foundation of “auditable cognition”.

### 4.3 Graceful Degradation
Failure of the transport layer must not cause cognitive amnesia.
- durable storage is the source of truth
- transport may be ephemeral, best-effort, or cache-like
- consumers can recover via replay

---

## 5. The Litmus Test for Any New Capability

Before adding any capability to the Bus, ask:

> Can this be implemented as a consumer that reads events and writes events?

- If **yes** → it must be implemented as a consumer (NOT in the Bus)
- If **no** → it may be considered a true primitive, and must be added minimally

Almost everything is “yes”.

---

## 6. Consequences

These invariants are the forcing function that makes Vitruvyan:
- explicit (logic lives in code, not in infrastructure magic)
- auditable (events in / events out)
- governable (validators can intercept and constrain)
- explainable (provenance trees are reconstructible)

The moment the Bus becomes “helpful” in a semantic sense, it becomes opaque.

Opacity is incompatible with Vitruvyan.

---

## 7. Amendment Protocol

These invariants are foundational. They are not subject to casual revision.

### 7.1 Amendment Criteria
Any proposed change must demonstrate:
1. The capability **cannot** be implemented as a consumer
2. The change does not introduce payload inspection, event synthesis, correlation inference, or semantic aggregation
3. The change preserves deterministic replay and auditability

### 7.2 Amendment Process
1. Written proposal with technical justification
2. Review by architectural governance (minimum 2 maintainers)
3. Explicit documentation of why the Litmus Test (Section 5) yields "no"
4. Version increment and changelog entry

### 7.3 Burden of Proof
The burden of proof lies with the proposer.  
If there is doubt, the answer is "implement as consumer."

---

## Changelog

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-01-18 | Initial foundational invariants |

---
