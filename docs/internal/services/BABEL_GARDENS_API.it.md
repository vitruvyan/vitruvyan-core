# Babel Gardens API

<p class="kb-subtitle">Service LIVELLO 2 per semantica multilingua: embedding, segnali sentiment/emozione, profili e routing cognitivo.</p>

## Posizione

- Service: `services/api_babel_gardens/`
- Core puro (LIVELLO 1): `vitruvyan_core/core/cognitive/babel_gardens/`

## Base URL / Port

Port di default **`8009`** (env: `PORT`).

## Endpoint (implementati)

### Health / metriche

- `GET /`
- `GET /health`
- `GET /metrics`

### Embedding

Definiti in `services/api_babel_gardens/api/routes_embeddings.py`:

- `POST /v1/embeddings/create` — embedding di un singolo testo
- `POST /v1/embeddings/multilingual` — embedding con path language-aware
- `POST /v1/embeddings/batch` — embedding batch
- `POST /v1/embeddings/similarity` — similarità coseno tra due testi

### Sentiment

Definiti in `services/api_babel_gardens/api/routes_sentiment.py`:

- `POST /v1/sentiment/analyze`
- `POST /v1/sentiment/batch`

### Emotion

Definiti in `services/api_babel_gardens/api/routes_emotion.py`:

- `POST /v1/emotion/detect`

### Profili + cognitive bridge

Definiti in `services/api_babel_gardens/api/routes_admin.py`:

- `POST /v1/profiles/create`
- `POST /v1/profiles/adapt`
- `POST /v1/profiles/recommend`
- `POST /v1/events/publish`
- `POST /v1/routing/intelligent`

## Schemi request/response

I modelli Pydantic sono in `services/api_babel_gardens/schemas/api_models.py`.

Tipi principali:

- `EmbeddingRequest` (`text`, `language`, `model_type`, `use_cache`)
- `BatchEmbeddingRequest` (`texts[]`, `language`, `model_type`, `use_cache`)
- `SentimentRequest` (`text`, `language`, `fusion_mode`, `use_cache`)
- `EmotionRequest` (`text`, `language`, `fusion_mode`, `use_cache`)

## Variabili env (config service)

Caricate in `services/api_babel_gardens/config.py`:

- `HOST`, `PORT`, `DEBUG`, `LOG_LEVEL`
- `EMBEDDING_SERVICE_URL`, `EMBEDDING_ENDPOINT`, `EMBEDDING_TIMEOUT`, `EMBEDDING_RETRIES`
- `SENTIMENT_SERVICE_URL`, `SENTIMENT_ENDPOINT`, `SENTIMENT_TIMEOUT`
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION_SEMANTIC`, `QDRANT_COLLECTION_SENTIMENT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

