# Vitruvyan Core — Module Status Map

> **Last updated**: February 14, 2026 (post-Priority 2B: hook pattern implementation)  
> **Purpose**: Single-source-of-truth inventory for developers onboarding to Vitruvyan  
> **Scope**: Module-level status (active/stub/legacy), domain-specificity, test coverage

---

## Quick Legend

| Status | Meaning |
|--------|---------|
| **ACTIVE** | Fully implemented, tested, production-ready |
| **HOOK** | Registry-based plugin pattern (graceful stub if domain not registered) |
| **STUB** | Placeholder implementation (passthrough or fake success) |
| **PARTIAL** | Core implementation present, integration gaps exist |
| **LEGACY** | Archived code (read-only, historical reference) |
| **REMOVED** | Deleted from active codebase |

---

## 1. LangGraph Nodes (Path B — Sync Query Pipeline)

**Location**: `vitruvyan_core/core/orchestration/langgraph/node/`  
**Total Active Nodes**: 19 (as of Feb 14, 2026) *(full graph wiring; graph terminates via LangGraph `END`, not a node module)*

| Node | Status | Domain-Specific | Env Var | Default Behavior | Notes |
|------|--------|----------------|---------|------------------|-------|
| `parse_node.py` | ACTIVE | No | - | Parses user input to BaseGraphState | Domain-agnostic text parsing |
| `intent_detection_node.py` | HOOK | Yes | `INTENT_DOMAIN` | Core intents (soft, unknown) | Finance intents if `INTENT_DOMAIN=finance` |
| `pattern_weavers_node.py` | ACTIVE | No (delegated) | - | Calls Pattern Weavers HTTP API | Ontology mapping, semantic context |
| `entity_resolver_node.py` | HOOK | Yes | `ENTITY_DOMAIN` | Passthrough stub | Finance: ticker→company if registered |
| `emotion_detector.py` (Babel) | ACTIVE | No | - | Calls Babel Gardens HTTP API | Emotion + language detection |
| `semantic_grounding_node.py` | ACTIVE | No | `VSGS_ENABLED` | VSGS semantic grounding | Feature-flagged |
| `params_extraction_node.py` | ACTIVE | No | - | Domain-neutral temporal patterns | Finance cleanup completed Feb 14 |
| `route_node.py` (decide) | ACTIVE | No | - | Intent-based routing | 6 route branches |
| `exec_node.py` | HOOK | Yes | `EXEC_DOMAIN` | Fake success stub | Finance: Neural Engine if registered |
| `qdrant_node.py` | ACTIVE | No | - | Semantic search via QdrantAgent | RAG fallback |
| `compose_node.py` | ACTIVE | No | - | VEE narrative composition | Domain-agnostic template engine |
| `cached_llm_node.py` | ACTIVE | No | - | LLM completion via LLMAgent | Mnemosyne caching |
| `llm_mcp_node.py` | ACTIVE | No | `USE_MCP` | OpenAI Function Calling + MCP tools | Optional route |
| `output_normalizer_node.py` | ACTIVE | No | - | Normalizes execution output | Sacred Flow entry |
| `orthodoxy_node.py` | ACTIVE | No | - | Validation + audit | Sacred Flow (Truth) |
| `vault_node.py` | ACTIVE | No | - | Archival persistence | Sacred Flow (Memory) |
| `can_node.py` | ACTIVE | No | - | Contextual Answer Normalizer | LLM-based synthesis |
| `advisor_node.py` | STUB | Yes | - | Returns "Domain plugin required" | Portfolio stub (finance) |
| `codex_hunters_node.py` | ACTIVE | No | - | System maintenance route | Codex Hunters HTTP API |

### Archived Nodes (_legacy/)

