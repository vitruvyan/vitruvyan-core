# Finance Vertical — Example Domain-Specific Extension

**Status**: ARCHIVED (Moved from core on Feb 11, 2026)

This directory contains **finance-specific nodes** that were moved out of the core graph to maintain domain-agnosticity.

---

## Purpose

Demonstrates how to:
- Extend the core graph with vertical-specific nodes
- Maintain domain separation (finance logic ≠ OS kernel)
- Preserve backward compatibility (finance vertical still works)

---

## Nodes (Archived from Core)

### 1. `screener_node.py` (258 lines)
**Purpose**: Stock screening based on fundamental/technical criteria  
**Finance-Specific**: ✅ YES (tickers, market data, financial ratios)

### 2. `portfolio_node.py` (278 lines)
**Purpose**: Portfolio/collection analysis with LLM reasoning  
**Finance-Specific**: ✅ YES (portfolio valuation, asset allocation)

### 3. `sentiment_node.py` (249 lines)
**Purpose**: Market sentiment analysis  
**Finance-Specific**: 🟡 PARTIAL (could be generic signal analysis)

### 4. `crew_node.py` (286 lines)
**Purpose**: CrewAI strategic analysis (trend/momentum/volatility/backtest)  
**Finance-Specific**: 🟡 PARTIAL (if routes are finance-specific)

### 5. `sentinel_node.py` (283 lines)
**Purpose**: Portfolio guardian / risk assessment  
**Finance-Specific**: 🟡 PARTIAL (could be generic monitoring if routes removed)

---

## Integration Pattern (Future)

To use finance nodes in a **finance-specific graph**:

```python
# examples/verticals/finance/finance_graph.py
from core.orchestration.langgraph.graph_flow import build_graph
from examples.verticals.finance.nodes.screener_node import screener_node
from examples.verticals.finance.nodes.portfolio_node import portfolio_node

def build_finance_graph():
    """
    Extends core OS graph with finance-specific nodes.
    NOT part of system core — vertical implementation only.
    """
    graph = build_graph()  # Core domain-agnostic graph
    
    # Add finance nodes
    graph.add_node("screener", screener_node)
    graph.add_node("portfolio", portfolio_node)
    
    # Add finance routes (from route_node)
    graph.add_edge("route", "screener")  # If route == "screener"
    graph.add_edge("screener", "output_normalizer")
    
    return graph
```

---

## Why Moved Out of Core?

**Vitruvyan-core is an epistemic OS kernel** (domain-agnostic).

Finance nodes contain:
- Ticker/market-specific assumptions
- Financial ratios/metrics
- Portfolio/asset allocation logic

These belong in **vertical implementations**, not the OS kernel.

---

## References

- **Domain-Agnostic Refactoring**: `/LANGGRAPH_DOMAIN_AGNOSTIC_REFACTORING.md`
- **Core Graph**: `/vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
- **Vertical Pattern**: `/examples/verticals/README.md`

---

**Archived**: February 11, 2026  
**Reason**: Maintain OS-agnostic core architecture  
**Status**: Preserved (not deleted) for vertical reuse
