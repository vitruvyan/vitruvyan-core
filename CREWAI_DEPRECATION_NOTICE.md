# CrewAI Deprecation Notice

**Date**: February 13, 2026  
**Status**: REMOVED

## Summary

CrewAI has been **completely removed** from Vitruvyan Core. Multi-agent orchestration is now handled exclusively by **LangGraph**.

## Rationale

1. **Architectural consolidation**: LangGraph provides sufficient orchestration capabilities
2. **Reduced complexity**: Eliminates redundant multi-agent frameworks
3. **Better maintainability**: Single orchestration layer (LangGraph) easier to maintain
4. **Performance**: LangGraph + Docker services proven sufficient for all use cases

## What Was Removed

### Dependencies
- `crewai==0.175.0` (removed from all requirements files)
- `crewai-tools==0.17.0` (removed from requirements-full.txt)
- Package uninstalled from system

### Files Deprecated
- `infrastructure/docker/requirements/requirements.crewai.txt` → `.deprecated`
- `infrastructure/docker/requirements/requirements.crewai.edge.txt` → `.deprecated`

### Configuration
- `.env`: `CREWAI_TELEMETRY_DISABLED` → commented out
- Service endpoints: `crewai_agents` removed from cognitive_bridge.py

### Metrics
- `crew_agent_latency_seconds` (Prometheus metric) → commented out in:
  - `services/api_graph/monitoring/health.py`
  - `services/api_graph/main.py.legacy`

### Documentation Updates
- `examples/verticals/finance/README.md` — marked `crew_node.py` as deprecated
- `services/api_babel_gardens/README.md` — removed `api_crewai:8002` integration note
- `services/api_graph/README.md` — marked CrewAI metrics as deprecated

## Migration Path

**Before** (CrewAI multi-agent):
```python
from crewai import Agent, Task, Crew

agent = Agent(role="analyst", goal="analyze", backstory="...")
task = Task(description="...", agent=agent)
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

**After** (LangGraph orchestration):
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(GraphState)
graph.add_node("analyze", analyze_node)
graph.add_edge("analyze", END)
app = graph.compile()
result = app.invoke({"input": "..."})
```

## References

- **LangGraph docs**: `vitruvyan_core/core/orchestration/langgraph/`
- **Sacred Orders**: Use StreamBus for multi-service orchestration
- **Domain verticals**: Implement custom nodes in `examples/verticals/<domain>/nodes/`

## Legacy Code

CrewAI stub placeholders remain in:
- `examples/verticals/finance/nodes/crew_node.py` (placeholder only — no actual CrewAI logic)

These are intentionally kept as architectural examples but contain no functional CrewAI code.

## Test Coverage

**All 264 tests pass** after CrewAI removal (no CrewAI-specific tests existed in test suite).

---

**For questions**: See `.github/copilot-instructions.md` section on LangGraph orchestration.