| Node | Reason | Date Archived |
|------|--------|--------------|
| `intent_detection_node.py` (old) | Rewritten for hook pattern (600L→314L) | Feb 12, 2026 |
| `codex_node.py` | Duplicate of `codex_hunters_node.py` | Feb 14, 2026 |
| `babel_gardens_node.py` | HTTP adapter now in `emotion_detector.py` | Feb 14, 2026 |
| `archivarium_node.py` | Renamed to `vault_node.py` | Feb 14, 2026 |
| `mnemosyne_node.py` | Caching moved to `cached_llm_node.py` | Feb 14, 2026 |
| `proactive_suggestions_node.py` | Finance-specific, domain leak | Feb 12, 2026 |
| `quality_check_node.py` | Finance-specific validation | Feb 12, 2026 |
| `llm_soft_node.py` | Dead code, replaced by `cached_llm_node` | Feb 12, 2026 |
| `enhanced_llm_node.py` | Dead code | Feb 12, 2026 |
| `gemma_node.py` | Never wired | Feb 12, 2026 |

---

## 2. Sacred Orders (Governance Primitives)

**Location**: `vitruvyan_core/core/governance/`  
**Pattern**: Two-level architecture (LIVELLO 1 pure domain, LIVELLO 2 services)

| Sacred Order | LIVELLO 1 Status | LIVELLO 2 Service | Conformance | main.py Lines |
|--------------|-----------------|-------------------|-------------|---------------|
| **Memory Orders** | ACTIVE | `api_memory_orders` | 100% | 93 |
| **Vault Keepers** | ACTIVE | `api_vault_keepers` | 100% | 59 |
| **Orthodoxy Wardens** | ACTIVE | `api_orthodoxy_wardens` | 95% | 87 |
| **Babel Gardens** | ACTIVE | `api_babel_gardens` | 100% | 87 |
| **Codex Hunters** | ACTIVE | `api_codex_hunters` | 100% | 75 |
| **Pattern Weavers** | ACTIVE | `api_pattern_weavers` | 100% | 62 |

**All Sacred Orders**: 10-directory structure (domain/, consumers/, governance/, events/, monitoring/, philosophy/, docs/, examples/, tests/, _legacy/)

---

## 3. Core Agents (Infrastructure Gateways)

**Location**: `vitruvyan_core/core/agents/`

| Agent | Purpose | Status | Dependencies |
|-------|---------|--------|--------------|
| `postgres_agent.py` | PostgreSQL access | ACTIVE | psycopg2-binary |
| `qdrant_agent.py` | Qdrant vector operations | ACTIVE | qdrant-client |
| `llm_agent.py` | Centralized LLM gateway (OpenAI) | ACTIVE | openai, litellm (fallback) |
| `penitent_agent.py` | Sacred penance simulation (governance) | ACTIVE | subprocess, docker (⚠️ LIVELLO 1 violation) |

**Archived**:
- `cached_qdrant_agent.py` → `_legacy/` (zero consumers, Feb 14, 2026)

---

## 4. Orchestration Registries (Hook Pattern)

**Location**: `vitruvyan_core/core/orchestration/`

| Registry | Node | Status | Env Var | Default | Example Domain Config |
|----------|------|--------|---------|---------|----------------------|
| `IntentRegistry` | `intent_detection_node.py` | ACTIVE | `INTENT_DOMAIN` | N/A (required) | `domains/finance/intent_config.py` |
| `EntityResolverRegistry` | `entity_resolver_node.py` | HOOK | `ENTITY_DOMAIN` | Passthrough stub | `domains/finance/entity_resolver_config.py` |
| `ExecutionRegistry` | `exec_node.py` | HOOK | `EXEC_DOMAIN` | Fake success stub | `domains/finance/execution_config.py` |
| `RouteRegistry` | (unused) | PARTIAL | - | Generic routing | Not wired in graph_flow.py |

---

## 5. Synaptic Conclave (Cognitive Bus)

**Location**: `vitruvyan_core/core/synaptic_conclave/`

| Component | Status | Purpose |
|-----------|--------|---------|
| `transport/streams.py` (StreamBus) | ACTIVE | Redis Streams transport (641L) |
| `events/event_envelope.py` | ACTIVE | TransportEvent, CognitiveEvent, EventAdapter |
| `transport/redis_client.py` | LEGACY | Herald compatibility shim (pre-streams) |
| Prometheus metrics | ACTIVE | 18 metrics (plasticity, entropy, coherence, etc.) |

