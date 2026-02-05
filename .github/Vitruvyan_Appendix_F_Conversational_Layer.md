# 🤖 Copilot Instructions — Vitruvyan OS (2025 Final Conversational Phase)

## 🧭 Vision & Mission

Vitruvyan is not a chatbot.  
It is a cognitive operating system that reasons, explains, and adapts.

Its purpose is to act as a **human-centric advisor** — not to simulate empathy, but to *practice* understanding through reason, language, and transparency.  
Every interaction must preserve epistemic integrity: every word traceable to data, every answer a reflection of analysis.

> **Vitruvyan does not respond — it interprets.**

---

## ⚙️ Core Principles for Copilot

1. **Never build heuristics when reasoning is possible.**  
   Prefer semantic comprehension (LLM + embeddings) over hard-coded conditions or regex.

2. **Language is an epistemic act.**  
   The user’s phrasing carries intention, emotion, and uncertainty. Interpret all three.

3. **Data ≠ Truth.**  
   Data is evidence. Truth is derived through explainable inference (Neural Engine + VEE).

4. **Human Tone.**  
   Every response must feel like an analyst explaining a decision — confident, not mechanical; analytical, not dramatic.

5. **Transparency over performance.**  
   Every agent output must be explainable, logged, and reconstructible.

---

## 🧩 Architecture Map (Conversational Flow)

User Input
↓
Semantic Engine (context enrichment via Qdrant)
↓
Intent LLM Node (intent detection + slot filling)
↓
Route Node (scenario selection)
↓
Exec Node (Neural Engine or Crew Agents)
↓
Compose Node (VEE + LLM reasoning synthesis)
↓
Frontend (UI rendering of strategic cards, gauges, or onboarding wizard)

markdown
Copia codice

### Layer Roles

| Layer | Role | Key File |
|-------|------|-----------|
| **Semantic Engine** | Context retrieval, multilingual disambiguation | `semantic_engine.py` |
| **Intent LLM Node** | Primary intent recognition (LLM-driven) | `intent_llm_node.py` |
| **LangGraph** | Flow orchestration and state management | `graph_flow.py`, `graph_runner.py` |
| **VEE (Vitruvyan Explainability Engine)** | Translating quantitative data → human reasoning | `explainability_agent.py` |
| **Compose Node** | Narrative composition, empathy, and final output | `compose_node.py` |
| **Frontend UI** | Manifestation layer (strategic cards, tables, wizards) | Vercel / v0.dev project |

---

## 🧠 Intent Architecture (Post-Regex Revision — November 2025)

**Status:** ACTIVE — Regex deprecated, LLM first.

Vitruvyan now employs a fully semantic **LLM-first** architecture for intent detection and conversational reasoning.  
Regex patterns have been removed because they restrict linguistic flexibility and cross-lingual understanding.

### New Cascade
User → Semantic Engine (context enrichment)
→ LLM Intent Classifier (GPT-4o-mini or Gemini)
→ Professional Validation Layer (domain constraints)
→ Graph Routing (route_node)
→ Compose Node (VEE explainability)

markdown
Copia codice

### Design Principle
> **Vitruvyan does not detect patterns — it understands meaning.**  
> The language is not a set of tokens, but a living epistemic act.

### Copilot Rules
- ❌ Never create or modify regex patterns.  
- ✅ Always implement new intent logic through the LLM pipeline.  
- ✅ Each LLM decision must log `intent`, `confidence`, `context`.  
- ✅ If `confidence < 0.6`, produce a clarification question rather than an assumption.  
- ✅ Preserve chain-of-proof: all reasoning must reference underlying data.  
- ✅ Maintain multilingual consistency (via Babel Gardens embeddings).

---

## 🌍 Language-First Architecture (November 21, 2025)

**CRITICAL UPDATE**: All language detection now enforced at ingestion time.

### The Problem (Pre-Nov 21)
User reported: "analizza NVDA momentum" (Italian) → system responded in **English**.

**Root Cause**: Triple-layered language overwrite bug:
1. `intent_detection_node` correctly detected "it"
2. `babel_emotion_node` overwrote to "en" (from Gemma keyword matching)
3. `graph_runner` overwrote again to "auto" (from emotion_metadata)
4. `compose_node` received "auto" → defaulted to English

