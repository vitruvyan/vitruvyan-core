# Cognitive Bus Documentation

**Welcome!** This directory contains complete documentation for Vitruvyan's Cognitive Bus - the distributed event backbone inspired by octopus neural systems and fungal mycelial networks.

---

## 🎯 Start Here

**New to Cognitive Bus?** Read documents in this order:

1. **[COGNITIVE_BUS_GUIDE.md](COGNITIVE_BUS_GUIDE.md)** ← **START HERE**
   - 988 lines, 5 parts: Philosophy, Architecture, Implementation, Patterns, Troubleshooting
   - Step-by-step listener creation guide
   - Complete code examples
   - **This is your main resource**

2. **[API_REFERENCE.md](API_REFERENCE.md)**
   - Quick reference for StreamBus, Herald, Scribe APIs
   - Method signatures, parameters, return values
   - Redis CLI commands
   - Error codes and solutions

3. **[ARCHITECTURAL_DECISIONS.md](ARCHITECTURAL_DECISIONS.md)**
   - Decision log (ADR-001/002/003)
   - Why Pub/Sub → Streams
   - Why mkstream=True (consumer autonomy)
   - Historical context and lessons learned

---

## 📚 Document Index

### Core Guides (Read These First)

| Document | Purpose | Lines | Read Time |
|----------|---------|-------|-----------|
| **COGNITIVE_BUS_GUIDE.md** | Complete implementation guide | 988 | 30 min |
| **API_REFERENCE.md** | API quick reference | 600 | 15 min |
| **ARCHITECTURAL_DECISIONS.md** | Decision log (ADR-001/002/003) | 800 | 20 min |

**Total: 2,388 lines, ~65 minutes read time**

---

### Architecture & Philosophy

| Document | Purpose | Lines |
|----------|---------|-------|
| **[Vitruvyan_Octopus_Mycelium_Architecture.md](Vitruvyan_Octopus_Mycelium_Architecture.md)** | Bio-inspired design principles | 416 |
| **[Vitruvyan_Bus_Invariants.md](Vitruvyan_Bus_Invariants.md)** | 4 Sacred Invariants (non-negotiable) | 216 |
| **[BUS_ARCHITECTURE.md](BUS_ARCHITECTURE.md)** | Technical architecture deep dive | 419 |
| **[REDIS_STREAMS_ARCHITECTURE.md](REDIS_STREAMS_ARCHITECTURE.md)** | Redis Streams internals | 461 |

---

### Implementation Details

| Document | Purpose | Lines |
|----------|---------|-------|
| **[BUS_HARDENING_PLAN.md](BUS_HARDENING_PLAN.md)** | Production readiness checklist | 300 |
| **[PLASTICITY_ADMIN_UI_SPEC.md](PLASTICITY_ADMIN_UI_SPEC.md)** | Admin dashboard specification | 1,200 |
| **[VITRUVYAN_COGNITIVE_ARCHITECTURE_EXPLAINED.md](VITRUVYAN_COGNITIVE_ARCHITECTURE_EXPLAINED.md)** | High-level cognitive architecture | 900 |

---

### Historical Context (Optional)

Phase reports and migration history are in **[history/](history/)** directory:

- `IMPLEMENTATION_ROADMAP.md` (1,782 lines) - Original roadmap
- `PHASE_0_BUS_HARDENING_REPORT.md` (1,000+ lines) - Pub/Sub → Streams migration
- `PHASE_4_IMPLEMENTATION_REPORT.md` - Listener migration
- `PHASE_6_PLASTICITY_*.md` - Plasticity system implementation
- `LISTENER_MIGRATION_STATUS.md` - Migration tracking

**These are historical records, not required reading for implementation.**

---

## 🎓 Learning Paths

### Path 1: I Want to Implement a Listener (45 min)

1. Read **COGNITIVE_BUS_GUIDE.md** sections:
   - Section 1: Philosophy & Vision (10 min)
   - Section 2: Core Architecture (10 min)
   - Section 3.1: Step-by-Step Listener Creation (20 min)
   - Section 5: Troubleshooting (5 min)

2. Copy template from Section 3.1
3. Implement your listener
4. Reference **API_REFERENCE.md** as needed

---

### Path 2: I Need Quick API Reference (10 min)

1. Read **API_REFERENCE.md**:
   - StreamBus section (methods, parameters)
   - Event Models section (TransportEvent, CognitiveEvent)
   - Redis CLI Commands (debugging)

2. Use as reference while coding

---

### Path 3: I Want to Understand Architecture (60 min)

1. **Vitruvyan_Octopus_Mycelium_Architecture.md** (15 min)
   - Why octopus + mycelium models?
   - How they map to Cognitive Bus

2. **BUS_ARCHITECTURE.md** (20 min)
   - 2-layer event model
   - Streams vs Pub/Sub comparison

3. **ARCHITECTURAL_DECISIONS.md** (20 min)
   - ADR-001: Why Streams?
   - ADR-003: Why consumer autonomy?

