# Vertical Pattern — Domain-Specific Graph Extensions

**Purpose**: Keep core graph **domain-agnostic** while enabling **vertical-specific functionality**.

---

## Philosophy

**Vitruvyan-core is an epistemic OS kernel**, not a vertical application.

- **Core graph** = Domain-agnostic orchestration (21 nodes)
- **Verticals** = Domain-specific extensions (finance, legal, medical, IoT, etc.)

**Injection points**:
- `exec_node`: Execute vertical-specific logic
- `route_node`: Add vertical-specific routes
- `context` field: Pass vertical metadata

---

## Directory Structure

```
examples/verticals/
├── README.md (this file)
├── finance/
│   ├── nodes/
│   │   ├── screener_node.py (stock screening)
│   │   ├── portfolio_node.py (portfolio analysis)
│   │   ├── sentiment_node.py (market sentiment)
│   │   └── sentinel_node.py (risk monitoring)
│   ├── finance_graph.py (example extension)
│   └── README.md
├── legal/ (future)
│   ├── nodes/
│   ├── legal_graph.py
│   └── README.md
└── medical/ (future)
    ├── nodes/
    ├── medical_graph.py
    └── README.md
```

---

## How to Create a Vertical

### Step 1: Create Directory Structure

```bash
mkdir -p examples/verticals/<domain>/nodes
```

### Step 2: Implement Domain-Specific Nodes

```python
# examples/verticals/<domain>/nodes/my_node.py
from typing import Dict, Any

def my_domain_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Domain-specific processing.
    Use state['context'] for vertical metadata.
    """
    context = state.get("context", {})
    domain = context.get("domain")  # e.g., "finance", "legal", "medical"
    
    # Domain logic here
    result = process_domain_logic(state, context)
    
    state["result"] = result
    state["route"] = "output_normalizer"  # Or next node
    return state
```

### Step 3: Create Graph Extension

```python
# examples/verticals/<domain>/<domain>_graph.py
from core.orchestration.langgraph.graph_flow import build_graph
from examples.verticals.<domain>.nodes.my_node import my_domain_node

def build_<domain>_graph():
    """
    Extends core OS graph with domain-specific nodes.
    NOT part of system core.
    """
    graph = build_graph()  # Core domain-agnostic graph
    
    # Add domain nodes
    graph.add_node("my_domain_node", my_domain_node)
    
    # Add domain routes
    # (Modify route_node to add domain-specific routes)
    graph.add_edge("route", "my_domain_node")  # Conditional
    graph.add_edge("my_domain_node", "output_normalizer")
    
    return graph
```

### Step 4: Document Vertical

```markdown
# <Domain> Vertical README.md

## Purpose
...

## Nodes
...

## Integration Pattern
...
```

---

## Example: Finance Vertical

**Location**: `examples/verticals/finance/`

**Nodes**:
- `screener_node` — Stock screening
- `portfolio_node` — Portfolio analysis
- `sentiment_node` — Market sentiment
- `sentinel_node` — Risk monitoring

**Extension Pattern** (future implementation):

```python
from examples.verticals.finance.finance_graph import build_finance_graph

graph = build_finance_graph()
result = graph.invoke({
    "input_text": "Screen top 10 tech stocks",
    "context": {"domain": "finance"}
})
```

---

## Example: Legal Vertical (Future)

**Location**: `examples/verticals/legal/` (planned)

**Potential Nodes**:
- `case_law_search_node` — Find precedents
- `contract_analyzer_node` — Analyze contract clauses
- `compliance_check_node` — Regulatory compliance

**Extension Pattern**:

```python
from examples.verticals.legal.legal_graph import build_legal_graph

graph = build_legal_graph()
result = graph.invoke({
    "input_text": "Find precedents for non-compete clause",
    "context": {"domain": "legal", "jurisdiction": "US"}
})
```

---

## Example: Medical Vertical (Future)

**Location**: `examples/verticals/medical/` (planned)

