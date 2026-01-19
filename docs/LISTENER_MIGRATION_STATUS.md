# Listener Migration Status - Phase 2

**Last Updated**: Jan 19, 2026 16:24 UTC  
**Progress**: 4/13 listeners complete (30.8%)

## Completed Migrations ✅

### 1. Vault Keepers (Jan 19, 2026) - PILOT
- **Channels**: 5 (ledger.*, audit.*, verification.*)
- **Pattern**: Standard wrap_legacy_listener
- **Migration Time**: 2 hours (initial pilot + debugging)

### 2. Codex Hunters (Jan 19, 2026)
- **Channels**: 7 (codex.data.refresh, technical.*, schema.validation, fundamentals.refresh, risk.refresh)
- **Pattern**: Standard wrap_legacy_listener
- **Migration Time**: 20 minutes

### 3. Babel Gardens (Jan 19, 2026)
- **Channels**: 6 (codex.discovery.mapped, babel.*, sentiment.requested, linguistic.analysis.requested)
- **Pattern**: Standard wrap_legacy_listener
- **Migration Time**: 15 minutes

### 4. Memory Orders (Jan 19, 2026) - COMPLEX
- **Channels**: 3 (memory.write/read/vector.match.requested)
- **Pattern**: Monkey-patch routing (channel-specific handlers)
- **Migration Time**: 25 minutes
- **Complexity**: Dual-memory (Archivarium + Mnemosyne)
- **Note**: Required custom handle_sacred_message router

## Remaining Migrations (9)

- [ ] Orthodoxy Wardens (5 channels) - **NEXT** (critical for Phase 3 non_liquet)
- [ ] Pattern Weavers (3 channels)
- [ ] Neural Engine (2 channels)
- [ ] Sentiment Node (2 channels)
- [ ] MCP Server (4 channels)
- [ ] LangGraph (8 channels) - Most complex
- [ ] VEE Engine (2 channels)
- [ ] Portfolio Architects (3 channels)
- [ ] CAN Node (2 channels)

## Patterns Proven

### Standard Pattern (3 listeners)
```python
legacy_listener = SomeListener()
adapter = wrap_legacy_listener(
    listener_instance=legacy_listener,
    name="service_name",
    sacred_channels=legacy_listener.sacred_channels
)
await adapter.start()
```

### Monkey-Patch Router Pattern (1 listener - Memory Orders)
```python
legacy_listener = MemoryOrdersCognitiveBusListener()

async def handle_sacred_message(message: dict):
    channel = message["channel"].decode("utf-8")
    if channel == "memory.write.requested":
        await legacy_listener.handle_memory_write_requested(message["data"])
    # ... other channels

legacy_listener.handle_sacred_message = handle_sacred_message
adapter = wrap_legacy_listener(...)
await adapter.start()
```

**Use Cases**:
- Standard: Listener has `handle_sacred_message(message)` method
- Monkey-patch: Listener has channel-specific handlers only

**Average Time**: 15-25 minutes per listener (after pilot)
