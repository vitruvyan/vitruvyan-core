# GROK CLEANUP PHASE 2 — Domain Abstraction Review

## Context

You are reviewing **vitruvyan-core**, a domain-agnostic cognitive operating system designed to be exported to multiple verticals (finance, healthcare, logistics, etc.). 

The codebase was originally built for **Mercator** (financial trading advisor) and has undergone **Phase 1 automated cleanup**:
- ✅ Deleted CrewAI, Neural Engine, Semantic Engine (domain-specific)
- ✅ Removed 95 files, ~40,000 lines
- ✅ Replaced ALL financial terminology (ticker→entity_id, stock→entity, portfolio→collection)
- ✅ Removed database migrations (verticals define their own schemas)
- ✅ Made PostgresAgent generic (only CRUD, no schema)

## Your Task

Review the **remaining 20-30% of code** that requires **human judgment** to decide:
1. **Keep & Generalize** — Core cognitive concepts (memory coherence, event tracking) that apply to ANY domain
2. **Delete** — Financial-specific logic that cannot be abstracted
3. **Document Assumptions** — Hidden financial assumptions in "generic" code

---

## Files to Review (Prioritized)

### 🔴 HIGH PRIORITY — Sacred Orders (Core Governance)

#### 1. Memory Orders (PostgreSQL ↔ Qdrant Coherence)
**Files**: 
- `vitruvyan_core/core/governance/memory_orders/coherence.py` (200 lines)
- `vitruvyan_core/core/governance/memory_orders/phrase_sync.py` (230 lines)
- `vitruvyan_core/core/governance/memory_orders/rag_health.py` (220 lines)

**Current State**:
```python
# coherence.py line 31
COLLECTION_NAME = "phrases_embeddings"  # ❌ HARDCODED financial collection

def coherence_check() -> Dict[str, Any]:
    # Queries PostgreSQL for "phrases with embedded=true"
    # Assumes 'phrases' table exists (financial RAG)
```

**Question**: 
- Is "coherence check between PostgreSQL and Qdrant" a **generic concept**?
- Should collection name be **parameterized**?
- Does `phrases` table assumption break domain-agnostic principle?

**Recommended Action**:
```python
# ✅ OPTION A: Parameterize (keep concept, make generic)
def coherence_check(
    pg_table: str = "entities",  # Generic default
    qdrant_collection: str = "entities_embeddings",
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Check coherence between any PostgreSQL table and Qdrant collection.
    Used by verticals to monitor dual-memory drift.
    """
    pass

# ❌ OPTION B: Delete (too specific)
# If coherence logic assumes financial data structures, delete entirely.
```

---

#### 2. Codex Hunters (Event-Driven Data Collection)
**Files**:
- `vitruvyan_core/core/governance/codex_hunters/event_hunter.py` (400 lines)
- `vitruvyan_core/core/governance/codex_hunters/tracker.py` (550 lines)
- `vitruvyan_core/core/governance/codex_hunters/scribe.py` (600 lines)
- `vitruvyan_core/core/governance/codex_hunters/binder.py` (450 lines)
- `vitruvyan_core/core/governance/codex_hunters/restorer.py` (400 lines)

**Current State**:
```python
# event_hunter.py
def hunt_events(entity_ids: List[str]) -> None:
    """
    Listen for Redis events and trigger data collection.
    """
    # Subscribes to: "codex:entity_update", "codex:backfill_request"
    # Assumes: entity_ids are stock tickers (financial assumption?)

# tracker.py
class Tracker:
    def track_entity(self, entity_id: str) -> None:
        # Tracks "momentum", "trend", "volatility" (financial metrics?)
        pass
```

**Questions**:
- Is **event-driven data collection** generic? (YES)
- Are event names financial-specific? (`codex:entity_update` is generic, `codex:backfill_momentum` is NOT)
- Does `Tracker` assume financial metrics? (Check method names)

**Recommended Action**:
1. **Keep event bus architecture** (Redis pub/sub is domain-agnostic)
2. **Parameterize event names** (let verticals define their own)
3. **Delete financial metric collection** (momentum, trend, volatility)
4. **Keep generic "track entity state change" concept**

---

