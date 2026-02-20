# Vertical Contract V1

Status: draft
Version: 1.0.0
Last Updated: 2026-02-18
Owner: Vitruvyan Core Architecture

## 1. Purpose

This contract defines the mandatory pattern for creating and operating domain verticals in Vitruvyan.

Normative terms use RFC 2119 semantics:
- MUST / MUST NOT
- SHOULD / SHOULD NOT
- MAY

## 2. Scope

This contract applies to any new or migrated vertical under `vitruvyan_core/domains/<domain_name>/`.

This contract does not redefine core behavior; it constrains how vertical logic integrates with the domain-agnostic core.

## 3. Core Boundary

1. Vertical implementations MUST NOT inject domain logic into core internals.
2. Sacred Orders MUST remain domain-agnostic; vertical behavior MUST be introduced through adapters/config hooks.
3. LangGraph base pipeline MUST remain domain-agnostic; vertical extensions MUST use plugin contracts.
4. Neural Engine core MUST remain domain-agnostic; domain scoring/data logic MUST implement contracts.

## 4. Required Artifacts

Each vertical MUST provide:
1. `intent_config.py`
2. `README.md`
3. `vertical_manifest.yaml` (from template)
4. Unit tests for vertical contracts

Each vertical SHOULD provide (production baseline):
1. `graph_plugin.py`
2. `governance_rules.py`
3. `slot_filler.py`
4. `response_formatter.py`
5. `graph_nodes/` (domain graph node pack, if custom graph routing/nodes are needed)
6. Integration tests

## 5. Mandatory Contracts

Verticals MUST integrate through the canonical contracts namespace:
- `contracts` / `vitruvyan_core.contracts`

When applicable, vertical components MUST implement:
1. `GraphPlugin`
2. `Parser` / `BaseParser`
3. `SlotFiller`
4. `ResponseFormatter`
5. Neural Engine interfaces (`IDataProvider`, `IScoringStrategy`) when using neural scoring flows

Direct imports from deprecated/legacy contract namespaces MUST NOT be introduced.

## 6. Domain Registration

1. Vertical loading MUST be controlled through environment selection (`INTENT_DOMAIN`, `ENTITY_DOMAIN`, `EXEC_DOMAIN`).
2. Optional graph extension loading MAY be controlled through `GRAPH_DOMAIN` (defaults to `INTENT_DOMAIN` in current implementation).
3. Vertical modules MUST expose expected factory functions:
   - `create_<domain>_registry` (intent registry)
   - optional graph node factories in `domains.<domain>.graph_nodes.registry`:
     - `get_<domain>_graph_nodes()`
     - `get_<domain>_graph_edges()` (optional)
     - `get_<domain>_route_targets()` (optional)
4. If dynamic import fails, runtime MUST preserve core fallback behavior.

## 7. Governance and Safety

1. Vertical outputs in regulated/sensitive contexts SHOULD define explicit governance rules.
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

Production gate (SHOULD):
1. Integration test through graph route
2. Governance behavior tests
3. Negative tests for invalid inputs

## 10. Manifest and Compliance

Each vertical MUST include `vertical_manifest.yaml` with:
1. `domain_name`
2. `contract_version`
3. `required_components`
4. `adapters`
5. `compliance`
6. `ownership`

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
