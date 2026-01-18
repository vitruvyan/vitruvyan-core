# CrewAI Deprecation Plan
**Date**: January 18, 2026  
**Status**: PLANNED  
**Rationale**: Replace external dependency with native Vitruvyan agents

---

## Executive Summary

CrewAI will be deprecated in `vitruvyan-core` in favor of native Vitruvyan agents built on top of our existing cognitive architecture.

**Reasons for deprecation:**
1. **Dependency bloat** — CrewAI adds unnecessary external complexity
2. **Architecture mismatch** — CrewAI's opinionated patterns conflict with Sacred Orders
3. **Control** — Native agents give us full control over behavior, logging, governance
4. **Domain flexibility** — Custom agents can be tailored per vertical without CrewAI constraints
5. **Lesson learned** — During Mercator development, we realized this work can be done in-house

---

## Current CrewAI Usage

### Files with CrewAI imports (20 files)

**Core orchestration (4 files):**
```
vitruvyan_core/core/orchestration/crewai/__init__.py (41 lines)
vitruvyan_core/core/orchestration/crewai/base_agent.py (264 lines)
vitruvyan_core/core/orchestration/crewai/base_tool.py (86 lines)
vitruvyan_core/core/orchestration/crewai/logging_utils.py (132 lines)
```

**LangGraph nodes using CrewAI (6 files):**
```
vitruvyan_core/core/orchestration/langgraph/node/crew_node.py
vitruvyan_core/core/orchestration/langgraph/node/quality_check_node.py
vitruvyan_core/core/orchestration/langgraph/node/compose_node.py
vitruvyan_core/core/orchestration/langgraph/node/llm_soft_node.py
vitruvyan_core/core/orchestration/langgraph/node/output_normalizer_node.py
vitruvyan_core/core/orchestration/langgraph/graph_flow.py
```

**Foundation (3 files):**
```
vitruvyan_core/core/foundation/cognitive_bus/herald.py
vitruvyan_core/core/foundation/cognitive_bus/event_schema.py
vitruvyan_core/core/foundation/cognitive_bus/lexicon.py
```

**Governance (4 files):**
```
vitruvyan_core/core/governance/vault_keepers/chamberlain.py
vitruvyan_core/core/governance/vault_keepers/chamberlain_crewai_backup.py
vitruvyan_core/core/governance/codex_hunters/scripts/backfill_*.py
```

---

## Replacement Architecture

### Native Vitruvyan Agent Pattern

```python
# vitruvyan_core/core/orchestration/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Standard agent roles in Vitruvyan architecture"""
    ANALYST = "analyst"       # Examines data, produces insights
    VALIDATOR = "validator"   # Checks quality and consistency
    EXECUTOR = "executor"     # Performs actions
    REPORTER = "reporter"     # Synthesizes information
    HUNTER = "hunter"         # Data acquisition (Codex Hunters)
    WARDEN = "warden"         # Governance (Orthodoxy Wardens)
    KEEPER = "keeper"         # Persistence (Vault Keepers)


@dataclass
class AgentContext:
    """Runtime context passed to agents"""
    correlation_id: str
    user_id: Optional[str]
    domain: str
    session_data: Dict[str, Any]


@dataclass
class AgentResult:
    """Standardized agent output"""
    success: bool
    data: Any
    confidence: float  # 0.0-1.0
    reasoning: str
    metadata: Dict[str, Any]


class VitruvyanAgent(ABC):
    """
    Base class for all Vitruvyan agents.
    
    Replaces CrewAI Agent with native implementation that:
    - Integrates with Sacred Orders (audit, validation)
    - Uses Cognitive Bus for event publishing
    - Provides standardized I/O contracts
    - Supports domain-agnostic behavior
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str,
        tools: List["VitruvyanTool"] = None,
        llm_config: Dict[str, Any] = None
    ):
        self.name = name
        self.role = role
        self.description = description
        self.tools = tools or []
        self.llm_config = llm_config or {}
    
    @abstractmethod
    def execute(self, task: str, context: AgentContext) -> AgentResult:
        """Execute the agent's primary task"""
        pass
    
    def validate_input(self, task: str, context: AgentContext) -> bool:
        """Pre-execution validation (override in subclasses)"""
        return True
    
    def post_process(self, result: AgentResult) -> AgentResult:
        """Post-execution processing (override in subclasses)"""
        return result
    
    def run(self, task: str, context: AgentContext) -> AgentResult:
        """Full execution pipeline with validation and post-processing"""
        if not self.validate_input(task, context):
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                reasoning="Input validation failed",
                metadata={"agent": self.name, "role": self.role.value}
            )
        
        result = self.execute(task, context)
        return self.post_process(result)


class VitruvyanTool(ABC):
    """
    Base class for agent tools.
    Replaces CrewAI Tool with native implementation.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Execute the tool"""
        pass
```

---

## Migration Plan

### Phase 1: Create Native Agent Framework (Week 1)
1. Create `vitruvyan_core/core/orchestration/agents/` directory
2. Implement `VitruvyanAgent` base class
3. Implement `VitruvyanTool` base class
4. Add Sacred Orders integration (audit logging, validation hooks)

### Phase 2: Migrate Existing Agents (Week 2)
1. Convert `crew_node.py` → native agent orchestration
2. Convert `quality_check_node.py` → native validator agent
3. Update `compose_node.py` to use native agents
4. Update graph_flow.py routing

### Phase 3: Remove CrewAI (Week 3)
1. Delete `vitruvyan_core/core/orchestration/crewai/` directory
2. Remove crewai from requirements.txt
3. Update all imports
4. Run full test suite

### Phase 4: Documentation (Week 3)
1. Update architecture docs
2. Add migration guide for verticals
3. Update README

---

## Compatibility Notes

### For Verticals (Mercator, Aegis, etc.)

Verticals that use CrewAI should:
1. Keep their own CrewAI dependency if needed
2. OR migrate to native VitruvyanAgent pattern
3. The core will provide base classes that work with OR without CrewAI

### LangGraph Integration

The native agents will integrate seamlessly with LangGraph:
```python
# In langgraph node
from vitruvyan_core.core.orchestration.agents import VitruvyanAgent

def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = MyCustomAgent()
    context = AgentContext(
        correlation_id=state["correlation_id"],
        user_id=state.get("user_id"),
        domain=state.get("domain", "generic"),
        session_data=state
    )
    result = agent.run(state["task"], context)
    return {"agent_result": result}
```

---

## Benefits of Native Agents

| Aspect | CrewAI | Native Vitruvyan |
|--------|--------|------------------|
| Dependencies | Heavy (langchain, etc.) | Minimal (stdlib + our libs) |
| Logging | CrewAI's format | Sacred Orders compliant |
| Governance | External | Integrated (Orthodoxy Wardens) |
| Customization | Limited by framework | Full control |
| Domain support | Generic | Tailored per vertical |
| Testing | CrewAI mocks needed | Direct unit testing |
| Performance | Framework overhead | Lean execution |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 18, 2026 | Deprecate CrewAI | Mercator development showed custom agents are more flexible |
| Jan 18, 2026 | Keep LangGraph | LangGraph provides orchestration, agents provide execution |
| Jan 18, 2026 | Native agent pattern | Aligns with Sacred Orders and epistemic principles |

---

## References

- [Sacred Orders Architecture](../foundational/Vitruvyan_Vertical_Specification.md)
- [Bus Invariants](../foundational/Vitruvyan_Bus_Invariants.md) — Agents must respect bus constraints
- [Epistemic Charter](../foundational/Vitruvyan_Epistemic_Charter.md) — Agents must implement uncertainty
