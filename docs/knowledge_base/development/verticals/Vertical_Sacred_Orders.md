# Vertical Sacred Orders

> Focus: real verticalization impact across Sacred Orders  
> Rule: document only what is verifiable in this repo

## TOC

1. [Simple view](#simple-view)
2. [Orthodoxy Wardens](#orthodoxy-wardens)
3. [Vault Keepers](#vault-keepers)
4. [Babel Gardens](#babel-gardens)
5. [Pattern Weavers](#pattern-weavers)
6. [Codex Hunters](#codex-hunters)
7. [Neural Engine](#neural-engine)
8. [Recommended rollout sequence for a new domain](#recommended-rollout-sequence-for-a-new-domain)

## Simple view

You do not need to modify all orders at once.

For each domain:

1. enable LangGraph hooks first (intent/entity/exec),
2. then enable only the required orders,
3. mark each capability with actual status: `ACTIVE`, `EXPERIMENTAL`, `PLANNED`.

## Orthodoxy Wardens

Real hook:

- `domains.<domain>.governance_rules`
- required function: `get_domain_rules()`
- loader: `GovernanceRuleRegistry.register_domain(domain)`

References:

- `vitruvyan_core/core/governance/orthodoxy_wardens/governance/rule_registry.py`
- `vitruvyan_core/domains/finance/governance_rules.py`

Status:

- `EXPERIMENTAL`

Why:

- hook is implemented in core
- default service startup does not register domain rules
- `GOVERNANCE_DOMAIN` appears in comments/docs but no startup wiring is currently in place

## Vault Keepers

Verified capability:

- domain-agnostic `signal_timeseries` archive/query with explicit `vertical` field
- adapter methods:
  - `handle_signal_timeseries_archival(...)`
  - `query_signal_timeseries(...)`

References:

- `services/api_vault_keepers/adapters/bus_adapter.py`
- `services/api_vault_keepers/adapters/persistence.py`
- `vitruvyan_core/core/governance/vault_keepers/domain/signal_archive.py`

Status:

- `ACTIVE` at adapter/internal flow level
- `PLANNED` for dedicated HTTP endpoints (not present in `services/api_vault_keepers/api/routes.py`)

LangGraph note:

- `vault_node.py` supports `state["_domain_config"]["vault_keywords"]`.
- automatic injection of that config via a global plugin loader is not wired in current `graph_flow.py`.

## Babel Gardens

Signals YAML contract:

- loader: `load_config_from_yaml(signals_path, taxonomy_path=None)`
- contract file: `vitruvyan_core/core/cognitive/babel_gardens/domain/signal_schema.py`

Service-level plugin pattern:

- finance example: `services/api_babel_gardens/plugins/finance_signals.py`

Status:

- `EXPERIMENTAL`

Why:

- YAML contract + plugin example exist
- no single automatic domain/plugin/config loader is wired in API startup

## Pattern Weavers

Existing config hook:

- domain config supports `PATTERN_TAXONOMY_PATH` via `PatternConfig.from_env()`
- service config also reads `PATTERN_TAXONOMY_PATH`

References:

- `vitruvyan_core/core/cognitive/pattern_weavers/domain/config.py`
- `services/api_pattern_weavers/config.py`

Status:

- `PLANNED`

Why:

- current service startup does not build and inject `PatternConfig.from_env()` into domain config via `set_config(...)`

## Codex Hunters

Available domain pattern:

- finance domain pack documented in `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`
- domain-agnostic config object: `CodexConfig` with `from_yaml(...)`

References:

- `vitruvyan_core/core/governance/codex_hunters/domain/config.py`
- `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

Status:

- `EXPERIMENTAL`

Why:

- pattern and components exist
- no automatic domain-pack/config startup wiring is visible in `api_codex_hunters`
- orchestration integration via graph plugin remains manual pattern

## Neural Engine

Real contracts:

- `IDataProvider`
- `IScoringStrategy`

References:

- `vitruvyan_core/contracts/neural_engine/data_provider.py`
- `vitruvyan_core/contracts/neural_engine/scoring_strategy.py`
- `services/api_neural_engine/modules/engine_orchestrator.py`

Status:

- `EXPERIMENTAL` (contracts + injection model are in place)
- `PLANNED` (automatic domain loader in service)

Why:

- API orchestrator currently initializes mock provider/strategy and contains explicit TODO for env-based domain loading

## Recommended rollout sequence for a new domain

1. LangGraph hooks (`intent_config.py`, then entity/exec).
2. Orthodoxy (`governance_rules.py`) only if domain is regulated/sensitive.
3. Babel/Pattern if domain needs signal or taxonomy extensions.
4. Codex/Neural only when advanced discovery or multi-factor ranking is required.

For the single matrix with files/env/wiring/status:

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
