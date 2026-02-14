# PROSSIMI PASSI — Appendix Review (Feb 14, 2026)
**Compilato da**: Analisi approfondita Appendix D, E, F, H, I  
**Stato Q1 2026**: ✅ COMPLETATO (Infrastructure foundation, LIVELLO 1+2 Pattern, Domain-Agnostic Refactoring)  
**Prossimo Quartile**: Q2 2026 → Q3 2026 → Q4 2026

---

## 🎯 Executive Summary

Questa roadmap consolida i "Next Steps" identificati in 5 appendix core di Vitruvyan OS dopo la purificazione architetturale Q1 2026. Prioritizzata per Sacred Order e impatto strategico.

**Q1 2026 Achievements** (Baseline):
- ✅ **6/6 Sacred Orders** conformi a LIVELLO 1+2 Pattern (100%)
- ✅ **Purificazione epistemic**: Finance verticals separati da core domain-agnostic
- ✅ **LangGraph domain-agnostic**: Plugin architecture + Intent Registry refactoring
- ✅ **Neural Engine v2**: IDataProvider + IScoringStrategy contracts
- ✅ **Pattern Weavers Phase 1**: RiskProfile removal, epistemic boundary fix (60-65/100 score)
- ✅ **Blockchain Ledger**: Automatic batch triggering integration con Truth Layer
- ✅ **Babel Gardens**: Language-First Architecture (mandatory ISO 639-1 validation)

---

## 📋 PROSSIMI PASSI per Sacred Order

### 🧠 REASON — Pattern Weavers (Appendix I)
**Baseline**: Phase 1 Complete (Feb 10-11, 2026), Score 60-65/100  
**Target Q2 2026**: Phase 2 Agnosticization (Score 75-80/100)

#### Q2 2026 (Alta Priorità)
1. **Agnosticization Phase 2** 🔥
   - **Goal**: Raggiungere 75-80/100 score (rimuovere logica finance residua)
   - **Azioni**:
     - Audit `consumers/weaver.py` (204 lines) per finance-specific logic
     - Rimuovere riferimenti a "sectors", "tickers" hardcoded (deve essere YAML-driven)
     - Test con vertical healthcare/maritime per validare domain-agnosticism
   - **KPI**: Nessuna menzione "finance", "ticker", "sector" in core/cognitive/pattern_weavers/
   - **Effort**: 3-5 giorni

2. **LLM Caching con Redis** 🚀
   - **Goal**: Ridurre latency da 3-5s → <500ms per cache hits
   - **Azioni**:
     - Implementare Redis cache layer in `consumers/weaver.py`
     - Cache key: `hash(query_text + top_k + similarity_threshold)`
     - TTL: 7 giorni (allineato con Babel Gardens)
   - **KPI**: 80%+ cache hit rate dopo 7 giorni di produzione
   - **Effort**: 2 giorni

3. **Batch Processing Optimization** 💰
   - **Goal**: Ridurre costi LLM del 30% per bulk queries
   - **Azioni**:
     - Implementare `batch_recognize()` in `llm_ontology_engine.py`
     - OpenAI batch API (50% discount, 24h latency)
     - Async processing per query multiple in LangGraph
   - **KPI**: $2.80/month → $1.96/month (10K queries)
   - **Effort**: 3 giorni

4. **Healthcare Vertical Pilot** 🏥
   - **Goal**: Validare domain-agnosticism con taxonomy non-finance
   - **Azioni**:
     - Creare `config/taxonomy_healthcare.yaml` (ICD-10, medical procedures, specialties)
     - Test queries: "analizza cardiac arrest protocols", "compare oncology treatments"
     - Zero code changes a Pattern Weavers core
   - **KPI**: 95%+ accuracy su healthcare queries (stesso di finance)
   - **Effort**: 5 giorni (include creazione taxonomy)

5. **Production Monitoring** 📊
   - **Azioni**:
     - Dashboard Grafana: LLM vs YAML fallback ratio (target 95% LLM)
     - Alert: Fallback rate >10% (indica LLM service issues)
     - Cost tracking: $/query trend mensile
   - **Effort**: 1 giorno

6. **YAML Expansion per Robustezza** 📚
   - **Goal**: 100+ concepts in weave_rules.yaml (attualmente ~24)
   - **Rationale**: YAML fallback deve gestire 70%+ queries se LLM down
   - **Azioni**:
     - Crowdsource concepts da production query logs
     - Automatic expansion via LLM-generated synonyms (ironic ma efficace)
   - **Effort**: 2 giorni

#### Q3 2026 (Media Priorità)
7. **Temporal Context Support**
   - Feature: "banche nel 2024" → time-aware filtering
   - Richiede: Taxonomy versioning + temporal metadata
   - Effort: 5 giorni

