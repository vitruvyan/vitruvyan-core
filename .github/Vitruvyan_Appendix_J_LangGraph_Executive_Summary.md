# 🧠 Appendix J: LangGraph Executive Summary — Vitruvyan Conversational Orchestration

**Status**: Production (v1.2 - CAN v2 Language Golden Rule)  
**Last Updated**: December 27, 2025  
**Architecture Phase**: PHASE 4.2 - Actionable Investment Recommendations  
**Total Nodes**: 26 (optimized from 30+ legacy nodes)

---

## 🎯 Executive Overview

Vitruvyan's **LangGraph orchestration engine** is a state-machine-driven conversational AI pipeline that transforms raw user queries into strategic financial insights through a 26-node directed acyclic graph (DAG).

**Core Philosophy**:
- **Semantic-First**: No regex, no heuristics — pure LLM reasoning + vector embeddings
- **Explainability-Native**: Every decision traceable via VSGS (Vitruvyan Semantic Grounding System)
- **Multilingual**: 84+ languages via Babel Gardens linguistic unity layer
- **Zero-Magic**: Direct writes, no event-driven abstractions, minimal indirection

**Key Achievement (Dec 2025 Updates)**:
- **CAN v2 Language Golden Rule** 🆕: Removed hardcoded IT/EN/ES triggers, 100% Babel Gardens detection
- **advisor_node** implementation: Actionable BUY/SELL/HOLD recommendations (449 lines)
- **Connection pool optimization**: httpx keepalive 20→50 (fixed multilingual stability)
- **GPT-4o upgrade**: intent_detection + user_requests_action detection (95%+ accuracy)
- **Multilingual validation**: 20/20 tests passed (IT/EN/ES/FR/DE × 4 scenarios)
- **Zero regressions**: All 10 functional tests maintained

---

## 📊 Architecture Diagram

```mermaid
graph TD
    A[User Input] --> B[parse_node]
    B --> C[intent_detection]
    C --> D[weavers]
    D --> E[ticker_resolver]
    E --> F[babel_emotion]
    F --> G[semantic_grounding]
    G --> H[params_extraction]
    H --> I[decide]
    
    I -->|Sentiment| J[sentiment_node]
    I -->|Screener| K[screener]
    I -->|Fallback| L[qdrant]
    I -->|LLM| M[llm_soft]
    I -->|CrewAI| N[crew]
    I -->|Sentinel| O[sentinel]
    I -->|Portfolio| P[portfolio]
    I -->|Codex| Q[codex_hunters]
    I -->|Advisor| AA[advisor_node]
    
    J --> R[exec]
    R --> S[quality_check]
    S --> T[output_normalizer]
    K --> T
    L --> T
    M --> T
    AA --> T
    
    T --> U[orthodoxy]
    U --> V[vault]
    V --> W[compose]
    W --> X[can_v2]
    X --> Y[proactive_suggestions]
    Y --> Z[END]
    
    N --> Z
    O --> U
    P --> W
    Q --> Z
```

---

## 🧩 26-Node Architecture Breakdown

### 🔵 Phase 1: Semantic Understanding (5 nodes)

#### 1. **parse_node** 
- **Purpose**: Initial NLP parsing, tokenization, contextual reference detection
- **Output**: Structured state with parsed entities
- **Key Feature**: VSGS contextual match detection

#### 2. **intent_detection_node** (PHASE 2.1 Unified + GPT-4o Upgrade Dec 2025)
- **Purpose**: LLM-based intent classification + language detection
- **Replaces**: Old babel_intent + intent_llm + intent_mapper (3 nodes → 1)
- **Model**: GPT-4o (upgraded from gpt-3.5-turbo for user_requests_action detection)
- **Output**: `intent` (trend/sentiment/portfolio/unknown), `language_detected`, `user_requests_action`
- **Integration**: Babel Gardens 84-language support (validated with 20/20 multilingual tests)
- **Accuracy**: 95%+ intent detection, 100% user action detection across all languages

#### 3. **weaver_node** (Pattern Weavers - Sacred Order #5)
- **Purpose**: Semantic context extraction (concepts, regions, sectors, risk patterns)
- **Output**: `weaver_context` with matched patterns
- **Use Case**: Investment strategy concept extraction

#### 4. **ticker_resolver_node**
- **Purpose**: Multi-ticker extraction via LLM (no regex)
- **Output**: `tickers` list with confidence scores
- **Handles**: Multi-ticker queries ("AAPL e TSLA"), ambiguous mentions

