# LLM / AI Layer (LLMAgent)

<p class="kb-subtitle">Canonical gateway for all LLM calls: caching, rate limiting, circuit breaking, tool use, and metrics — without embedding prompts inside the core.</p>

## What it does

- Enforces a **single entry point** for LLM calls across services: `get_llm_agent()` → `LLMAgent`.
- Provides operational safety primitives:
  - **rate limiting** to prevent provider throttling
  - **circuit breaker** for graceful degradation
  - **cache** as an optimization layer (Redis-backed when available)
  - **metrics** for latency/tokens/cache hit rate
- Supports multiple interaction styles:
  - `complete()` for simple prompt + optional system prompt
  - `complete_with_messages()` for full message arrays
  - `complete_with_tools()` for function calling / tool execution

## Core contract

### “Gateway, not a brain”

- `LLMAgent` is a **gateway**: it does not own business logic, domain prompts, or truth rules.
- Callers (nodes/services) own:
  - prompts and schemas
  - validation (Truth layer) and governance decisions
  - what gets persisted or emitted

### Configuration (model resolution)

Model resolution chain:

`VITRUVYAN_LLM_MODEL` → `GRAPH_LLM_MODEL` → `OPENAI_MODEL` → `gpt-4o-mini`

Required secret:

`OPENAI_API_KEY`

Code: `vitruvyan_core/core/agents/llm_agent.py`

## Typical usage

```python
from core.agents.llm_agent import get_llm_agent

llm = get_llm_agent()
text = llm.complete(
    prompt="Classify intent for: 'analyze NVDA momentum'",
    system_prompt="Return a short intent label.",
    temperature=0.0,
)
```

## Failure modes (designed behavior)

- If the provider throttles: the **rate limiter** blocks calls pre-emptively (predictive token accounting).
- If failures accumulate: the **circuit breaker** opens to stop cascading errors, then auto-resets after cooldown.
- If Redis/cache is unavailable: caching is **disabled** automatically (warning logged), calls still proceed.

## Integration points

In the current architecture, `LLMAgent` is used by orchestration nodes and services that need:

- intent classification / parsing
- tool routing and structured extraction
- conversational composition

See: `docs/architecture/MAPPA_ARCHITETTURALE_MODULI.md`

## References (deep dive)

- LLM gateway: `vitruvyan_core/core/agents/llm_agent.py`
- Conversational layer context: `.github/Vitruvyan_Appendix_F_Conversational_Layer.md`

