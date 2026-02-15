# Codex Hunters

> **Last Updated**: February 15, 2026

## What it does

- Discovers/validates entities from sources and turns payloads into canonical domain objects
- Normalizes and quality-scores data before persistence
- Binds entities for storage (dedupe keys + storage refs; service executes I/O)

- **Epistemic Layer**: Perception (Data Acquisition / Canonicalization)
- **Mandate**: acquire raw knowledge from sources and normalize it into canonical records
- **Verticalization**: domain pack binds `entity_id`, sources, and stream namespace

## Start here

The authoritative component README (code-co-located) is:

- `vitruvyan_core/core/governance/codex_hunters/README.md`

Finance pilot “domain pack”:

- `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## Interfaces

### Service (LIVELLO 2)
- `services/api_codex_hunters/` — API + adapters + Streams listener

### Orchestration hook (finance)
- `vitruvyan_core/domains/finance/graph_plugin.py` routes to `codex_expedition` when discovery is required.

## Verticalization (finance pilot)

Concrete artifacts:

- Config: `examples/verticals/finance/config/codex_hunters_finance.yaml`
- Normalizer example: `examples/verticals/finance/codex_hunters_domain_pack.py`
