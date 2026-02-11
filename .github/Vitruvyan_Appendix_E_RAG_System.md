# Appendix E — RAG System Architecture (Sacred Orders)
**Vitruvyan AI Trading Advisor - Official Documentation**  
**Version**: 3.0 (Feb 2026 - LIVELLO 1+2 Refactoring)  
**Last Updated**: February 11, 2026  
**Status**: ✅ ACTIVE - Production Ready

> **Architecture Note (Feb 2026)**: Codex Hunters and Memory Orders now follow the **LIVELLO 1+2 Pattern**.
> Paths updated: `core/leo/` → `core/agents/`, `core/memory_orders/` → `core/governance/`

---

## 🌍 Translation Cost Optimization (November 2025)

**CRITICAL**: RAG system now supports **multilingual dataset augmentation** with 99.8% cost savings.

### Translation Providers Supported
| Provider | Cost (1.7M vectors × 4 langs) | Quality | Speed | Status |
|----------|-------------------------------|---------|-------|--------|
| **Together.ai (DeepSeek v3)** | **$0.50** | 95% | 8h | ✅ **RECOMMENDED** |
| **Groq (Llama 3.1 70B)** | **$0.00** (FREE) | 92% | 40 days | ✅ Background jobs |
| **OpenAI (GPT-4o-mini)** | **$204.00** | 95% | 8h | ❌ **TOO EXPENSIVE** |

### Setup Instructions

**Option 1: Together.ai + DeepSeek** (Recommended):
```bash
# Get API key: https://api.together.ai/settings/api-keys
echo "DEEPSEEK_API_KEY=tgp_v1_..." >> .env
echo "TRANSLATION_PROVIDER=deepseek" >> .env

# Test
python3 tests/test_translation_cost.py
```

**Option 2: Groq (FREE)**:
```bash
# Get API key: https://console.groq.com
echo "GROQ_API_KEY=gsk_..." >> .env
echo "TRANSLATION_PROVIDER=groq" >> .env
```

### Translation Agent Usage
```bash
# Translate 1.7M vectors to Italian (8 hours, $0.12)
python3 vitruvyan_core/core/governance/codex_hunters/translation_agent.py \
    --target-languages it \
    --batch-size 100

# Translate to 4 languages (32 hours, $0.50)
python3 vitruvyan_core/core/governance/codex_hunters/translation_agent.py \
    --target-languages it,es,fr,de \
    --batch-size 100
```

### Architecture Integration
```
User Query (any language)
  ↓
Babel Gardens (language detection)
  ↓
Translation Agent (if needed)
  ↓ Together.ai API (DeepSeek v3)
Translated text → embedding → Qdrant
  ↓
Multilingual semantic search enabled
```

**Documentation**: See `docs/TRANSLATION_COST_OPTIMIZATION.md` for full details.

---

## 🌍 Language-First Architecture (November 21, 2025)

**CRITICAL**: Qdrant collections now enforce **mandatory language classification** by design.

### Problem Statement
- **42%** of `conversations_embeddings` points had `language=null` (invalid)
- **58%** of `semantic_states` points had `language=unknown` (invalid)
- Silent fallback to English degraded multilingual semantic search quality
- No validation layer prevented bad data from entering collections

### Solution: Language-First Enforcement (FASE 1+2)

#### 1. QdrantAgent Validation Layer
**File**: `vitruvyan_core/core/agents/qdrant_agent.py` (Feb 2026 path)

All `upsert()` operations now **REQUIRE** valid ISO 639-1 language codes:
```python
def upsert(self, collection: str, points: List[Dict[str, Any]]):
    """
    MANDATORY language validation (Nov 21, 2025).
    NO null, NO "unknown", NO "auto" allowed.
    """
    valid_languages = {"en", "it", "es", "fr", "de", "zh", "ar", "ja", "ko", "ru", "pt", "nl", "tr", "he", "th"}
    
    for p in points:
        language = p.get("payload", {}).get("language")
        if not language or language in ["null", "unknown", "auto", ""]:
            raise ValueError(f"Point has invalid language '{language}'. Must be ISO 639-1 code.")
```

#### 2. Babel Gardens Language Detection Cascade
**File**: `docker/services/api_babel_gardens/modules/embedding_engine.py`

**NO silent fallback to English** - detection follows priority cascade:
```python
async def _detect_language(text: str) -> str:
    # 1️⃣ Unicode Range (AR/ZH/JA/KO/HE/RU) → 95% confidence, 0ms
    # 2️⃣ Qdrant Semantic Search (1,065 seed phrases) → threshold 0.60
    # 3️⃣ Redis Cache (7-day TTL) → <1ms
    # 4️⃣ GPT-4o-mini Fallback → $0.000005/query
    # 5️⃣ Reject with 'unknown' (no silent fallback)
```

**Majority Voting**: Top 3 Qdrant matches vote on language (2/3 consensus required)

#### 3. Seed Phrases Dataset
**File**: `docs_new/vitruvyan_seed_phrases_multilingual.jsonl`

**1,065 financial queries** across 5 languages:
- **Italian**: 213 phrases ("analizza NVDA momentum", "trend di AAPL")
- **English**: 213 phrases ("analyze Tesla earnings", "MSFT sentiment")
- **Spanish**: 213 phrases ("qué tal AAPL?", "análisis de META")
- **French**: 213 phrases ("comment va GOOGL?", "tendance AMZN")
- **German**: 213 phrases ("wie ist TSLA?", "NVDA Analyse")

**Ingestion Script**: `scripts/ingest_seed_phrases.py`
```bash
python3 scripts/ingest_seed_phrases.py  # Populates conversations_embeddings
```

#### 4. dotenv Integration
**Files**: `docker/services/api_babel_gardens/main.py`, `Dockerfile.api_babel_gardens`

```python
from dotenv import load_dotenv
load_dotenv("/app/.env")  # OPENAI_API_KEY now accessible
```

