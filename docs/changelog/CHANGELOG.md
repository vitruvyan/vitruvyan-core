# Vitruvyan Core — Changelog

> **Last updated**: February 17, 2026

Cronologia consolidata di tutte le milestone architetturali di Vitruvyan Core, dalla fondazione al V1.0.

---

## Feb 17, 2026 — LangGraph 1.0.8 Production Upgrade

Graph Orchestrator upgraded from LangGraph 0.5.4 to 1.0.8 (major version jump). Isolated test container validated compatibility. Dependencies upgraded: `langgraph-checkpoint` 2.1.2 → 4.0.0, `langgraph-prebuilt` 0.5.2 → 1.0.7, `langgraph-sdk` 0.1.74 → 0.3.6. All functional tests passed. Production deployment successful (port 9004, service healthy, dispatch endpoint validated).

## Jan 25–26, 2026 — Herald → Redis Streams Migration: 100% Complete

All 7 listeners migrated from pub/sub Herald to Redis Streams. ReadOnlyError fix (2-line fix in `listener_adapter.py`). Shadow Traders + MCP Listener migrated (Phase 3 of 3).

## Jan 24, 2026 — Cognitive Bus Phase 6: Plasticity System

Bounded, auditable, reversible parameter adaptation. Consumers learn from outcomes with 5 structural guarantees (bounded, auditable, reversible, opt-in, governance-validated). 6/6 tests passing.

## Jan 24, 2026 — Cognitive Bus Phase 0: Bus Hardening (BREAKING)

Redis Streams made canonical transport. Pub/Sub archived. Fixed BaseConsumer (broken async), unified 4 incompatible event models into `TransportEvent` / `CognitiveEvent` / `EventAdapter`.

## Jan 20, 2026 — Cognitive Bus Phase 4: Working Memory System

Distributed working memory for consumers. Octopus-mycelium architecture: isolated local memory + optional mycelial sharing via events. Memory Inspector API for debugging.

## Jan 19, 2026 — Cognitive Bus Phase 3: Socratic Pattern (non_liquet)

Orthodoxy Wardens gained epistemic gatekeeping: 5-state verdict system (blessed, purified, heretical, non_liquet, clarification_needed). Vitruvyan can now explicitly say "I don't know" instead of hallucinating.

## Dec 30, 2025 — v1.0.0 Milestone: Domain-Agnostic Framework Complete

Vitruvyan Core declared production-ready. Phases 1–3D complete. Mercator (finance) validated as PoC. AEGIS (governance) ready to proceed.

## Dec 30, 2025 — Phase 3D: Neural Engine Integration Pattern

Canonical integration pipeline: NE → VWRE → VARE → VEE. VerticalOrchestrator, BatchProcessor, ResultAggregator utilities. Mercator-lite demo vertical as proof-of-concept.

## Dec 30, 2025 — Phase 3: Domain Abstraction (VEE/VARE/VWRE)

VEE, VARE, VWRE engines refactored from finance-specific to domain-agnostic. 3 abstract contracts (Explainability, Risk, Aggregation) + 3 finance provider implementations for backward compatibility. COO approval granted.

## Dec 29, 2025 — Phase 1E: Neural Engine Abstraction

Domain-agnostic Neural Engine: `AbstractFactor`, `NormalizerStrategy`, `AggregationProfile` contracts + `EvaluationOrchestrator` + 3 built-in normalizers (ZScore, MinMax, Rank).

## Dec 29, 2025 — Phase 1D: Node Abstraction (Finance Logic Removal)

Finance-specific logic removed from 5 LangGraph nodes. Boot test validated all containers (zero import errors, APIs responsive).

## Dec 28, 2025 — Phase 1A–1C: Foundation & Domain Contracts

Repository created (vitruvyan_os → vitruvyan_core), package renamed, domain contracts defined (`EntitySchema`, `SignalSchema`, `DomainPolicy`), `GenericDomain` fallback implemented.

---

> **Note**: This file consolidates 21 per-phase reports that existed in this directory prior to Feb 16, 2026. The original detailed reports are preserved in git history.
