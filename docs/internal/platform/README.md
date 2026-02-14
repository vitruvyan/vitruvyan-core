# Core Agents & Layers

<p class="kb-subtitle">Internal cross-cutting primitives: dual-memory (PostgreSQL + Qdrant), RAG assembly, and the LLM gateway used by multiple Sacred Orders.</p>

## What it covers

- **Dual memory + RAG**: how Archivarium (PostgreSQL) and Mnemosyne (Qdrant) cooperate, where embeddings fit, and how coherence is monitored.
- **LLM / AI layer**: the canonical LLM gateway (`LLMAgent`) and the rules for using it safely across services.

## Pages

- Dual Memory & RAG: `docs/internal/platform/DUAL_MEMORY_RAG.md`
- LLM / AI Layer: `docs/internal/platform/LLM_LAYER.md`

