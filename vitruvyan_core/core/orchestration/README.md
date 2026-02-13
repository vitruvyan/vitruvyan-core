# Orchestration Layer (`core/orchestration/`)

> **Last updated**: February 13, 2026

**Domain-agnostic LangGraph orchestration with plugin architecture**

---

## Overview

The Orchestration Layer is Vitruvyan's cognitive routing engine, powered by **LangGraph**. It provides a domain-agnostic framework for conversational AI, slot filling, entity resolution, and multi-step reasoning.

**Key Characteristics:**
- **Domain-agnostic**: Finance, logistics, healthcare are plugins, not core logic
- **Graph-based**: LangGraph state machine for multi-step flows
- **Intent-driven**: Registry-based intent classification + routing
- **Composable**: Modular response formatters + slot fillers
- **Extensible**: Plugin system for domain-specific logic

---

## Architecture

### Directory Structure

```
vitruvyan_core/core/orchestration/
├── __init__.py
├── base_state.py              # StateGraph base class
├── graph_engine.py            # Main orchestration engine
├── intent_registry.py         # Intent classification + routing
├── parser.py                  # Input text parsing utilities
├── route_registry.py          # Route definitions
├── sacred_flow.py             # Sacred Orders integration
├── compose/                   # Response composition layer
│   ├── base_composer.py       # Abstract base
│   ├── response_formatter.py  # Domain-agnostic formatter interface
│   └── slot_filler.py         # Domain-agnostic slot filling interface
└── langgraph/                 # LangGraph implementation
    ├── graph_runner.py        # Entry point (run_graph)
    ├── graph_flow.py          # Graph builder (407L, domain-agnostic)
    ├── simple_graph_audit_monitor.py  # Execution monitoring
    └── node/                  # Graph nodes (~30 nodes)
        ├── babel_gardens_node.py      # Semantic signal extraction (HTTP adapter)
        ├── cached_llm_node.py         # LLM completion (via LLMAgent)
        ├── compose_node.py            # Response composition
        ├── emotion_detector_node.py   # Emotion detection (HTTP adapter)
        ├── entity_resolver.py         # Entity database matching
        ├── pattern_weavers_node.py    # Ontology resolution (HTTP adapter)
        ├── qdrant_node.py             # Semantic search (domain-agnostic)
        └── vault_*.py                 # Memory persistence
```

---

## Core Concepts

### 1. Intent Registry

**Purpose**: Classify user input and route to appropriate graph nodes

```python
from core.orchestration.intent_registry import IntentRegistry

registry = IntentRegistry()

# Classify intent
intent = registry.classify("Should I invest in Apple?")
# → "investment_verdict"

# Get nodes to execute
nodes = registry.get_nodes_for_intent("investment_verdict")
# → ["entity_resolver", "screener", "sentiment", "compose"]
```

**Built-in intents** (finance domain):
- `investment_verdict` — Buy/Sell/Hold recommendation
- `portfolio_diversification` — Portfolio health analysis
- `stock_comparison` — A vs B comparison matrix
- `sector_rotation` — Sector allocation advice
- `market_sentiment` — Market mood analysis

**Extensibility**: Add new intents via domain plugins

### 2. Graph Engine

**Purpose**: Execute LangGraph state machine

```python
from core.orchestration.langgraph.graph_runner import run_graph

result = run_graph({
    "input_text": "Analyze entity E007",
    "user_id": "demo_user"
})

# Returns:
# {
#   "intent": "...",
#   "entities": ["E007"],
#   "human": "...",
#   ...
# }
```

**Graph Flow:**
1. **Parse input** → Extract intent + entities
2. **Check slots** → Are all required parameters present?
3. **If slots missing** → Ask clarifying questions (slot_filler)
4. **Resolve entities** → Match to database (`entity_resolver`)
5. **Execute domain logic** → Run nodes (screener, sentiment, portfolio)
6. **Compose response** → Format result (ResponseFormatter)
7. **Return** → JSON + human-readable message

### 3. Slot Filling

**Purpose**: Multi-turn dialogue for missing information

