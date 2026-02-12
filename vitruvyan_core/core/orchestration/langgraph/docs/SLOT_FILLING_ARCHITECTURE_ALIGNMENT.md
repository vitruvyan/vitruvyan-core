# Slot-Filling Architecture Alignment

**Date**: Feb 10, 2026  
**Status**: ACTIVE IN VITRUVYAN-CORE  
**Cross-Repository**: Upstream deprecated, Core keeps active

---

## 📊 Repository Comparison

| Aspect | Upstream (`vitruvyan`) | This Repo (`vitruvyan-core`) |
|--------|------------------------|------------------------------|
| **Slot-Filling Status** | ❌ DEPRECATED (Jan 13, 2026) | ✅ ACTIVE (intentional) |
| **Architecture** | LLM-first (CAN + MCP) | Hybrid (slot-filling + LLM) |
| **Feature Flag** | `DISABLE_SLOT_FILLING=1` | No flag (always enabled) |
| **Use Case** | Finance vertical (UX optimization) | OS-agnostic kernel (primitives) |
| **Deprecation** | Hard removal Q2 2026 | No planned deprecation |
| **Routing** | `intent=unknown` → CAN node | `intent=unknown` → slot_filler |

---

## 🎯 Why Different Strategies?

### Upstream Deprecation Rationale (Finance Vertical)
**Problem solved**:
- **UX friction**: 3+ message roundtrips for single query
- **Latency**: 7-10s (multi-turn LLM calls)
- **Cost**: $19/mth per 10K MAU
- **Context loss**: Rigid slot collection killed conversation flow

**Solution**: CAN node + OpenAI Function Calling + MCP tools
- **1 roundtrip**: LLM extracts context semantically
- **3-5s latency**: -57% improvement
- **$10/mth cost**: -47% improvement
- **95% context understanding**: vs 0% (regex-based)

**Metrics** (measured):
```
Latency:    7-10s → 3-5s   (-57%)
Cost:       $19   → $10    (-47%)
Messages:   3+    → 1      (-66%)
Context:    0%    → 95%    (+95%)
Languages:  4     → 84     (+2000%)
```

### Vitruvyan-Core Retention Rationale (OS Kernel)

**Why keep slot-filling**:
1. **Generic primitive**: OS-level dialogue parameter management
2. **Domain-neutral**: Not tied to finance vertical assumptions
3. **Flexibility**: Verticals choose to use/override/extend
4. **No UX coupling**: Core doesn't dictate vertical UX patterns
5. **Backwards compatibility**: Existing verticals depend on pattern

**Design principle**:
> "vitruvyan-core provides **primitives**, verticals decide **patterns**"

Slot-filling = primitive for **"collect missing parameters via dialogue"**.  
Verticals (finance, etc.) decide if to use it or replace with LLM-first.

---

## 🔧 Implementation Differences

### Upstream (LLM-First Architecture)

**compose_node.py**:
```python
# Feature flag (default: slot-filling disabled)
DISABLE_SLOT_FILLING = int(os.getenv("DISABLE_SLOT_FILLING", "1"))

if DISABLE_SLOT_FILLING:
    # Skip slot checking, let CAN handle missing params
    return state
else:
    # Legacy slot-filling (with warnings)
    warnings.warn("DEPRECATED: Migrate to LLM-first", DeprecationWarning)
    return check_slots(state)
```

**CAN node** (Conversational Analysis Node):
```python
# Semantic context extraction via GPT-4o-mini
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Extract parameters from context"},
        {"role": "user", "content": user_query},
        {"role": "user", "content": f"Semantic context: {vsgs_matches}"}
    ],
    tools=mcp_tools  # 11 MCP tools via OpenAI Function Calling
)

# LLM decides which tool to call + extracts args
tool_call = response.choices[0].message.tool_calls[0]
result = execute_mcp_tool(tool_call.name, tool_call.arguments)
```

### Vitruvyan-Core (Slot-Filling Active)

**route_node.py** (line 64):
```python
elif intent == "unknown":
    # "unknown" goes to slot_filler for priority slot check in compose_node
    state["route"] = "slot_filler"
    print(f"➡️ Routing: intent 'unknown' → slot_filler (compose with slot check priority)")
```

**slot_filler.py** (core/orchestration/compose/):
```python
def slot_filler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multi-turn dialogue for missing parameters.
    Generic OS primitive - domain-agnostic.
    """
    missing = []
    
    # Check required slots (generic entity/param collection)
    if not state.get("entity_ids"):
        missing.append("entities")
    if not state.get("horizon"):
        missing.append("horizon")
    
    if missing:
        # Generate clarification question (LLM-enhanced)
        question = generate_slot_question(
            missing_slots=missing,
            user_input=state["input_text"],
            language=state.get("language", "en")
        )
        return {
            "response": {"action": "clarify", "message": question},
            "route": "slot_filler_complete"
        }
    
    # All slots filled → continue to execution
    return state
```

**finance/slot_filler.py** (domain-specific override):
```python
class FinanceSlotFiller(SlotFiller):
    """
    Finance-specific slot-filling logic.
    Extends generic OS primitive with domain rules.
    """
    def check_slots(self, state: Dict[str, Any]) -> List[str]:
        missing = super().check_slots(state)  # Call OS primitive
        
        # Finance-specific: ticker validation
        if state.get("entity_ids"):
            invalid = [t for t in state["entity_ids"] if not is_valid_ticker(t)]
            if invalid:
                missing.append("valid_tickers")
        
        return missing
```

---

## 🔀 Migration Paths (Future Considerations)

### Option A: Add DISABLE_SLOT_FILLING Flag to Core (Recommended)
**Benefit**: Vertical flexibility (choose pattern per service)

