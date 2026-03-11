# Package Manager — `vit install` / `vit remove`

> **Last updated**: Feb 20, 2026 14:30 UTC
> **Status**: Implemented — M1-M6 complete
> **CLI Commands**: `vit install`, `vit remove`, `vit list`, `vit search`, `vit info`
> **Architecture**: Registry + Resolver + Installer (pure domain) + CLI (thin commands)

## Overview

The Package Manager extends the Vitruvyan update system with **optional package installation**, separate from core upgrades. It implements an apt/apk-style experience:

- **Core tier** (Sacred Orders, Graph, Conclave, etc.) → managed via `vit upgrade`
- **Package tier** (Neural Engine, MCP, DSE, verticals) → managed via `vit install`

## Quick Start

```bash
# List all available packages
vit list --all

# Search by name or description
vit search engine

# Show package details
vit info neural_engine

# Install a package
vit install neural_engine

# Install a vertical (meta-package) with all optional deps
vit install vertical-finance --with-optional

# Remove a package
vit remove mcp
vit remove mcp --purge    # also remove data

# List installed packages
vit list
```

## Architecture

```
vitruvyan_core/core/platform/
├── package_manager/              # Pure domain layer (LIVELLO 1)
│   ├── models.py                 # PackageManifest, InstalledPackage, InstallPlan
│   ├── registry.py               # Discovers .vit manifests, multi-key lookup
│   ├── resolver.py               # Topological dependency sort, conflict detection
│   ├── installer.py              # Docker compose + script install methods
│   ├── state.py                  # .vitruvyan/installed_packages.json (atomic writes)
│   └── packages/
│       ├── VIT_FORMAT_SPEC.md    # Full .vit format specification
│       └── manifests/            # Builtin .vit package manifests
│           ├── order-babel-gardens.vit
│           ├── service-graph.vit
│           ├── service-neural-engine.vit
│           ├── service-mcp.vit
│           ├── service-edge-dse.vit
│           ├── vertical-finance.vit
│           └── VERTICAL_TEMPLATE.vit
│
└── update_manager/cli/commands/  # CLI layer (thin commands)
    ├── install.py                # vit install <package>
    ├── remove.py                 # vit remove <package>
    ├── list_cmd.py               # vit list [--all]
    ├── search.py                 # vit search <query>
    └── info.py                   # vit info <package>
```

## .vit Manifest Format

Packages are defined as `.vit` YAML files (branded extension, like `.deb`, `.apk`, `.rpm`).

```yaml
package_name: service-neural-engine
package_version: "2.1.0"
package_type: service         # service|order|vertical|extension
status: stable                # stable|beta|experimental|deprecated
tier: package                 # core|package

compatibility:
  min_core_version: "1.15.0"
  max_core_version: "1.x.x"

dependencies:
  required:
    - "vitruvyan-core>=1.15.0"
  optional:
    - "service-mcp>=0.5.0"
  system:
    - docker

installation:
  method: docker_compose      # docker_compose|script
  compose_service: neural_engine
  ports:
    - "9003:8003"

health:
  endpoint: "http://localhost:9003/health"
```

See `VIT_FORMAT_SPEC.md` for the complete specification.

## Package Types

| Type | Description | Install method | Example |
|------|-------------|---------------|---------|
| **service** | Standalone microservice with Docker container | docker_compose | service-neural-engine |
| **order** | Sacred Order service (core governance component) | docker_compose | order-babel-gardens |
| **vertical** | Meta-package: domain config + required services | script | vertical-finance |
| **extension** | Plugin/extension for existing services | script | (future) |

## Tier System

| Tier | Managed by | Description |
|------|-----------|-------------|
| **core** | `vit upgrade` | Sacred Orders, Graph, Conclave, Agents, Contracts, Platform, Redis, PG, Qdrant, Embedding |
| **package** | `vit install` | Neural Engine, MCP, DSE/Edge, domain verticals |

Core tier packages cannot be installed via `vit install` — the CLI blocks them with a clear message.

## Dependency Resolution

The resolver uses topological sort to determine install order:

```
vit install vertical-finance
→ Resolves: service-neural-engine (required dep)
→ Install order: [service-neural-engine, vertical-finance]
→ Optional: service-mcp, service-edge-dse (prompted interactively)
```

**Conflict detection**:
- Name conflicts (packages that declare `conflicts_with`)
- Port conflicts (same host port already in use)

**System dependency checks**:
- `docker` binary available
- Redis/PostgreSQL/Qdrant containers running

## Vertical Meta-Packages

Verticals are domain-specific meta-packages that:
1. Install required service dependencies (e.g., neural-engine)
2. Register domain configuration (intents, prompts, contracts)
3. Optionally install extra services (MCP, DSE)

### Creating a New Vertical

1. Copy `VERTICAL_TEMPLATE.vit` as `vertical-<domain>.vit`
2. Fill in domain-specific fields
3. Place in `packages/manifests/`
4. Create domain code under `vitruvyan_core/domains/<domain>/`
5. Test: `vit info <domain>`, `vit install <domain>`

### Example: vertical-finance

```bash
$ vit install vertical-finance --with-optional

  Package: vertical-finance v1.0.0
  Type:    vertical (stable)
  Desc:    Finance domain — trading analysis, portfolio management...

  Will install:
    + service-neural-engine v2.1.0
    + vertical-finance v1.0.0

  Optional packages:
    ? service-mcp v0.5.2 — MCP tool integration server
    ? service-edge-dse v1.0.0 — Edge computing engine

  --with-optional: will install 2 optional package(s)

  Domain components:
    - finance-intents: Finance intent detection configuration
    - finance-prompts: Finance-specific LLM prompts
    - finance-contracts: Finance domain contracts and rules

  Proceed with installation? [Y/n]
```

## Jenkins CI/CD Integration

The Jenkinsfile supports per-package releases:

- **Change Detection**: Automatically detects which services changed
  - Core change → rebuild all services
  - Service-only change → rebuild only affected service(s)
  - Docs/scripts change → skip Docker builds
- **Per-Package Tags**: Release stage reads `.vit` manifests and creates tags like `service-neural-engine/2.1.0`
- **Docker Images**: `vit-<service>:latest` naming convention

### Pipeline Stages

```
Install → Change Detection → Quality Gate → Docker Build → Push → Release
```

| Stage | Trigger | What it does |
|-------|---------|-------------|
| Install | Always | Python venv + dependencies |
| Change Detection | Always | Git diff → affected services |
| Quality Gate | Always | Tests, arch tests, contracts, smoke tests |
| Docker Build | If services changed | Parallel build of changed images |
| Docker Push | Manual (PUSH_IMAGES) | Push to registry |
| Release | Manual (main only) | Monorepo tag + per-package tags |

## State Management

Installed packages are tracked in `.vitruvyan/installed_packages.json`:

```json
{
  "service-neural-engine": {
    "name": "service-neural-engine",
    "version": "2.1.0",
    "installed_at": "2026-02-20T14:30:00",
    "install_method": "docker_compose",
    "status": "active",
    "ports": ["9003:8003"]
  }
}
```

State file uses atomic writes (write to `.tmp` → `os.replace`) to prevent corruption.

## Related Documentation

- [Update Manager System](Update_Manager_System.md) — Core upgrade system (`vit upgrade`)
- [Vertical Implementation Guide](Vertical_Implementation_Guide.md) — Building domain verticals
- `.vit` Format Spec: `vitruvyan_core/core/platform/package_manager/packages/VIT_FORMAT_SPEC.md`