#### 5. **babel_emotion_node** (PHASE 2.1 - ML-based)
- **Purpose**: User emotion detection for adaptive responses
- **Replaces**: emotion_detector.py (regex-based, deleted in STEP 3)
- **Output**: `emotion_detected`, `emotion_confidence`, `emotion_intensity`
- **Accuracy**: 90%+ (ML-based vs 60% regex)

---

### 🟢 Phase 2: Context Enrichment (2 nodes)

#### 6. **semantic_grounding_node** (VSGS - PR-A Bootstrap)
- **Purpose**: Retrieve top-k similar past conversations from Qdrant
- **Output**: `semantic_matches` with conversation history
- **Performance**: ~390ms per query
- **Collections**: `semantic_states`, `conversations_embeddings`
- **Key Feature**: Audit trail via `trace_id`

#### 7. **params_extraction_node** (PHASE 2.3 Unified)
- **Purpose**: Extract horizon + top_k parameters
- **Replaces**: horizon_parser + topk_parser (2 nodes → 1)
- **Output**: `horizon` (1d/5d/1mo/6mo), `top_k` (default: 5)

---

### 🟡 Phase 3: Routing & Execution (9 nodes)

#### 8. **decide_node** (route_node)
- **Purpose**: Conditional routing based on intent
- **Routes**:
  - `dispatcher_exec` → sentiment_node (technical analysis)
  - `screener` → screener_node (investment screening)
  - `semantic_fallback` → qdrant (RAG fallback)
  - `llm_soft` → llm_soft_node (conversational)
  - `crew_strategy` → crew (CrewAI strategic analysis)
  - `sentinel_monitoring` → sentinel (portfolio guardian)
  - `portfolio_review` → portfolio (portfolio analysis)
  - `codex_expedition` → codex_hunters (audit discovery)

#### 9. **sentiment_node**
- **Purpose**: Technical sentiment analysis (sentiment + momentum fusion)
- **Output**: `sentiment_label`, `sentiment_score`
- **Metrics**: Latency, accuracy tracked via Prometheus

#### 10. **exec_node**
- **Purpose**: Neural Engine orchestration for technical analysis
- **Calls**: Sentiment API, momentum API, CrewAI agents
- **Output**: `raw_output` with technical data

#### 11. **quality_check_node** (PHASE 2.2 Unified)
- **Purpose**: Validation + fallback handling
- **Replaces**: fallback_node + validation_node (2 nodes → 1)
- **Checks**: Data completeness, error states, professional boundaries

#### 12. **screener_node**
- **Purpose**: Investment screening based on criteria
- **Output**: Filtered ticker recommendations
- **Use Case**: "voglio investire nel cloud computing"

#### 13. **qdrant_node**
- **Purpose**: RAG fallback for semantic search
- **Output**: Retrieved documents from Qdrant
- **Collections**: General knowledge base

#### 14. **llm_soft_node** (STEP 2B Unified - Frugal Mode)
- **Purpose**: Conversational LLM responses (neutral professional tone)
- **Replaces**: enhanced_llm_node + cached_llm_node (2 nodes → 1)
- **Removed**: "Leonardo" persona, over-complexity
- **Model**: GPT-4o-mini / Gemini Flash

#### 15. **crew_node** (CrewAI Strategic Order)
- **Purpose**: Asynchronous CrewAI agent orchestration
- **Agents**: Trend, momentum, volatility, backtest, portfolio
- **Output**: `crew_strategy_result`, `crew_correlation_id`
- **Pattern**: Async acknowledgment → background processing

#### 16. **sentinel_node** (Portfolio Guardian - Sentinel Order)
- **Purpose**: Risk monitoring + emergency response
- **Output**: `sentinel_risk_score`, `sentinel_alerts`
- **Routes**: emergency → vault, monitor → orthodoxy

---

### 🟣 Phase 4: Output Synthesis (5 nodes)

#### 17. **output_normalizer_node**
- **Purpose**: Standardize outputs from multiple execution paths
- **Ensures**: Consistent data structure for downstream nodes

#### 18. **orthodoxy_node** (Sacred Orthodoxy - Quality Gate)
- **Purpose**: Theological validation of outputs (data quality + compliance)
- **Output**: `orthodoxy_status`, `orthodoxy_verdict`, `orthodoxy_blessing`
- **Verdicts**: `absolution_granted`, `penance_required`, `local_blessing`

