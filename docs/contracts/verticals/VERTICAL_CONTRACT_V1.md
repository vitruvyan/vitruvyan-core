# Vertical Contract V1

Status: active
Version: 1.1.0
Last Updated: 2026-03-15
Owner: Vitruvyan Core Architecture

## 1. Purpose

This contract defines the mandatory pattern for creating and operating domain verticals in Vitruvyan.

The Vitruvyan core is domain-agnostic by design. Its value is realized through **domain specialization**: verticals that configure Sacred Orders, graph extensions, prompts, and governance for a specific domain. This contract ensures every vertical fully leverages the architecture.

Normative terms use RFC 2119 semantics:
- MUST / MUST NOT
- SHOULD / SHOULD NOT
- MAY

## 2. Scope

This contract applies to any new or migrated vertical under `vitruvyan_core/domains/<domain_name>/`.

This contract does not redefine core behavior; it constrains how vertical logic integrates with the domain-agnostic core.

## 3. Core Boundary

1. Vertical implementations MUST NOT inject domain logic into core internals.
2. Sacred Orders MUST remain domain-agnostic; vertical behavior MUST be introduced through domain packs (config, YAML, adapters).
3. LangGraph base pipeline MUST remain domain-agnostic; vertical extensions MUST use the `graph_nodes/registry.py` hook pattern.
4. Neural Engine core MUST remain domain-agnostic; domain scoring/data logic MUST implement contracts (`IDataProvider`, `IScoringStrategy`).

## 4. Required Artifacts

Each vertical MUST provide:
1. `intent_config.py` — intent registry with `create_<domain>_registry()` factory
2. `prompts/__init__.py` — domain prompts with `register_<domain>_prompts()` factory
3. `graph_nodes/registry.py` — graph extension with `get_<domain>_graph_nodes()` factory (may return empty dict in early phases)
4. `governance_rules.py` — domain-specific governance rules
5. `README.md` — vertical overview, architecture, quick start
6. `vertical_manifest.yaml` (from template)
7. Unit tests for vertical contracts

Each vertical MUST provide Sacred Orders domain packs (see §13):
1. `pattern_weavers/` — domain ontology taxonomy (YAML + config)
2. `babel_gardens/` — domain signal configuration (YAML + config)
3. `orthodoxy_wardens/` — domain compliance rules and strictness config

Each vertical MUST provide when the domain has persistent data:
1. `memory_orders/` — coherence thresholds, collection mappings
2. `vault_keepers/` — retention policies, backup schedules

Each vertical SHOULD provide (production enhancement):
1. `execution_config.py` — ExecutionRegistry handler for exec intents
2. `entity_resolver_config.py` — domain entity resolution
3. `compose_formatter.py` — compose_node domain context formatter
4. Integration tests

### Deprecated Artifacts

The following artifacts are DEPRECATED and MUST NOT be used in new verticals:
1. `graph_plugin.py` — superseded by `graph_nodes/registry.py` (Feb 2026)

## 5. Mandatory Contracts

Verticals MUST integrate through the canonical contracts namespace:
- `contracts` / `vitruvyan_core.contracts`

When applicable, vertical components MUST implement:
1. `GraphPlugin` — via `graph_nodes/registry.py` factories (canonical pattern)
2. `Parser` / `BaseParser`

Verticals SHOULD implement when the domain has structured scoring/ranking:
1. Neural Engine interfaces (`IDataProvider`, `IScoringStrategy`)

Direct imports from deprecated/legacy contract namespaces MUST NOT be introduced.

## 6. Domain Registration

1. Vertical loading MUST be controlled through environment selection:
   - `INTENT_DOMAIN` — intent registry (MUST)
   - `GRAPH_DOMAIN` — graph nodes extension (MUST, defaults to `INTENT_DOMAIN`)
   - `EXEC_DOMAIN` — execution handler (MUST when exec intents are defined)
   - `ENTITY_DOMAIN` — entity resolver (SHOULD)
