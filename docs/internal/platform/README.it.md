# Core Agents & Layers

<p class="kb-subtitle">Primitivi interni trasversali: dual-memory (PostgreSQL + Qdrant), composizione RAG e gateway LLM usato da più Sacred Orders.</p>

## Cosa copre

- **Dual memory + RAG**: come cooperano Archivarium (PostgreSQL) e Mnemosyne (Qdrant), dove si innestano gli embedding e come viene monitorata la coerenza.
- **Layer LLM / AI**: il gateway canonico (`LLMAgent`) e le regole per usarlo in modo sicuro nei servizi.

## Pagine

- Dual Memory & RAG: `docs/internal/platform/DUAL_MEMORY_RAG.md`
- Layer LLM / AI: `docs/internal/platform/LLM_LAYER.md`