4. **Vitruvyan_Bus_Invariants.md** (5 min)
   - 4 Sacred Invariants (non-negotiable rules)

---

### Path 4: I'm Debugging a Problem (20 min)

1. **COGNITIVE_BUS_GUIDE.md** Section 5: Troubleshooting
   - XGROUP errors
   - ReadOnlyError
   - Events not being consumed
   - Container crash loops
   - Memory leaks

2. **API_REFERENCE.md** Redis CLI Commands
   - Check stream existence
   - Inspect consumer groups
   - View pending events

3. Check logs:
   ```bash
   docker logs vitruvyan_vault_keepers_listener
   docker logs vitruvyan_redis_master
   ```

---

## 🔑 Key Concepts

### The 4 Sacred Invariants

These MUST NEVER be violated:

1. ❌ Bus NEVER inspects payload content
2. ❌ Bus NEVER correlates events
3. ❌ Bus NEVER does semantic routing
4. ❌ Bus NEVER creates events autonomously

**Why?** Keep bus simple (dumb transport). Intelligence belongs in consumers.

---

### Consumer Autonomy (mkstream=True)

**CRITICAL DECISION** (Feb 5, 2026):

```python
# ✅ CORRECT: Consumer creates stream if missing
bus.create_consumer_group("channel", "group")  # mkstream=True by default

# ❌ WRONG: Wait for publisher to create stream
bus.create_consumer_group("channel", "group", mkstream=False)  # Can deadlock!
```

**Rationale**: Octopus arms don't wait for brain permission, mycelium nodes self-organize.

---

### 2-Layer Event Model

```
CognitiveEvent (consumer layer)
  - Mutable, rich semantics
  - Causal chains (causation_id)
       ↕️
EventAdapter (serialization)
       ↕️
TransportEvent (bus layer)
  - Immutable, opaque payload
  - Bus never inspects content
```

---

## 📖 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| COGNITIVE_BUS_GUIDE.md | ✅ Current | Feb 5, 2026 |
| API_REFERENCE.md | ✅ Current | Feb 5, 2026 |
| ARCHITECTURAL_DECISIONS.md | ✅ Current | Feb 5, 2026 |
| Vitruvyan_Octopus_Mycelium_Architecture.md | ✅ Current | Jan 24, 2026 |
| Vitruvyan_Bus_Invariants.md | ✅ Current | Jan 24, 2026 |
| BUS_ARCHITECTURE.md | ✅ Current | Jan 24, 2026 |
| REDIS_STREAMS_ARCHITECTURE.md | ✅ Current | Jan 24, 2026 |

**Historical documents** (in history/) are frozen snapshots, not updated.

---

## 🛠️ Quick Start Commands

### Test Listener

```bash
# Start listener
docker compose up -d vitruvyan_vault_keepers_listener

# Check logs
docker logs vitruvyan_vault_keepers_listener

# Emit test event
docker exec vitruvyan_redis_master redis-cli \
  XADD stream:vitruvyan:codex.discovery.mapped '*' ticker AAPL sector Technology

# Verify listener processed it
docker logs vitruvyan_vault_keepers_listener | grep "Archiving ticker"
```

---

### Debug Redis Streams

```bash
# List all streams
docker exec vitruvyan_redis_master redis-cli KEYS "stream:*"

# Check stream length
docker exec vitruvyan_redis_master redis-cli \
  XLEN stream:vitruvyan:codex.discovery.mapped

# Check consumer groups
docker exec vitruvyan_redis_master redis-cli \
  XINFO GROUPS stream:vitruvyan:codex.discovery.mapped

# Check pending events
docker exec vitruvyan_redis_master redis-cli \
  XPENDING stream:vitruvyan:codex.discovery.mapped vault_keepers
```

---

## 🤝 Contributing

**Found a gap in documentation?**

1. Check if it's in existing docs (use search)
2. If missing, add to appropriate doc:
   - Implementation → **COGNITIVE_BUS_GUIDE.md**
   - API → **API_REFERENCE.md**
   - Decision → **ARCHITECTURAL_DECISIONS.md**
3. Submit PR with clear description

---

## ❓ Questions?

**If documentation doesn't answer your question**:

1. Check **COGNITIVE_BUS_GUIDE.md** Troubleshooting section
2. Check **API_REFERENCE.md** Error Codes
3. Check **ARCHITECTURAL_DECISIONS.md** for historical context
4. Ask on #cognitive-bus Slack channel
5. File issue on GitHub

---

## 📊 Documentation Statistics

- **Total documents**: 11 core + 6 historical
- **Total lines**: ~8,500 lines (core docs)
- **Read time**: ~4 hours (all core docs)
- **Quick start**: 45 minutes (COGNITIVE_BUS_GUIDE.md sections 1-3)

**Documentation last restructured**: February 5, 2026

**Rationale**: Previous structure had 14 fragmented files with no clear entry point. Consolidated to 3 main guides + supporting docs for easier onboarding and maintenance.

---

**Happy coding!** 🚀

---

**End of README** | Version 1.0 | February 5, 2026
