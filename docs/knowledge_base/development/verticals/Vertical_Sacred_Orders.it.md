# Vertical Sacred Orders

> Focus: impatto reale della verticalizzazione sui Sacred Orders
> Regola: documentare solo cio che e verificato nel repo

## TOC

1. [Visione semplice](#visione-semplice)
2. [Orthodoxy Wardens](#orthodoxy-wardens)
3. [Vault Keepers](#vault-keepers)
4. [Babel Gardens](#babel-gardens)
5. [Pattern Weavers](#pattern-weavers)
6. [Codex Hunters](#codex-hunters)
7. [Neural Engine](#neural-engine)
8. [Sequenza consigliata per un nuovo dominio](#sequenza-consigliata-per-un-nuovo-dominio)

## Visione semplice

Verticalizzare non significa toccare tutti gli ordini subito.

Per ogni dominio:

1. attivi prima LangGraph (intent/entity/exec),
2. poi abiliti solo gli ordini necessari,
3. per ogni ordine dichiari lo stato reale: `ACTIVE`, `EXPERIMENTAL`, `PLANNED`.

## Orthodoxy Wardens

Hook reale:

- `domains.<domain>.governance_rules`
- funzione richiesta: `get_domain_rules()`
- loader: `GovernanceRuleRegistry.register_domain(domain)`

Riferimenti:

- `vitruvyan_core/core/governance/orthodoxy_wardens/governance/rule_registry.py`
- `vitruvyan_core/domains/finance/governance_rules.py`

Stato:

- `EXPERIMENTAL`

Perche:

- hook implementato a livello core
- startup di default non registra il dominio
- `GOVERNANCE_DOMAIN` citato in alcuni testi/commenti ma non wired in startup runtime

## Vault Keepers

Capacita reale verificata:

- archiviazione/query `signal_timeseries` domain-agnostic con campo `vertical`
- metodi adapter:
  - `handle_signal_timeseries_archival(...)`
  - `query_signal_timeseries(...)`

Riferimenti:

- `services/api_vault_keepers/adapters/bus_adapter.py`
- `services/api_vault_keepers/adapters/persistence.py`
- `vitruvyan_core/core/governance/vault_keepers/domain/signal_archive.py`

Stato:

- `ACTIVE` a livello adapter interno
- `PLANNED` per endpoint HTTP dedicati (non presenti in `services/api_vault_keepers/api/routes.py`)

Nota LangGraph:

- `vault_node.py` supporta `state["_domain_config"]["vault_keywords"]`.
- l'iniezione automatica di questa config via plugin globale non risulta wired nel `graph_flow` corrente.

## Babel Gardens

Contratto YAML segnali:

- loader: `load_config_from_yaml(signals_path, taxonomy_path=None)`
- file contratto: `vitruvyan_core/core/cognitive/babel_gardens/domain/signal_schema.py`

Pattern plugin service-level:

- esempio finance: `services/api_babel_gardens/plugins/finance_signals.py`

Stato:

- `EXPERIMENTAL`

Perche:

- contratto YAML e plugin example esistono
- non c'e un auto-loader dominio unico in startup API per selezionare plugin + config path in modo centralizzato

## Pattern Weavers

Hook di configurazione esistente:

- domain config supporta `PATTERN_TAXONOMY_PATH` via `PatternConfig.from_env()`
- service config legge anche `PATTERN_TAXONOMY_PATH`

Riferimenti:

- `vitruvyan_core/core/cognitive/pattern_weavers/domain/config.py`
- `services/api_pattern_weavers/config.py`

Stato:

- `PLANNED`

Perche:

- nel servizio corrente non risulta wiring startup che costruisce `PatternConfig.from_env()` e lo inietta nel domain layer con `set_config(...)`

## Codex Hunters

Pattern dominio disponibile:

- domain pack finance documentato in `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`
- config domain-agnostic: `CodexConfig` con `from_yaml(...)`

Riferimenti:

- `vitruvyan_core/core/governance/codex_hunters/domain/config.py`
- `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

Stato:

- `EXPERIMENTAL`

Perche:

- pattern e componenti ci sono
- non risulta auto-wiring startup del domain pack/config nel servizio `api_codex_hunters`
- integrazione orchestrazione via graph plugin resta pattern manuale

## Neural Engine

Contratti reali:

- `IDataProvider`
- `IScoringStrategy`

Riferimenti:

- `vitruvyan_core/contracts/neural_engine/data_provider.py`
- `vitruvyan_core/contracts/neural_engine/scoring_strategy.py`
- `services/api_neural_engine/modules/engine_orchestrator.py`

Stato:

- `EXPERIMENTAL` (contratti e injection core)
- `PLANNED` (domain loading automatico nel servizio)

Perche:

- l'orchestrator API usa mock provider/strategy e contiene TODO esplicito per loader dominio da env

## Sequenza consigliata per un nuovo dominio

1. LangGraph hooks (`intent_config.py`, poi entity/exec).
2. Orthodoxy (`governance_rules.py`) solo se dominio regolato/sensibile.
3. Babel/Pattern se servono segnali o taxonomy verticale.
4. Codex/Neural solo se il dominio richiede discovery avanzata o ranking multi-fattore.

Per la matrice unica con file/env/wiring/status:

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