```python
from core.orchestration.compose.slot_filler import SlotFiller

# Example: User says "Should I invest in tech stocks?"
# Missing: specific entities, investment horizon

slots_needed = {
    "entities": None,        # Missing
    "horizon": None,         # Missing
    "risk_tolerance": None   # Missing
}

questions = slot_filler.generate_questions(slots_needed)
# → [
#   "Which specific tech companies are you interested in?",
#   "What is your investment horizon? (short-term, medium-term, long-term)",
#   "What is your risk tolerance? (conservative, moderate, aggressive)"
# ]
```

**Multi-turn conversation:**
```
User: "Should I invest in tech stocks?"
Bot: "Which specific tech companies are you interested in?"
User: "Apple and Microsoft"
Bot: "What is your investment horizon?"
User: "Long term"
Bot: "Got it. Based on Apple and Microsoft for long-term investment..."
```

### 4. Response Formatter

**Purpose**: Domain-specific output formatting

```python
from core.orchestration.compose.response_formatter import ResponseFormatter

# Input: Raw graph state
state = {
    "intent": "investment_verdict",
    "entities": ["AAPL"],
    "scores": {"fundamental": 8.5, "technical": 7.2, "sentiment": 9.1}
}

# Output: Formatted response
response = formatter.format(state)
# → {
#   "verdict": "BUY",
#   "confidence": 0.85,
#   "human": "Leonardo: Apple shows strong fundamentals (8.5/10) and excellent sentiment (9.1/10). Recommended BUY.",
#   "gauge": "🟢🟢🟢🟢⚪",
#   "factors": [...]
# }
```

---

## Domain Plugins

### Plugin Architecture

Domains are **plugins**, not hardcoded into core:

```python
# domains/finance/finance_plugin.py

class FinancePlugin:
    def register_intents(self, registry: IntentRegistry):
        """Register finance-specific intents"""
        registry.add_intent("investment_verdict", ...)
        registry.add_intent("portfolio_diversification", ...)
        
    def get_response_formatter(self) -> ResponseFormatter:
        """Return finance-specific formatter"""
        return FinanceResponseFormatter()
        
    def get_slot_filler(self) -> SlotFiller:
        """Return finance-specific slot filler"""
        return FinanceSlotFiller()
```

**Usage:**
```python
from domains.finance.finance_plugin import FinancePlugin

# Register plugin
registry = IntentRegistry()
plugin = FinancePlugin()
plugin.register_intents(registry)
```

**Benefits:**
- ✅ Add new domains (logistics, healthcare, legal) without touching core
- ✅ Swap plugins at runtime (A/B testing)
- ✅ Test core orchestration independently

### Finance Domain Example

**Location**: `vitruvyan_core/domains/finance/`

```
domains/finance/
├── __init__.py
├── finance_plugin.py          # Plugin registration
├── response_formatter.py      # Verdict/gauge/comparison formatting
└── slot_filler.py             # Investment-specific slot questions
```

**Conversation types:**
- `investment_verdict` — Buy/Sell/Hold + confidence gauge
- `portfolio_gauge` — Portfolio health visualization
- `comparison_matrix` — Side-by-side entity comparison
- `onboarding_cards` — Welcome + entity suggestions

---

## State Management

### Base State (`base_state.py`)

**StateGraph schema** for LangGraph:

```python
from core.orchestration.base_state import BaseState

class BaseState(TypedDict):
    input_text: str                    # User input
    user_id: str                       # User identifier
    intent: str                        # Classified intent
    entities: List[str]                # Resolved entities
    slots: Dict[str, Any]              # Slot filling state
    results: Dict[str, Any]            # Node execution results
    response: Dict[str, Any]           # Final formatted response
    conversation_history: List[Dict]   # Multi-turn dialogue
```

**Graph nodes** operate on this state:
```python
def entity_resolver(state: BaseState) -> BaseState:
    """Resolve entity names to database IDs"""
    entities = state["entities"]
    resolved = database.match(entities)
    return {**state, "entities": resolved}
```

---

## Graph Nodes

### Entity Resolver (`langgraph/node/entity_resolver.py`)

**Purpose**: Match entity names to database IDs

```python
# Input: "Apple" (ambiguous)
# Output: "AAPL" (ticker symbol)

entities = entity_resolver_node(state)
# → ["AAPL"]
```

**Logic:**
1. Fuzzy match against `entity_ids` table
2. Rank by match score (exact > starts_with > contains)
3. Return top N matches
4. If ambiguous, ask clarifying question

