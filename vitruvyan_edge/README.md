# Vitruvyan Edge — Multi-Module Pluggable Ingestion Layer
> **Last updated**: Feb 22, 2026 16:30 UTC

Domain-agnostic edge ingestion layer for Vitruvyan OS.  
Package contenitore multi-modulo: ogni modulo è un plugin indipendente che si integra con `vitruvyan_core`.

## Architecture

- **Core OS**: `vitruvyan_core/` (autonomous epistemic kernel — runs independently)
- **Edge Layer**: `vitruvyan_edge/` (pluggable acquisition/ingestion modules)
  - Ogni modulo si "plugga" nel core tramite contratti e StreamBus events
  - Moduli sono indipendenti tra loro (no cross-module imports)

## Modules

| Module | Status | Description |
|--------|--------|-------------|
| **Oculus Prime** | ✅ Active | Multi-modal intake gateway (documents, images, audio, video, CAD, GIS) |
| **DSE-CPS** | 📋 Planned | DSE-CPS engine integration |
| *(others)* | 📋 Planned | Stream intake, API gateway, etc. |

### Oculus Prime
Multi-modal intake gateway — acquires raw evidence from multiple media types, normalizes to literal format, emits immutable Evidence Packs to the Redis Cognitive Bus.

**Location**: `vitruvyan_edge/oculus_prime/`  
**Service**: `services/api_edge_oculus_prime/`  
**Docs**: [Oculus Prime README](oculus_prime/README.md)

## Adding New Modules

New edge modules follow the same pattern:
```
vitruvyan_edge/
├── oculus_prime/   # ✅ Reference implementation
├── new_module/     # Create following oculus_prime structure
│   ├── __init__.py
│   ├── core/
│   └── README.md
```

Each module MUST:
1. Be self-contained (no cross-module imports within edge)
2. Import from `vitruvyan_core` for OS primitives (agents, bus, contracts)
3. Communicate with other modules via StreamBus events (not direct imports)
4. Have its own service under `services/api_edge_<module>/`

## Installation

```bash
pip install -e .  # Installs both vitruvyan_core and vitruvyan_edge
```

## Usage

```python
from vitruvyan_edge.oculus_prime.core.agents.document_intake import DocumentIntakeAgent
from vitruvyan_edge.oculus_prime.core.event_emitter import IntakeEventEmitter

# Initialize agents
agent = DocumentIntakeAgent(event_emitter=emitter, postgres_agent=pg)
```

## Philosophy

Edge modules are **intake-only** (no inference, no business logic).  
Semantic processing happens in the **Core OS** (Memory Orders, Pattern Weavers, etc.).