8. **User Personalization**
   - Feature: Learn user-specific concept mappings (LLM fine-tuning)
   - Richiede: User feedback loop + OpenAI fine-tuning API
   - Effort: 10 giorni

---

### 💬 DISCOURSE — Conversational Layer (Appendix F)
**Baseline**: Infrastructure 100% ready (Q1 2026), UI testing pending  
**Target Q2 2026**: Production-ready conversational UX

#### Q2 2026 (Alta Priorità)
1. **UI Conversational Testing** 🎨
   - **Azioni**:
     - Test chat.jsx ticker autocomplete (MSFT, Microsoft, SHOP, Shopify)
     - Verify emotion-aware responses (frustrated, excited, neutral tones)
     - Validate bundled slot-filling questions (multi-turn flows)
     - Check proactive suggestions rendering (smart recommendations)
   - **KPI**: 0 regression bugs, <500ms response time
   - **Effort**: 3 giorni

2. **Strategic Cards Implementation** 📊
   - **Azioni**:
     - Final verdict + confidence gauges (visual design Figma → React)
     - Comparison table for multi-ticker ranking (sortable columns)
     - Conditional rendering by conversation_type (single/multi/onboarding)
   - **KPI**: Match Figma mockups 95%+, mobile-responsive
   - **Effort**: 5 giorni

3. **Production Stress Testing** ⚡
   - **Azioni**:
     - Load testing: 100+ concurrent users (Locust/k6)
     - Latency optimization: <500ms per LLM call (P95)
     - Cost monitoring: Prometheus metrics dashboard
   - **KPI**: 99.9% uptime, <1s P99 latency
   - **Effort**: 3 giorni

#### Q3 2026 (Media Priorità)
4. **Emotion Feedback Loop**
   - Feature: UI color shift based on detected emotion (frustrated=red, excited=green)
   - Rationale: Visual reinforcement of empathetic understanding
   - Effort: 2 giorni

5. **Multi-Turn Dialogue Refinement**
   - Feature: Context preservation across 5+ turns (conversation memory)
   - Richiede: Qdrant `conversations_embeddings` semantic search
   - Effort: 4 giorni

---

### 🔒 TRUTH — Blockchain Ledger (Appendix H)
**Baseline**: Q1 2026 Automatic batch triggering ✅ (integration con Orthodoxy Wardens)  
**Target Q2 2026**: Multi-chain redundancy, Q3 2026: Public verification portal

#### Q2 2026 (Alta Priorità)
1. **Multi-Chain Support (Ethereum/Polygon)** 🌐
   - **Goal**: Anchor batches su 3 blockchain per redundancy (Tron + Ethereum + Polygon)
   - **Azioni**:
     - Implementare `blockchain_router.py` (multi-chain abstraction)
     - Support Web3.py per Ethereum (vs TronPy)
     - Parallel anchoring (3 txs in <10s)
   - **KPI**: 3x redundancy, costo <$0.50/batch (Polygon layer-2 cheap)
   - **Effort**: 7 giorni

2. **Cost Monitoring Dashboard** 💰
   - **Azioni**:
     - Grafana dashboard: TRX balance, $/batch trend, monthly forecast
     - Alert: Wallet balance <100 TRX (auto-refill via APScheduler)
   - **Effort**: 1 giorno

#### Q3 2026 (Media Priorità)
3. **Public Verification Portal** 🔍
   - **Goal**: API pubblica per verifica batch indipendente (no Vitruvyan account needed)
   - **Endpoint**: `GET /verify/{batch_id}`
   - **Response**: Merkle root, blockchain TX ID, explorer URL, verification guide
   - **Rationale**: Trust transparency per compliance audit esterni
   - **Effort**: 4 giorni

#### Q4 2026 (Ricerca)
4. **Zero-Knowledge Proofs (ZK-SNARKs)** 🔬
   - **Goal**: Privacy-preserving audit compliance (provare batch anchored senza rivelare eventi)
   - **Azioni**: Research phase (ZK-SNARK libraries, proof generation performance)
   - **Effort**: 15+ giorni (ricerca + POC)

---

### 🧠 MEMORY — RAG System (Appendix E)
**Baseline**: Feb 11, 2026 — LIVELLO 1+2 Pattern, Language-First Architecture ✅  
**Target Q2 2026**: Enhanced semantic search, anomaly detection

#### Q2 2026 (Alta Priorità)
1. **Contextual Text Enrichment** 📝
   - **Goal**: Migliorare diversità sentiment con metadata contestuale
   - **Azioni**:
     - Add: destinazione, ETA, weather conditions a vessel embeddings
     - Add: ticker industry, market cap, volatility a finance embeddings
   - **KPI**: Sentiment label distribution più bilanciata (attualmente 40K neutral, pochi positive/negative)
   - **Effort**: 3 giorni