### Screener Node (`langgraph/node/screener_node.py`)

**Purpose**: Compute entity scores (finance domain)

```python
# Input: ["AAPL"]
# Output: {
#   "AAPL": {
#     "fundamental": 8.5,
#     "technical": 7.2,
#     "sentiment": 9.1
#   }
# }
```

**Scoring factors** (finance):
- Fundamental analysis (PE ratio, revenue growth, margins)
- Technical analysis (RSI, MACD, price momentum)
- Sentiment analysis (news, social media, analyst ratings)

### Compose Node (`langgraph/node/compose_node.py`)

**Purpose**: Format final response using ResponseFormatter

```python
response = compose_node(state)
# → {
#   "verdict": "BUY",
#   "human": "Leonardo: Strong buy recommendation...",
#   "gauge": "🟢🟢🟢🟢⚪",
#   "confidence": 0.85
# }
```

### Vault Nodes (`langgraph/node/vault_*.py`)

**Purpose**: Memory persistence integration

- `vault_save_query.py` — Save user query to memory
- `vault_save_result.py` — Save analysis result to memory
- `vault_update_sentiment.py` — Update entity sentiment

---

## Entry Points

### `graph_runner.py`

**Main API** for executing graphs:

```python
from core.orchestration.langgraph.graph_runner import run_graph

# Execute graph with payload
result = run_graph({
    "input_text": "Compare entities A vs B",
    "user_id": "demo",
    "validated_entities": ["E001", "E002"],  # Pre-validated
    "intent": "comparison"                    # Pre-classified
})
```

**Parameters:**
- `input_text` (str): User query
- `user_id` (str): User identifier
- `validated_entities` (List[str], optional): Pre-validated entities (skip resolution)
- `intent` (str, optional): Pre-classified intent (skip parsing)

**Returns:**
```python
{
    "intent": str,              # Classified intent
    "entities": List[str],      # Resolved entities
    "results": Dict,            # Node execution results
    "response": Dict,           # Formatted response
    "human": str,               # Human-readable message
    "json": str,                # One-line JSON (for API)
    "audit_monitored": bool,    # Audit state
    "execution_timestamp": str  # ISO timestamp
}
```

---

## Audit Monitoring

### Simple Audit Monitor (`simple_graph_audit_monitor.py`)

**Purpose**: Track graph execution metrics

```python
from core.orchestration.langgraph.simple_graph_audit_monitor import (
    get_simple_graph_monitor,
    initialize_simple_graph_monitoring,
    shutdown_simple_graph_monitoring
)

monitor = get_simple_graph_monitor()

# Track execution
async with monitor.monitor_graph_execution(context):
    result = run_graph_once(input_text, user_id)

# Get metrics
metrics = monitor.performance_metrics
# → {
#   "executions": 142,
#   "errors": 3,
#   "avg_duration_ms": 1850,
#   "last_execution": "2026-02-10T15:30:45"
# }
```

**Metrics collected:**
- Execution count
- Error count + types
- Average/min/max duration
- Last execution timestamp
- Node-level timings

---

## Testing

### Unit Tests

```python
# Test intent classification
def test_intent_classification():
    registry = IntentRegistry()
    intent = registry.classify("Should I buy Apple stock?")
    assert intent == "investment_verdict"

# Test entity resolution
def test_entity_resolver():
    state = {"input_text": "Apple", "entities": ["Apple"]}
    resolved = entity_resolver_node(state)
    assert "AAPL" in resolved["entities"]

# Test slot filling
def test_slot_filler():
    filler = FinanceSlotFiller()
    questions = filler.generate_questions({"horizon": None})
    assert "investment horizon" in questions[0].lower()
```

### Integration Tests

```python
# Test full graph execution
def test_graph_execution():
    result = run_graph_once(
        input_text="Should I invest in Apple?",
        user_id="test_user"
    )
    assert result["intent"] == "investment_verdict"
    assert "AAPL" in result["entities"]
    assert "verdict" in result["response"]
```

### E2E Tests

See `services/api_graph/examples/` for HTTP-based E2E tests.

---

## Extension Guide

### Adding a New Domain

