# Babel Gardens

## A cosa serve

- Estrae segnali semantici strutturati dal testo (con confidence + tracciabilità)
- Produce embedding/feature consumabili in sicurezza dai downstream
- Espone un boundary pulito via eventi/API (il service esegue l’I/O)

- **Livello epistemico**: Perception (Linguistic Processing / Signal Extraction)
- **Mandato**: trasformare testo non strutturato in **segnali semantici strutturati e spiegabili**
- **Verticalizzazione**: segnali YAML + plugin opzionali

## Charter (Mandato + Non-goals)

### Mandato
Estrarre segnali ancorati al testo ed utilizzabili downstream (Neural Engine, Orthodoxy, Vault).

### Non-goals
- Non è un decision engine (no scoring/ranking).
- Non è un taxonomy engine (ontology → Pattern Weavers).

## Interfacce

### Contratto eventi (Cognitive Bus)
Definiti in `vitruvyan_core/core/cognitive/babel_gardens/events/__init__.py` (estratto):

- `babel.embedding.request` → `babel.embedding.response`
- `babel.sentiment.request` → `babel.sentiment.response`
- `babel.synthesis.request` → `babel.synthesis.response`
- `babel.error`

### Servizio (LIVELLO 2)
- `services/api_babel_gardens/`

## Pipeline (happy path)

1. Testo → (opzionale) language detection
2. Inference modello/plugin → valori + confidence
3. Emissione risultati con trace di explainability

## Mappa codice

### LIVELLO 1 (pure)
- `vitruvyan_core/core/cognitive/babel_gardens/domain/`
- `vitruvyan_core/core/cognitive/babel_gardens/consumers/`

### LIVELLO 2 (adapters)
- `services/api_babel_gardens/plugins/`

## Verticalizzazione (pilota finanza)

Finanza definisce i segnali in YAML e (se serve) un plugin di inferenza; la schema dei segnali vive nel domain pack, non nel core.

## Comprehension Engine v3

Con `BABEL_COMPREHENSION_V3=1`, Babel Gardens acquisisce una pipeline di comprensione unificata che produce sia segnali semantici (`SemanticPayload`) che struttura ontologica (`OntologyPayload`) in una **singola chiamata LLM**.

### Nuovi endpoint
- `POST /v2/comprehend` — comprensione completa (ontologia + semantica)
- `POST /v2/fuse` — fusione segnali multi-sorgente (LLM + modelli dominio)

### Architettura a 3 livelli
- **L1**: Comprensione LLM → `ComprehensionResult` (ontologia + semantica)
- **L2**: Modelli di dominio (es. FinBERT) → `SignalEvidence[]`
- **L3**: Fusione segnali (weighted/bayesian/LLM-arbitrated) → `FusionResult`

### Sistema plugin
- `IComprehensionPlugin` — modellazione prompt a livello di dominio (sezioni ontologia + semantica)
- `ISignalContributor` — contributi modelli specifici di dominio (lazy-loaded, verifica disponibilità)

Per la filosofia architetturale completa, vedi [Architettura Semantica & Ontologica](../architecture/SEMANTIC_ONTOLOGY_ARCHITECTURE.it.md).