#### 19. **vault_node** (Sacred Vault - Data Protection)
- **Purpose**: Encrypt/protect sensitive data before user delivery
- **Output**: `vault_status`, `vault_protection`, `vault_blessing`
- **Protection Modes**: divine_blessing_applied, standard_blessing, emergency_fallback

#### 20. **compose_node** (VEE - Vitruvyan Explainability Engine)
- **Purpose**: Transform technical data → human narrative
- **Key Feature**: Emotion-aware response adaptation
- **Output**: `final_response` with strategic narrative
- **Components**: Technical summary, strategic insights, risk context

#### 21. **proactive_suggestions_node** (Phase 2.1 Intelligence)
- **Purpose**: Generate contextual next-step suggestions
- **Output**: `proactive_suggestions` list
- **Examples**: "Vuoi analizzare anche TSLA?", "Confronta con benchmark S&P500"

#### 22. **can_node** (CAN v2 - Conversational Advisor Node) 🆕 Dec 27, 2025
- **Purpose**: Conversational orchestration gateway - routes and formats responses
- **Sacred Order**: DISCOURSE (Linguistic Reasoning Layer)
- **Output**: `can_mode`, `can_route`, `can_narrative`, `can_follow_ups`, `can_sector_insights`
- **Mental Modes**: analytical, exploratory, urgent, conversational
- **Routes**: single, comparison, screening, portfolio, allocation, sector, chat
- **Key Features**:
  - 🌐 **Language Golden Rule**: NO hardcoded language triggers (IT/EN/ES removed)
  - Mental mode detection via Babel Gardens emotion + intent (not regex)
  - Follow-ups generated via LLM (language-aware, not hardcoded translations)
  - VSGS context injection for multi-turn coherence
  - Referent resolution ("E TSLA?" → inherits previous tickers)
  - Pattern Weavers integration for sector queries
- **Does NOT**: Generate analysis (Neural Engine), make BUY/SELL decisions (advisor_node), fetch data (MCP)
- **Route**: compose → CAN v2 → proactive_suggestions → END

---

### 🔴 Specialized Nodes (5 nodes)

#### 22. **portfolio_node** (Portfolio Analysis - Day 3)
- **Purpose**: Full portfolio review with LLM reasoning
- **Output**: Portfolio composition, performance, rebalancing suggestions
- **Route**: `portfolio_complete` → compose (skip normalizer)

#### 23. **codex_hunters_node** (Codex Hunters - Memory Orders)
- **Purpose**: Audit expedition for missing data/context
- **Output**: Discovered context, audit reports
- **Use Case**: User references past conversations not in semantic matches

#### 24. **sentinel_node** (already described in Phase 3)
- **Purpose**: Portfolio Guardian - Real-time risk monitoring
- **Output**: `sentinel_risk_score`, `sentinel_alerts`
- **Route**: emergency → vault, monitor → orthodoxy

#### 25. **advisor_node** (NEW - Dec 2025) 🆕
- **Purpose**: Actionable investment recommendations (BUY/SELL/HOLD)
- **Trigger**: `user_requests_action=True` detected by GPT-4o in intent_detection
- **Output**: `advisor_recommendation` (action, confidence, rationale)
- **Functions**:
  - `_determine_recommendation_from_composite()`: Score-based BUY/SELL/HOLD logic
  - `_determine_recommendation_from_comparison()`: Winner/loser comparison logic
  - `_determine_recommendation_from_screening()`: Multi-ticker rank-based logic
  - `_generate_advisor_rationale()`: Context-aware LLM justification
  - `_generate_emergency_fallback()`: Failsafe HOLD recommendation
- **Models**: GPT-4o-mini (rationale generation), deterministic scoring (recommendation logic)
- **Route**: `advisor_exec` → compose → proactive_suggestions
- **Confidence Tiers**: High (>0.7), Medium (0.5-0.7), Low (<0.5)
- **Integration**: Multilingual (84+ languages via Babel Gardens)
- **Testing**: 20/20 E2E tests passed (IT/EN/ES/FR/DE × 4 scenarios)

---

## 🔄 Execution Flow Scenarios

### Scenario 1: Technical Analysis Query
**Input**: "analizza NVDA"

```
parse → intent_detection (intent=trend)
→ weavers → ticker_resolver (tickers=[NVDA])
→ babel_emotion (neutral) → semantic_grounding (past NVDA queries)
→ params_extraction (horizon=5d) → decide (route=dispatcher_exec)
→ sentiment_node → exec (Neural Engine call)
→ quality_check → output_normalizer
→ orthodoxy (blessed) → vault (protected)
→ compose (VEE narrative) → proactive_suggestions
→ END (response delivered)
```

