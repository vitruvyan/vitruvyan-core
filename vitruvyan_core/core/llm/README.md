# core/llm — LLM Infrastructure Layer

## Architecture

```
core/agents/llm_agent.py   ← THE canonical LLM gateway (singleton)
core/llm/                  ← Prompt system + cache utilities
├── prompts/               ← PromptRegistry (domain-aware prompt management)
├── cache_manager.py       ← Redis-backed response caching (LLMCacheManager)
├── cache_api.py           ← Cache REST API utilities
├── gemma_client.py        ← Local Gemma model client (experimental)
└── _legacy/               ← Archived abstractions (llm_interface, conversational_llm)
```

## Nuclear Option Philosophy (Appendix G)

> **LLM is PRIMARY, validation is MANDATORY, cache is OPTIMIZATION.**

All LLM access flows through `LLMAgent` — no direct `OpenAI()` instantiation allowed anywhere in the codebase.

## Usage

### Basic completion
```python
from core.agents.llm_agent import get_llm_agent

llm = get_llm_agent()  # singleton
result = llm.complete(
    prompt="Analyze this signal",
    system_prompt="You are a domain expert.",
    temperature=0.3,
    max_tokens=500
)
# result is a string
```

### JSON mode
```python
result = llm.complete_json(
    prompt="Extract parameters as JSON",
    system_prompt="Return valid JSON only.",
)
# result is a parsed dict
```

### Raw messages (multi-turn)
```python
result = llm.complete_with_messages(
    messages=[
        {"role": "system", "content": "Expert analyst"},
        {"role": "user", "content": "What do you see?"}
    ],
    temperature=0.7
)
content = result["content"]
```

### Function calling / MCP tools
```python
result = llm.complete_with_tools(
    messages=[{"role": "user", "content": "Get latest data"}],
    tools=[{"type": "function", "function": {...}}],
    tool_choice="auto"
)
if result.get("tool_calls"):
    for tc in result["tool_calls"]:
        print(tc["function"]["name"], tc["function"]["arguments"])
```

## Model Resolution

Environment variable chain (priority order):
```
VITRUVYAN_LLM_MODEL → GRAPH_LLM_MODEL → OPENAI_MODEL → "gpt-4o-mini"
```

Per-call override: pass `model="gpt-4o"` to any method.

## PromptRegistry

Domain-aware prompt templates. Auto-registers `"generic"` domain at boot.

```python
from core.llm.prompts.registry import PromptRegistry

registry = PromptRegistry()
registry.register_domain("support", {
    "identity": "You are a support assistant.",
    "scenarios": {"ticket_triage": "Classify this ticket..."}
})

prompt = registry.get_combined("support", "ticket_triage", user_input="...")
```

## Built-in Resilience

| Feature | Description |
|---------|-------------|
| **Rate Limiter** | Token bucket (configurable RPM) |
| **Circuit Breaker** | Opens after N consecutive failures, auto-resets |
| **Caching** | Redis-backed, prompt-hash keyed, optional per call |
| **Metrics** | Prometheus-compatible counters/histograms |

## What NOT to do

```python
# ❌ FORBIDDEN — direct OpenAI instantiation
from openai import OpenAI
client = OpenAI()

# ❌ FORBIDDEN — scattered env var reads
model = os.getenv("GRAPH_LLM_MODEL", "gpt-4o-mini")

# ✅ CORRECT — use LLMAgent
from core.agents.llm_agent import get_llm_agent
llm = get_llm_agent()
```