```python
# vitruvyan_core/core/orchestration/langgraph/node/route_node.py
DISABLE_SLOT_FILLING = int(os.getenv("DISABLE_SLOT_FILLING", "0"))  # Default: enabled

elif intent == "unknown":
    if DISABLE_SLOT_FILLING:
        state["route"] = "compose"  # Let compose handle via semantic fallback
    else:
        state["route"] = "slot_filler"  # Multi-turn dialogue
```

**Usage**:
```bash
# Finance vertical (LLM-first)
DISABLE_SLOT_FILLING=1 docker compose up vitruvyan_finance

# Other verticals (slot-filling)
DISABLE_SLOT_FILLING=0 docker compose up vitruvyan_analytics
```

### Option B: Semantic Parameter Negotiation (Future Evolution)
**Concept**: Hybrid approach (best of both)

```python
# Combine slot-filling UX with LLM context awareness
def semantic_slot_negotiation(state: Dict[str, Any]) -> Dict[str, Any]:
    missing = check_slots(state)  # OS primitive
    
    if missing:
        # Try semantic extraction first (LLM-first attempt)
        extracted = extract_via_vsgs_and_llm(
            user_input=state["input_text"],
            semantic_context=state.get("semantic_matches", [])
        )
        
        # Fill slots from semantic extraction
        for slot in missing:
            if slot in extracted and extracted[slot]:
                state[slot] = extracted[slot]
        
        # Re-check (still missing after LLM extraction?)
        still_missing = check_slots(state)
        
        if still_missing:
            # Fallback to slot-filling dialogue (only if LLM failed)
            return generate_slot_question(still_missing, state)
    
    return state  # All slots filled (via LLM or dialogue)
```

**Benefit**: 
- **Fast path**: LLM extracts → 1 roundtrip (like upstream)
- **Fallback**: Slot-filling dialogue if LLM uncertain (safety net)
- **Best UX**: <5s when context clear, clarification when ambiguous

### Option C: Keep Current Architecture (Status Quo)
**Decision**: Valid if:
- ✅ Core remains domain-agnostic (no vertical assumptions)
- ✅ Verticals have freedom to override/extend patterns
- ✅ Slot-filling UX acceptable for generic OS usage

**Risk**: Vertical duplication (each vertical reimplements deprecation)

---

## 📚 References

### Upstream Deprecation Docs
- **Commit**: `c7bd99f9` (Jan 13, 2026) — Soft deprecation + feature flag
- **Commit**: `4a66d379` (Jan 17, 2026) — Production merge (LLM-first active)
- **File**: `core/langgraph/node/compose_node.py` (DISABLE_SLOT_FILLING flag)
- **Tests**: `tests/test_slot_filling_removal.py` (337 lines)
- **Metrics**: -57% latency, -47% cost, +95% context understanding

### Vitruvyan-Core Implementation
- **File**: `route_node.py` (line 64) — `intent=unknown` → `slot_filler`
- **Core**: `core/orchestration/compose/slot_filler.py` (OS primitive)
- **Domain**: `domains/finance/slot_filler.py` (finance-specific)
- **Tests**: `services/api_graph/examples/test_graph_slots.py`

### Architecture Docs
- **Instructions**: `.github/copilot-instructions.md` section 7
- **Debug plan**: `DEBUG_LANGGRAPH.md` (architectural divergence note)
- **This file**: `SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md`

---

## 🎯 Decision Matrix (When to Use What)

| Scenario | Upstream Pattern | Core Pattern | Recommendation |
|----------|------------------|--------------|----------------|
| **Finance vertical** | LLM-first (CAN + MCP) | Slot-filling | ✅ Use upstream (proven metrics) |
| **Analytics vertical** | LLM-first fallback | Slot-filling | ⚠️ Evaluate: params structured? |
| **Generic OS usage** | N/A | Slot-filling | ✅ Use core primitive |
| **New vertical** | LLM-first | Slot-filling | 🔧 Choose based on UX needs |
| **Prototype/MVP** | Complex setup | Simple dialogue | ✅ Start with slot-filling |

**Rule of Thumb**:
- **Conversational UX** (freeform queries) → LLM-first (upstream pattern)
- **Structured params** (form-like collection) → Slot-filling (core pattern)
- **Hybrid** → Option B (semantic parameter negotiation)

---

## ✅ Validation Checklist

**When working in vitruvyan-core**:
- [ ] ✅ Recognize slot-filling is **NOT deprecated** here
- [ ] ✅ `route_node.py` routing to `slot_filler` is **intentional**
- [ ] ✅ Document trade-offs (latency vs simplicity)
- [ ] ⚠️ Don't blindly copy upstream deprecation to core
- [ ] ⚠️ Respect OS-agnostic principle (no vertical coupling)

**When working in verticals/services**:
- [ ] 🔍 Evaluate: LLM-first vs slot-filling for **this domain**
- [ ] 📊 Consider metrics: latency, cost, UX flow
- [ ] ⚙️ If migrating: add `DISABLE_SLOT_FILLING` flag
- [ ] 📚 Document pattern choice in service README

**When refactoring**:
- [ ] 🚫 Don't remove slot-filling from core (OS primitive)
- [ ] ✅ Consider adding toggle flag (Option A)
- [ ] 🔮 Evaluate semantic parameter negotiation (Option B)
- [ ] 📖 Update docs to reflect architectural decisions

---

**Status**: ACTIVE IN VITRUVYAN-CORE  
**Last Updated**: Feb 10, 2026  
**Next Review**: Q2 2026 (align with upstream hard removal timeline)