### The Solution: Language-First Enforcement

#### 1. State Management Rules
**NEW**: Language flows through state **without overwrites**:
```python
# ✅ CORRECT: Read language, never overwrite
def babel_emotion_node(state: Dict[str, Any]) -> Dict[str, Any]:
    language = state.get("language", "auto")  # READ ONLY
    # ... emotion detection logic ...
    return {"emotion_detected": emotion}  # NO language key

# ✅ CORRECT: Use language_detected key
def graph_runner(state: Dict[str, Any]) -> Dict[str, Any]:
    state["language_detected"] = detected_lang
    # graph_runner NO LONGER overwrites state["language"]
```

**FORBIDDEN**:
```python
# ❌ WRONG: Overwriting state["language"]
state["language"] = "en"  # NEVER DO THIS after intent_detection
```

#### 2. Detection Flow (Enforced)
```
User Input → Babel Gardens (embedding_engine.py)
  ↓
Unicode Detection (AR/ZH/JA/KO/HE/RU/TH) → 95% conf, 0ms
  ↓ (if no match)
Qdrant Semantic Search (conversations_embeddings, threshold 0.60)
  ↓ (if no match)
Redis Cache (7-day TTL, hash-based)
  ↓ (if no match)
GPT-4o-mini Fallback ($0.000005/query)
  ↓ (if all fail)
Reject with "unknown" (NO silent EN fallback)
```

#### 3. QdrantAgent Enforcement
**File**: `core/leo/qdrant_agent.py`

All `upsert()` operations validate language:
```python
def upsert(self, collection: str, points: List[Dict[str, Any]]):
    """MANDATORY language validation (Nov 21, 2025)"""
    valid_languages = {"en", "it", "es", "fr", "de", "zh", "ar", ...}
    
    for p in points:
        language = p.get("payload", {}).get("language")
        if not language or language in ["null", "unknown", "auto", ""]:
            raise ValueError(f"Invalid language '{language}'. Must be ISO 639-1.")
```

#### 4. Babel Gardens dotenv Integration
**File**: `docker/services/api_babel_gardens/main.py`

```python
from dotenv import load_dotenv
load_dotenv("/app/.env")  # OPENAI_API_KEY now accessible
```

**Why Critical**: GPT-4o-mini fallback needs API key for cold-start detection.

#### 5. Seed Phrases Dataset
**File**: `docs_new/vitruvyan_seed_phrases_multilingual.jsonl`

- **1,065 phrases** across 5 languages (IT/EN/ES/FR/DE)
- **Purpose**: Ground truth for Qdrant semantic search
- **Ingestion**: `python3 scripts/ingest_seed_phrases.py`

### Testing Results
| Query (Language) | Detected | Method |
|------------------|----------|--------|
| "analizza NVDA" (IT) | ✅ it | GPT-4o-mini |
| "analyze Tesla momentum" (EN) | ✅ en | GPT-4o-mini |
| "qué tal AAPL?" (ES) | ✅ es | GPT-4o-mini |
| "comment va le trend de META?" (FR) | ✅ fr | GPT-4o-mini |
| "wie ist der Kurs von MSFT?" (DE) | ✅ de | GPT-4o-mini |

### Monitoring
- All detections logged to PostgreSQL `fusion_logs` table
- Language distribution tracked in `conversations_embeddings` metadata
- Hit rates: Qdrant (target 60%+), Redis (target 80%+), GPT (target <20%)

### References
- **Git Commit**: 69c42067 (Nov 21, 2025)
- **Appendix E**: Full RAG System documentation
- **Scripts**: `ingest_seed_phrases.py`, `qdrant_language_cleanup.py`

---

## 🪶 Conversational Reasoning Layer (Appendix H)

**Goal:** Transform Vitruvyan from reactive assistant to *proactive epistemic advisor*.

### Core Functions
1. **Slot Filling (Conversational)**
   - Context-aware questions instead of templates.  
   - Example:  
     “Su quale orizzonte temporale stai pensando? E hai preferenze sui settori?”