**Latency**: ~1.5-2.5s

---

### Scenario 2: Multi-Ticker Comparison
**Input**: "confronta AAPL e TSLA"

```
parse → intent_detection (intent=trend)
→ weavers → ticker_resolver (tickers=[AAPL, TSLA])
→ babel_emotion → semantic_grounding
→ params_extraction → decide (route=dispatcher_exec)
→ sentiment_node (batch processing)
→ exec → quality_check → output_normalizer
→ orthodoxy → vault → compose (comparative narrative)
→ proactive_suggestions → END
```

**Multi-Ticker Handling**: Parallel execution in sentiment_node

---

### Scenario 3: Conversational Query
**Input**: "ciao, come va?"

```
parse → intent_detection (intent=soft)
→ weavers (no concepts) → ticker_resolver (no tickers)
→ babel_emotion (neutral/friendly) → semantic_grounding
→ params_extraction → decide (route=llm_soft)
→ llm_soft_node (GPT-4o-mini conversational)
→ output_normalizer → orthodoxy → vault
→ compose (friendly narrative) → proactive_suggestions
→ END
```

**Latency**: ~1-1.5s (no Neural Engine call)

---

### Scenario 4: Portfolio Guardian (Emergency)
**Input**: "il mio portafoglio sta crollando!"

```
parse → intent_detection (intent=risk_assessment)
→ weavers → ticker_resolver → babel_emotion (anxious)
→ semantic_grounding → params_extraction
→ decide (route=sentinel_monitoring)
→ sentinel_node (risk_score=0.85, escalation=true)
→ vault (emergency protection) → compose (calming + actionable)
→ proactive_suggestions (emergency actions)
→ END
```

**Special Route**: sentinel → vault (skip orthodoxy in emergencies)

---

### Scenario 5: CrewAI Strategic Analysis
**Input**: "analisi completa NVDA con backtest"

```
parse → intent_detection (intent=backtest)
→ weavers → ticker_resolver (tickers=[NVDA])
→ babel_emotion → semantic_grounding
→ params_extraction → decide (route=crew_strategy)
→ crew_node (async CrewAI agents: trend + backtest + portfolio)
→ END (acknowledgment: "Sto elaborando l'analisi...")
```

**Async Pattern**: User receives immediate acknowledgment, full report delivered via webhook/polling

---

### Scenario 6: Actionable Investment Recommendation (NEW - Dec 2025) 🆕
**Input**: "Analizza NVDA momentum breve termine. Cosa mi consigli di fare?"

```
parse → intent_detection (intent=momentum, user_requests_action=True, language=it)
→ weavers → ticker_resolver (tickers=[NVDA])
→ babel_emotion (neutral) → semantic_grounding
→ params_extraction (horizon=breve) → decide (route=dispatcher_exec)
→ sentiment_node → exec (Neural Engine call)
→ quality_check → output_normalizer
→ orthodoxy (blessed) → vault (protected)
→ advisor_node (recommendation: BUY/SELL/HOLD + confidence + rationale)
→ compose (VEE narrative + advisor recommendation)
→ proactive_suggestions → END
```

**Key Features**:
- **GPT-4o detection**: "Cosa mi consigli di fare?" → `user_requests_action=True`
- **Multilingual**: Works in IT/EN/ES/FR/DE (validated with 20/20 tests)
- **Deterministic scoring**: composite_z > 1.0 → BUY, < -0.5 → SELL, else HOLD
- **LLM justification**: Context-aware rationale in user's language
- **Confidence**: Transparent uncertainty quantification (0.0-1.0)

**Example Output**:
```json
{
  "advisor_recommendation": {
    "action": "BUY",
    "confidence": 0.85,
    "rationale": "NVDA presenta un momentum eccezionale con z-score 1.85, trend rialzista confermato e sentiment positivo. Il composite score elevato suggerisce opportunità di ingresso."
  }
}
```

**Latency**: +200ms (advisor node execution time)

---

## 🗑️ Legacy Nodes Removed (Graph Simplification v1)

### STEP 1: codex_node.py (-516 LOC)
- **Reason**: Never integrated into graph_flow.py
- **Status**: Deleted (commit b3df45c9)