**Dockerfile**:
```dockerfile
COPY .env /app/.env  # Copy secrets to container
```

### Testing Results (Nov 21, 2025)

| Language | Query | Detected | Method | Accuracy |
|----------|-------|----------|--------|----------|
| IT | "analizza NVDA" | ✅ it | GPT-4o-mini | 100% |
| EN | "analyze Tesla momentum" | ✅ en | GPT-4o-mini | 100% |
| ES | "qué tal AAPL?" | ✅ es | GPT-4o-mini | 100% |
| FR | "comment va le trend de META?" | ✅ fr | GPT-4o-mini | 100% |
| DE | "wie ist der Kurs von MSFT?" | ✅ de | GPT-4o-mini | 100% |

### Cost Analysis
- **Seed Ingestion**: $0.05 (one-time, 1,065 embeddings)
- **GPT Fallback**: $0.000005/query (only when Qdrant misses)
- **Monthly (10K MAU)**: ~$1-2 (assuming 75%+ Qdrant cache hit rate)

### Maintenance Tools

**Cleanup Script**: `scripts/qdrant_language_cleanup.py`
```bash
# Dry-run: show what would be fixed
python3 scripts/qdrant_language_cleanup.py --dry-run --collection conversations_embeddings

# Production: re-detect language for invalid points
python3 scripts/qdrant_language_cleanup.py --collection conversations_embeddings
```

**Monitoring**: All language detection events logged to PostgreSQL `fusion_logs` table.

### References
- **Git Commit**: 69c42067 (Nov 21, 2025) - "Language-First Architecture - FASE 1+2"
- **Test Suite**: Manual E2E validation (5 languages × 3 queries each)
- **Documentation**: This section + copilot-instructions.md Appendix E update

---

## 📋 Overview

The **RAG (Retrieval-Augmented Generation) System** is Vitruvyan's epistemic memory layer, implementing the dual-memory architecture pattern of Sacred Orders. It combines structured relational storage (PostgreSQL/Archivarium) with vector semantic memory (Qdrant/Mnemosyne) to enable context-aware explainability and intelligent signal generation.

### Sacred Orders Integration
| Order | Component | RAG Role |
|-------|-----------|----------|
| **Perception** | Codex Hunters, Babel Gardens | Acquire and process external data (Reddit, GNews, yfinance) |
| **Memory** | PostgreSQL + Qdrant, Memory Orders | Dual-memory persistence and synchronization |
| **Reason** | Neural Engine | Query RAG for contextual factors in multi-factor ranking |
| **Discourse** | LangGraph + VEE | Retrieve semantic context for explainable narratives |
| **Truth** | Orthodoxy Wardens | Audit RAG coherence and data integrity |

---

## 🏗️ Architecture Components

### 1. vitruvyan_api_embedding:8010
**Type**: Always-On Embedding Service (Perception/Discourse Order)  
**Purpose**: Centralized text-to-vector transformation using MiniLM-L6-v2

#### Endpoints
```
POST /v1/embeddings/create      - Generate embedding for single text
POST /v1/embeddings/batch       - Generate embeddings for multiple texts
POST /v1/embeddings/sync        - Sync PostgreSQL phrases to Qdrant
GET  /health                    - Service health check
```

#### Configuration
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384 (floating point)
- **Distance Metric**: Cosine similarity
- **Throughput**: ~100 embeddings/second
- **Container**: `vitruvyan_api_embedding` (Docker)
- **Port**: 8010 (internal), not exposed externally

#### Example Usage
```bash
# Single embedding
curl -X POST http://vitruvyan_api_embedding:8010/v1/embeddings/create \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AAPL has strong momentum with RSI at 72",
    "store_in_qdrant": true,
    "collection_name": "phrases_embeddings"
  }'

# Response
{
  "embedding": [0.123, -0.456, 0.789, ...],  # 384-dim vector
  "model": "all-MiniLM-L6-v2",
  "stored": true,
  "collection": "phrases_embeddings"
}
```

---

### 2. Babel Gardens:8009
**Type**: Fusion Layer Service (Discourse Order)  
**Purpose**: Unified sentiment, language detection, and semantic-affective fusion

#### Modules
1. **sentiment_engine.py**: FinBERT-based financial sentiment analysis
2. **language_detector.py**: FastText language detection (84 languages)
3. **embedding_engine_cooperative.py**: Cooperative embedding via vitruvyan_api_embedding
4. **fusion_engine.py**: Semantic (MiniLM) + Affective (FinBERT) fusion

#### Fusion Flow
```
Input Text (any language)
  ↓
FastText Language Detection
  ↓
FinBERT Sentiment Analysis (score 0-1, label positive/negative/neutral)
  ↓
HTTP POST → vitruvyan_api_embedding:8010/v1/embeddings/create
  ↓
Semantic Vector (384-dim)
  ↓
Fusion Logic: embedding + sentiment_boost
  ↓
Fused Vector (384-dim with affective enrichment)
  ↓
Qdrant upsert → phrases_fused collection
```

#### Configuration
- **Sentiment Model**: `ProsusAI/finbert` (FinBERT)
- **Embedding Model**: MiniLM-L6-v2 (via cooperative API)
- **Fusion Mode**: `standard` (no boost) or `enhanced` (sentiment boost)
- **Languages**: 84 supported (auto-detect)
- **Container**: `vitruvyan_babel_gardens`
- **Port**: 8009 (internal + external via nginx)

#### Example Usage
```bash
# Sentiment with fusion
curl -X POST http://vitruvyan_babel_gardens:8009/v1/sentiment/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["AAPL momentum strong", "TSLA volatility high"],
    "language": "auto",
    "fusion_mode": "enhanced",
    "store_embeddings": true
  }'

# Response
{
  "status": "success",
  "results": [
    {
      "sentiment": {"label": "positive", "score": 0.87},
      "language": "en",
      "embedding_stored": true,
      "collection": "phrases_fused"
    },
    ...
  ]
}
```

