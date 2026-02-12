# LangGraph Domain-Agnostic Refactoring — Feb 11, 2026
**Mission**: Rendere il grafo un **OS kernel agnostico**, spostare logica finance in **examples verticali**.

---

## 🚨 Executive Summary

**Current state**: graph_flow.py (501 lines) contiene **5 nodi finance-specific** + **10 routes finance** + **3 state fields finance**.

**Target state**: 
- **Core graph**: Domain-agnostic orchestration (~350 lines)
- **Finance nodes**: Spostati in `examples/verticals/finance/`
- **State schema**: Generic entity/signal fields (no budget/horizon/ticker)

**Impact**: -30% complessità, +100% riusabilità cross-domain (legal, medical, IoT, etc.)

---

## 📊 Audit Results — Finance-Specific Components

### 🔴 Nodi da Rimuovere/Spostare (5)

| Node | Lines | Finance-Specific? | Action |
|------|-------|-------------------|--------|
| **screener_node** | 258 | ✅ YES (stock screening) | Move to `examples/verticals/finance/` |
| **portfolio_node** | 278 | ✅ YES (portfolio analysis) | Move to `examples/verticals/finance/` |
| **sentiment_node** | 249 | 🟡 PARTIAL (market sentiment) | Refactor → generic `signal_analysis_node` |
| **crew_node** | 286 | 🟡 PARTIAL (if used for trend/momentum) | Move finance routes to examples |
| **sentinel_node** | 283 | 🟡 PARTIAL (if "risk assessment") | Keep sentinel, remove finance routes |

### 🔴 Routes da Eliminare (10)

```python
# FROM graph_flow.py line 340-370
"screener": "screener",                # Finance
"portfolio_guardian": "sentinel",      # Finance
"risk_assessment": "sentinel",         # Finance
"emergency": "sentinel",               # Finance (situational, could be generic)
"portfolio_review": "collection",      # Finance
"trend": "crew",                       # Finance
"momentum": "crew",                    # Finance
"volatility": "crew",                  # Finance
"backtest": "crew",                    # Finance
"collection": "crew",                  # Finance (legacy)
```

### 🔴 State Fields da Re-Pensare (3)

```python
# FROM graph_flow.py line 78-83
budget: Optional[str]                  # Finance-specific
entity_ids: Optional[list[str]]        # Context: tickers (finance)
horizon: Optional[str]                 # Finance-specific (investment horizon)
```

**Refactor proposal**:
```python
# Domain-agnostic state fields
entities: Optional[List[Dict[str, Any]]]  # Generic entities (id, type, attributes)
signals: Optional[Dict[str, Any]]         # Generic signals (sentiment, score, metadata)
context: Optional[Dict[str, Any]]         # Vertical-specific context (extensible)
```

---

## ✅ Nodi Domain-Agnostic da Mantenere (21)

**Core Cognitive Spine** (mantengono grafo OS-agnostic):

1. ✅ `parse_node` — Parsing generico
2. ✅ `intent_detection_node` — Intent detection generico
3. ✅ `weaver_node` — Pattern Weavers (ontology, semantic enrichment)
4. ✅ `entity_resolver_node` — Entity resolution generico
5. ✅ `params_extraction_node` — Parameter extraction generico
6. ✅ `route_node` — Routing generico
7. ✅ `exec_node` — Execution generico
8. ✅ `quality_check_node` — Quality check generico
9. ✅ `qdrant_node` — Vector search generico
10. ✅ `cached_llm_node` — LLM caching generico
11. ✅ `output_normalizer_node` — Output normalization generico
12. ✅ `compose_node` — Composizione risposta generico
13. ✅ `proactive_suggestions_node` — Suggerimenti proattivi generico
14. ✅ `advisor_node` — Decision-making generico
15. ✅ `can_node` — Conversational advisor generico (CAN v2)
16. ✅ `orthodoxy_node` — Sacred Orders (governance)
17. ✅ `vault_node` — Sacred Orders (memory protection)
18. ✅ `codex_hunters_node` — Sacred Orders (knowledge acquisition)
19. ✅ `babel_emotion_node` — Babel Gardens (emotion detection)
20. ✅ `semantic_grounding_node` — VSGS (semantic grounding)
21. ✅ `llm_mcp_node` — MCP integration (OpenAI Function Calling)

---

## 🎯 Refactoring Strategy — 3 Phases

### Phase A: Clean Finance Nodes (IMMEDIATE)
**Effort**: 45 minutes  
**Impact**: -30% complexity, +100% domain-agnosticity

**Actions**:
1. ✂️ **Remove finance nodes** from graph_flow.py:
   ```python
   # DELETE lines 258, 278, 286 (screener, portfolio, crew finance routes)
   # DELETE lines 340-370 (finance routes in conditional_edges)
   ```