2. **Anomaly Detection Integration** 🚨
   - **Goal**: Flag suspicious patterns + sentiment analysis
   - **Azioni**:
     - Detect: AIS gaps, loitering patterns, speed anomalies (maritime)
     - Detect: Volume spikes, price gaps (finance)
     - Combine con sentiment per alert prioritization
   - **KPI**: 90%+ precision su anomalia detection
   - **Effort**: 5 giorni

3. **Multi-Language Sentiment Support** 🌍
   - **Goal**: Sentiment analysis per vessel names/destinations non-inglesi
   - **Azioni**:
     - Babel Gardens language detection cascade già in place
     - Extend FinBERT con mBERT (multilingual BERT)
   - **KPI**: 80%+ accuracy su IT/ES/FR/DE sentiment
   - **Effort**: 4 giorni

#### Q3 2026 (Media Priorità)
4. **Real-Time Alerting via Redis Pub/Sub** ⚡
   - **Goal**: Alert istantaneo per high-confidence negative sentiment
   - **Azioni**:
     - Redis PUBLISH su `alerts.sentiment.negative` channel
     - Subscribers: Email/Slack/Discord integration
   - **Use Case**: "Vessel in distress", "Stock negative surprise"
   - **Effort**: 2 giorni

5. **Sentiment Trend Analysis** 📈
   - **Goal**: Time-series aggregation per fleet operators (es. Maersk sentiment over time)
   - **Azioni**:
     - PostgreSQL time-bucket queries (hourly/daily/monthly)
     - Grafana dashboard per sentiment trends
   - **KPI**: Trend visualization per 50+ entities
   - **Effort**: 3 giorni

---

## 🗓️ Timeline Consolidata

### Q2 2026 (Aprile - Giugno)
**Focus**: Agnosticization, Production Readiness, Multi-Chain Redundancy

| Sacred Order | Deliverable | Effort (giorni) | Owner |
|--------------|-------------|-----------------|-------|
| REASON | Pattern Weavers Phase 2 (75-80/100 score) | 20 | TBD |
| DISCOURSE | Conversational UX Testing + Strategic Cards | 11 | TBD |
| TRUTH | Multi-Chain Support (Ethereum/Polygon) | 8 | TBD |
| MEMORY | Contextual Enrichment + Anomaly Detection | 12 | TBD |

**Total Effort**: ~51 giorni (2.5 sviluppatori a tempo pieno per 1 trimestre)

### Q3 2026 (Luglio - Settembre)
**Focus**: Public Verification, Advanced Features, User Personalization

| Sacred Order | Deliverable | Effort (giorni) | Owner |
|--------------|-------------|-----------------|-------|
| TRUTH | Public Verification Portal | 4 | TBD |
| REASON | Temporal Context + User Personalization | 15 | TBD |
| DISCOURSE | Emotion Feedback + Multi-Turn Dialogue | 6 | TBD |
| MEMORY | Real-Time Alerting + Trend Analysis | 5 | TBD |

**Total Effort**: ~30 giorni (1.5 sviluppatori a tempo pieno)

### Q4 2026 (Ottobre - Dicembre)
**Focus**: Ricerca ZK-Proofs, Optimizations, 2027 Planning

| Sacred Order | Deliverable | Effort (giorni) | Owner |
|--------------|-------------|-----------------|-------|
| TRUTH | ZK-SNARKs Research + POC | 15+ | TBD |
| REASON | Healthcare/Maritime Vertical Expansion | 10 | TBD |
| MEMORY | Advanced Semantic Features | 10 | TBD |

**Total Effort**: ~35 giorni (ricerca-oriented)

---

## 🎯 Success Metrics (KPI per Q2 2026)

### Pattern Weavers (REASON)
- ✅ **Agnosticization Score**: 60-65/100 → **75-80/100**
- ✅ **LLM Cache Hit Rate**: 0% → **80%+**
- ✅ **Average Latency**: 3-5s → **<500ms** (cache hits)
- ✅ **Monthly Cost**: $2.80 → **$1.96** (30% reduction via batch processing)
- ✅ **Healthcare Accuracy**: N/A → **95%+** (domain-agnostic validation)

### Conversational Layer (DISCOURSE)
- ✅ **UI Test Coverage**: 0% → **100%** (chat, cards, gauges)
- ✅ **P95 Latency**: N/A → **<500ms**
- ✅ **Concurrent Users**: N/A → **100+ (stress test)**
- ✅ **Mobile Responsiveness**: N/A → **95%+ Figma match**