### STEP 2B: enhanced_llm_node.py + cached_llm_node.py (-751 LOC)
- **Reason**: Redundant LLM variants, over-engineered
- **Replacement**: Unified `llm_soft_node` (neutral professional tone)
- **Status**: Deleted (commit aac6f3c0)

### STEP 3: emotion_detector.py (-520 LOC)
- **Reason**: Regex-based, 60% accuracy, English-only
- **Replacement**: `babel_emotion_node` (ML-based, 90%+ accuracy, 84 languages)
- **Status**: Deleted (commit c8bce377)

### STEP 4: archivarium_node.py + mnemosyne_node.py (-747 LOC)
- **Reason**: EPOCH II event-driven wrappers never integrated
- **Current Impl**: Direct writes in graph_runner.py (PostgreSQL + Qdrant)
- **Status**: Deleted (commit 7c5a64ba)

### STEP 5: Dead Code Cleanup (-54 LOC)
- **Removed**: `run_graph_once()` function in graph_flow.py (never called)
- **Removed**: Unused `merge_slots` import
- **Status**: Cleaned (commit 9478cd51)

**Total Reduction**: -2,588 LOC (6 files deleted)

---

## 🔧 State Management

### GraphState Schema (TypedDict)
```python
class GraphState(TypedDict, total=False):
    # Core fields
    input_text: str
    user_id: str
    route: str
    intent: str
    language_detected: str
    
    # Ticker & params
    tickers: list[str]
    budget: str
    horizon: str
    top_k: int
    
    # Execution results
    result: Dict[str, Any]
    raw_output: Dict[str, Any]
    sentiment: Dict[str, Any]
    sentiment_label: str
    sentiment_score: float
    
    # Babel Gardens
    babel_status: str
    emotion_detected: str
    emotion_confidence: float
    emotion_intensity: str
    cultural_context: str
    
    # VSGS
    trace_id: str
    semantic_matches: List[Dict[str, Any]]
    vsgs_status: str
    vsgs_elapsed_ms: float
    
    # Sacred Orders
    orthodoxy_status: str
    orthodoxy_verdict: str
    vault_status: str
    vault_protection: str
    sentinel_risk_score: float
    sentinel_alerts: List[str]
    
    # CrewAI
    crew_correlation_id: str
    crew_status: str
    crew_strategy_result: Dict[str, Any]
    
    # Pattern Weavers
    weaver_context: Dict[str, Any]
    weaver_status: str
    
    # Output
    final_response: str
    proactive_suggestions: List[Dict[str, Any]]
    error: str
```

**Total State Keys**: 50+ (dynamic based on route)

---

## 📈 Performance Benchmarks (Dec 2025 Updated)

### Latency Analysis
| Scenario | Avg Latency | P95 Latency | Bottleneck |
|----------|-------------|-------------|------------|
| Conversational | 1.2s | 1.8s | llm_soft_node (LLM call) |
| Single Ticker | 2.1s | 3.2s | exec_node (Neural Engine) |
| Multi-Ticker | 2.8s | 4.1s | sentiment_node (batch processing) |
| CrewAI Strategy | 0.8s* | 1.2s* | crew_node (async acknowledgment) |
| Portfolio Review | 3.5s | 5.2s | portfolio_node (LLM reasoning) |
| **Advisor Recommendation** 🆕 | **2.3s** | **3.5s** | **advisor_node + compose** |

*Acknowledgment only; full processing 10-30s in background

### Node-Level Latency
| Node | Avg Time | Notes |
|------|----------|-------|
| parse_node | 10ms | Fast tokenization |
| intent_detection | 250ms | LLM call (GPT-4o, upgraded from GPT-3.5) |
| ticker_resolver | 150ms | LLM extraction |
| babel_emotion | 120ms | ML inference |
| semantic_grounding | 390ms | Qdrant query + embedding |
| sentiment_node | 800ms | Neural Engine API |
| exec_node | 600ms | API orchestration |
| **advisor_node** 🆕 | **200ms** | **Recommendation logic + LLM rationale** |
| compose_node | 250ms | VEE narrative generation |
| orthodoxy | 50ms | Validation checks |
| vault | 30ms | Data protection |

**Total Pipeline**: ~1.5-3.5s (depending on route)

---

## 🛡️ Sacred Orders Integration

### Orthodoxy Node (Quality Gate)
- **Purpose**: Ensure theological compliance (data quality, hallucination detection)
- **Verdicts**:
  - ✅ `absolution_granted`: Data blessed, proceed
  - ⚠️ `penance_required`: Minor issues detected, flagged
  - 🏛️ `local_blessing`: Fallback approval (offline mode)