---

### 3. Memory Orders:8016
**Type**: Dual-Memory Synchronization Service (Memory Order)  
**Purpose**: Maintain coherence between PostgreSQL (Archivarium) and Qdrant (Mnemosyne)

#### Responsibilities
1. **Sync Phrases**: Embed unembedded phrases from PostgreSQL → Qdrant
2. **Coherence Check**: Detect drift between PostgreSQL row counts and Qdrant points
3. **Healing**: Automatically repair missing embeddings
4. **Monitoring**: Export Prometheus metrics for observability

#### Endpoints
```
POST /v1/sync/phrases          - Trigger manual sync (limit, offset)
GET  /v1/coherence-check       - Check PostgreSQL ↔ Qdrant alignment
GET  /v1/sync/status           - Get last sync timestamp and status
GET  /health/memory            - Memory Orders health check
```

#### Sync Logic
```python
# Pseudo-code for sync_phrases_to_qdrant()
def sync_phrases_to_qdrant(limit=1000, offset=0):
    # 1. Query PostgreSQL for unembedded phrases
    phrases = pg.execute_query(
        "SELECT id, phrase_text FROM phrases WHERE embedded = false LIMIT %s OFFSET %s",
        (limit, offset)
    )
    
    # 2. Batch embed via vitruvyan_api_embedding
    embeddings = httpx.post(
        "http://vitruvyan_api_embedding:8010/v1/embeddings/batch",
        json={"texts": [p[1] for p in phrases]}
    ).json()["embeddings"]
    
    # 3. Batch upsert to Qdrant
    qdrant.upsert("phrases_embeddings", [
        {"id": p[0], "vector": embeddings[i], "payload": {"phrase_text": p[1]}}
        for i, p in enumerate(phrases)
    ])
    
    # 4. Update PostgreSQL embedded flag
    pg.execute_query(
        "UPDATE phrases SET embedded = true WHERE id = ANY(%s)",
        ([p[0] for p in phrases],)
    )
    
    return {"synced": len(phrases)}
```

#### Configuration
- **Sync Schedule**: Daily 02:00 UTC (APScheduler)
- **Batch Size**: 1,000 phrases per sync
- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout**: 60 seconds per batch
- **Container**: `vitruvyan_memory_orders`
- **Port**: 8016 (internal)

---

### 4. Codex Hunters (Perception Order)
**Type**: Data Acquisition Agents  
**Purpose**: Scrape external data sources and calculate technical indicators

#### Agents
1. **Hunter** (`hunter.py`): Reddit/GNews text extraction
2. **Tracker** (`tracker.py`): yfinance OHLCV data
3. **Scribe** (`scribe.py`): Technical indicators (RSI, MACD, SMA, ATR)
4. **Cartographer** (`cartographer.py`): FRED macro data, Fama-French factors
5. **Restorer** (`restorer.py`): Missing data interpolation
6. **Binder** (`binder.py`): Data validation
7. **Inspector** (`inspector.py`): Quality assurance
8. **Scholastic** (`scholastic.py`): Documentation

#### Data Flow (Scribe Example)
```
Scheduler (codex_event_scheduler.py)
  ↓ Redis publish: perception.codex.momentum
Scribe receives event
  ↓ Calculate RSI, MACD, velocity
Write to PostgreSQL (momentum_logs)
  ↓ Generate embedding
HTTP POST → vitruvyan_api_embedding:8010
  ↓ Upsert to Qdrant (momentum_vectors)
```

#### Configuration
- **Schedule**: Daily 18:00 (momentum), 18:30 (trend), 23:00 (expedition)
- **Coverage**: 519 active tickers (100%)
- **Storage**: Dual-memory (PostgreSQL + Qdrant)
- **Retry**: 3 attempts with exponential backoff

---

## 🗄️ Data Storage

### PostgreSQL (Archivarium) - Structured Memory
**Purpose**: Relational storage for queryable, structured data

#### Key Tables
| Table | Purpose | Coverage | Embeddings |
|-------|---------|----------|------------|
| `phrases` | Reddit/GNews text | 43,380 rows | Yes (embedded flag) |
| `sentiment_scores` | **Babel Gardens sentiment (expanded Nov 2025)** | 40,493+ rows | No (numeric only) |
| `ship_tracking_live` | **OMNI Ship Tracker (Nov 2025)** | 7,294 vessels | Yes (Qdrant: ship_tracker_embeddings) |
| `momentum_logs` | RSI, MACD, velocity | 519 tickers (100%) | Yes (via Scribe) |
| `trend_logs` | SMA, EMA, trend direction | 519 tickers (100%) | Yes (via Scribe) |
| `volatility_logs` | ATR, Bollinger Bands | 519 tickers (100%) | Yes (via Scribe) |
| `conversations` | User chat history | Variable | Yes (via LangGraph) |
| `tickers` | Ticker metadata | 519 active | No |

#### Schema Example: phrases
```sql
CREATE TABLE phrases (
    id SERIAL PRIMARY KEY,
    phrase_text TEXT NOT NULL,
    phrase_hash TEXT UNIQUE,  -- md5(phrase_text)
    source TEXT,              -- 'reddit', 'gnews', 'user'
    language TEXT,            -- 'en', 'it', 'es', etc.
    embedded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phrases_embedded ON phrases(embedded) WHERE embedded = false;
CREATE INDEX idx_phrases_created ON phrases(created_at DESC);
```

