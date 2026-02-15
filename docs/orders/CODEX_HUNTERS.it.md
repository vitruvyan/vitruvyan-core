# Codex Hunters

## A cosa serve

- Esegue discovery/validazione da sorgenti e trasforma payload in oggetti canonici
- Normalizza e assegna segnali di qualità prima della persistenza
- Prepara il binding per lo storage (dedupe keys + storage refs; il service esegue l’I/O)

- **Livello epistemico**: Perception (Data Acquisition / Canonicalization)
- **Mandato**: acquisire dati da sorgenti e normalizzarli in record canonici
- **Verticalizzazione**: il domain pack lega `entity_id`, sorgenti e namespace streams

## Da dove partire

README canonico (co-locato al codice):

- `vitruvyan_core/core/governance/codex_hunters/README.md`

Domain pack pilota finanza:

- `examples/verticals/finance/CODEX_HUNTERS_DOMAIN_PACK.md`

## Interfacce

### Servizio (LIVELLO 2)
- `services/api_codex_hunters/`

### Hook orchestrazione (finanza)
- `vitruvyan_core/domains/finance/graph_plugin.py` instrada su `codex_expedition` in modalità discovery.

## Verticalizzazione (pilota finanza)

Artefatti:

- Config: `examples/verticals/finance/config/codex_hunters_finance.yaml`
- Esempio normalizer: `examples/verticals/finance/codex_hunters_domain_pack.py`
