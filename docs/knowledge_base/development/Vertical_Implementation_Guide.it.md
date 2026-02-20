# Vertical Implementation Guide (Overview)

> **Status**: Canonical entrypoint  
> **Audience**: developers who must implement a new vertical without touching core internals  
> **Read this first**, then go to topic pages.

## TOC

1. [Perche questa guida](#perche-questa-guida)
2. [Verticalizzare senza spaventarsi](#verticalizzare-senza-spaventarsi)
3. [Le 4 aree della verticalizzazione](#le-4-aree-della-verticalizzazione)
4. [Percorso consigliato di lettura](#percorso-consigliato-di-lettura)
5. [Contratti vincolanti](#contratti-vincolanti)

## Perche questa guida

Questa pagina e l'entrypoint unico per capire **come ragionare** sulla verticalizzazione.

La regola chiave rimane contract-first:

- il core resta domain-agnostic
- la verticale entra tramite hook/registry/adapters
- il rilascio passa da manifest + checklist di conformita

## Verticalizzare senza spaventarsi

In pratica una verticale non significa riscrivere il sistema.  
Significa aggiungere un pacchetto `vitruvyan_core/domains/<domain>/` e poi collegarlo dove serve.

Il lavoro reale si distribuisce in poche aree:

1. definisci il **dominio** (intenti/config/file contrattuali)
2. fai il **wiring in orchestrazione LangGraph** (env var + import dinamici + registrazioni)
3. abiliti i **Sacred Orders** che ti servono (governance/signals/taxonomy/domain pack)
4. usi i **pattern/esempi** solo come riferimento, non come guida normativa

In pratica: le aree operative obbligatorie sono 3 (`domain`, `langgraph`, `sacred orders`), mentre `pattern` serve per accelerare ma non sostituisce i contratti.

## Le 4 aree della verticalizzazione

### 1) Domain

Qui vivi nel tuo pacchetto `vitruvyan_core/domains/<domain>/`: intent, manifest, test, e componenti opzionali (entity resolver, execution handler, governance rules, ecc.).

- Pagina: `docs/knowledge_base/development/verticals/Vertical_Domain.md`

### 2) Orchestrazione (LangGraph)

Qui colleghi la verticale al runtime (`INTENT_DOMAIN`, `ENTITY_DOMAIN`, `EXEC_DOMAIN`, opzionale `GRAPH_DOMAIN`) e verifichi cosa e auto-load vs manual wiring.

Confine importante: i nodi graph domain-specific non vivono in `vitruvyan_core/core/orchestration/langgraph/node/`; vivono in `vitruvyan_core/domains/<domain>/graph_nodes/registry.py` e vengono caricati come hook.

- Pagina: `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`

### 3) Sacred Orders

Qui valuti impatto per ordine (Orthodoxy, Vault, Babel, Pattern Weavers, Codex, Neural) e dichiari chiaramente cosa e ACTIVE vs EXPERIMENTAL vs PLANNED.

- Pagina: `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`

### 4) Pattern

Qui trovi pattern/esempi riusabili. Non sostituisce le regole implementative.

- Pagina: `docs/knowledge_base/development/verticals/Vertical_Patterns.md`
- Esempi: `examples/verticals/README.md`

## Percorso consigliato di lettura

Per un dev nuovo:

1. questa pagina (overview)
2. `docs/knowledge_base/development/verticals/Vertical_Domain.md`
3. `docs/knowledge_base/development/verticals/Vertical_Orchestration_LangGraph.md`
4. `docs/knowledge_base/development/verticals/Vertical_Sacred_Orders.md`
5. `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## Contratti vincolanti

Riferimenti normativi:

- `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md`
- `docs/contracts/verticals/VERTICAL_CONFORMANCE_CHECKLIST.md`
- `docs/contracts/verticals/templates/vertical_manifest.yaml`
- `docs/contracts/verticals/schema/vertical_manifest.schema.json`

Riferimento tecnico centralizzato (matrice, status, troubleshooting):

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