2. 📦 **Move to examples/** (not deleted, archived):
   ```bash
   mkdir -p examples/verticals/finance/nodes/
   mv vitruvyan_core/core/orchestration/langgraph/node/screener_node.py examples/verticals/finance/nodes/
   mv vitruvyan_core/core/orchestration/langgraph/node/portfolio_node.py examples/verticals/finance/nodes/
   # sentiment_node → Refactor to signal_analysis_node (generic)
   ```

3. 🧹 **Clean state schema**:
   ```python
   # BEFORE (finance-specific)
   budget: Optional[str]
   entity_ids: Optional[list[str]]
   horizon: Optional[str]
   
   # AFTER (domain-agnostic)
   entities: Optional[List[Dict[str, Any]]]  # Generic entities
   signals: Optional[Dict[str, Any]]         # Generic signals
   context: Optional[Dict[str, Any]]         # Vertical-specific extensible
   ```

4. 📝 **Create finance vertical example**:
   ```python
   # examples/verticals/finance/finance_graph.py
   from core.orchestration.langgraph.graph_flow import build_graph
   from examples.verticals.finance.nodes.screener_node import screener_node
   
   def build_finance_graph():
       """Finance-specific graph extension (NOT system core)"""
       base_graph = build_graph()  # Core OS graph
       # Add finance-specific nodes as extensions
       base_graph.add_node("screener", screener_node)
       # ... finance routes
       return base_graph
   ```

**Result**: graph_flow.py: 501 → ~350 lines, 0 finance assumptions

---

### Phase B: Refactor Sentiment Node → Signal Analysis (OPTIONAL)
**Effort**: 1 hour  
**Impact**: Sentiment diventa generic signal processor

**Actions**:
1. Rename `sentiment_node.py` → `signal_analysis_node.py`
2. Refactor: Accept generic signals (not just market sentiment)
3. Update routes: `"sentiment_node"` → `"signal_analysis"`

---

### Phase C: Document Vertical Pattern (CRITICAL FOR UX)
**Effort**: 30 minutes  
**Deliverable**: `examples/verticals/README.md`

**Content**:
```markdown
# Vertical Pattern — Domain-Specific Extensions

## Core Principle
**vitruvyan-core** is domain-agnostic. Verticals extend the OS, don't modify core.

## How to Create a Vertical

1. **Directory structure**:
   ```
   examples/verticals/<domain>/
   ├── nodes/              # Domain-specific nodes
   ├── <domain>_graph.py   # Graph extension
   ├── schemas.py          # Domain state fields
   └── README.md
   ```

2. **Example: Finance Vertical**:
   ```python
   from core.orchestration.langgraph.graph_flow import build_graph
   from examples.verticals.finance.nodes.screener_node import screener_node
   
   def build_finance_graph():
       g = build_graph()  # Core OS graph
       g.add_node("screener", screener_node)
       g.add_edge("route", "screener")
       return g
   ```

3. **Available Verticals**:
   - `finance/` — Stock screening, portfolio analysis
   - `legal/` — (future) Contract analysis, case law
   - `medical/` — (future) Clinical reasoning, diagnosis
```

---

## 🧬 Core Graph Architecture (Target)

**Philosophy**: OS kernel pattern (Linux/BSD model)

```
Core Graph (domain-agnostic)
├── Perception Layer
│   ├── parse_node (input normalization)
│   ├── intent_detection_node (intent classification)
│   └── babel_emotion_node (emotion detection)
│
├── Memory Layer (Sacred Orders)
│   ├── weaver_node (semantic enrichment)
│   ├── entity_resolver_node (entity resolution)
│   └── semantic_grounding_node (VSGS grounding)
│
├── Reason Layer
│   ├── params_extraction_node (parameter extraction)
│   ├── route_node (routing decision)
│   ├── exec_node (execution) ← VERTICAL INJECTION POINT
│   ├── quality_check_node (validation)
│   └── llm_mcp_node (MCP tool calls)
│
├── Discourse Layer
│   ├── output_normalizer_node (output formatting)
│   ├── compose_node (narrative generation)
│   ├── can_node (conversational advisor)
│   ├── advisor_node (decision-making)
│   └── proactive_suggestions_node (proactive intelligence)
│
└── Truth Layer (Sacred Orders)
    ├── orthodoxy_node (governance validation)
    ├── vault_node (memory protection)
    └── codex_hunters_node (knowledge acquisition)

Verticals (domain-specific)
├── examples/verticals/finance/
│   ├── screener_node.py (stock screening)
│   ├── portfolio_node.py (portfolio analysis)
│   └── finance_graph.py (extension)
│
├── examples/verticals/legal/ (future)
└── examples/verticals/medical/ (future)
```

**Injection points for verticals**:
- **exec_node**: Execute vertical-specific logic
- **route_node**: Add vertical-specific routes
- **context field**: Pass vertical metadata

---

## 📋 Implementation Checklist

### Phase A: Clean Finance Nodes
- [ ] Remove `screener_node` from graph_flow.py (line 258)
- [ ] Remove `portfolio_node` from graph_flow.py (line 278)
- [ ] Remove finance routes from conditional_edges (lines 340-370)
- [ ] Move screener_node.py to `examples/verticals/finance/nodes/`
- [ ] Move portfolio_node.py to `examples/verticals/finance/nodes/`
- [ ] Refactor GraphState: budget/horizon/entity_ids → entities/signals/context
- [ ] Update imports in graph_flow.py (remove finance node imports)
- [ ] Create `examples/verticals/finance/finance_graph.py` (extension example)
- [ ] Test core graph: `python3 -c "from core.orchestration.langgraph.graph_flow import build_graph; g = build_graph(); print('✅ Core graph builds')"`

### Phase B: Refactor Sentiment Node (OPTIONAL)
- [ ] Rename sentiment_node.py → signal_analysis_node.py
- [ ] Refactor: Accept generic signals (not market-specific)
- [ ] Update graph_flow.py: "sentiment_node" → "signal_analysis"
- [ ] Test: Signal analysis works with non-finance entities

### Phase C: Document Vertical Pattern
- [ ] Create `examples/verticals/README.md` (pattern documentation)
- [ ] Create `examples/verticals/finance/README.md` (finance vertical docs)
- [ ] Update main README.md: Link to vertical pattern
- [ ] Add examples: Legal/Medical vertical stubs (future roadmap)

---

## 🎯 Success Criteria

1. ✅ **Domain-Agnosticity**: Core graph has 0 finance-specific assumptions
2. ✅ **Reusability**: Legal/Medical verticals can extend without forking
3. ✅ **Maintainability**: Finance logic isolated in examples/ (not core/)
4. ✅ **Documentation**: Clear vertical pattern for contributors
5. ✅ **Backward Compatibility**: Finance vertical works as example

---

## 🚀 Quick Start (After Refactoring)

### Core OS Graph (Domain-Agnostic)
```python
from core.orchestration.langgraph.graph_flow import build_graph

graph = build_graph()  # Pure OS kernel
result = graph.invoke({"input_text": "Analyze entity X", "context": {}})
```

### Finance Vertical (Example Extension)
```python
from examples.verticals.finance.finance_graph import build_finance_graph

graph = build_finance_graph()  # Core + finance nodes
result = graph.invoke({
    "input_text": "Screen top 10 tech stocks",
    "context": {"domain": "finance"}
})
```

### Legal Vertical (Future Example)
```python
from examples.verticals.legal.legal_graph import build_legal_graph

graph = build_legal_graph()  # Core + legal nodes
result = graph.invoke({
    "input_text": "Find precedents for contract clause X",
    "context": {"domain": "legal"}
})
```

---

## 📚 References

- **Sacred Orders Pattern**: `.github/copilot-instructions.md` (LIVELLO 1/2 separation)
- **OS-Agnostic Philosophy**: README.md ("Core stays generic")
- **Vertical Examples**: `examples/verticals/` (post-refactoring)

---

## 🧠 Strategic Rationale

### Why Domain-Agnostic Matters

1. **Reusability**: Legal/Medical/IoT verticals use same OS
2. **Maintainability**: Finance bugs don't break core
3. **Testability**: Core graph testable without finance mocks
4. **Scalability**: Add verticals without core changes
5. **Philosophy Alignment**: Vitruvyan is an **epistemic OS**, not a finance app

### User's Original Concern (Validated)

> "481 lines added for Phase 1 is a signal... orchestration growing too much"

**Root cause**: Phase 1 added abstraction layers ON TOP of finance-heavy core.  
**Correct fix**: REMOVE finance from core, THEN add abstractions.

**Order of operations**:
1. ✅ Rollback Phase 1 (DONE)
2. 🔄 Remove finance nodes (THIS REFACTORING)
3. 🔜 Re-evaluate Phase 1 on clean core (FUTURE)

---

## 🎯 Next Steps

**User Decision Required**:

**Option 1**: Execute Phase A (Clean Finance Nodes) — 45 min  
**Option 2**: Read/Review proposal, then decide — 0 min  
**Option 3**: Alternative approach — TBD

**Recommendation**: Option 1 (Execute Phase A)

- Core graph will be 30% lighter
- Finance examples preserved in `examples/verticals/`
- Sacred Orders stay intact (domain-agnostic by design)
- Foundation ready for future Phase 1 re-evaluation

---

**Status**: ⏸️ AWAITING USER DECISION  
**Date**: February 11, 2026  
**Impact**: HIGH (architectural foundation)  
**Risk**: LOW (finance nodes preserved in examples/)
