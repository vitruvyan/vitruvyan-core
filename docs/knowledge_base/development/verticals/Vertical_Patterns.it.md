# Vertical Patterns

> Focus: esempi e pattern riusabili (non regole normative)
> Source of truth implementativa: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`

## TOC

1. [Cosa e un pattern qui](#cosa-e-un-pattern-qui)
2. [Dove trovare i pattern](#dove-trovare-i-pattern)
3. [Come usare un pattern senza copiare errori](#come-usare-un-pattern-senza-copiare-errori)
4. [Schema operativo "files da implementare"](#schema-operativo-files-da-implementare)

## Cosa e un pattern qui

Un pattern e un esempio di struttura o integrazione.

Non sostituisce:

- i contratti verticali V1
- la checklist di conformita
- il wiring reale dei servizi

## Dove trovare i pattern

- Panoramica esempi: `examples/verticals/README.md`
- Domain pack Codex (finance): `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`
- Pattern notes contrattuali: `docs/contracts/verticals/pattern.md`

## Come usare un pattern senza copiare errori

1. Parti dai contratti (`VERTICAL_CONTRACT_V1`, checklist, manifest template).
2. Prendi dal pattern solo struttura e naming.
3. Verifica wiring reale su LangGraph/servizi prima di dichiarare "ACTIVE".
4. Marca sempre gli elementi non cablati come `PLANNED` o `EXPERIMENTAL`.

## Schema operativo "files da implementare"

Formato consigliato (semplice per onboarding):

### Domain `<domain>`

- `vitruvyan_core/domains/<domain>/intent_config.py`
- `vitruvyan_core/domains/<domain>/README.md`
- `vitruvyan_core/domains/<domain>/vertical_manifest.yaml`

### Graph / Orchestrazione

- `vitruvyan_core/domains/<domain>/entity_resolver_config.py`
- `vitruvyan_core/domains/<domain>/execution_config.py`
- startup registration nel servizio orchestrator

### Sacred Orders (solo quelli necessari)

- Orthodoxy: `vitruvyan_core/domains/<domain>/governance_rules.py`
- Babel: `signals_<domain>.yaml` (+ eventuale plugin service-level)
- Pattern Weavers: taxonomy YAML + wiring config
- Codex: domain pack/config
- Neural: provider/strategy contrattuali

Per file map completa, env, loader e status ufficiali:

- `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`
