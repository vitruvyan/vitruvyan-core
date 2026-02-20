# Vertical Patterns

> Focus: reusable examples and patterns (not normative rules)  
> Implementation source of truth: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [What "pattern" means here](#what-pattern-means-here)
2. [Where to find patterns](#where-to-find-patterns)
3. [How to use patterns without copying mistakes](#how-to-use-patterns-without-copying-mistakes)
4. [Operational "files to implement" template](#operational-files-to-implement-template)

## What "pattern" means here

A pattern is an implementation example.

It does not replace:

- vertical contracts V1
- conformance checklist
- real runtime wiring

## Where to find patterns

- Pattern overview: `examples/verticals/README.md`
- Codex domain pack (finance): `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`
- Contract pattern notes: `docs/contracts/verticals/pattern.md`

## How to use patterns without copying mistakes

1. Start from contracts (`VERTICAL_CONTRACT_V1`, checklist, manifest template).
2. Reuse naming and structure from patterns only.
3. Validate real wiring on LangGraph/services before claiming `ACTIVE`.
4. Explicitly mark non-wired parts as `PLANNED` or `EXPERIMENTAL`.

## Operational "files to implement" template

Recommended onboarding format:

### Domain `<domain>`

- `vitruvyan_core/domains/<domain>/intent_config.py`
- `vitruvyan_core/domains/<domain>/README.md`
- `vitruvyan_core/domains/<domain>/vertical_manifest.yaml`

### Graph / Orchestration

- `vitruvyan_core/domains/<domain>/entity_resolver_config.py`
- `vitruvyan_core/domains/<domain>/execution_config.py`
- startup registration in orchestrator service

### Sacred Orders (only as needed)

- Orthodoxy: `vitruvyan_core/domains/<domain>/governance_rules.py`
- Babel: `signals_<domain>.yaml` (+ optional service-level plugin)
- Pattern Weavers: taxonomy YAML + config wiring
- Codex: domain pack/config
- Neural: contract-based provider/strategy implementations

For complete file map, env vars, loaders, and official statuses:

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