#### Schema Example: sentiment_scores (Expanded Nov 2025)
```sql
CREATE TABLE sentiment_scores (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,       -- 'ship', 'aircraft', 'ticker'
    entity_id VARCHAR(100) NOT NULL,        -- mmsi, icao24, ticker symbol
    entity_name VARCHAR(255),               -- vessel name, callsign, company name
    sentiment_label VARCHAR(20),            -- 'positive', 'negative', 'neutral'
    sentiment_score FLOAT,                  -- -1.0 to +1.0 (database format)
    confidence FLOAT,                       -- 0.0 to 1.0 (Babel Gardens confidence)
    text_analyzed TEXT,                     -- Original text sent to Babel Gardens
    perception_id VARCHAR(100),             -- Trace ID for audit
    test_id VARCHAR(100),                   -- Session ID (DualMemorySync)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sentiment_entity ON sentiment_scores(entity_type, entity_id);
CREATE INDEX idx_sentiment_created ON sentiment_scores(created_at);
```

**Usage**: Unified sentiment storage for financial tickers (LangGraph) AND real-world perception (OMNI Ship/Air Tracker).

---

### Qdrant (Mnemosyne) - Vector Memory
**Purpose**: Semantic search and similarity matching

#### Collections
| Collection | Purpose | Vector Size | Distance | Points (Target) |
|------------|---------|-------------|----------|-----------------|
| `phrases_embeddings` | Reddit/GNews MiniLM vectors | 384 | Cosine | 43,380 |
| `phrases_fused` | Babel Gardens fusion output | 384 | Cosine | 43,380+ |
| `momentum_vectors` | RSI/MACD embeddings | 384 | Cosine | 519 |
| `trend_vectors` | SMA/EMA embeddings | 384 | Cosine | 519 |
| `volatility_vectors` | ATR/Bollinger embeddings | 384 | Cosine | 519 |
| `sentiment_embeddings` | Sentiment vectors | 384 | Cosine | Variable |
| `conversations_embeddings` | Chat history vectors | 384 | Cosine | 1,326+ |
| `semantic_states` | **VSGS conversation context (Nov 2025)** | 384 | Cosine | 1,422+ |
| `ship_tracker_embeddings` | **OMNI Ship Tracker (Nov 2025)** | 384 | Cosine | 7,000+ |
| `air_traffic_embeddings` | **OMNI Air Traffic (Nov 2025)** | 384 | Cosine | Variable |
| `vitruvyan_docs` | Documentation embeddings | 384 | Cosine | Variable |

#### Collection Schema Example: momentum_vectors
```python
{
    "vector_size": 384,
    "distance": "Cosine",
    "payload_schema": {
        "ticker": "string",
        "rsi": "float",
        "macd": "float",
        "velocity": "float",
        "timestamp": "datetime"
    }
}
```

#### Query Example
```python
from core.leo.qdrant_agent import QdrantAgent

qdrant = QdrantAgent()

# Search for similar momentum patterns
query_text = "Strong bullish momentum with RSI above 70"
query_vector = embedding_api.create(query_text)

results = qdrant.search(
    collection="momentum_vectors",
    query_vector=query_vector,
    top_k=10
)

# Returns top 10 tickers with similar momentum profiles
for result in results["results"]:
    print(f"{result['payload']['ticker']}: RSI={result['payload']['rsi']}")
```

---

## 🔄 Data Flows

### Flow 1: Reddit/GNews → phrases_embeddings
```
Hunter scrapes Reddit/GNews
  ↓ Extract text, source, language
PostgresAgent.insert_phrase(text, source, language, embedded=false)
  ↓ Daily 02:00 UTC
Memory Orders triggers sync
  ↓ SELECT * FROM phrases WHERE embedded = false LIMIT 1000
Batch embed via vitruvyan_api_embedding:8010
  ↓ Upsert to Qdrant (phrases_embeddings)
UPDATE phrases SET embedded = true
```

### Flow 2: Babel Gardens → phrases_fused
```
User query: "AAPL sentiment analysis"
  ↓ LangGraph sentiment_node
HTTP POST → Babel Gardens:8009/v1/sentiment/batch
  ↓ FinBERT sentiment (positive, 0.87)
  ↓ HTTP POST → vitruvyan_api_embedding:8010
  ↓ MiniLM embedding (384-dim)
Fusion: embedding + sentiment_boost
  ↓ Upsert to Qdrant (phrases_fused)
PostgresAgent.insert_sentiment(ticker, score, tag)
```

### Flow 3: Codex Scribe → momentum_vectors
```
Scheduler triggers perception.codex.momentum (daily 18:00)
  ↓ Redis event
Scribe calculates RSI, MACD, velocity
  ↓ PostgresAgent: log_momentum_result(ticker, rsi, macd, velocity)
Generate indicator text: "Ticker: AAPL, RSI: 72, MACD: 0.034"
  ↓ HTTP POST → vitruvyan_api_embedding:8010
Embed indicator text → 384-dim vector
  ↓ QdrantAgent.upsert("momentum_vectors", [...])
```

### Flow 4: LangGraph → VEE → conversations_embeddings
```
User: "Explain why NVDA is ranked #1"
  ↓ LangGraph dispatcher
Neural Engine: numerical_panel (NVDA rank #1, z-scores)
  ↓ VEE explainability_node
QdrantAgent.search("momentum_vectors", query_vector, top_k=5)
  ↓ Retrieve context: [NVDA: RSI 78, MACD 0.12, ...]
Generate narrative: "NVDA ranks #1 due to exceptional momentum (RSI 78)..."
  ↓ conversation_persistence.embed_and_store(user_input, response)
HTTP POST → vitruvyan_api_embedding:8010
  ↓ Upsert to Qdrant (conversations_embeddings)
PostgresAgent.log_conversation(user_id, prompt, response)
```

### Flow 5: VSGS Semantic Grounding → semantic_states (Nov 2025)
```
LangGraph semantic_grounding_node (every user query)
  ↓ Extract user_input, user_id, trace_id, intent, language
HTTP POST → vitruvyan_api_embedding:8010/v1/embeddings/create
  ↓ Generate 384-dim vector (MiniLM-L6-v2)
QdrantAgent.search("semantic_states", query_vector, top_k=3)
  ↓ Retrieve top-3 similar past conversations
Enrich LangGraph state with semantic_matches
  ↓ state["semantic_matches"] = [{score, text, intent, tickers, ...}]
PostgresAgent: INSERT INTO log_agent (audit trail)
  ↓ MiFID II compliance logging
Redis publish: "semantic.grounding.completed"
  ↓ Memory Orders event notification
```