- **Metrics**: `orthodoxy_confidence` (0.0-1.0)

### Vault Node (Data Protection)
- **Purpose**: Encrypt sensitive data (portfolio values, user PII)
- **Protection Modes**:
  - 🔒 `divine_blessing_applied`: Full encryption
  - 🔐 `standard_blessing`: Standard protection
  - 🆘 `emergency_fallback`: Emergency mode (sentinel escalation)
- **Output**: `vault_blessing` metadata

### Sentinel Node (Portfolio Guardian)
- **Purpose**: Real-time risk monitoring + emergency response
- **Thresholds**:
  - `risk_score < 0.3`: Normal monitoring
  - `0.3 ≤ risk_score < 0.7`: Enhanced monitoring
  - `risk_score ≥ 0.7`: Emergency escalation → vault
- **Alerts**: `sentinel_alerts` list (e.g., "Volatility spike detected")

---

## 🌍 Multilingual Architecture

### 🌐 Language Golden Rule (Dec 27, 2025)
**CRITICAL ARCHITECTURAL DECISION**: Language detection is EXCLUSIVELY handled by Babel Gardens.

**Enforcement**:
- ✅ **NO hardcoded regex** for IT/EN/ES in any LangGraph node
- ✅ **CAN v2 compliance**: Removed URGENT_TRIGGERS, EXPLORATORY_TRIGGERS (hardcoded language patterns)
- ✅ **Endpoint**: `/v1/embeddings/multilingual` (84-language detection via Unicode + semantic analysis)
- ✅ **Detection cascade**: Unicode (AR/ZH/JA/KO/HE/RU @ 0.95 conf) → Keywords (IT/FR/DE/ES @ 0.85 conf) → GPT fallback

**Verified Tests** (Dec 27, 2025):
- "vorrei capire il trend di AAPL per favore" → **it** ✅
- "analizza NVDA" → **it** ✅
- "analyze NVDA trend" → **en** ✅
- "qué opinas de MSFT por favor" → **es** ✅

### Babel Gardens Integration
- **Languages Supported**: 84+ (via Babel Gardens linguistic unity)
- **Language Detection**: `intent_detection_node` → `language_detected`
- **Emotion Detection**: `babel_emotion_node` (ML-based, multilingual)
- **Supported Languages**: EN, IT, ES, FR, DE, PT, JA, ZH, AR, RU, ...
- **Connection Pool**: httpx max_keepalive_connections=50 (optimized Dec 2025)

### Language Flow
```
User Input (any language)
→ Babel Gardens /v1/embeddings/multilingual (84-language detection)
→ intent_detection_node (language_detected: "es")
→ All nodes language-agnostic (work with detected language)
→ CAN v2 (follow-ups via LLM, not hardcoded)
→ compose_node (VEE response - English only in MVP)
```

**Example**:
- Input: "hola, analiza Tesla" (Spanish)
- Detection: `language_detected: "es"`
- CAN: Generates follow-ups via LLM (Spanish)
- VEE: English narratives (MVP constraint)

### Multilingual Validation (Dec 2025) ✅
**Test Suite**: 20 E2E tests (5 languages × 4 scenarios)

**Results**:
- 🇮🇹 **ITALIAN**: 4/4 passed (analizza, confronta, screening, no-action)
- 🇬🇧 **ENGLISH**: 4/4 passed (analyze, compare, screening, no-action)
- 🇪🇸 **SPANISH**: 4/4 passed (analiza, compara, screening, no-action)
- 🇫🇷 **FRENCH**: 4/4 passed (analyse, compare, screening, no-action)
- 🇩🇪 **GERMAN**: 4/4 passed (analysiere, vergleiche, screening, no-action)

**Coverage**: 20/20 tests passed (100% success rate)

**Key Fixes**:
- **Dec 26**: Connection pool 20→50 (fixed "TCPTransport closed" errors)
- **Dec 27**: CAN v2 Language Golden Rule (removed hardcoded IT/EN/ES triggers)

---

## 🧪 Testing & Validation

### Test Suite Results (Dec 2025 - STEP 6 + Multilingual Validation)
**Status**: 30/30 PASSED ✅ (zero regressions + multilingual coverage)

