# Vertical Domain

> Focus: what to create under `vitruvyan_core/domains/<domain>/`  
> Canonical technical details: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [Why start from the domain package](#why-start-from-the-domain-package)
2. [Minimal structure](#minimal-structure)
3. [Production structure](#production-structure)
4. [Where domain nodes belong](#where-domain-nodes-belong)
5. [Practical template (security domain)](#practical-template-security-domain)
6. [Quick checklist](#quick-checklist)

## Why start from the domain package

Verticalization should not start from LangGraph or Sacred Orders.  
It starts from the domain package.

If domain scope and contracts are clear, technical wiring becomes straightforward.

## Minimal structure

Minimum required to load domain intents:

```text
vitruvyan_core/domains/<domain>/
  __init__.py
  intent_config.py
```

`intent_config.py` must expose:

- `create_<domain>_registry()`

Optional but recommended from day one:

- `CONTEXT_KEYWORDS`
- `AMBIGUOUS_PATTERNS`

Contract-first reference:

- `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`

## Production structure

MUST (contract V1):

- `intent_config.py`
- `README.md`
- `vertical_manifest.yaml`
- conformance tests

SHOULD (contract baseline):

- `graph_plugin.py`
- `governance_rules.py`
- `slot_filler.py` (legacy; no longer part of active core LangGraph path)
- `response_formatter.py`
- integration tests

SHOULD (current runtime hooks):

- `entity_resolver_config.py`
- `execution_config.py`
- `graph_nodes/registry.py` (optional graph extension hook)

For loader/env/status details:

- `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`
- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## Where domain nodes belong

Domain-specific logic must not be implemented inside core graph node files.

- Do not add domain logic under `vitruvyan_core/core/orchestration/langgraph/node/` unless the change is truly domain-agnostic core behavior.
- Implement domain behavior under `vitruvyan_core/domains/<domain>/...`.
- In current runtime, domain logic is typically attached through hook modules (`intent_config.py`, `entity_resolver_config.py`, `execution_config.py`) consumed by core nodes.

## Practical template (security domain)

Operational template in the exact “files to implement” style.

### Security domain: files to implement

- `vitruvyan_core/domains/security/intent_config.py`
- `vitruvyan_core/domains/security/README.md`
- `vitruvyan_core/domains/security/vertical_manifest.yaml`
- `tests/verticals/test_security_vertical.py`

### Graph / orchestration: files to implement

- `vitruvyan_core/domains/security/entity_resolver_config.py`
- `vitruvyan_core/domains/security/execution_config.py`
- `vitruvyan_core/domains/security/graph_nodes/registry.py` (optional)
- startup wiring in service entrypoint (handler registration)

Note:

- these are domain hook modules, not new core graph node files.

### Sacred Orders: files to implement (based on needs)

- Orthodoxy: `vitruvyan_core/domains/security/governance_rules.py`
- Babel: `signals_security.yaml` + optional service-level plugin
- Pattern Weavers: taxonomy YAML + startup config wiring
- Codex: domain pack/config YAML + optional routing plugin
- Neural: `data_provider.py` + `scoring_strategy.py` (contracts)

## Quick checklist

- `create_<domain>_registry()` exists in `intent_config.py`.
- Manifest is filled with ownership + compatibility.
- Minimum load/conformance tests are present.
- Only required Sacred Orders are enabled.
- Every capability is explicitly marked `ACTIVE` vs `EXPERIMENTAL` vs `PLANNED`.
