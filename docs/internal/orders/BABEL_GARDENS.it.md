# Babel Gardens

<p class="kb-subtitle">Estrazione testo→segnali: embeddings, sentiment/segnali e output linguistici spiegabili.</p>

## A cosa serve

- Estrae **segnali semantici strutturati** da testo non strutturato (con confidence + tracciabilità)
- Produce embedding e feature model-driven per ordini downstream (Pattern Weavers, Neural Engine, Vault)
- Pubblica eventi ed espone API via LIVELLO 2 (service), mantenendo LIVELLO 1 puro

- **Livello epistemico**: Perception (Linguistic Processing / Semantic Grounding)
- **Mandato**: trasformare testo multilingua in **artefatti strutturati e auditabili** (vettori + segnali)
- **Output**: embedding, segnali sentiment/emozione, topic match, vettori fusi, trace di explainability

## Charter (mandato + non-goals)

### Mandato

- rilevare lingua (o validare l’hint fornito dal chiamante)
- generare embedding semantici (single/batch, multilingua)
- esporre segnali semantici (sentiment/emozione + trace strutturati)
- classificare testo in topic configurabili (tassonomia)
- fondere vettori in modo deterministico quando necessario (synthesis)

### Non-goals

- nessuna decisione di business (no ranking, no risk scoring)
- nessuna risoluzione ontologica di dominio (è di Pattern Weavers)
- nessuna governance storage (è di Vault Keepers / Memory Orders)

## Interfacce

- **HTTP (LIVELLO 2)**: `services/api_babel_gardens/`
  - Embedding: `/v1/embeddings/*`
  - Sentiment: `/v1/sentiment/*`
  - Emotion: `/v1/emotion/detect`
  - Profili + cognitive routing: `/v1/profiles/*`, `/v1/events/*`, `/v1/routing/*`
- **Cognitive Bus (opzionale, LIVELLO 2)**: listener streams + canali eventi

## Contratto eventi (Cognitive Bus)

Definito in `vitruvyan_core/core/cognitive/babel_gardens/events/__init__.py`:

- `babel.embedding.request` / `babel.embedding.response`
- `babel.sentiment.request` / `babel.sentiment.response`
- `babel.emotion.request` / `babel.emotion.response`
- `babel.topic.request` / `babel.topic.response`
- `babel.synthesis.request` / `babel.synthesis.response`
- `babel.error`

## Mappa codice

- **LIVELLO 1 (puro, niente I/O)**: `vitruvyan_core/core/cognitive/babel_gardens/`
  - Config dominio: `domain/config.py` (language + cache + injection tassonomia)
  - Consumer topic + lingua: `consumers/classifiers.py`
  - Consumer fusion vettori: `consumers/synthesis.py`
  - Eventi: `events/__init__.py`
  - Esempi: `examples/*.yaml` (schema segnali verticali)
- **LIVELLO 2 (service + modules + adapters)**: `services/api_babel_gardens/`
  - Embedding engine: `modules/embedding_engine.py`
  - Sentiment fusion: `modules/sentiment_fusion.py`
  - Emotion detection: `modules/emotion_detector.py`
  - Profile processor + cognitive bridge: `modules/profile_processor.py`, `modules/cognitive_bridge.py`
  - Route HTTP: `api/routes_*.py`

## Pipeline (happy path)

1. Il service riceve testo (+ hint lingua opzionale)
2. La lingua viene rilevata/validata (path multilingua)
3. Si genera l’embedding (con cache opzionale)
4. Opzionale: si estraggono segnali sentiment/emozione
5. Opzionale: si fondono vettori (synthesis) per downstream
6. Il risultato torna via HTTP e/o viene emesso sul bus

---

## Consumers (LIVELLO 1)

### `LanguageDetectorConsumer` — detection lingua (euristica)

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/classifiers.py`
- Scopo: detection leggera per mantenere la purezza (gli adapter possono usare ML più robusto)

### `TopicClassifierConsumer` — classificazione tassonomica

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/classifiers.py`
- Scopo: classificare il testo in topic usando tassonomia deploy-time (YAML-driven, domain-agnostic)

### `SynthesisConsumer` — fusion vettoriale

- File: `vitruvyan_core/core/cognitive/babel_gardens/consumers/synthesis.py`
- Scopo: fondere vettori semantici + sentiment in modo deterministico (`semantic_garden_fusion` default)

## Verticalizzazione (dominio pilota: finanza)

Finanza “lega” Babel Gardens fornendo:

- **tassonomia topic** (keyword/categorie) via injection YAML
- **schema segnali** (primitivi domain-agnostic): `vitruvyan_core/core/cognitive/babel_gardens/examples/signals_finance.yaml`
- plugin opzionali del service: `services/api_babel_gardens/plugins/finance_signals.py`

Regola: la **schema/config vive nel verticale**, non nel core di Babel Gardens.