#### 3. Pattern Weavers (Semantic Contextualization)
**Files**:
- `vitruvyan_core/core/cognitive/pattern_weavers/weaver_node.py` (350 lines)
- `vitruvyan_core/core/cognitive/pattern_weavers/weaver_engine.py` (280 lines)

**Current State**:
```python
# weaver_node.py
def weaver_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # Extracts concepts: ["Banking", "Technology", "Healthcare"]
    # Extracts regions: ["Europe", "North America"]
    # Extracts sectors: ["Information Technology", "Financials"]
```

**Questions**:
- Are "sectors" and "regions" **financial taxonomy**? (YES — GICS sectors)
- Is semantic contextualization **generic**? (YES — "extract entities from text")

**Recommended Action**:
```python
# ✅ OPTION A: Parameterize taxonomy
def weaver_node(state: Dict[str, Any], taxonomy: Dict[str, List[str]] = None) -> Dict[str, Any]:
    """
    Extract domain-specific concepts from text.
    
    Args:
        taxonomy: User-defined categories (e.g., {"sectors": ["Tech", "Finance"]})
    """
    pass

# ❌ OPTION B: Delete hardcoded financial taxonomy
# Remove: weave_rules.yaml with GICS sectors
```

---

### 🟡 MEDIUM PRIORITY — LangGraph Orchestration

#### 4. VEE (Vitruvyan Explainability Engine)
**Files**:
- `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_engine.py` (455 lines)
- `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_memory_adapter.py` (400 lines)

**Current State**:
```python
# vee_engine.py
def explain_entity(entity_id: str, data: Dict[str, Any]) -> str:
    """
    Generate natural language explanation for entity analysis.
    """
    # Assumes: data contains z-scores, momentum, trend (financial?)
    # Returns: "AAPL shows strong momentum with z-score 1.85..." (financial narrative)
```

**Questions**:
- Is **explainability engine** generic? (YES — ANY domain needs explanations)
- Are input data keys financial-specific? (z_scores, momentum → YES)
- Can narratives be domain-agnostic? (YES — template-based)

