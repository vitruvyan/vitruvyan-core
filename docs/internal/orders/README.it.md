# Sacred Orders (Admin)

Questa sezione è la vista **interna** (admin) dei Sacred Orders: note di implementazione, mappa del codice, responsabilità per-agente e comportamento operativo.

!!! note "Pubblico vs admin"
    La documentazione pubblica descrive i concetti.  
    La documentazione admin descrive *come funziona nel codice*.

## Ordini

- **Codex Hunters** — discovery → normalizzazione → binding (sorgenti → entità canoniche)
- **Orthodoxy Wardens** — governance epistemica (confessione → findings → verdetto)
- **Vault Keepers** — archiviazione, integrità, pianificazione backup/restore e audit trail
- **Memory Orders** — integrità di coerenza Postgres ↔ Qdrant (drift, health, sync planning)
- **Babel Gardens** — testo → segnali semantici strutturati (embeddings, sentiment/segnali, explainability)
- **Pattern Weavers** — risoluzione ontologica/tassonomica (weave semantico + fallback keyword)

Alcune pagine potrebbero essere ancora in espansione (soprattutto Babel Gardens in refactor), ma il riassunto in testa ad ogni pagina è il punto di partenza stabile.
