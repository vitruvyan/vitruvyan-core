# Vertical Domain

> Focus: cosa creare dentro `vitruvyan_core/domains/<domain>/`
> Canonical technical details: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [Perche partire dal domain](#perche-partire-dal-domain)
2. [Struttura minima](#struttura-minima)
3. [Struttura produzione](#struttura-produzione)
4. [Dove vanno i nodi di dominio](#dove-vanno-i-nodi-di-dominio)
5. [Template pratico (domain security)](#template-pratico-domain-security)
6. [Checklist rapida](#checklist-rapida)

## Perche partire dal domain

La verticalizzazione non parte da LangGraph o dai Sacred Orders.
Parte dal pacchetto di dominio.

Se il dominio e chiaro e contrattualizzato, il wiring tecnico diventa meccanico.

## Struttura minima

Minimo per avere un dominio caricabile sugli intent:

```text
vitruvyan_core/domains/<domain>/
  __init__.py
  intent_config.py
```

`intent_config.py` deve esporre:

- `create_<domain>_registry()`

Opzionale ma utile fin da subito:

- `CONTEXT_KEYWORDS`
- `AMBIGUOUS_PATTERNS`

Contract-first:

- riferimento obbligatorio: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`

## Struttura produzione

MUST (contract V1):

- `intent_config.py`
- `README.md`
- `vertical_manifest.yaml`
- test di conformita

SHOULD (baseline contract):

- `graph_plugin.py`
- `governance_rules.py`
- `slot_filler.py` (legacy; non piu parte del percorso core LangGraph attivo)
- `response_formatter.py`
- integration test

SHOULD (runtime hooks attuali):

- `entity_resolver_config.py`
- `execution_config.py`
- `graph_nodes/registry.py` (hook opzionale per estendere il grafo)

Per dettagli su loader, env e status wiring:

- `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`
- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## Dove vanno i nodi di dominio

La logica domain-specific non va implementata nei file nodo core del grafo.

- Non aggiungere logica di dominio in `vitruvyan_core/core/orchestration/langgraph/node/` salvo modifiche davvero domain-agnostic.
- Implementa il dominio in `vitruvyan_core/domains/<domain>/...`.
- Nel runtime corrente, la logica dominio si aggancia tipicamente via hook (`intent_config.py`, `entity_resolver_config.py`, `execution_config.py`) usati dai nodi core.

## Template pratico (domain security)

Esempio esattamente nel formato operativo richiesto.

### Domain security: files da implementare

- `vitruvyan_core/domains/security/intent_config.py`
- `vitruvyan_core/domains/security/README.md`
- `vitruvyan_core/domains/security/vertical_manifest.yaml`
- `tests/verticals/test_security_vertical.py`

### Graph / orchestrazione: files da implementare

- `vitruvyan_core/domains/security/entity_resolver_config.py`
- `vitruvyan_core/domains/security/execution_config.py`
- `vitruvyan_core/domains/security/graph_nodes/registry.py` (opzionale)
- startup wiring nel servizio (registrazione handler)

Nota:

- questi sono moduli hook di dominio, non nuovi file nodo core del grafo.

### Sacred Orders: files da implementare (in base ai bisogni)

- Orthodoxy: `vitruvyan_core/domains/security/governance_rules.py`
- Babel: `signals_security.yaml` + eventuale plugin service-level
- Pattern Weavers: taxonomy YAML + wiring startup config
- Codex: domain pack/config YAML + eventuale routing plugin
- Neural: `data_provider.py` + `scoring_strategy.py` (contratti)

## Checklist rapida

- Hai `create_<domain>_registry()` in `intent_config.py`.
- Hai manifesto compilato con ownership + compatibility.
- Hai test minimi di load e conformance.
- Hai deciso quali Sacred Orders servono davvero al dominio.
- Hai marcato in modo esplicito cio che e `ACTIVE` vs `EXPERIMENTAL` vs `PLANNED`.