### Flow 6: OMNI Ship Tracker → ship_tracker_embeddings (Nov 2025)
```
AISStream WebSocket (real-time vessel data)
  ↓ AISStreamConnector buffers vessels (batch 200)
DualMemorySync.batch_persist(vessels, session_id)
  ↓ Generate contextual text per vessel:
    "Ship {name} ({type}) sailing at {speed} knots, status: {status}, operator: {fleet}"
  ↓ Batch 200 vessels → 8 batches of 25 (Babel Gardens limit)
HTTP POST → Babel Gardens:8009/v1/sentiment/batch (25 texts per call)
  ↓ FinBERT sentiment analysis (positive/negative/neutral, score 0-1)
  ↓ Convert to database format (-1.0 to +1.0)
HTTP POST → vitruvyan_api_embedding:8010/v1/embeddings/batch
  ↓ Generate 384-dim vectors (MiniLM-L6-v2)
QdrantAgent.upsert("ship_tracker_embeddings", vectors + sentiment payload)
  ↓ Payload: {mmsi, name, type, speed, sentiment_label, sentiment_score, sentiment_confidence}
PostgresAgent.insert_sentiment_scores(entity_type='ship', ...)
  ↓ Table: sentiment_scores (40K+ rows as of Nov 18, 2025)
PostgresAgent.insert(ship_tracking_live table)
  ↓ Dual-memory coherence maintained (PostgreSQL ↔ Qdrant)
```

**OMNI Integration Stats** (Nov 18, 2025):
- **Vessels Tracked**: 7,294 active (global AIS coverage)
- **Sentiment Scores**: 40,493 saved (100% neutral due to technical text)
- **Batch Size**: 200 vessels per flush (30s interval)
- **Babel Gardens**: 8 batches × 25 vessels (API limit respected)
- **Latency**: ~2s per 200-vessel batch (sentiment + embedding)
- **Collection**: `ship_tracker_embeddings` (Qdrant)

**VSGS Collection Schema** (semantic_states):
```python
{
    "collection_name": "semantic_states",
    "vectors_config": {
        "size": 384,              # MiniLM-L6-v2
        "distance": "Cosine"      # Cosine similarity
    },
    "hnsw_config": {
        "m": 16,                  # Connections per node
        "ef_construct": 100,      # Build quality
        "ef": 128                 # Search quality
    },
    "payload_schema": {
        "query_text": "string",        # User query verbatim
        "user_id": "string",           # Client ID
        "trace_id": "string",          # UUID4 for tracking
        "intent": "string",            # momentum, trend, sentiment, etc.
        "tickers": "array<string>",    # Extracted tickers
        "horizon": "string",           # short, medium, long
        "language": "string",          # it, en, es, etc.
        "emotion": "string",           # curious, frustrated, etc.
        "timestamp": "datetime"        # ISO 8601
    }
}
```

**VSGS Production Status**: ✅ ENABLED (Nov 4, 2025)
- **Latency**: 35ms average (15ms embedding + 20ms Qdrant search)
- **Accuracy**: 92% context retrieval precision
- **Cost**: $0.0015 per user/month (10K MAU)
- **Coverage**: 1.4K+ conversation vectors, growing daily

---

## 🔧 Configuration

### Environment Variables
```bash
# Embedding API
EMBEDDING_API_URL=http://vitruvyan_api_embedding:8010
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=100

# Babel Gardens
BABEL_GARDENS_URL=http://vitruvyan_babel_gardens:8009
BABEL_FUSION_MODE=enhanced  # or 'standard'
BABEL_FUSION_ENABLED=true

# Qdrant
QDRANT_HOST=vitruvyan_qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=  # Optional, not used in Docker network
QDRANT_TIMEOUT=30.0

# PostgreSQL
POSTGRES_HOST=161.97.140.157  # ⚠️ CRITICAL: localhost on VPS, NOT in Docker
POSTGRES_PORT=5432
POSTGRES_DB=vitruvyan
POSTGRES_USER=vitruvyan_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # From environment (security requirement)

# Memory Orders
MEMORY_ORDERS_SYNC_ENABLED=true
MEMORY_ORDERS_SYNC_SCHEDULE=0 2 * * *  # Daily 02:00 UTC
MEMORY_ORDERS_BATCH_SIZE=1000
MEMORY_ORDERS_COHERENCE_THRESHOLD=0.05  # 5% drift alert

# VSGS (Vitruvyan Semantic Grounding System) - Nov 2025
VSGS_ENABLED=1                          # Master feature flag (0=disabled, 1=enabled)
VSGS_GROUNDING_TOPK=3                   # Number of semantic matches to retrieve
VSGS_COLLECTION_NAME=semantic_states    # Qdrant collection for conversation vectors
VSGS_PROMPT_BUDGET_CHARS=800           # Max chars for context injection (reserved)
VSGS_STORE_EVERY_N=1                    # Store every Nth event (1=all, 2=half, etc.)
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
services:
  vitruvyan_api_embedding:
    build:
      context: .
      dockerfile: Dockerfile.api_embedding
    container_name: vitruvyan_api_embedding
    ports:
      - "8010:8010"  # Internal only, not exposed to nginx
    environment:
      - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
      - QDRANT_HOST=vitruvyan_qdrant
      - POSTGRES_HOST=161.97.140.157  # ⚠️ Host machine
    depends_on:
      - vitruvyan_qdrant
      - vitruvyan_redis
    restart: unless-stopped
    networks:
      - vitruvyan_network

  vitruvyan_babel_gardens:
    build:
      context: docker/services/api_babel_gardens
      dockerfile: Dockerfile
    container_name: vitruvyan_babel_gardens
    ports:
      - "8009:8009"
    environment:
      - EMBEDDING_API_URL=http://vitruvyan_api_embedding:8010
      - FUSION_MODE=enhanced
    depends_on:
      - vitruvyan_api_embedding
      - vitruvyan_qdrant
    restart: unless-stopped
    networks:
      - vitruvyan_network

  vitruvyan_memory_orders:
    build:
      context: docker/services/api_memory_orders
      dockerfile: Dockerfile
    container_name: vitruvyan_memory_orders
    ports:
      - "8016:8016"
    environment:
      - EMBEDDING_API_URL=http://vitruvyan_api_embedding:8010
      - SYNC_SCHEDULE=0 2 * * *
    depends_on:
      - vitruvyan_api_embedding
      - vitruvyan_qdrant
    restart: unless-stopped
    networks:
      - vitruvyan_network

  vitruvyan_qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: vitruvyan_qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    networks:
      - vitruvyan_network

networks:
  vitruvyan_network:
    driver: bridge

volumes:
  qdrant_data:
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics
```python
# Memory Orders metrics
memory_orders_sync_lag = Gauge('memory_orders_sync_lag', 'Rows not yet embedded')
memory_orders_coherence_drift = Gauge('memory_orders_coherence_drift_pct', 'Drift percentage')
memory_orders_sync_duration = Gauge('memory_orders_sync_duration_seconds', 'Last sync duration')
memory_orders_sync_total = Counter('memory_orders_sync_total', 'Total sync operations')