**1. Create domain plugin:**
```python
# vitruvyan_core/domains/logistics/logistics_plugin.py

class LogisticsPlugin:
    def register_intents(self, registry: IntentRegistry):
        registry.add_intent("route_optimization", nodes=[...])
        registry.add_intent("delivery_forecast", nodes=[...])
        
    def get_response_formatter(self) -> ResponseFormatter:
        return LogisticsResponseFormatter()
        
    def get_slot_filler(self) -> SlotFiller:
        return LogisticsSlotFiller()
```

**2. Implement response formatter:**
```python
# vitruvyan_core/domains/logistics/response_formatter.py

class LogisticsResponseFormatter(ResponseFormatter):
    def format_route_optimization(self, state: Dict) -> Dict:
        return {
            "route": state["optimal_route"],
            "distance_km": state["distance"],
            "est_time_hours": state["time"],
            "human": f"Optimal route: {state['route_summary']}"
        }
```

**3. Register plugin:**
```python
from domains.logistics.logistics_plugin import LogisticsPlugin

registry = IntentRegistry()
plugin = LogisticsPlugin()
plugin.register_intents(registry)
```

### Adding a New Intent

**1. Define intent:**
```python
registry.add_intent(
    name="new_intent",
    keywords=["keyword1", "keyword2"],
    nodes=["entity_resolver", "custom_node", "compose"],
    slots_required=["param1", "param2"]
)
```

**2. Create custom node (if needed):**
```python
def custom_node(state: BaseState) -> BaseState:
    # Domain-specific logic
    result = compute_custom_logic(state["entities"])
    return {**state, "results": {"custom": result}}
```

**3. Add to graph:**
```python
graph = build_graph()
graph.add_node("custom_node", custom_node)
```

---

## Performance Considerations

### Caching

```python
# Cache entity resolutions
@lru_cache(maxsize=1000)
def resolve_entity(entity_name: str) -> str:
    return database.match(entity_name)
```

### Parallel Execution

```python
# Execute independent nodes in parallel
async def parallel_scoring(entities: List[str]) -> Dict:
    tasks = [
        score_fundamental(entity),
        score_technical(entity),
        score_sentiment(entity)
    ]
    results = await asyncio.gather(*tasks)
    return combine_scores(results)
```

### Timeout Handling

```python
# Graph timeout (configurable)
GRAPH_TIMEOUT_SECONDS = int(os.getenv("GRAPH_TIMEOUT_SECONDS", "30"))

try:
    result = asyncio.wait_for(
        run_graph_once(input_text, user_id),
        timeout=GRAPH_TIMEOUT_SECONDS
    )
except asyncio.TimeoutError:
    return {"error": "Graph execution timeout"}
```

---

## Related Documentation

- **Graph Orchestrator API**: [`services/api_graph/README.md`](../../../services/api_graph/README.md)
- **LangGraph Refactoring**: [`.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md`](../../../.github/Vitruvyan_Appendix_J_LangGraph_Executive_Summary.md)
- **Domain Contracts**: [`vitruvyan_core/domains/README.md`](../../domains/README.md)
- **Finance Plugin**: [`vitruvyan_core/domains/finance/`](../../domains/finance/)

---

## Changelog

**Feb 13, 2026** — Legacy elimination & cleanup
- ✅ Removed `run_graph_once()` dead function (55L) from graph_flow.py
- ✅ Replaced 2 legacy imports with HTTP adapter nodes (emotion_detector, pattern_weavers)
- ✅ Renamed `sentinel_portfolio_value` → `sentinel_collection_value` (domain-agnostic)
- ✅ Cleaned cached_llm_node.py: removed `_archived_emotion_detector_v1` import
- ✅ Removed qdrant_node.py finance hardcoding → `QDRANT_SOURCE_FILTER` env var
- ✅ Deleted all `_legacy/` directories (0 legacy files remaining)

**Feb 2026** — Domain-agnostic refactoring
- ✅ Extracted finance logic into plugin
- ✅ Created intent registry abstraction
- ✅ Standardized ResponseFormatter + SlotFiller interfaces
- ✅ Added 51 files (6,920 lines)

**Jan 2026** — Initial LangGraph implementation
- Created graph_runner + graph_flow
- Implemented entity resolver + screener nodes
- Added audit monitoring

---

## License

Proprietary — Vitruvyan Core Team