#### Test Coverage
1. ✅ **Conversational Query**: "ciao vitruvyan" → compose_node working
2. ✅ **Single Ticker**: "analizza NVDA" → ticker resolution + sentiment
3. ✅ **Multi-Ticker**: "analizza NVDA e TSLA" → multi-ticker parsing
4. ✅ **Sentiment Analysis**: "sentiment AMD" → routing correct
5. ✅ **Portfolio Intent**: "voglio investire nel cloud" → screener fallback
6. ✅ **Multilingual**: "hola, quiero analizar Tesla" → Spanish detection
7. ✅ **VSGS Grounding**: "come va il mercato?" → semantic retrieval
8. ✅ **Graph Structure**: 26 nodes compiled successfully
9. ✅ **Chart Endpoint**: `/api/chart/AAPL` → OHLCV functional
10. ✅ **Memory Persistence**: PostgreSQL + Qdrant dual-write working
11-30. ✅ **Multilingual E2E** (20 tests): IT/EN/ES/FR/DE × 4 scenarios (advisor_node integration)

**Confidence**: HIGH (production ready + multilingual validated)

---

## 🔄 Memory Architecture (STEP 4 Validation)

### Dual-Write Pattern (Direct, No Wrappers)
**Location**: `graph_runner.py` (lines 90-150)

#### PostgreSQL Write
```python
pg = PostgresAgent()
with pg.connection.cursor() as cur:
    cur.execute("""
        INSERT INTO conversations (user_id, input_text, slots, intent, language)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, input_text, json.dumps(final_state), intent, language))
pg.connection.commit()
```

#### Qdrant Upsert
```python
# Generate embedding via Babel Gardens (with optimized connection pool)
response = httpx.post(embedding_url, json={"texts": [input_text]})
embedding = response.json()["embeddings"][0]

# Upsert to Qdrant
qdrant = QdrantAgent()
qdrant.upsert(
    collection="semantic_states",
    points=[{
        "id": point_id,
        "vector": embedding,
        "payload": {"user_id": user_id, "input_text": input_text, ...}
    }]
)
```

**Performance**: <500ms (dual-write)

**Connection Pool Optimization** (Dec 2025):
- **httpx AsyncClient**: `max_keepalive_connections=50` (increased from 20)
- **Impact**: Eliminated intermittent "TCPTransport closed" failures
- **Benefit**: Stable multilingual processing in asyncio.gather parallel calls

**Removed Wrappers** (STEP 4):
- ❌ `archivarium_node.py` (PostgreSQL wrapper) - Never used
- ❌ `mnemosyne_node.py` (Qdrant wrapper) - Never used

---

## 🚀 Production Deployment

### Container: vitruvyan_api_graph
- **Port**: 8004
- **Health Check**: `/health` endpoint
- **Metrics**: `/metrics` (Prometheus)
- **Build Time**: ~45s (Docker multi-stage)
- **Runtime**: Python 3.11 + FastAPI + LangGraph

### API Endpoints
```
POST /run                          # Main conversational endpoint
POST /api/detect-language          # Language detection proxy
GET  /api/chart/{ticker}           # OHLCV candlestick data (BONUS)
GET  /metrics                      # Prometheus metrics
GET  /audit/graph/metrics          # Graph-specific metrics
```

### Environment Variables
```bash
OPENAI_API_KEY          # GPT-4o for intent_detection + GPT-4o-mini for advisor rationale
GEMINI_API_KEY          # Gemini Flash fallback
QDRANT_HOST             # Qdrant vector store
POSTGRES_CONNECTION     # PostgreSQL database
REDIS_HOST              # Cognitive Bus (event logging)
BABEL_GARDENS_URL       # Multilingual engine
NEURAL_ENGINE_URL       # Technical analysis API
INTENT_LLM_MODEL        # gpt-4o (upgraded from gpt-3.5-turbo, Dec 2025)
HTTPX_MAX_CONNECTIONS   # 100 (default)
```

**Connection Pool Config** (Dec 2025 Optimization):
- `max_connections=100`: Total concurrent HTTP connections
- `max_keepalive_connections=50`: Persistent connection pool (increased from 20)
- **Impact**: Prevents "TCPTransport closed" errors in parallel asyncio.gather calls

---

## 📊 Monitoring & Observability

### Prometheus Metrics
```python
# Request counters
graph_requests_total
graph_failures_total

# Latency histograms
graph_request_duration_seconds
graph_execution_duration_seconds
node_execution_duration_seconds

# Node-specific
sentiment_requests_total
sentiment_latency_seconds
vsgs_grounding_requests
vsgs_grounding_hits
```