**Potential Nodes**:
- `diagnosis_support_node` — Clinical reasoning
- `drug_interaction_node` — Medication safety
- `medical_literature_node` — PubMed search

**Extension Pattern**:

```python
from examples.verticals.medical.medical_graph import build_medical_graph

graph = build_medical_graph()
result = graph.invoke({
    "input_text": "Differential diagnosis for fever + rash",
    "context": {"domain": "medical", "patient_age": 35}
})
```

---

## Core Graph (Domain-Agnostic)

**21 nodes** maintained in `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`:

### Perception Layer
- `parse_node` — Input normalization
- `intent_detection_node` — Intent classification
- `babel_emotion_node` — Emotion detection

### Memory Layer (Sacred Orders)
- `weaver_node` — Semantic enrichment (Pattern Weavers)
- `entity_resolver_node` — Entity resolution
- `semantic_grounding_node` — VSGS grounding

### Reason Layer
- `params_extraction_node` — Parameter extraction
- `route_node` — Routing decision ← **VERTICAL INJECTION POINT**
- `exec_node` — Execution ← **VERTICAL INJECTION POINT**
- `quality_check_node` — Validation
- `llm_mcp_node` — MCP tool calls

### Discourse Layer
- `output_normalizer_node` — Output formatting
- `compose_node` — Narrative generation
- `can_node` — Conversational advisor (CAN v2)
- `advisor_node` — Decision-making
- `proactive_suggestions_node` — Proactive intelligence

### Truth Layer (Sacred Orders)
- `orthodoxy_node` — Governance validation
- `vault_node` — Memory protection
- `codex_hunters_node` — Knowledge acquisition

### Infrastructure
- `qdrant_node` — Vector search
- `cached_llm_node` — LLM caching

---

## State Schema

### Core Fields (Domain-Agnostic)

```python
class GraphState(TypedDict, total=False):
    # Core OS
    input_text: str
    route: str
    result: Dict[str, Any]
    error: Optional[str]
    response: Dict[str, Any]
    user_id: Optional[str]
    intent: Optional[str]
    final_response: Optional[str]
    
    # Domain-agnostic entity/signal fields
    entities: Optional[List[Dict[str, Any]]]  # Generic entities
    signals: Optional[Dict[str, Any]]         # Generic signals
    context: Optional[Dict[str, Any]]         # Vertical-specific ← USE THIS
    top_k: Optional[int]
    
    # Sacred Orders fields (domain-agnostic governance)
    orthodoxy_status: Optional[str]
    vault_status: Optional[str]
    # ... (40+ Sacred Orders fields)
```

### Vertical Extension Pattern

**Don't add vertical fields to GraphState**. Use `context` field:

```python
# Finance vertical
state["context"] = {
    "domain": "finance",
    "budget": "10000",
    "horizon": "1y",
    "risk_tolerance": "moderate"
}

# Legal vertical
state["context"] = {
    "domain": "legal",
    "jurisdiction": "US",
    "case_type": "contract"
}

# Medical vertical
state["context"] = {
    "domain": "medical",
    "patient_age": 35,
    "symptoms": ["fever", "rash"]
}
```

---

## Benefits

1. **Reusability**: Legal/Medical/IoT use same OS kernel
2. **Maintainability**: Finance bugs don't break core
3. **Testability**: Core graph testable without domain mocks
4. **Scalability**: Add verticals without core changes
5. **Philosophy Alignment**: Vitruvyan is an **epistemic OS**, not a vertical app

---

## References

- **Core Graph**: `/vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- **Domain-Agnostic Refactoring**: `/LANGGRAPH_DOMAIN_AGNOSTIC_REFACTORING.md`
- **Sacred Orders Pattern**: `/.github/copilot-instructions.md`

---

**Created**: February 11, 2026  
**Purpose**: Enable vertical extensions without polluting OS core  
**Status**: ACTIVE (finance vertical archived, others planned)
