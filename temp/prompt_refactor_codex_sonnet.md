You are performing a constitutional refactor of Vitruvyan Core.

This is NOT a cleanup.
This is NOT a finance-generalization exercise.
This is an epistemic re-foundation.

Vitruvyan must become a truly domain-agnostic Cognitive Operating System.

------------------------------------------------------------
CONTEXT
------------------------------------------------------------

Vitruvyan originated as a financial vertical (Mercator).
Many core modules still contain implicit finance assumptions:

- tickers as canonical entity
- risk scoring inside ingestion layers
- technical indicators as default taxonomy
- yfinance as default source
- Postgres + Qdrant as baked dual-memory
- Pub/Sub legacy in listeners
- Direct HTTP cross-order calls
- Domain-specific channels in Synaptic Conclave

This must end.

We are moving from:
“Finance-first system with extensibility”

To:
“Epistemically neutral Cognitive OS capable of hosting any vertical.”

------------------------------------------------------------
CORE PRINCIPLES
------------------------------------------------------------

1) ONTOLOGICAL PURITY

Core modules must:
- Contain no domain semantics (finance, healthcare, logistics, etc.)
- Avoid privileged worldviews (tickers, sectors, fundamentals)
- Operate on generic primitives only:
  - entity_id
  - source
  - data_category
  - signal
  - taxonomy
  - canonical_record

2) EPISTEMIC BOUNDARIES

Each Sacred Order must strictly respect its cognitive layer:

- Babel Gardens → Signal Extraction
- Pattern Weavers → Ontology Resolution
- Codex Hunters → Data Acquisition & Canonicalization
- Neural Engine → Scoring & Interpretation
- Decision Engine → Strategic Reasoning

No Order may:
- Perform logic belonging to another Order
- Emit domain interpretation outside its layer
- Call another Order via HTTP

All inter-order communication must occur via Redis Streams.

3) PROVIDER AGNOSTIC CORE

LIVELLO 1 (pure domain layer) must not:

- Know Qdrant
- Know PostgreSQL
- Know Redis
- Know embedding providers
- Know HTTP endpoints
- Hardcode embedding dimensions

It must operate on abstract contracts only.

4) CONFIGURATION AS SINGLE SOURCE OF TRUTH

All domain-specific assumptions must be:

- Injected via YAML
- Loaded explicitly at service startup
- Never defaulted silently
- Never hardcoded in entity constructors

------------------------------------------------------------
MISSION
------------------------------------------------------------

Perform a structural audit and produce:

1) A Domain-Agnostic Compliance Plan
2) A commit-by-commit migration roadmap
3) Identification of cross-layer violations
4) Required interface redesign (if necessary)
5) A proposed neutral vocabulary for core primitives

------------------------------------------------------------
SPECIFIC OBJECTIVES
------------------------------------------------------------

A) Pattern Weavers

- Remove all domain semantics (risk, sector, etc.)
- Ensure output contract is purely ontological
- Remove provider coupling (Qdrant shape assumptions)
- Validate that it only emits OntologicalMapping

B) Codex Hunters

Redefine as:

“Canonical Data Acquisition & Normalization Order”

It must:

- Accept entity_id (not tickers)
- Accept source (not yfinance default)
- Normalize raw data
- Deduplicate deterministically (hash-based only)
- Emit canonical_record events

It must NOT:

- Perform risk analysis
- Emit domain signals
- Use Pub/Sub
- Perform HTTP calls to other Orders
- Encode domain channel taxonomy (technical.momentum etc.)

C) Synaptic Conclave

- Enforce Streams-only communication
- Validate that no Order uses redis.publish
- Ensure channel naming is domain-neutral
- Remove finance-coded event names from core

D) LangGraph Orchestration

- Remove direct HTTP cross-service calls
- Replace with event-driven dispatch
- Remove target="audit_engine" hardcoding

------------------------------------------------------------
DELIVERABLES
------------------------------------------------------------

Produce:

1) A “Domain-Agnostic Constitution” summary
2) A risk assessment of breaking changes
3) A 3-phase migration roadmap:

Phase 1: Ontological Purification
Phase 2: Provider Decoupling
Phase 3: Micelial Enforcement

4) A list of neutral primitives that replace finance-specific ones:

Example:
- ticker → entity_id
- fundamentals → structured_attributes
- technical_indicators → derived_metrics
- risk_profile → interpretation_output
- finance_channel → domain_event

5) A Streams Namespace Standard proposal

------------------------------------------------------------
CRITICAL INSTRUCTION
------------------------------------------------------------

Do NOT propose incremental cosmetic changes.
Do NOT protect finance semantics.
Do NOT maintain backward compatibility inside core.

Backward compatibility, if needed, must live in vertical plugins,
not in the core cognitive substrate.

The core must become epistemically neutral.

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return:

1) Executive architectural diagnosis
2) Domain contamination map
3) Commit-by-commit roadmap
4) Neutral vocabulary table
5) Streams namespac
