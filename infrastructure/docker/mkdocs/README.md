# MkDocs Documentation Server

> **Last Updated**: February 12, 2026  
> **Purpose**: Serve Vitruvyan Core documentation as navigable static site  
> **Type**: Infrastructure utility (monitoring-like)

## 🎯 Cosa Contiene

Server containerizzato **MkDocs** per knowledge base utenti/amministratori:

- **Hot-reload**: modifica `.md` → aggiornamento automatico browser
- **Material theme**: UI moderna, responsive, dark/light mode
- **Plugins**: Mermaid diagrams, search, git revision dates
- **Production-ready**: `mkdocs build` → HTML statico ottimizzato

## 📂 Struttura

```
infrastructure/docker/mkdocs/
├── Dockerfile           # Python 3.11-slim + MkDocs + plugins
├── mkdocs.yml           # Config sito (nav, theme, plugins)
├── requirements.txt     # mkdocs-material, mermaid2, minify
└── README.md            # Questa guida
```

**Source docs**: mounted da host (read-only)
- `/docs` → `../../docs` (global docs)
- `/vitruvyan_core` → `../../vitruvyan_core` (module READMEs)
- `/services` → `../../services` (service READMEs)

## 🚀 Quick Start

### 1. Avvia il servizio

```bash
cd infrastructure/docker
docker compose up -d mkdocs
```

### 2. Accedi alla documentation

**Browser**: http://localhost:9800

### 3. Modifica documentazione

1. Edita qualsiasi `.md` nel repo (es. `docs/foundational/VITRUVYAN_OVERVIEW.md`)
2. Salva il file → **MkDocs rileva il cambiamento** → browser si aggiorna automaticamente
3. Nessun rebuild necessario (hot-reload)

### 4. Build statico (production)

```bash
# Entra nel container
docker exec -it core_mkdocs bash

# Build HTML statico
mkdocs build

# Output: /app/site/ (HTML ottimizzato + minificato)
```

Opzionale - copia output su host:
```bash
docker cp core_mkdocs:/app/site ./mkdocs_build
```

## 🎨 Features

### Theme Material Design
- **Palette**: Indigo primary, Deep Purple accent
- **Modes**: Light/dark auto-switch (prefers-color-scheme)
- **Navigation**: Tabs, sections, instant loading (SPA-like)
- **Search**: Suggerimenti + highlight termini

### Plugins Attivi
- **search**: Ricerca full-text
- **git-revision-date**: Mostra "Last updated X ago" per ogni pagina
- **mermaid2**: Diagrammi Mermaid in code blocks
- **minify**: Compressione HTML/CSS per production

### Markdown Extensions
- **Admonitions**: Note, warnings, tips styled
- **Code blocks**: Syntax highlighting + copy button
- **Tabs**: Content tabs (`=== "Tab 1"`)
- **Tables**: Full table support
- **Mermaid**: `graph TD; A-->B` → rendering diagrammi

## 📖 Configurazione Navigation

**File**: `infrastructure/docker/mkdocs/mkdocs.yml`

**Struttura attuale** (7 sezioni):
1. **Getting Started**: Overview, Quick Start, Charter
2. **Architecture**: Sacred Orders Pattern, Cognitive Bus, Technical Debt
3. **Sacred Orders**: 6 READMEs (Memory Orders, Vault Keepers, etc.)
4. **Services**: Service layer (API Graph, MCP, etc.)
5. **Infrastructure**: Docker, monitoring, deployment
6. **Development**: Tests, examples, config, scripts
7. **Planning**: ALBERATURA roadmap, refactoring plans

**Aggiungere pagine**:
```yaml
nav:
  - New Section:
    - Page Title: path/to/file.md
```

**Path relativi**: da `/docs` root mounted in container

## 🔧 Configurazione Docker

**docker-compose.yml entry**:
```yaml
mkdocs:
  container_name: core_mkdocs
  build:
    context: ./mkdocs
    dockerfile: Dockerfile
  ports:
    - "9800:8000"
  volumes:
    - ../../docs:/docs:ro
    - ../../vitruvyan_core:/vitruvyan_core:ro
    - ../../services:/services:ro
    - ./mkdocs/mkdocs.yml:/app/mkdocs.yml:ro
  command: mkdocs serve -a 0.0.0.0:8000
  networks:
    - core-net
  restart: unless-stopped
```

**Ports**: 9800 (host) → 8000 (container)  
**Volumes**: Read-only mounts (documentazione immutabile da container)  
**Network**: `core-net` (può comunicare con altri servizi se necessario)

## 🎯 Use Cases

### Utenti (Developers)
- **Naviga architettura**: Sacred Orders, services, infrastructure
- **Quick start**: esempi, tutorial, pattern
- **API reference**: endpoint, contracts, esempi

### Amministratori
- **Deploy guide**: Docker setup, secrets, monitoring
- **Troubleshooting**: logs, health checks, common issues
- **Planning**: roadmap, technical debt status

### Contributori
- **Development**: test suite, coding standards, git workflow
- **Documentation**: come aggiornare docs, MkDocs config
- **Refactoring**: SACRED_ORDER_PATTERN, ALBERATURA framework

## 🛠️ Comandi Utili

```bash
# Logs real-time
docker logs -f core_mkdocs

# Rebuild dopo cambio requirements.txt
docker compose build mkdocs
docker compose up -d mkdocs

# Stop servizio
docker compose stop mkdocs

# Remove container + riavvio
docker compose down mkdocs
docker compose up -d mkdocs

# Entra in container (debug)
docker exec -it core_mkdocs bash
```

## 📚 Documentazione Esterna

- **MkDocs**: https://www.mkdocs.org/
- **Material theme**: https://squidfunk.github.io/mkdocs-material/
- **Mermaid**: https://mermaid.js.org/
- **PyMdown Extensions**: https://facelessuser.github.io/pymdown-extensions/

## 🎯 Design Principles

1. **Read-only mounts**: container non modifica docs (sicurezza)
2. **Hot-reload**: developer experience ottimale (no restart)
3. **Production-ready**: `mkdocs build` → static site deployable
4. **Pattern consistency**: segue infrastructure/ pattern (monitoring/)
5. **Optional deployment**: può restare spento (non critical path)

## 📖 Link Utili

- **Root README**: [/README.md](../../../README.md) (repository overview)
- **Infrastructure README**: [/infrastructure/README_INFRASTRUCTURE.md](../README_INFRASTRUCTURE.md)
- **Docs README**: [/docs/README_DOCS.md](../../../docs/README_DOCS.md)
- **Docker Compose**: [docker-compose.yml](../docker-compose.yml)

---

**Pattern**: Infrastructure utility (documentation server)  
**Tools**: MkDocs 1.5.3, Material 9.5.3, Mermaid, Git revision dates  
**Status**: ✅ Ready (Feb 12, 2026) — Hot-reload enabled