2. Sacred Orders domain packs MUST be activated through environment variables:
   - `PATTERN_DOMAIN` — Pattern Weavers taxonomy
   - `BABEL_DOMAIN` — Babel Gardens signals
   - Other Sacred Orders load domain config from their pack directories
3. Vertical modules MUST expose expected factory functions:
   - `create_<domain>_registry()` — intent registry factory
   - `register_<domain>_prompts()` — prompt registration factory
   - `get_<domain>_graph_nodes()` — graph nodes factory (MUST, may return `{}`)
   - `get_<domain>_graph_edges()` — graph edges factory (optional, may return `[]`)
   - `get_<domain>_route_targets()` — route targets factory (optional, may return `{}`)
4. If dynamic import fails, runtime MUST preserve core fallback behavior.

## 7. Governance and Safety

1. Verticals MUST define explicit governance rules for regulated or sensitive contexts.
2. Vertical governance rules MUST NOT bypass Orthodoxy/Vault safety boundaries.
3. Vertical contracts MUST state data-classification assumptions and constraints.

## 8. Event and Data Principles

1. Verticals MUST follow existing Cognitive Bus invariants.
2. Event payloads MUST include version identifiers and traceability fields where applicable.
3. Vertical-specific schemas SHOULD be versioned and backward-compatible whenever possible.

## 9. Testing Requirements

Minimum test gate (MUST):
1. Contract conformance tests (imports + required methods/factories)
2. Intent registry load test
3. Manifest validation test
4. Sacred Orders domain pack load test (taxonomy loads, signals load, rules load)

Production gate (SHOULD):
1. Integration test through graph route
2. Governance behavior tests
3. Negative tests for invalid inputs
4. Pattern Weavers ontology coverage test (domain queries resolve to taxonomy categories)

## 10. Manifest and Compliance

Each vertical MUST include `vertical_manifest.yaml` with:
1. `domain_name`
2. `contract_version`
3. `required_components`
4. `sacred_orders_packs` (see §13)
5. `adapters`
6. `compliance`
7. `ownership`

Conformance MUST be evaluated via checklist and CI validation.

## 11. Change Control

1. Contract-breaking changes require a new major contract version.
2. Vertical-specific derogations MUST include:
   - reason
   - owner
   - expiry date
   - remediation plan
3. Permanent exceptions are NOT allowed.

## 12. Compliance Decision

A vertical is compliant only if:
1. all MUST clauses pass
2. no MUST NOT violation exists
3. manifest is valid
4. required tests pass
5. Sacred Orders domain packs are present and loadable

## 13. Sacred Orders Domain Packs

The Vitruvyan architecture is built on 6 domain-agnostic Sacred Orders. Each order provides core infrastructure; **verticals MUST specialize them** to deliver domain-specific intelligence.

Without domain packs, Sacred Orders operate in generic mode — the domain loses ontology resolution, signal extraction, compliance enforcement, and coherence monitoring. The core is agnostic **so that domains can specialize it**; not specializing defeats the architecture's purpose.

### 13.1 Pattern Weavers (MUST)

**Purpose**: Domain ontology mapping. Maps user queries to domain-specific taxonomy categories.

**Location**: `domains/<domain>/pattern_weavers/`

**Required artifacts**:
- `taxonomy_<domain>.yaml` — domain taxonomy categories with keywords, codes, hierarchy
- `weave_config.py` — domain thresholds, boosts, matching configuration

**Activation**: `PATTERN_DOMAIN=<domain>`

**Rationale**: Pattern Weavers is the ontology engine — it teaches the system the **conceptual vocabulary** of the domain. Without it, the weaver_node contributes no context to conversation, reducing response quality. Every domain has concepts worth mapping.

**Reference**: `vitruvyan_core/domains/finance/pattern_weavers/` (GICS sectors, financial concepts)