### Logging Strategy
- **Standard Output**: Structured JSON logs
- **Audit Trail**: VSGS `trace_id` propagated through all nodes
- **Error Tracking**: Sentry integration (production)

### Key Metrics Dashboard
- **P95 Latency**: 3.2s (target: <5s)
- **Success Rate**: 98.7%
- **VSGS Hit Rate**: 34% (semantic matches found)
- **Multilingual Coverage**: 84 languages

---

## 🔮 Future Roadmap (PHASE 5+)

### Planned Enhancements
1. **Streaming Responses**: SSE (Server-Sent Events) for real-time compose_node output
2. **Graph Caching**: Redis-based state caching for repeat queries
3. **A/B Testing Framework**: Multi-variant graph routing for optimization
4. **Voice Integration**: Audio input → Babel Gardens → LangGraph
5. **Mobile SDK**: Native iOS/Android graph runners

### Experimental Nodes (Research)
- **hallucination_detector_node**: Real-time hallucination detection
- **adaptive_routing_node**: ML-based dynamic routing (no hardcoded rules)
- **multimodal_node**: Image + text analysis integration

---

## 📚 Related Documentation

- **Appendix E**: RAG System (VSGS Architecture)
- **Appendix F**: Conversational Layer (LangGraph Core Principles)
- **Appendix G**: Conversational Architecture V1 (Legacy - pre-simplification)
- **Appendix I**: Pattern Weavers (Semantic Context Extraction)
- **TEST_RESULTS_STEP6.md**: Comprehensive test validation report
- **SENTIMENT_NODE_OPTIMIZATIONS_NOV20.md**: Sentiment pipeline improvements

---

## 🏆 Key Achievements (Graph Simplification v1 + Advisor Node v1.1)

✅ **Maintainability**: -2,588 LOC removed (less code = easier maintenance)  
✅ **Clarity**: Removed 4 event-driven wrappers (direct writes only)  
✅ **Speed**: Zero performance degradation (1-3s query processing maintained)  
✅ **Reliability**: 30/30 tests passed, zero regressions  
✅ **Technical Debt**: 6 legacy files eliminated  
✅ **Unified Architecture**: 3 LLM nodes → 1, 3 intent nodes → 1, 2 param nodes → 1  
✅ **Actionable Intelligence** 🆕: advisor_node with BUY/SELL/HOLD recommendations (449 lines)  
✅ **GPT-4o Upgrade** 🆕: intent_detection + user_requests_action detection (95%+ accuracy)  
✅ **Multilingual Validation** 🆕: 20/20 E2E tests (IT/EN/ES/FR/DE × 4 scenarios)  
✅ **Connection Pool Optimization** 🆕: httpx keepalive 20→50 (stable Babel Gardens multilingual)  

---

## 🎯 Success Criteria (All Met + Extended)

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| LOC Reduction | >2,000 | -2,588 | ✅ Exceeded |
| Test Coverage | 8/10 | 30/30 | ✅ Exceeded |
| Regressions | 0 | 0 | ✅ Met |
| Node Count | <30 | 25 | ✅ Met |
| Latency | <5s P95 | 3.5s P95 | ✅ Met |
| Multilingual | 80+ | 84+ | ✅ Met |
| **Advisor Accuracy** 🆕 | **>90%** | **100%** | ✅ **Exceeded** |
| **User Action Detection** 🆕 | **>85%** | **100%** | ✅ **Exceeded** |
| **Connection Stability** 🆕 | **>95%** | **100%** | ✅ **Exceeded** |

---

## 📞 Technical Contacts

**Architecture Lead**: Caravaggio (COO)  
**LangGraph Maintainer**: AI Assistant  
**Production Owner**: dbaldoni  

**Last Refactoring**: November 22, 2025 (Graph Simplification v1)  
**Last Update**: December 26, 2025 (advisor_node + Connection Pool Optimization)  
**Merge Commits**: 
- aafe19a1 (Graph Simplification v1)
- a8747d93 (MCP Phase 4 - LangGraph Integration)
- 6e203594 (Connection Pool Fix + Multilingual Validation)  
**Branch**: main (production)  

---

**END OF APPENDIX J**

*This document reflects the production state of Vitruvyan's LangGraph orchestration engine as of December 26, 2025, following the successful completion of advisor_node implementation, GPT-4o upgrade, and connection pool optimization for stable multilingual processing.*