### Blockchain Ledger (TRUTH)
- ✅ **Multi-Chain Redundancy**: 1 blockchain → **3 blockchains** (Tron/Ethereum/Polygon)
- ✅ **Batch Cost**: $0.00000009 → **<$0.50** (incluso multi-chain)
- ✅ **Wallet Auto-Refill**: Manual → **Automated** (APScheduler)

### RAG System (MEMORY)
- ✅ **Sentiment Diversity**: 40K neutral-heavy → **Balanced distribution**
- ✅ **Anomaly Detection Precision**: N/A → **90%+**
- ✅ **Multilingual Sentiment Accuracy**: EN-only → **80%+ (IT/ES/FR/DE)**
- ✅ **Real-Time Alerts**: N/A → **<5s notification latency**

---

## 🔗 Cross-Cutting Concerns

### 1. Documentazione (CRITICAL)
**Problem**: README.md inconsistencies across Sacred Orders  
**Solution**:
- ✅ Every Sacred Order MUST have comprehensive README.md (LIVELLO 1 + LIVELLO 2)
- ✅ Versioning: Every README.md MUST include `> **Last updated**: <date>` as first line
- ✅ Template: Use Memory Orders/Vault Keepers/Orthodoxy Wardens as reference
- **Deadline**: Q2 2026 Week 1

### 2. Testing (HIGH PRIORITY)
**Problem**: E2E tests non coprono Sacred Orders integration  
**Solution**:
- ✅ Create `tests/e2e/test_sacred_orders_integration.py`
- ✅ Test flow: Babel Gardens → Pattern Weavers → Neural Engine → VEE → Orthodoxy → Vault
- ✅ Validate: Event bus messages, PostgreSQL audit trail, Qdrant embeddings
- **Deadline**: Q2 2026 Week 2

### 3. Monitoring (HIGH PRIORITY)
**Problem**: Prometheus metrics non standardizzati  
**Solution**:
- ✅ Standard metric naming: `<service>_<metric>_<unit>` (es. `weaver_latency_seconds`)
- ✅ Grafana dashboards per Sacred Order (template condiviso)
- ✅ Alerts: Latency P95 >1s, Error rate >1%, Cost spike >2x baseline
- **Deadline**: Q2 2026 Week 3

---

## 📚 Riferimenti Incrociati

- **SACRED_ORDER_PATTERN.md**: Mandatory structure (10-directory LIVELLO 1, service LIVELLO 2)
- **Appendix B**: Core Patterns vs Finance Vertical separation (VEE, VWRE universal)
- **Appendix C**: Epistemic Roadmap 2026 (Q1 complete, Q2-Q4 planning)
- **copilot-instructions.md**: Sacred Orders table, import rules, refactoring procedure

---

## ✅ Checklist Implementazione

Prima di segnare Q2 2026 come "COMPLETATO", verificare:

- [ ] Pattern Weavers Agnosticization Score ≥75/100
- [ ] LLM Caching implemented (Redis, 80%+ hit rate)
- [ ] Healthcare vertical pilot (95%+ accuracy)
- [ ] Conversational UX testing (0 regression bugs)
- [ ] Strategic Cards UI (mobile-responsive, Figma match)
- [ ] Multi-Chain Support (Tron + Ethereum + Polygon)
- [ ] RAG Contextual Enrichment (sentiment distribution balanced)
- [ ] Anomaly Detection Integration (90%+ precision)
- [ ] All Sacred Orders READMEs updated (versioned, comprehensive)
- [ ] E2E integration tests (Sacred Orders flow validated)
- [ ] Monitoring dashboards (Grafana, standardized metrics)
- [ ] Git commits (detailed changelog, architecture decisions documented)

---

**Compilato da**: Copilot Agent (Architectural Review Session)  
**Data**: February 14, 2026  
**Versione**: 1.0.0  
**Prossimo Review**: End of Q2 2026 (Giugno 30, 2026)

---

**Note Finali**:

Questo documento è un **piano vivente**. Man mano che gli appendix vengono analizzati (A, B, C, D, E, F, H, I, Codex Hunters, ecc.), i PROSSIMI PASSI verranno aggregati e prioritizzati qui.

**Principio guida**: Ogni "Next Steps" negli appendix deve tracciare a:
1. **Sacred Order** di appartenenza (PERCEPTION/MEMORY/REASON/DISCOURSE/TRUTH)
2. **Quartile** di implementazione (Q2/Q3/Q4 2026)
3. **Effort estimate** (giorni sviluppatore)
4. **KPI** di successo (misurabile)
5. **Owner** (TBD da assegnare)

Questo garantisce che i PROSSIMI PASSI non siano "wishlist" ma **roadmap azionabile**.