**Key Invariants**:
- Bus is **payload-blind** (no semantic routing)
- At-least-once delivery (consumer groups + ACK/PEL)
- Channel naming: `<service>.<domain>.<action>` (dot notation)

---

## 6. Services (LIVELLO 2)

**Location**: `services/`  
**Total Services**: 11 (+ 1 exporter)

| Service | Purpose | Container Name | Status | Listener |
|---------|---------|---------------|--------|----------|
| `api_graph` | LangGraph HTTP gateway (/run) | `core_graph` | ACTIVE | No |
| `api_memory_orders` | RAG, coherence analysis | `core_memory_orders` | ACTIVE | Yes (`core_memory_orders_listener`) |
| `api_vault_keepers` | Archival persistence | `core_vault_keepers` | ACTIVE | Yes (`core_vault_keepers_listener`) |
| `api_orthodoxy_wardens` | Validation, audit | `core_orthodoxy_wardens` | ACTIVE | Yes (`core_orthodoxy_wardens_listener`) |
| `api_babel_gardens` | Emotion, language, sentiment | `core_babel_gardens` | ACTIVE | Yes (`core_babel_listener`) |
| `api_codex_hunters` | System maintenance, discovery | `core_codex_hunters` | ACTIVE | Yes (`core_codex_listener`) |
| `api_pattern_weavers` | Ontology mapping | `core_pattern_weavers` | ACTIVE | No |
| `api_neural_engine` | Entity ranking (finance) | `core_neural_engine` | ACTIVE | No |
| `api_embedding` | Text embeddings | `core_embedding` | ACTIVE | No |
| `api_conclave` | Bus observatory + metrics | `core_conclave` | ACTIVE | Yes (`core_conclave_listener`) |
| `api_mcp` | MCP tools gateway | `core_mcp` | ACTIVE | No |
| `redis_streams_exporter` | Prometheus exporter | `core_redis_streams_exporter` | UNHEALTHY | No |

**Container Health**: 32/32 UP, 31/32 healthy (redis_streams_exporter unhealthy pre-existing issue)

---

## 7. Domain Plugins

**Location**: `vitruvyan_core/domains/`

| Domain | Configs | Status | Wired |
|--------|---------|--------|-------|
| **finance** | intent_config.py | ACTIVE | Yes (`INTENT_DOMAIN=finance`) |
| | entity_resolver_config.py | EXAMPLE | No (stub default) |
| | execution_config.py | EXAMPLE | No (stub default) |
| | prompts/ | ACTIVE | PromptRegistry loaded |
| **generic** | (fallback) | ACTIVE | Core domain for agnostic prompts |

**Future domains** (not implemented): logistics, healthcare, etc.

---

## 8. Test Coverage

**Location**: `tests/`

| Directory | Test Count | Focus |
|-----------|-----------|-------|
| `unit/` | ~120 | LIVELLO 1 pure functions |
| `integration/` | ~80 | PostgreSQL, Qdrant, Redis interactions |
| `graph/` | ~50 | LangGraph node execution |
| `e2e/` | ~30 | Full pipeline (/run endpoint) |
| `architectural/` | ~15 | Import checks, LIVELLO 1 purity |

**Total**: 449 test functions, 7.7K LOC (~11% test-to-code ratio for 71K core+services)

**Key Gaps**:
- Hook pattern registries (EntityResolverRegistry, ExecutionRegistry) — unit tests pending
- Finance domain configs (entity_resolver_config, execution_config) — integration tests pending
- MCP integration tests (currently manual verification only)

---

## 9. Documentation Status

**Location**: `docs/`

| Document | Status | Purpose |
|----------|--------|---------|
| `foundational/VITRUVYAN_PIPELINE_WALKTHROUGH.md` | UPDATED (Feb 14) | Technical pipeline deep-dive |
| `foundational/MODULE_STATUS_MAP.md` | NEW (Feb 14) | This file - module inventory |
| `README.md` (root) | NEEDS UPDATE | Project overview, quick start |
| `architecture/*.md` | CURRENT | Refactoring reports, architectural decisions |
| `orders/*.md` | CURRENT | Sacred Orders charters, governance specs |
| `services/*.md` | CURRENT | Service-specific documentation |
| MkDocs site | DEPLOYED | http://localhost:8000 (Portainer port 30800) |