### 13.2 Babel Gardens (MUST)

**Purpose**: Domain signal extraction configuration. Defines what structured signals to extract from text.

**Location**: `domains/<domain>/babel_gardens/`

**Required artifacts**:
- `signals_<domain>.yaml` — signal catalog with names, value ranges, extraction models
- `<domain>_context.py` — domain query detection (keyword model for boundary enforcement)

**Activation**: `BABEL_DOMAIN=<domain>`

**Rationale**: Babel Gardens extracts structured signals from text. Without domain signals, the system extracts only generic emotion. Domain-specific signals (urgency, compliance risk, operational severity) are critical for accurate analysis.

**Reference**: `vitruvyan_core/domains/finance/babel_gardens/` (sentiment_valence, market_fear, volatility)

### 13.3 Orthodoxy Wardens (MUST)

**Purpose**: Domain compliance rules and strictness configuration.

**Location**: `domains/<domain>/orthodoxy_wardens/`

**Required artifacts**:
- `compliance_config.py` — domain ruleset metadata, strictness defaults, confidence thresholds

**Activation**: loaded from domain pack directory

**Rationale**: Every domain operates under regulatory or ethical constraints. Finance has SEC/FINRA rules; enterprise has GDPR/privacy; healthcare has HIPAA. Without domain-specific compliance, Orthodoxy can only apply generic safety checks.

**Reference**: `vitruvyan_core/domains/finance/orthodoxy_wardens/` (SEC, FINRA patterns)

### 13.4 Memory Orders (MUST when domain has persistent data)

**Purpose**: Domain coherence monitoring configuration.

**Location**: `domains/<domain>/memory_orders/`

**Required artifacts**:
- `<domain>_config.py` — collection mappings, drift thresholds, canonical data sources

**Activation**: loaded from domain pack directory

**Rationale**: Memory Orders monitors consistency between PostgreSQL and Qdrant. Domain config tells it which tables/collections matter and what drift thresholds are acceptable.

**Reference**: `vitruvyan_core/domains/finance/memory_orders/` (Mercator sources, drift thresholds)

### 13.5 Vault Keepers (MUST when domain has persistent data)

**Purpose**: Domain backup and retention policies.

**Location**: `domains/<domain>/vault_keepers/`

**Required artifacts**:
- `<domain>_config.py` — retention periods, backup schedules, archive normalization

**Activation**: loaded from domain pack directory

**Rationale**: Different domains have different retention requirements. Finance retains market data for 5 years; enterprise retains invoices for 10 years (Italian fiscal law). Without domain config, Vault uses generic defaults.

**Reference**: `vitruvyan_core/domains/finance/vault_keepers/` (retention policies, backup modes)

### 13.6 Codex Hunters (MAY)

**Purpose**: Domain data acquisition configuration.

**Location**: `domains/<domain>/codex_hunters/` (if needed)

**Required artifacts**: domain-specific source registry, quality thresholds

**Activation**: source-agnostic by design; MAY be specialized

**Rationale**: Codex Hunters is source-agnostic by design (any data source feeds the same pipeline). Domain specialization is useful when the domain has specific quality scoring rules or source normalization requirements, but is not mandatory.

### 13.7 Neural Engine (SHOULD when domain has structured scoring)

**Purpose**: Multi-factor scoring and ranking engine.

**Location**: `domains/<domain>/neural_engine/`

**Required contracts**: `IDataProvider`, `IScoringStrategy`

**Activation**: `EXEC_DOMAIN=<domain>` + ExecutionRegistry handler

**Rationale**: Neural Engine is a generic multi-factor Z-score ranking system. It is valuable when the domain has entities with numerical features that benefit from scoring/ranking (customer scoring, supplier ranking, risk assessment). Not every domain has this requirement — conversational/advisory domains may not need it.

**Reference**: `vitruvyan_core/domains/finance/neural_engine/` (ticker scoring with 30+ features, 6 profiles)