**Recommended Action**:
1. **Keep VEE concept** (explainability is universal)
2. **Parameterize data schema** (don't assume z-scores exist)
3. **Remove financial narrative templates** (let verticals define prompts)

---

#### 5. LangGraph Nodes with Residual Financial Logic
**Files**:
- `vitruvyan_core/core/orchestration/langgraph/node/parse_node.py` (500 lines)
- `vitruvyan_core/core/orchestration/langgraph/node/can_node.py` (660 lines)
- `vitruvyan_core/core/orchestration/langgraph/node/compose_node.py` (1600 lines)
- `vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py` (400 lines)

**Check For**:
- Hardcoded entity validation (e.g., "check if entity_id is valid ticker")
- Financial intent detection ("sentiment", "momentum", "portfolio")
- Financial slot-filling ("horizon", "risk tolerance")

**Recommended Action**:
- **Keep orchestration flow** (parse → intent → execute → compose is generic)
- **Delete financial intent types** (or move to vertical)
- **Parameterize slot schemas** (let verticals define their own)

---

### 🟢 LOW PRIORITY — Infrastructure

#### 6. Conversation Context & Memory
**Files**:
- `vitruvyan_core/core/orchestration/langgraph/memory/conversation_context.py` (200 lines)

**Current State**:
```python
# conversation_context.py line 120
tech_entities = ["EXAMPLE_ENTITY_1", "EXAMPLE_ENTITY_4", ...]  # ❌ Financial examples
finance_entities = ["JPM", "BAC", "WFC", "GS"]  # ❌ Hardcoded banks
```

**Recommended Action**:
- **Delete hardcoded entity lists** (use generic placeholders)
- **Keep conversation memory concept** (domain-agnostic)

---

## Decision Framework

For each file, ask:

### 1. **Is the CONCEPT generic?**
- ✅ YES: Event-driven data collection, memory coherence, explainability
- ❌ NO: "Calculate momentum z-score", "Fetch earnings calendar"

### 2. **Are the IMPLEMENTATIONS generic?**
- ✅ YES: `execute(sql)`, `fetch(sql)`, Redis pub/sub
- ❌ NO: `INSERT INTO sentiment_scores`, `CREATE INDEX idx_momentum_entity`

### 3. **Are the ASSUMPTIONS hidden?**
Example: `coherence_check()` assumes `phrases` table exists (financial RAG assumption).

---

## Output Format

For each reviewed file, provide:

```markdown
### File: vitruvyan_core/core/governance/memory_orders/coherence.py

**Decision**: KEEP & GENERALIZE

**Reasoning**:
- Concept (memory coherence) is domain-agnostic
- Implementation assumes financial 'phrases' table (line 45)
- Collection name hardcoded (line 31)

**Changes Required**:
1. Parameterize `pg_table` argument (default: "entities")
2. Parameterize `qdrant_collection` argument (default: "entities_embeddings")
3. Remove assumption that table has `embedded` boolean column
4. Update docstring to reflect generic usage

**Code Example**:
```python
def coherence_check(
    pg_table: str = "entities",
    qdrant_collection: str = "entities_embeddings",
    pg_id_column: str = "id",
    drift_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Domain-agnostic coherence check between PostgreSQL and Qdrant.
    Verticals call with their own table/collection names.
    """
    pass
```
```

---

## Files Already Cleaned (DO NOT REVIEW)

✅ PostgresAgent (generic CRUD only)  
✅ QdrantAgent (generic vector ops)  
✅ All terminology (entity_id, entity_ids, collection)  
✅ Database migrations (deleted)  
✅ Seed data (deleted)  
✅ Neural Engine (deleted)  
✅ Semantic Engine (deleted)  
✅ CrewAI (deleted)  

---

## Success Criteria

After your review, vitruvyan-core should:
1. ✅ Have ZERO financial domain assumptions
2. ✅ Provide ONLY infrastructure (LangGraph + Redis + PostgreSQL + Qdrant)
3. ✅ Allow verticals to define their own:
   - Database schemas
   - Event types
   - Taxonomy/sectors
   - Analysis metrics
   - Narrative templates

---

## Quick Check Commands

```bash
# Check for remaining financial terms
grep -rn "momentum\|sentiment\|trend\|earnings\|dividend" vitruvyan_core/ --include="*.py"

# Check for hardcoded entity lists
grep -rn "AAPL\|NVDA\|TSLA\|MSFT\|JPM" vitruvyan_core/ --include="*.py"

# Check for hardcoded database tables
grep -rn "CREATE TABLE\|INSERT INTO" vitruvyan_core/ --include="*.py"

# Check for financial metrics
grep -rn "z.score\|percentile\|volatility" vitruvyan_core/ --include="*.py"
```

---

## Example: Before/After

### ❌ BEFORE (Financial-Specific)
```python
# codex_hunters/tracker.py
class Tracker:
    def track_entity(self, entity_id: str) -> None:
        """Track stock momentum and trend."""
        momentum = calculate_rsi(entity_id)  # Financial metric
        trend = calculate_sma(entity_id)     # Financial metric
        self.pg.execute(
            "INSERT INTO momentum_logs (entity_id, rsi, sma) VALUES (%s, %s, %s)",
            (entity_id, momentum, trend)
        )
```

### ✅ AFTER (Domain-Agnostic)
```python
# codex_hunters/tracker.py
class Tracker:
    def track_entity_state(
        self, 
        entity_id: str, 
        state_data: Dict[str, Any],
        table_name: str = "entity_states"
    ) -> None:
        """
        Track entity state changes (domain-agnostic).
        Verticals define what 'state_data' contains.
        """
        columns = ", ".join(state_data.keys())
        placeholders = ", ".join(["%s"] * len(state_data))
        values = tuple(state_data.values())
        
        self.pg.execute(
            f"INSERT INTO {table_name} (entity_id, {columns}) VALUES (%s, {placeholders})",
            (entity_id, *values)
        )
```

---

## Priority Order

1. **Memory Orders** (3 files, 650 lines) — 4 hours
2. **Codex Hunters** (5 files, 2000 lines) — 8 hours
3. **Pattern Weavers** (2 files, 630 lines) — 3 hours
4. **VEE** (2 files, 855 lines) — 4 hours
5. **LangGraph Nodes** (4 files, 3160 lines) — 6 hours

**Total Estimated**: ~25 hours of review work

---

## Final Question

After Phase 2 cleanup, can you **confidently deploy vitruvyan-core to a healthcare vertical** without ANY financial assumptions breaking?

If YES → Cleanup complete ✅  
If NO → Identify remaining financial coupling and iterate.