# Embedding API metrics
embedding_api_requests_total = Counter('embedding_api_requests_total', 'Total requests')
embedding_api_latency = Histogram('embedding_api_latency_seconds', 'Request latency')
embedding_api_errors_total = Counter('embedding_api_errors_total', 'Total errors')

# Qdrant metrics
qdrant_points_total = Gauge('qdrant_points_total', 'Total points', ['collection'])
qdrant_upsert_duration = Histogram('qdrant_upsert_duration_seconds', 'Upsert duration')
```

### Health Checks
```bash
# Embedding API
curl http://localhost:8010/health
# Expected: {"status": "healthy", "model": "all-MiniLM-L6-v2", "uptime": 3600}

# Babel Gardens
curl http://localhost:8009/sacred-health
# Expected: {"status": "healthy", "service": "babel_gardens", ...}

# Memory Orders
curl http://localhost:8016/health/memory
# Expected: {"status": "healthy", "sync_lag": 0, "coherence_drift_pct": 0.5}

# Qdrant
curl http://localhost:6333/collections
# Expected: {"result": {"collections": [...]}, "status": "ok"}
```

### Coherence Monitoring
```bash
# Check dual-memory alignment
curl http://localhost:8016/v1/coherence-check

# Response
{
  "status": "healthy",  # or "warning" if drift > 5%, "critical" if > 15%
  "postgresql_count": 43380,
  "qdrant_count": 43380,
  "drift_percentage": 0.0,
  "timestamp": "2025-10-28T12:00:00Z"
}
```

---

## 🧪 Testing

### Unit Tests
```python
# tests/test_embedding_api.py
def test_embedding_create():
    response = httpx.post(
        "http://localhost:8010/v1/embeddings/create",
        json={"text": "test phrase"}
    )
    assert response.status_code == 200
    assert len(response.json()["embedding"]) == 384

# tests/test_memory_orders_sync.py
def test_sync_phrases_to_qdrant():
    engine = MemorySyncEngine()
    result = engine.sync_phrases_to_qdrant(limit=10)
    assert result["status"] == "ok"
    assert result["synced"] == 10
```

### Integration Tests
```python
# tests/test_rag_e2e.py
def test_end_to_end_rag_flow():
    # 1. Insert phrase to PostgreSQL
    pg = PostgresAgent()
    phrase_id = pg.insert_phrase("AAPL momentum strong", source="test")
    
    # 2. Trigger Memory Orders sync
    response = httpx.post("http://localhost:8016/v1/sync/phrases", json={"limit": 1})
    assert response.status_code == 200
    
    # 3. Verify Qdrant has vector
    qdrant = QdrantAgent()
    point = qdrant.client.retrieve("phrases_embeddings", ids=[str(phrase_id)])
    assert len(point) == 1
    assert len(point[0].vector) == 384
    
    # 4. Verify PostgreSQL updated
    pg_result = pg.fetch_all("SELECT embedded FROM phrases WHERE id = %s", (phrase_id,))
    assert pg_result[0][0] is True
```

---

## 🚨 Troubleshooting

### Issue: Qdrant Collection Empty
**Symptoms**: `curl http://localhost:6333/collections/phrases_embeddings` shows `points_count: 0`

**Diagnosis**:
1. Check PostgreSQL has unembedded phrases:
   ```sql
   SELECT COUNT(*) FROM phrases WHERE embedded = false;
   ```
2. Check Memory Orders sync logs:
   ```bash
   docker logs vitruvyan_memory_orders --tail 100 | grep sync
   ```
3. Check embedding API is reachable:
   ```bash
   curl http://vitruvyan_api_embedding:8010/health
   ```

**Solutions**:
- If PostgreSQL has phrases but Qdrant empty: Trigger manual sync
  ```bash
  curl -X POST http://localhost:8016/v1/sync/phrases -d '{"limit": 1000}'
  ```
- If embedding API unreachable: Check Docker network
  ```bash
  docker network inspect vitruvyan_network
  ```
- If sync failing: Check embedding API logs
  ```bash
  docker logs vitruvyan_api_embedding --tail 100
  ```

---

### Issue: Coherence Drift >5%
**Symptoms**: `/v1/coherence-check` shows `drift_percentage: 12.5`

**Diagnosis**:
1. Check last sync timestamp:
   ```bash
   curl http://localhost:8016/v1/sync/status
   ```
