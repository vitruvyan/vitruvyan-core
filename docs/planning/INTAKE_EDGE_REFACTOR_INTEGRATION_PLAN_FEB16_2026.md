# Intake + Edge Refactor & Integration Plan

> **Date**: February 16, 2026  
> **Status**: Planning Baseline (pre-implementation)  
> **Scope**: Refactor Intake and integrate as default interoperability layer in Vitruvyan Core

---

## 1. Mission

Refactor Intake into a robust, streams-native, pre-epistemic acquisition layer and integrate it with the new Edge architecture under `infrastructure/edge`, preserving strict separation of concerns and enabling multi-platform deployment.

---

## 2. Non-Negotiable Architectural Decisions

1. Intake remains **pre-epistemic only**:
- No NER
- No embeddings
- No semantic relevance judgments
2. Event transport is **Redis Streams only** (no Pub/Sub fallback).
3. MCP is **control-plane/H2M only**, not intake data-plane.
4. Orthodoxy validates governance invariants, but does not replace intake runtime responsibilities.
5. File upload/acquisition remains in dedicated intake/edge services; LangGraph orchestration triggers flow but does not become file-transfer infrastructure.

---

## 3. Target Architecture

`External Sources (H2M + M2M) -> Edge Gateway -> Local Policy + Local Outbox -> Core Streams -> Intake -> Codex -> Pattern Weavers -> Memory Orders -> Vault Keepers`

Core components:
1. `services/api_edge_gateway`: ingress adapters, local queue/outbox, replay engine, telemetry.
2. `infrastructure/edge/oculus_prime/core`: media-specific agents + canonical evidence/event contracts.
3. `service intake API`: upload + ingestion endpoints + retrieval.
4. `StreamBus`: intake event emission + downstream consumption with consumer groups.
5. Governance checkpoints: Orthodoxy rulepacks for edge/intake events.

---

## 4. Refactor Workstreams

### WS-1: Contract & Schema Alignment
1. Freeze canonical `Evidence Pack v1` fields.
2. Freeze canonical `intake.evidence.created v1` schema.
3. Align SQL schema, agent payloads, and retrieval APIs to one naming convention.
4. Add contract tests to prevent drift.

### WS-2: Streams Migration
1. Replace publish/subscribe logic with StreamBus emit/consume APIs.
2. Introduce consumer groups, ack, retry policy, dead-letter streams.
3. Add idempotency persistence strategy (DB uniqueness + key checks).

### WS-3: Intake Runtime Stabilization
1. Fix import-path and packaging inconsistencies.
2. Normalize all agents to a single persistence/event emission contract.
3. Remove legacy assumptions and mixed schemas.
4. Keep append-only immutability guarantees.

### WS-4: Edge Gateway MVP
1. Implement ingress adapters:
- HTTP/Webhook
- MQTT
- File watcher
2. Add local outbox (`SQLite`) with deterministic replay.
3. Add offline mode behavior (`buffer -> replay -> ack`).
4. Expose operational endpoints: `/health`, `/status`, `/metrics`.

### WS-5: Security & Governance Hardening
1. Device identity model.
2. mTLS edge-core transport.
3. Signed payload + anti-replay (`nonce` + timestamp window).
4. Policy-driven authorization per adapter/source.
5. Orthodoxy invariants for edge-originated intake events.

### WS-6: LangGraph Integration
1. Add `intake_node` as orchestration trigger path (intent/routing), not binary transport layer.
2. Support orchestrated intake invocation and evidence ID propagation.
3. Keep downstream Sacred Flow unchanged after intake event.

### WS-7: Multi-Platform Optimization
1. Runtime profiles: `eco`, `balanced`, `performance`.
2. Resource caps by deployment profile.
3. Packaging targets:
- Docker (VPS/server)
- systemd (mini PC/SBC)
- lightweight relay profile (mobile/embedded bridge)

### WS-8: Observability & Operability
1. Metrics:
- ingest throughput
- stream lag
- retry rate
- DLQ rate
- replay backlog
2. Structured logs with correlation IDs.
3. Runbooks for failure/recovery and reconnect behavior.

---

## 5. Implementation Phases

### Phase 0 (Week 1): Contract Freeze
Deliverables:
1. Frozen contracts: Evidence Pack, Intake Event, Edge Envelope/Policy/Capability.
2. ADRs: MCP role, Streams-only, Offline semantics, Security baseline.
3. Acceptance tests definition.

### Phase 1 (Week 2-3): Intake Core Refactor
Deliverables:
1. Agent/event/schema alignment completed.
2. API retrieval and persistence consistency.
3. Contract tests green.

### Phase 2 (Week 4): Streams-Native Transition
Deliverables:
1. Full StreamBus migration.
2. Retry + DLQ mechanisms active.
3. Consumer-group processing verified.

### Phase 3 (Week 5-6): Edge Gateway MVP
Deliverables:
1. HTTP+MQTT ingress operational.
2. Local outbox + replay working in offline/online transitions.
3. Health/status/metrics endpoints available.

### Phase 4 (Week 7): Governance + Security
Deliverables:
1. mTLS and signed payload validation.
2. Orthodoxy rulepack for edge-intake flow.
3. Audit trail completeness checks.

### Phase 5 (Week 8): LangGraph Integration + E2E
Deliverables:
1. `intake_node` integration in orchestration flow.
2. End-to-end ingestion test from upload to downstream event chain.
3. Documentation and operational handoff.

### Phase 6 (Week 9): Multi-Platform Validation
Deliverables:
1. Deployment profile certification (`eco`, `balanced`, `performance`).
2. Benchmarks across constrained and standard devices.
3. Final go-live recommendation.

---

## 6. Acceptance Criteria

1. Delivery reliability >= 99.5% under intermittent connectivity.
2. Duplicate downstream processing <= 0.1% via idempotency controls.
3. Offline buffering and replay with no data loss in tested scenarios.
4. Intake layer remains semantically neutral (pre-epistemic compliance).
5. MCP used only for edge control-plane operations.
6. Streams observability provides actionable lag/retry/DLQ visibility.
7. Multi-platform deployments pass runtime stability checks.

---

## 7. Risks and Mitigations

1. **Schema drift between code and DB**
- Mitigation: contract tests + migration gating.
2. **Legacy Pub/Sub residues**
- Mitigation: explicit deprecation checklist and CI grep guard.
3. **MCP-intake coupling regression**
- Mitigation: ADR + dependency boundary checks.
4. **Offline replay inconsistencies**
- Mitigation: deterministic queue ordering + replay idempotency verification suite.
5. **Performance issues on constrained hardware**
- Mitigation: profile-based runtime tuning + batch/interval controls.

---

## 8. First Execution Sprint (Recommended)

1. Finalize and freeze contract documents.
2. Refactor `event_emitter` + SQL schema alignment.
3. Implement one canonical path end-to-end:
- document ingest
- evidence pack insert
- streams event emit
- downstream consumer ack
4. Add base metrics dashboard (ingest/lag/retry).
5. Publish conformance report for go/no-go to next phase.

---

## 9. Immediate Next Documents

1. `EDGE_INTEROPERABILITY_CONTRACT_V1.md` (freeze from draft).
2. JSON schemas:
- `edge_evidence_envelope_v1.json`
- `edge_policy_v1.json`
- `edge_capability_v1.json`
3. ADR set:
- `ADR-EDGE-001` MCP role boundary
- `ADR-EDGE-002` Streams-only transport
- `ADR-EDGE-003` Offline replay semantics
- `ADR-EDGE-004` Edge security baseline
