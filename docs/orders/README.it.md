# Sacred Orders — Indice Documentazione

Queste pagine documentano i **Sacred Orders** di Vitruvyan OS come componenti production:

- **Cosa fa** l’ordine (mandato) e **cosa non deve fare** (confini)
- **Interfacce** (eventi, API) e contratti di integrazione
- **Mappa del codice** (LIVELLO 1 vs LIVELLO 2) per onboarding rapido
- **Verticalizzazione**: come un dominio (es. finanza) si innesta senza contaminare il core

## Ordini

1. [Memory Orders](MEMORY_ORDERS.md) — Coerenza dual-memory & pianificazione sync (PostgreSQL ↔ Qdrant)
2. [Vault Keepers](VAULT_KEEPERS.md) — Integrità, backup/recovery, archival
3. [Orthodoxy Wardens](ORTHODOXY_WARDENS.md) — Tribunale epistemico (validazione, verdetti, audit)
4. [Babel Gardens](BABEL_GARDENS.md) — Estrazione segnali semantici (YAML-driven)
5. [Codex Hunters](CODEX_HUNTERS.md) — Acquisizione dati & canonicalizzazione (domain-agnostic)
6. [Pattern Weavers](PATTERN_WEAVERS.md) — Risoluzione ontologica / contesto semantico (YAML-driven)

## Percorso di lettura (consigliato)

1) Babel Gardens → 2) Pattern Weavers → 3) Codex Hunters → 4) Memory Orders → 5) Vault Keepers → 6) Orthodoxy Wardens