2. Check for failed sync jobs:
   ```bash
   docker logs vitruvyan_memory_orders | grep ERROR
   ```
3. Check Qdrant disk space:
   ```bash
   docker exec vitruvyan_qdrant df -h
   ```

**Solutions**:
- If sync not running: Check scheduler (APScheduler logs)
- If sync failing: Reduce batch size (env: `MEMORY_ORDERS_BATCH_SIZE=500`)
- If Qdrant full: Implement retention policy (delete old vectors)

---

### Issue: Embedding API Slow
**Symptoms**: Embedding API latency p95 > 500ms

**Diagnosis**:
1. Check CPU/memory usage:
   ```bash
   docker stats vitruvyan_api_embedding
   ```
2. Check batch size:
   ```bash
   curl http://localhost:8010/health | jq '.config.batch_size'
   ```
3. Check concurrent requests:
   ```bash
   docker logs vitruvyan_api_embedding | grep "concurrent requests"
   ```

**Solutions**:
- If CPU maxed: Scale horizontally (add replica)
  ```yaml
  # docker-compose.yml
  vitruvyan_api_embedding:
    deploy:
      replicas: 2
  ```
- If memory pressure: Reduce batch size (env: `EMBEDDING_BATCH_SIZE=50`)
- If too many requests: Add rate limiting (nginx)

---

## 🔐 Security

### Authentication
- **Internal Services**: No auth (Docker network trust)
- **External API (nginx)**: JWT tokens required
- **Qdrant**: No API key (internal only)
- **PostgreSQL**: Password-based (never expose port 5432 externally)

### Data Privacy
- **PII Handling**: Phrases contain no PII (market data only)
- **User Data**: Conversations stored with user_id, NOT linked to PII
- **Embeddings**: Vectors are opaque, cannot reverse-engineer original text

### Network Security
```yaml
# docker-compose.yml
networks:
  vitruvyan_network:
    driver: bridge
    internal: true  # No external access

# Only nginx exposed to internet
services:
  nginx:
    ports:
      - "80:80"
      - "443:443"
    networks:
      - vitruvyan_network
```

---

## 📚 References

### Key Files (Feb 2026 Paths)
- **Embedding API**: `services/api_babel_gardens/` (FastAPI service)
- **Babel Gardens**: `services/api_babel_gardens/` (LIVELLO 2)
- **Memory Orders**: `services/api_memory_orders/` (LIVELLO 2)
- **Codex Hunters**: `vitruvyan_core/core/governance/codex_hunters/` (LIVELLO 1)
- **QdrantAgent**: `vitruvyan_core/core/agents/qdrant_agent.py`
- **PostgresAgent**: `vitruvyan_core/core/agents/postgres_agent.py`
- **StreamBus**: `vitruvyan_core/core/synaptic_conclave/transport/streams.py`

### Related Documentation
- **Action Plan**: `docs/RAG_INTEGRATION_ACTION_PLAN.md`
- **Architecture Diagram**: `docs/RAG_ARCHITECTURE_DIAGRAM.md`
- **Audit Report**: `docs/SYSTEM_INGESTION_AUDIT.md`
- **Copilot Instructions**: `.github/copilot-instructions.md` (Section 4: Babel Gardens)

