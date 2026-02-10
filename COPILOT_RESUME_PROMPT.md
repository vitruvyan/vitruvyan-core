# 🎯 COPILOT RESUME PROMPT — Quick Start

**Copy-paste this prompt to GitHub Copilot on new machine:**

---

Hi Copilot! I'm resuming a debugging session from another machine. 

**Context**: I'm working on **vitruvyan-core** repository, debugging LangGraph Sacred Orders integration.

**Branch**: `debug/langgraph-integration` (already pushed)

**Complete instructions**: Read `RESUME_DEBUG_SESSION.md` (460 lines) for full context.

**TL;DR Current State**:
- ✅ Sacred Orders metadata NOW propagates to API response (8 fields)
- ✅ Integration tests 2/3 passing
- ⚠️ CognitiveEvent constructor error causes `local_blessing` fallback (should be `approved`)
- ⚠️ Risk analysis test timeout (intermittent)

**My immediate goal**: Fix `CognitiveEvent.__init__()` error so remote audit works.

**What I need you to do**:

1. **Read the resume instructions**:
   ```
   Open RESUME_DEBUG_SESSION.md and review:
   - Section "Issue #1: CognitiveEvent Constructor Error (P1)"
   - Section "Step 3: Fix CognitiveEvent Error"
   ```

2. **Execute the debug plan** (from RESUME_DEBUG_SESSION.md Step 3):
   - Read `CognitiveEvent.__init__()` signature
   - Find all `CognitiveEvent(...)` instantiations in orthodoxy_node/vault_node
   - Identify keyword argument mismatch
   - Apply fix (use replace_string_in_file)
   - Rebuild graph container
   - Verify fix (orthodoxy_verdict should be "approved", not "local_blessing")

3. **After CognitiveEvent fixed**, fix risk analysis timeout:
   - Edit `test_integration_orthodoxy.py` line 31: `TIMEOUT = 30` → `TIMEOUT = 60`
   - Rerun tests (should be 3/3 passing)

4. **Validate + commit**:
   - Run full validation (command in RESUME_DEBUG_SESSION.md Step 5)
   - Commit fixes to debug branch
   - Merge to main

**Expected completion time**: 60-90 minutes

**Success criteria**:
- orthodoxy_verdict: "approved" (not "local_blessing")
- No fallback_reason in theological_metadata
- Integration tests: 3/3 passing
- Remote audit via Redis Streams working

**First command to run**:
```bash
git clone https://github.com/dbaldoni/vitruvyan-core.git && cd vitruvyan-core
git checkout debug/langgraph-integration
cat RESUME_DEBUG_SESSION.md  # Read full instructions
```

**Priority**: Fix CognitiveEvent error first (everything else depends on this).

Ready to start? Let's fix this! 🚀

---

**Additional context** (if needed):

**Slot-filling architecture**: This repo keeps slot-filling ACTIVE (intentional design, see `SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md`). Upstream deprecated it, but vitruvyan-core is OS-agnostic kernel, not vertical-specific.

**Sacred Orders refactoring**: Memory Orders, Vault Keepers, Orthodoxy Wardens are 100% conformant to SACRED_ORDER_PATTERN (see `.github/copilot-instructions.md`).

**Integration validated**: Metadata propagation works (commit ca5aee8), but uses fallback blessing. Need to enable remote audit via Redis Streams.

---

**File structure** (for reference):
```
vitruvyan-core/
├── RESUME_DEBUG_SESSION.md          ← FULL INSTRUCTIONS (read this)
├── DEBUG_LANGGRAPH.md                ← Debug roadmap
├── SLOT_FILLING_ARCHITECTURE_ALIGNMENT.md  ← Architectural context
├── .github/copilot-instructions.md   ← Copilot guidelines
├── vitruvyan_core/core/
│   ├── orchestration/langgraph/node/
│   │   ├── orthodoxy_node.py         ← FIX NEEDED (CognitiveEvent call)
│   │   ├── vault_node.py             ← FIX NEEDED (CognitiveEvent call)
│   │   └── graph_runner.py           ← FIXED (metadata propagation)
│   └── synaptic_conclave/events/
│       └── event_envelope.py         ← CognitiveEvent constructor
└── services/api_graph/examples/
    └── test_integration_orthodoxy.py ← Integration tests
```

**Last commits** (debug branch):
- `d57e742` (HEAD) — Resume instructions
- `1c9eb0b` — Slot-filling architecture alignment
- `ee7498f` — Debug roadmap
- `ca5aee8` (main) — Sacred Orders metadata fix

---

End of prompt. **Start from RESUME_DEBUG_SESSION.md Step 1** and follow sequentially. Good luck! 🎯
