# events/

> Event type constants and envelope for Cognitive Bus communication.

## Contents

| File | Description |
|------|-------------|
| `orthodoxy_events.py` | All event type constants + `OrthodoxyEvent` dataclass |

## Event Naming Convention

All events follow the Cognitive Bus dot notation:
```
<sacred_order>.<domain>.<action>
```

Examples:
- `orthodoxy.confession.received`
- `orthodoxy.verdict.rendered`
- `orthodoxy.heresy.detected`

## Channel Groups

**Publishes to:**
- `orthodoxy.verdict.rendered` — Every verdict
- `orthodoxy.heresy.detected` — Blocked outputs
- `orthodoxy.purification.requested` — Correction requests (for Penitent)
- `orthodoxy.archive.requested` — Archival requests (for Vault Keepers)

**Consumes from:**
- `codex.discovery.mapped` — New data from Codex Hunters
- `engine.eval.completed` — Evaluation results ready
- `langgraph.output.ready` — LLM output awaiting validation
- `synaptic.conclave.broadcast` — System announcements
- `conclave.mcp.actions` — MCP tool executions

## Constraints

- Event types are **string constants**, not enums (Redis Streams compatibility)
- `OrthodoxyEvent` is `frozen=True` — immutable
- Payload uses `tuple` of `(key, value)` pairs, not `dict`
- `to_dict()` / `from_dict()` for bus serialization