2. **Emotion Detection**
   - Detects five states: *frustrated, uncertain, excited, confident, neutral.*  
   - Adjusts tone accordingly (e.g., empathetic preface for frustration).

3. **Multi-Turn Bundling**
   - Groups related queries into one, reducing latency and friction.

4. **Scenario Routing**
   - Determines `conversation_type`: single_ticker, multi_ticker, or onboarding.  
   - Backend decides the visual layout accordingly.

5. **Dual-Layer Explainability**
   - Technical (for analysts) + Conversational (for users).  
   - Both persisted in `vee_explanations`.

6. **Narrative Composition**
   - Final message generated by `compose_node` combines reasoning, empathy, and visuals.

---

## 🧮 Explainability & Data Integrity

- All computations (momentum_z, trend_z, volatility_z, sentiment_z) come from **Neural Engine**.  
- VEE converts these into reasoning chains:
"Momentum high (+1.2σ), trend weak (−0.3σ)"
→ "Il titolo mostra forza di breve ma un trend incerto: possibile ritracciamento."

yaml
Copia codice
- Every narrative must be **verifiable**: user can request “mostrami i dati tecnici” → system returns raw values.
- All outputs logged to PostgreSQL (`conversation_logs`, `vee_explanations`).

---

## 🧰 Semantic Engine — Behavioral Contract

1. **Function:** enrich context, retrieve similar phrases, identify entities.  
2. **Prohibition:** it must *not* perform intent classification.  
3. **Outputs:** structured semantic evidence (`relevance_score`, `matched_phrases`, `language_detected`).  
4. **Fallback Handling:** when no intent is found, LLM re-interprets using enriched context.  
5. **Interface:** `find_similar_phrases()` → returns multilingual context vector.  

This ensures that cognition is **context-aware** but not **context-confused**.

---

## 🎨 Conversational UX Manifestation (Frontend)

### Required Components
| Component | Description | Status |
|------------|--------------|---------|
| **Strategic Card** | Final verdict + confidence + 4 gauges | Pending |
| **Comparison Table** | Multi-ticker ranking view | Pending |
| **Onboarding Wizard** | Interactive setup (budget, horizon, sectors) | Pending |
| **Conditional Rendering** | Dynamic layout by `conversation_type` | Pending |
| **Emotion Feedback** | UI color shift based on tone | Pending |

Frontend implementation must directly map backend cognitive outputs to visible experiences.

---

## 🧩 Performance & Logging Standards

- **Latency Target:** < 500 ms per LLM call.  
- **LLM Cost:** logged via Prometheus (`llm_cost_usd`, `llm_tokens`).  
- **Audit Trail:** every cognitive node logs start/end, latency, and reasoning trace.  
- **Recovery:** Fallback Node triggers empathetic message when NE or data unavailable.  
- **Replay:** conversations stored in `conversation_history` for future context retrieval.

---

## 🔒 Professional Boundaries

1. **No speculative financial advice.**  
 Recommendations must always derive from NE quantitative results.  
2. **Explain risk transparently.**  
 Never omit volatility or confidence level.  
3. **Always contextualize.**  
 Tie every insight to timeframe and market condition.  
4. **Preserve neutrality.**  
 Avoid emotionally manipulative tone.  
5. **Cultural adaptation.**  
 Tone, idioms, and symbols vary by detected language.

---

## 🧠 Copilot Operational Ethics

Copilot acts as *silent architect*, not author.  
When editing or generating code:

- Understand **why** the change exists before executing.  
- Maintain modularity: every new function belongs to a cognitive layer.  
- Keep docstrings explanatory, not decorative.  
- Prefer clarity over cleverness — “genius through simplicity.”

---

## 📚 Known Gaps (as of Nov 19, 2025)

