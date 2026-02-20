# Vertical Orchestration (LangGraph)

> Focus: wiring runtime tramite env var + import dinamici + registry
> Canonical matrix/status: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [Flusso mentale semplice](#flusso-mentale-semplice)
2. [INTENT_DOMAIN](#intent_domain)
3. [ENTITY_DOMAIN](#entity_domain)
4. [EXEC_DOMAIN](#exec_domain)
5. [GRAPH_DOMAIN (hook `graph_nodes`)](#graph_domain-hook-graph_nodes)
6. [Dove implementare i nodi di dominio](#dove-implementare-i-nodi-di-dominio)
7. [Attivazione completa (checklist)](#attivazione-completa-checklist)
8. [Stato GraphPlugin](#stato-graphplugin)

## Flusso mentale semplice

In orchestrazione hai tre hook reali:

1. `INTENT_DOMAIN` decide quale registry intent caricare.
2. `ENTITY_DOMAIN` decide quale entity resolver registrare/usare.
3. `EXEC_DOMAIN` decide quale execution handler chiamare.

Il core resta invariato; cambi solo pacchetto dominio + startup wiring.

## INTENT_DOMAIN

Loader:

- `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`

Comportamento:

- importa `domains.<domain>.intent_config`
- cerca `create_<domain>_registry()`
- configura `intent_detection_node` e `route_node`
- fallback su generic se import/factory fallisce

Status:

- `ACTIVE`

## ENTITY_DOMAIN

Loader/registration:

- `graph_flow.py` importa `domains.<domain>.entity_resolver_config`
- chiama `register_<domain>_entity_resolver()`

Execution point:

- `vitruvyan_core/core/orchestration/langgraph/node/entity_resolver_node.py`
- usa `ENTITY_DOMAIN` + `EntityResolverRegistry`

Status:

- `ACTIVE`

Nota pratica:

- imposta `ENTITY_DOMAIN` esplicitamente.
- la registrazione in `graph_flow.py` puo usare default da `INTENT_DOMAIN`, ma il nodo esecutivo legge `ENTITY_DOMAIN` direttamente.

## EXEC_DOMAIN

Execution point:

- `vitruvyan_core/core/orchestration/langgraph/node/exec_node.py`
- usa `ExecutionRegistry` + `EXEC_DOMAIN`

Wiring reale:

- handler non auto-loadato da `graph_flow.py`
- va registrato a startup servizio (pattern documentato in `services/api_graph/README.md`)

Status:

- `EXPERIMENTAL` (hook implementato, wiring manuale richiesto)

Pattern startup:

```python
import os
from domains.<domain>.execution_config import register_<domain>_execution_handler

if os.getenv("EXEC_DOMAIN") == "<domain>":
    register_<domain>_execution_handler()
```

## GRAPH_DOMAIN (hook `graph_nodes`)

Loader:

- `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- env var: `GRAPH_DOMAIN` (default a `INTENT_DOMAIN`)

Contratto modulo atteso:

- modulo: `domains.<domain>.graph_nodes.registry`
- factory richiesta:
  - `get_<domain>_graph_nodes() -> Dict[str, Callable]`
- factory opzionali:
  - `get_<domain>_graph_edges() -> List[Tuple[str, str]]`
  - `get_<domain>_route_targets() -> Dict[str, str]`

Comportamento:

- se modulo/factory manca, il grafo usa solo nodi/route core (fallback sicuro)
- l'estensione non puo sovrascrivere nomi di nodi core esistenti

Status:

- `EXPERIMENTAL`

## Dove implementare i nodi di dominio

Regola contract-first nel repo attuale:

- i nodi core in `vitruvyan_core/core/orchestration/langgraph/node/` restano domain-agnostic.
- il comportamento di dominio si implementa in `vitruvyan_core/domains/<domain>/...`.
- i nodi core (`intent_detection_node`, `entity_resolver_node`, `exec_node`) richiamano logica dominio via hook/registry.

Modifica o aggiungi file in `core/.../langgraph/node/` solo quando il comportamento e generico per tutti i domini.

## Attivazione completa (checklist)

```bash
export INTENT_DOMAIN=<domain>
export ENTITY_DOMAIN=<domain>
export EXEC_DOMAIN=<domain>
```

Poi:

1. registra execution handler nello startup del servizio.
2. riavvia `api_graph`.
3. verifica logs: niente fallback generic non attesi.

## Stato GraphPlugin

`graph_plugin.py` esiste come pattern (esempio finance), ma nel `graph_flow.py` corrente non c'e un auto-loader globale del contratto `GraphPlugin` completo.

Status operativo:

- `PLANNED/EXPERIMENTAL` per il caricamento automatico globale di `GraphPlugin`.
- usa oggi gli hook concreti `INTENT_DOMAIN` / `ENTITY_DOMAIN` / `EXEC_DOMAIN` / `GRAPH_DOMAIN` (estensione `graph_nodes`).
