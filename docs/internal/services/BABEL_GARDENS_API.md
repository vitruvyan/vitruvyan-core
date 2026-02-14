# Babel Gardens API

<p class="kb-subtitle">LIVELLO 2 service for multilingual semantics: embeddings, sentiment/emotion signals, profiles, and cognitive routing.</p>

## Location

- Service: `services/api_babel_gardens/`
- Pure core (LIVELLO 1): `vitruvyan_core/core/cognitive/babel_gardens/`

## Base URL / Port

Default port is **`8009`** (env: `PORT`).

## Endpoints (implemented)

### Health / metrics

- `GET /`
- `GET /health`
- `GET /metrics`

### Embeddings

Defined in `services/api_babel_gardens/api/routes_embeddings.py`:

- `POST /v1/embeddings/create` — embedding for a single text
- `POST /v1/embeddings/multilingual` — embedding with language-aware path
- `POST /v1/embeddings/batch` — batch embeddings
- `POST /v1/embeddings/similarity` — cosine similarity between two texts

### Sentiment

Defined in `services/api_babel_gardens/api/routes_sentiment.py`:

- `POST /v1/sentiment/analyze`
- `POST /v1/sentiment/batch`

### Emotion

Defined in `services/api_babel_gardens/api/routes_emotion.py`:

- `POST /v1/emotion/detect`

### Profiles + cognitive bridge

Defined in `services/api_babel_gardens/api/routes_admin.py`:

- `POST /v1/profiles/create`
- `POST /v1/profiles/adapt`
- `POST /v1/profiles/recommend`
- `POST /v1/events/publish`
- `POST /v1/routing/intelligent`

## Request/response schemas

Pydantic models live in `services/api_babel_gardens/schemas/api_models.py`.

Most important request types:

- `EmbeddingRequest` (`text`, `language`, `model_type`, `use_cache`)
- `BatchEmbeddingRequest` (`texts[]`, `language`, `model_type`, `use_cache`)
- `SentimentRequest` (`text`, `language`, `fusion_mode`, `use_cache`)
- `EmotionRequest` (`text`, `language`, `fusion_mode`, `use_cache`)

## Service config env vars

Loaded in `services/api_babel_gardens/config.py`:

- `HOST`, `PORT`, `DEBUG`, `LOG_LEVEL`
- `EMBEDDING_SERVICE_URL`, `EMBEDDING_ENDPOINT`, `EMBEDDING_TIMEOUT`, `EMBEDDING_RETRIES`
- `SENTIMENT_SERVICE_URL`, `SENTIMENT_ENDPOINT`, `SENTIMENT_TIMEOUT`
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION_SEMANTIC`, `QDRANT_COLLECTION_SENTIMENT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