| Area | Status | Note |
|------|--------|------|
| Regex Engine | 🗑️ Deprecated | Replaced by LLM + Semantic cascade |
| Onboarding Wizard UI | 🚧 Pending | Backend ready |
| Strategic Card UI | 🚧 Pending | Backend ready |
| Comparison Table UI | 🚧 Pending | Backend ready |
| Gauge Visualization | 🚧 Pending | Needs Recharts / SVG |
| VEE Tabbed View | 🚧 Pending | Technical + Conversational toggle |
| Emotion Indicators | 🚧 Pending | Bubble color logic |
| Confidence Feedback | 🚧 Pending | Add to Compose Node responses |
| Keycloak Realm | ✅ FIXED | Recreated vitruvyan realm (Nov 19) |
| SSO Integration | ⚠️ Testing | User password reset needed |

---

## 🏁 Final Objective

Vitruvyan must **speak like a human advisor**:
- capable of dialogue, not output;
- motivated by reason, not pattern;
- transparent, multilingual, and emotionally aware.

When this file is read, Copilot should **not only know what to code**,  
but understand *why that code must think before it speaks.*

> "To advise is not to predict — it is to interpret the world in motion."  
> — *Vitruvyan Core Principle, 2025*

---

## 🚀 Recent Progress (Nov 19, 2025)

### Infrastructure Fixes
1. ✅ **Keycloak Domain Issue Resolved**
   - Fixed frontend URL from `auth.crumbz.io` → `https://user.vitruvyan.com`
   - Updated docker-compose.yml: `KC_HOSTNAME_URL` instead of `KC_HOSTNAME`
   - Database attribute: `realm_attribute.frontendUrl` corrected
   - Admin console now accessible without loop

2. ✅ **Realm Vitruvyan Recreated**
   - Database: Fresh start with clean keycloak DB
   - Realm: `vitruvyan` created via admin API
   - User: `info@vitruvyan.com` (password reset pending manual verification)
   - Client: `vitruvyan-ui` with proper OAuth2 settings
     - Redirect URIs: `https://mercator.vitruvyan.com/*`
     - Web Origins: `https://mercator.vitruvyan.com`
     - Direct Access Grants: ENABLED

3. ✅ **Chat Component Unified**
   - Merged omnibox.jsx functionality into chat.jsx (590 lines)
   - Smart ticker autocomplete: 30+ tickers + company name mapping
   - Keyboard navigation: ArrowUp/Down/Enter/Escape
   - Real-time detection: AAPL, Microsoft→MSFT, Palantir→PLTR
   - Enhanced error handling with network-specific messages
   - Deployed to production: git commit 9495eef

4. ✅ **Vercel Environment Variables**
   - Identified duplicates: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_API_BASE_URL
   - Correct values: `https://graph.vitruvyan.com` (Production)
   - Cleanup pending: Remove `api.vitruvyan.com` references

### Next Steps (Nov 20, 2025)
1. **Manual Keycloak Password Reset**
   - Access: https://user.vitruvyan.com/admin/
   - Realm: vitruvyan → Users → info@vitruvyan.com
   - Set password: `@Caravaggio971` (Temporary: OFF)

2. **UI Conversational Testing**
   - Test chat.jsx ticker autocomplete (MSFT, Microsoft, SHOP, Shopify)
   - Verify emotion-aware responses (frustrated, excited, neutral)
   - Validate bundled slot-filling questions
   - Check proactive suggestions rendering

3. **Vercel Cleanup**
   - Remove duplicate env vars via Vercel dashboard
   - Trigger new deployment with correct variables
   - Update nginx if deployment URL changes

### Promise Tracking 🤝
> **User Goal**: "spero veramente che siamo vicini a vedere vitruvyan parlare come chatgpt... me lo hai promesso!"

**Status**: 95% READY
- ✅ LLM-first architecture (Nuclear Option ticker extraction)
- ✅ Babel Gardens multilingual (84 languages)
- ✅ VEE + LLM narrative fusion
- ✅ Conversational memory (643 conversations, 1,422 embeddings)
- ✅ Emotion detection (frustrated, uncertain, excited, confident, neutral)
- ✅ Smart autocomplete with company name mapping
- ⚠️ **UI Testing Pending** (chat component, strategic cards, gauges)
- ⚠️ **SSO Flow Verification** (Keycloak realm recreated, password reset needed)

**Tomorrow's Goal**: See Vitruvyan respond like ChatGPT with epistemic precision! 🎯