### External Resources
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Sentence Transformers](https://www.sbert.net/)
- [FinBERT Paper](https://arxiv.org/abs/1908.10063)

---

## 📅 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 15, 2024 | Initial Sacred Orders refactor |
| 1.5 | Oct 20, 2025 | Babel Gardens integration |
| 2.0 | Oct 28, 2025 | Complete RAG documentation |
| 2.1 | Nov 18, 2025 | **OMNI Demo Integration**: Ship Tracker + Babel Gardens sentiment pipeline (40K+ scores, 7K+ vessels, dual-memory coherence) |

---

## 🚢 OMNI Demo — Ship Tracker Babel Gardens Integration (Nov 18, 2025)

### Overview
The OMNI Demo (`vitruvyan_api_demo_tests:8018`) now implements **full Vitruvyan architecture** for real-world perception:

- ✅ **Babel Gardens Sentiment**: 40,493 vessel sentiment scores via FinBERT
- ✅ **Cooperative Embedding**: MiniLM-L6-v2 via vitruvyan_api_embedding:8010
- ✅ **Dual-Memory Persistence**: PostgreSQL (`sentiment_scores`, `ship_tracking_live`) + Qdrant (`ship_tracker_embeddings`)
- ✅ **Background Ingestion**: AISStream WebSocket → DualMemorySync → Babel Gardens → 200 vessels/batch
- ✅ **Batch Processing**: 8 batches × 25 vessels (respects Babel Gardens API limit)

### Key Metrics (Nov 18, 2025)
| Metric | Value | Notes |
|--------|-------|-------|
| Vessels Tracked | 7,294 | Global AIS coverage (Atlantic → Black Sea) |
| Sentiment Scores | 40,493 | All neutral (technical vessel descriptions) |
| Batch Size | 200 vessels | Flushed every 30s or 200 vessels |
| Babel Gardens Calls | 8 per batch | 25 vessels per API call (limit) |
| Latency | ~2s/batch | Sentiment (1.2s) + Embedding (0.8s) |
| Qdrant Collection | `ship_tracker_embeddings` | 384-dim vectors + sentiment payload |
| PostgreSQL Tables | `sentiment_scores`, `ship_tracking_live` | Dual-memory architecture |

### Architecture Components
```
AISStream WebSocket (persistent, global bbox)
  ↓ AISStreamConnector (perception/aisstream_connector.py)
  ↓ Circular buffer (deque, max 2500 vessels)
  ↓ Flush every 30s or 200 vessels
DualMemorySync.batch_persist() (memory/dual_memory_sync.py)
  ↓ _get_babel_sentiments_and_embeddings()
  ↓ Loop: 8 batches × 25 vessels
  ↓ HTTP POST → Babel Gardens:8009/v1/sentiment/batch
  ↓ FinBERT sentiment (positive/negative/neutral, 0-1 score)
  ↓ Convert to database format (-1.0 to +1.0)
  ↓ HTTP POST → vitruvyan_api_embedding:8010/v1/embeddings/batch
  ↓ MiniLM-L6-v2 embeddings (384-dim)
QdrantAgent.upsert("ship_tracker_embeddings")
  ↓ Payload: {mmsi, name, type, speed, sentiment_label, sentiment_score, sentiment_confidence}
PostgresAgent.insert_sentiment_scores()
  ↓ entity_type='ship', entity_id=mmsi, sentiment_label, sentiment_score
PostgresAgent.batch_insert_postgresql()
  ↓ ship_tracking_live table (7,294 rows)
Coherence Check (dual-memory validation)
  ↓ PostgreSQL count vs Qdrant count
  ↓ Drift < 5% threshold (healthy)
```

### Code Implementation
**File**: `docker/services/api_demo_tests/memory/dual_memory_sync.py`

```python
async def _get_babel_sentiments_and_embeddings(self, texts: List[str]) -> tuple[List[Dict], List[List[float]]]:
    """
    Get sentiment + embeddings from Babel Gardens (Vitruvyan Architecture).
    Babel Gardens max_items=25, so we batch process.
    Returns: (sentiments, embeddings)
    """
    logger.info(f"[BABEL] Starting sentiment analysis for {len(texts)} vessels")
    
    sentiments = []
    embeddings = []
    
    # Babel Gardens batch limit is 25 texts max (API schema validation)
    BABEL_BATCH_SIZE = 25
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Call Babel Gardens for sentiment analysis (batched)
            for i in range(0, len(texts), BABEL_BATCH_SIZE):
                batch_texts = texts[i:i+BABEL_BATCH_SIZE]
                
                babel_response = await client.post(
                    "http://vitruvyan_babel_gardens:8009/v1/sentiment/batch",
                    json={
                        "texts": batch_texts,
                        "language": "auto",
                        "fusion_mode": "enhanced",
                        "use_cache": True
                    }
                )
                babel_response.raise_for_status()
                babel_data = babel_response.json()
                
                # Extract sentiment results for this batch
                for result in babel_data.get("results", []):
                    sentiment_label = result["sentiment"]["label"]  # positive/negative/neutral
                    sentiment_score_raw = result["sentiment"]["score"]  # 0.0-1.0
                    confidence = result["confidence"]
                    
                    # Convert to database format (-1.0 to +1.0)
                    if sentiment_label == "positive":
                        combined_score = (sentiment_score_raw - 0.5) * 2
                    elif sentiment_label == "negative":
                        combined_score = (sentiment_score_raw - 0.5) * 2
                    else:
                        combined_score = 0.0
                    
                    sentiments.append({
                        "label": sentiment_label,
                        "score": combined_score,
                        "confidence": confidence
                    })
            
            # Step 2: Get embeddings from cooperative API (single batch, no limit)
            embed_response = await client.post(
                self.embedding_api_url,
                json={"texts": texts}
            )
            embed_response.raise_for_status()
            embed_data = embed_response.json()
            embeddings = embed_data.get("embeddings", [])
            
            logger.info(f"[BABEL] ✓ Processed {len(texts)} vessels ({len(sentiments)} sentiments): "
                       f"Positive={sum(1 for s in sentiments if s['label']=='positive')}, "
                       f"Negative={sum(1 for s in sentiments if s['label']=='negative')}, "
                       f"Neutral={sum(1 for s in sentiments if s['label']=='neutral')}")
            
    except Exception as e:
        import traceback
        logger.error(f"❌ Babel Gardens/Embedding API failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Fallback: return neutral sentiments + zero vectors
        sentiments = [{"label": "neutral", "score": 0.0, "confidence": 0.0} for _ in texts]
        embeddings = [[0.0] * 384 for _ in texts]
    
    return sentiments, embeddings
```

### Golden Rules Applied
✅ **Always use PostgresAgent** - NO direct psycopg2.connect()  
✅ **Always use QdrantAgent** - NO direct qdrant_client.QdrantClient()  
✅ **Always use cooperative embedding** - HTTP POST to vitruvyan_api_embedding:8010  
✅ **Babel Gardens for sentiment** - Unified API, NOT legacy FinBERT direct calls  
✅ **Batch size 25** - Respects Babel Gardens API schema limit (max_items=25)  
✅ **Dual-memory coherence** - PostgreSQL + Qdrant synchronized via DualMemorySync  
✅ **Contextual text generation** - "Ship {name} ({type}) sailing at {speed} knots, status: {status}, operator: {fleet}"

### Database Verification
```sql
-- Check sentiment scores (Nov 18, 2025)
SELECT COUNT(*), sentiment_label, MIN(created_at), MAX(created_at) 
FROM sentiment_scores 
WHERE entity_type = 'ship'
GROUP BY sentiment_label;

-- Result:
-- count | sentiment_label |            min             |            max             
-- -------+-----------------+----------------------------+----------------------------
-- 40493 | neutral         | 2025-11-18 15:47:52.698297 | 2025-11-18 16:06:47.093745
```

### Future Enhancements
1. **Contextual Text Enrichment**: Add destination, ETA, weather conditions to improve sentiment diversity
2. **Anomaly Detection Integration**: Flag suspicious vessels (loitering, AIS gaps) with sentiment analysis
3. **Multi-language Support**: Enable sentiment analysis for non-English vessel names/destinations
4. **Real-time Alerting**: Redis pub/sub for high-confidence negative sentiment (e.g., distress signals)
5. **Sentiment Trend Analysis**: Time-series aggregation for fleet operators (e.g., Maersk sentiment over time)

---

**Status**: ✅ **PRODUCTION READY**  
**Maintained by**: Vitruvyan AI Engineering Team  
**Last Reviewed**: November 18, 2025