---

## 10. Environment Variables Reference

**Critical configuration knobs**:

| Env Var | Default | Effect |
|---------|---------|--------|
| `INTENT_DOMAIN` | `finance` | Intent detection domain plugin |
| `ENTITY_DOMAIN` | (unset) | Entity resolver domain plugin (stub if unset) |
| `EXEC_DOMAIN` | (unset) | Execution handler domain plugin (stub if unset) |
| `VITRUVYAN_LLM_MODEL` | `gpt-4o-mini` | LLM model (resolution chain: VITRUVYAN_LLM_MODEL → GRAPH_LLM_MODEL → OPENAI_MODEL) |
| `USE_MCP` | `0` | Enable MCP tools routing |
| `ENABLE_MINIMAL_GRAPH` | `false` | Use 4-node minimal graph |
| `VSGS_ENABLED` | `1` | Enable semantic grounding |
| `QDRANT_FILTER_DOMAIN` | `1` | Enable domain-specific Qdrant filtering |
| `DISABLE_SLOT_FILLING` | (unset) | Slot-filling still active in vitruvyan-core (upstream deprecated) |

---

## 11. Known Issues & Tech Debt

**High Priority**:
1. ⚠️ **LIVELLO 1 violations**: `penitent_agent.py` imports subprocess/docker (should be LIVELLO 2)
2. ⚠️ **redis_streams_exporter**: Container unhealthy (pre-existing, metrics collection impacted)
3. ⚠️ **Herald compatibility shim**: orthodoxy/vault nodes degrade to local fallback if streams fail

**Medium Priority**:
4. **Test coverage gaps**: Hook pattern registries, finance domain configs
5. **Documentation debt**: README.md still references "OS kernel" terminology (needs engineering framing)
6. **Babel streams listener**: ACK/log only, full stream-driven enrichment not guaranteed

**Low Priority** (design decisions):
7. **Slot-filling active**: vitruvyan-core keeps slot-filling pattern (upstream deprecated for LLM-first)
8. **Finance stubs exist**: advisor_node.py portfolio stub, graph_engine.py finance in comments (tolerable)

---

## 12. Migration Checklist (New Developer Onboarding)

**To understand the system**:
1. ✅ Read this file (MODULE_STATUS_MAP.md)
2. ✅ Read VITRUVYAN_PIPELINE_WALKTHROUGH.md (technical deep-dive)
3. ✅ Read `.github/copilot-instructions.md` (architecture invariants)
4. ✅ Explore MkDocs site: http://localhost:8000

**To run locally**:
```bash
# 1. Start infrastructure
cd infrastructure/docker
docker compose up -d

# 2. Verify containers
docker ps --filter "name=core_" --format "table {{.Names}}\t{{.Status}}"

# 3. Test graph endpoint
curl -X POST http://localhost:9004/run \
  -H "Content-Type: application/json" \
  -d '{"input_text":"test query","user_id":"dev_user"}'

# 4. Check logs
docker logs --tail=50 core_graph
```

**To add a new domain plugin**:
1. Create `vitruvyan_core/domains/<domain>/intent_config.py`
2. Create `vitruvyan_core/domains/<domain>/entity_resolver_config.py`
3. Create `vitruvyan_core/domains/<domain>/execution_config.py`
4. Register in `services/api_graph/main.py` with env var checks

**To extend the graph**:
1. Add node: `vitruvyan_core/core/orchestration/langgraph/node/<node_name>.py`
2. Wire in `vitruvyan_core/core/orchestration/langgraph/graph_flow.py`
3. Add tests: `tests/graph/test_<node_name>.py`
4. Update this file (MODULE_STATUS_MAP.md) with node status

---

**Last updated**: February 14, 2026  
**Maintainer**: Vitruvyan Core Team  
**Next update trigger**: Sacred Order conformance change, new node addition, or major refactoring
