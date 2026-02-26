# Vertical Implementation Guide (Overview)

> **Status**: Canonical entrypoint  
> **Audience**: developers implementing a new vertical without changing core internals  
> **Read this first**, then continue with topic pages.

## TOC

1. [Why this guide exists](#why-this-guide-exists)
2. [Verticalization without overwhelm](#verticalization-without-overwhelm)
3. [The 4 verticalization areas](#the-4-verticalization-areas)
4. [Known vertical domains](#known-vertical-domains)
5. [Recommended reading path](#recommended-reading-path)
6. [Binding contracts](#binding-contracts)

## Why this guide exists

This page is the single entrypoint to understand **how to reason** about verticalization.

Core rule: contract-first.

- core remains domain-agnostic
- the vertical enters through hooks/registries/adapters
- release quality is gated by manifest + conformance checklist

## Verticalization without overwhelm

A vertical does not mean rewriting the system.  
It means adding a package under `vitruvyan_core/domains/<domain>/` and wiring it where needed.

Work is distributed across a few clear areas:

1. define the **domain** (intents/config/contract files)
2. wire **LangGraph orchestration** (env vars + dynamic imports + registrations)
3. enable only the **Sacred Orders** you actually need
4. use **patterns/examples** as accelerators, not as normative rules

In practice, required implementation areas are 3 (`domain`, `langgraph`, `sacred orders`), while `pattern` is supporting material.

## The 4 verticalization areas

### 1) Domain

Your main work happens in `vitruvyan_core/domains/<domain>/`: intent config, manifest, tests, plus optional components (entity resolver, execution handler, governance rules, etc.).

- Page: `docs/knowledge_base/development/verticals/Vertical_Domain.md`

### 2) Orchestration (LangGraph)

This is where runtime wiring happens (`INTENT_DOMAIN`, `ENTITY_DOMAIN`, `EXEC_DOMAIN`, optional `GRAPH_DOMAIN`) and where you distinguish auto-load from manual startup registration.

Important boundary: domain-specific graph nodes do not live in `vitruvyan_core/core/orchestration/langgraph/node/`; they live in `vitruvyan_core/domains/<domain>/graph_nodes/registry.py` and are loaded as hooks.

- Page: `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`

### 3) Sacred Orders

This is where you assess per-order impact (Orthodoxy, Vault, Babel, Pattern Weavers, Codex, Neural) and explicitly mark `ACTIVE` vs `EXPERIMENTAL` vs `PLANNED`.

- Page: `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`

### 4) Pattern

This is where reusable patterns and examples live. It does not replace implementation rules.

- Page: `docs/knowledge_base/development/verticals/Vertical_Patterns.md`
- Examples: `examples/verticals/README.md`

## Known vertical domains

Below is the current list of vertical domains with available documentation and brainstorm/design artefacts.

| Domain | Status | Reference |
|--------|--------|-----------|
| **Finance** | Active (reference implementation) | [Codex Hunters Domain Pack](../../../examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md) |
| **Security / AICOMSEC** | Brainstorm / Design phase | [AICOMSEC Brainstorm Report](verticals/security/AICOMSEC_BRAINSTORM_REPORT.md) |

## Recommended reading path

For a new developer:

1. this page (overview)
2. `docs/knowledge_base/development/verticals/Vertical_Domain.md`
3. `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`
4. `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`
5. `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## Binding contracts

Normative references:

- `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`
- `docs/contracts/verticals/VERTICAL_CONFORMANCE_CHECKLIST.md`
- `docs/contracts/verticals/templates/vertical_manifest.yaml`
- `docs/contracts/verticals/schema/vertical_manifest.schema.json`

Centralized technical reference (matrix, status, troubleshooting):

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
