# Package Manager System Contract V1.0

> **Last updated**: Feb 20, 2026 10:30 UTC  
> **Status**: Draft — Phase 5 Foundation  
> **Scope**: Vitruvyan Platform Package Management  
> **Extends**: [UPDATE_SYSTEM_CONTRACT_V1](./UPDATE_SYSTEM_CONTRACT_V1.md)

## Purpose

This contract defines the **Package Manager System** for Vitruvyan Core, enabling installation, removal, and lifecycle management of:

- **Services** (microservices: api_babel_gardens, api_neural_engine, etc.)
- **Sacred Orders** (governance modules: orthodoxy_wardens, pattern_weavers, etc.)
- **Verticals** (domain applications: finance, healthcare, etc.)
- **Extensions** (plugins: MCP tools, exporters, adapters, etc.)

**Non-negotiable principle**: Package management must be **declarative**, **transactional**, and **contract-driven**.

---

## 1. Package Types & Taxonomy

### 1.1 Package Types

| Type | Identifier | Installation Method | Examples |
|------|------------|---------------------|----------|
| **Service** | `service` | Docker Compose | `api_babel_gardens`, `api_neural_engine` |
| **Order** | `order` | Python package + migrations | `orthodoxy_wardens`, `vault_keepers` |
| **Vertical** | `vertical` | Manifest + contracts | `vertical-finance`, `vertical-healthcare` |
| **Extension** | `extension` | Optional dependencies | `mcp-tools`, `prometheus-exporter` |

### 1.2 Naming Convention

**Pattern**: `<type>-<name>` (lowercase, hyphen-separated)

**Examples**:
- Services: `service-babel-gardens`, `service-neural-engine`
- Orders: `order-orthodoxy-wardens`, `order-pattern-weavers`
- Verticals: `vertical-finance`, `vertical-healthcare`
- Extensions: `extension-mcp-tools`, `extension-grafana-exporter`

**Abbreviations** (CLI shortcuts):
- `vit install babel_gardens` → resolves to `service-babel-gardens`
- `vit install orthodoxy_wardens` → resolves to `order-orthodoxy-wardens`

---

## 2. Package Manifest Schema

**File**: `packages/manifests/<package-name>.yaml`

**Required sections**:

```yaml
# Metadata
package_name: "service-babel-gardens"
package_version: "1.2.0"
package_type: "service"  # service|order|vertical|extension
status: "stable"  # stable|beta|experimental|deprecated

# Description
description: "Multilingual NLU preprocessing service (Perception layer)"
homepage: "https://docs.vitruvyan.io/services/babel-gardens"
repository: "https://github.com/vitruvyan/vitruvyan-core"

# Compatibility
compatibility:
  min_core_version: "1.0.0"
  max_core_version: "1.x.x"
  contracts_major: 1
  conflicts_with: []  # List of incompatible packages

# Dependencies
dependencies:
  required:
    - "vitruvyan-core>=1.0.0"
    - "service-pattern-weavers>=1.0.0"  # Optional: depends on other packages
  optional:
    - "extension-mcp-tools>=0.5.0"
  system:
    - docker
    - redis
    - postgres

# Installation
installation:
  method: "docker_compose"  # docker_compose|pip|git_clone|script
  
  # Docker Compose specific
  compose_service: "babel_gardens"
  compose_file: "infrastructure/docker/docker-compose.yml"
  
  # Environment
  env_template: "services/api_babel_gardens/.env.example"
  env_required:
    - BABEL_LLM_MODEL
    - OPENAI_API_KEY
  env_optional:
    - BABEL_LANGUAGE_DETECTION
  
  # Ports
  ports:
    - "8004:8004"
  
  # Volumes
  volumes:
    - ".vitruvyan/babel_gardens:/data"
  
  # Initialization
  init_commands:
    - "docker exec core_babel_gardens python -m vitruvyan_core.scripts.init_babel"

# Configuration
configuration:
  feature_flags:
    - emotion_detection
    - sarcasm_analysis
  secrets:
    - OPENAI_API_KEY  # Marks as required secret
  config_files:
    - path: "services/api_babel_gardens/config.yaml"
      template: "services/api_babel_gardens/config.yaml.example"

# Testing
smoke_tests:
  path: "services/api_babel_gardens/tests/smoke/"
  timeout: 120
  required_endpoints:
    - "http://localhost:8004/health"

# Uninstallation
uninstallation:
  preserve_data: true  # Keep .vitruvyan/<package>/
  cleanup_streams: true  # Remove Redis Streams
  remove_volumes: false  # Keep Docker volumes
  cleanup_commands:
    - "docker exec core_postgres psql -c 'DROP SCHEMA IF EXISTS babel_gardens CASCADE;'"

# Metadata
ownership:
  team: "perception-team"
  tech_lead: "john.doe"
  contact: "perception@vitruvyan.io"

# Changelog
changelog:
  - version: "1.2.0"
    date: "2026-02-15"
    changes:
      - "Added emotion detection"
      - "Fixed sarcasm analyzer bug"
  - version: "1.1.0"
    date: "2026-01-10"
    changes:
      - "Initial release"
```

---

## 3. Dependency Resolution

### 3.1 Resolution Algorithm

1. **Parse manifest**: Load package manifest from registry
2. **Topological sort**: Build dependency graph (DAG)
3. **Version resolution**: Find compatible versions for all dependencies
4. **Conflict detection**: Check for incompatible packages (`conflicts_with`)
5. **Circular dependency check**: Abort if cycle detected
6. **Generate install plan**: Ordered list of packages to install

### 3.2 Version Constraints

**Supported operators**:
- `>=1.0.0`: Minimum version
- `<=2.0.0`: Maximum version
- `==1.5.0`: Exact version
- `~=1.2.0`: Compatible release (`>=1.2.0, <1.3.0`)
- `1.x.x`: Wildcard (any minor/patch within major version 1)

### 3.3 Conflict Resolution

**Conflicts arise when**:
- Two packages require incompatible Core versions
- Package explicitly lists another in `conflicts_with`
- Two packages bind to same port
- Same service name in Docker Compose

**Resolution strategy**:
- **Block installation**: Display error message with conflict details
- **Suggest alternatives**: Recommend compatible package versions
- **Manual override**: `--force` flag (dangerous, discouraged)

---

## 4. Installation Methods

### 4.1 Docker Compose (`method: docker_compose`)

**Steps**:
1. Parse `compose_service` from manifest
2. Verify service exists in `compose_file`
3. Copy `.env.example` → `.env.<service>` (if missing)
4. Prompt for required `env_required` variables
5. Update `docker-compose.yml` (add service if missing)
6. Run `docker compose up -d <service>`
7. Wait for health check (poll `required_endpoints`)
8. Run `init_commands` (if defined)
9. Run smoke tests

**Example**:
```bash
vit install babel_gardens
# Output:
# → Checking dependencies... ✅
# → Resolving versions... ✅
# → Installing service-babel-gardens v1.2.0
# → Configuring environment (.env.babel_gardens)
#   OPENAI_API_KEY: [paste here]
# → Starting Docker container... ✅
# → Running smoke tests... ✅ (3/3 passed)
# → Installation complete! Service available at http://localhost:8004
```

### 4.2 Python Package (`method: pip`)

**Steps**:
1. Determine install command: `pip install <repository>@<version>`
2. Run `pip install --no-deps <package>` (avoid dependency conflicts)
3. Run database migrations (if `migrations_path` defined)
4. Register in `.vitruvyan/installed_packages.json`
5. Run smoke tests

**Example**:
```bash
vit install extension-mcp-tools
# Output:
# → Installing extension-mcp-tools v0.5.2
# → pip install anthropic==0.38.0 ✅
# → Registering extension... ✅
# → Installation complete!
```

### 4.3 Git Clone (`method: git_clone`)

**Reserved for development/experimental packages**.

**Steps**:
1. Clone repository to `.vitruvyan/packages/<name>/`
2. Run setup script (if `setup_script` defined)
3. Register package
4. Run smoke tests

### 4.4 Custom Script (`method: script`)

**Escape hatch for complex installations**.

**Steps**:
1. Download installation script from `script_url`
2. Verify checksum (SHA256)
3. Execute script with `bash <script> install`
4. Register package
5. Run smoke tests

---

## 5. State Management

### 5.1 Installed Packages Registry

**File**: `.vitruvyan/installed_packages.json`

**Schema**:
```json
{
  "version": "1.0",
  "last_updated": "2026-02-20T10:30:00Z",
  "packages": [
    {
      "name": "service-babel-gardens",
      "version": "1.2.0",
      "installed_at": "2026-02-15T14:20:00Z",
      "installed_method": "docker_compose",
      "dependencies": ["vitruvyan-core", "service-pattern-weavers"],
      "status": "active",  // active|disabled|error
      "config": {
        "ports": ["8004:8004"],
        "volumes": [".vitruvyan/babel_gardens:/data"]
      }
    },
    {
      "name": "extension-mcp-tools",
      "version": "0.5.2",
      "installed_at": "2026-02-18T09:15:00Z",
      "installed_method": "pip",
      "dependencies": ["anthropic"],
      "status": "active"
    }
  ]
}
```

**Invariants**:
- Updated after every `vit install` / `vit remove`
- Atomic writes (write to `.tmp` → rename)
- Git-ignored (local machine state)

### 5.2 Rollback Support

**Pre-install snapshot**:
- Tag: `pre-install-<package>-<timestamp>` (Git)
- Backup: `.vitruvyan/backups/installed_packages_<timestamp>.json`

**Rollback triggers**:
- Smoke tests fail
- Service crashes during startup
- User explicitly runs `vit rollback`

**Rollback procedure**:
1. Stop service (`docker compose stop <service>`)
2. Restore Git state (`git checkout <tag>`)
3. Restore `.vitruvyan/installed_packages.json` from backup
4. Remove package files
5. Update audit log

---

## 6. CLI Commands

### 6.1 Install

```bash
vit install <package> [--channel stable|beta] [--version X.Y.Z] [--yes]

# Examples:
vit install babel_gardens                    # Latest stable
vit install babel_gardens --version 1.2.0    # Specific version
vit install babel_gardens --channel beta     # Latest beta
vit install babel_gardens --yes              # Non-interactive
```

**Output**:
- Dependency tree
- Installation plan (packages, order, disk space)
- Configuration prompts (env vars, secrets)
- Progress indicators
- Success/failure summary

**Exit codes**:
- `0`: Success
- `1`: Incompatible dependencies
- `2`: Installation failed
- `3`: Smoke tests failed (auto-rollback)

### 6.2 Remove

```bash
vit remove <package> [--purge] [--yes]

# Examples:
vit remove babel_gardens                     # Remove package, keep data
vit remove babel_gardens --purge             # Remove package + data + volumes
vit remove babel_gardens --yes               # Non-interactive
```

**Safety checks**:
- List dependent packages (block if any)
- Confirm data deletion (if `--purge`)
- Snapshot before removal

### 6.3 List

```bash
vit list [--all] [--type service|order|vertical|extension]

# Examples:
vit list                                     # Installed packages
vit list --all                               # All available packages
vit list --type service                      # Filter by type
```

**Output**:
```
Installed Packages:
  service-babel-gardens        1.2.0    active    (8004)
  service-neural-engine        2.1.0    active    (8002)
  extension-mcp-tools          0.5.2    active
  vertical-finance             1.0.0    active

Total: 4 packages
```

### 6.4 Info

```bash
vit info <package>

# Example:
vit info babel_gardens
```

**Output**:
- Package name, version, status
- Description, homepage
- Dependencies (tree view)
- Installation method
- Ports, volumes, env vars
- Configuration options
- Changelog (last 3 versions)

### 6.5 Search

```bash
vit search <query> [--type service|order|vertical|extension]

# Examples:
vit search llm                               # All LLM-related packages
vit search llm --type service                # Only LLM services
```

**Search fields**: name, description, tags

---

## 7. Package Registry

### 7.1 Registry Location

**Phase 5 (local manifests)**:
- **Path**: `vitruvyan_core/core/platform/package_manager/packages/manifests/`
- **Format**: YAML files (one per package)
- **Versioning**: Git-tracked (part of Core repository)

**Future (remote registry — Phase 6+)**:
- **URL**: `https://packages.vitruvyan.io/v1/`
- **API**: REST (JSON responses)
- **Cache**: Local cache in `.vitruvyan/registry_cache/`

### 7.2 Manifest Discovery

**Search paths** (in order):
1. Local manifests: `vitruvyan_core/core/platform/package_manager/packages/manifests/`
2. User manifests: `.vitruvyan/custom_packages/`
3. Remote registry: `https://packages.vitruvyan.io/v1/` (if configured)

### 7.3 Versioning & Channels

**Channels**:
- `stable`: Production-ready releases
- `beta`: Pre-release testing
- `experimental`: Development/unstable

**Version format**: SemVer `X.Y.Z[-channel.N]`

**Examples**:
- `1.2.0` → stable
- `1.3.0-beta.1` → beta
- `2.0.0-rc.2` → release candidate

---

## 8. Safety Guarantees

### 8.1 Pre-Installation Checks

1. **Compatibility**: Core version, contracts version
2. **Dependencies**: All required packages available
3. **Conflicts**: No incompatible packages installed
4. **Resources**: Disk space (100MB minimum), ports available
5. **Prerequisites**: Docker running (if needed), databases accessible

### 8.2 Transactional Installation

**Atomic operations**:
- Git snapshot before install
- Backup `.vitruvyan/installed_packages.json`
- Rollback on any failure

**Failure modes**:
- Smoke tests fail → auto-rollback
- Service crashes → rollback + error report
- User Ctrl+C → rollback in progress (safe interruption)

### 8.3 Post-Installation Validation

1. **Smoke tests**: Run package-defined tests
2. **Health checks**: Poll HTTP endpoints
3. **Dependency verification**: Check all dependencies loaded
4. **Stream connectivity**: Verify Redis Streams working (services)

---

## 9. Integration with Update Manager

### 9.1 Unified CLI

**Both systems use `vit` command**:

```bash
# Update Manager (Core versions)
vit update                    # Check for Core updates
vit upgrade                   # Upgrade Core
vit rollback                  # Revert Core upgrade

# Package Manager (Services/Orders/Verticals/Extensions)
vit install <package>         # Install package
vit remove <package>          # Remove package
vit list                      # List packages
vit search <query>            # Search packages
vit info <package>            # Package details

# Shared
vit status                    # Core + packages status
vit channel [stable|beta]     # Switch update channel
```

### 9.2 Shared Components

**Reused from Update Manager**:
- `engine/registry.py` → Extended to `PackageRegistry`
- `engine/compatibility.py` → Version matching (unchanged)
- `engine/planner.py` → Reused for install plans
- `engine/executor.py` → Extended to `PackageExecutor`
- `ci/contract_validator.py` → Package manifest validation

**New components**:
- `engine/package_resolver.py` → Dependency resolution
- `engine/catalog.py` → Package discovery
- `packages/manifests/` → Package manifest storage

### 9.3 Compatibility Enforcement

**Package installation checks**:
- Package `min_core_version` ≤ Current Core ≤ `max_core_version`
- Package `contracts_major` == Core contracts major
- All dependencies satisfy version constraints

**Core upgrade checks**:
- New Core compatible with all installed packages
- If incompatible → block upgrade OR suggest package updates

---

## 10. Versioning & Evolution

### 10.1 Contract Version

**Current**: `PACKAGE_MANAGER_SYSTEM_CONTRACT_V1.0`

**Versioning policy**:
- **Major**: Breaking changes to manifest schema
- **Minor**: Backwards-compatible additions
- **Patch**: Clarifications, typo fixes

**Deprecation policy**:
- 2 minor versions warning period
- 1 major version grace period
- Migration guide required for major changes

### 10.2 Manifest Schema Evolution

**Backwards compatibility**:
- New optional fields → default values
- Deprecated fields → ignored with warning
- Required fields → validation error

**Migration tools**:
- `vit migrate-manifest <package>` → Auto-upgrade manifest to latest schema

---

## 11. Implementation Phases

### Phase 5 - Package Management Foundation (Weeks 7-8)

**Deliverables**:
- Contract published (this document)
- Package manifest schema defined
- `PackageRegistry` implemented (local manifests)
- `DependencyResolver` implemented (topological sort)
- 3 example packages created:
  - `service-babel-gardens`
  - `service-neural-engine`
  - `vertical-finance`

### Phase 6 - Install/Remove Commands (Weeks 9-10)

**Deliverables**:
- `vit install` command working
- `vit remove` command working
- `vit list` command working
- Docker Compose integration
- State management (`.vitruvyan/installed_packages.json`)
- Rollback support

### Phase 7 - Discovery & Catalog (Week 11)

**Deliverables**:
- `vit search` command
- `vit info` command
- Local manifest discovery
- Tab completion for package names

---

## 12. Open Questions (To be decided)

1. **Remote registry**: When to implement? URL structure?
2. **Package signing**: GPG signatures for security?
3. **Multi-version support**: Allow multiple versions of same package?
4. **Virtual environments**: Isolate Python dependencies?
5. **Package namespaces**: Support third-party packages (`@myorg/package`)？
6. **Upgrade strategy**: How to upgrade packages independently of Core?

---

## Appendix A: Package Manifest Examples

### A.1 Service Package (Docker Compose)

See Section 2 (Babel Gardens example)

### A.2 Order Package (Python + Migrations)

```yaml
package_name: "order-orthodoxy-wardens"
package_version: "1.0.0"
package_type: "order"
status: "stable"

description: "Truth & Governance layer (validation, audit, compliance)"
homepage: "https://docs.vitruvyan.io/orders/orthodoxy-wardens"

compatibility:
  min_core_version: "1.0.0"
  max_core_version: "1.x.x"
  contracts_major: 1

dependencies:
  required:
    - "vitruvyan-core>=1.0.0"
  system:
    - postgres
    - redis

installation:
  method: "pip"
  package: "vitruvyan-core"  # Already installed, register only
  migrations_path: "vitruvyan_core/core/governance/orthodoxy_wardens/migrations/"
  init_commands:
    - "python -m vitruvyan_core.scripts.init_db --module orthodoxy_wardens"

configuration:
  env_required:
    - POSTGRES_CONNECTION_STRING
  database_schemas:
    - orthodoxy_wardens
  redis_streams:
    - "orthodoxy.validation.request"
    - "orthodoxy.audit.completed"

smoke_tests:
  path: "vitruvyan_core/core/governance/orthodoxy_wardens/tests/smoke/"
  timeout: 60
```

### A.3 Vertical Package (Manifest + Contracts)

```yaml
package_name: "vertical-finance"
package_version: "1.0.0"
package_type: "vertical"
status: "stable"

description: "Finance domain (trading, portfolio management, risk analysis)"
homepage: "https://docs.vitruvyan.io/verticals/finance"

compatibility:
  min_core_version: "1.0.0"
  max_core_version: "1.x.x"
  contracts_major: 1

dependencies:
  required:
    - "vitruvyan-core>=1.0.0"
    - "service-neural-engine>=2.0.0"
  optional:
    - "extension-bloomberg-adapter>=1.0.0"

installation:
  method: "git_clone"
  repository: "https://github.com/vitruvyan/vertical-finance.git"
  branch: "main"
  install_path: ".vitruvyan/verticals/finance/"
  setup_script: "scripts/setup.sh"

configuration:
  manifest_path: "vertical_manifest.yaml"
  contracts_compliance: true

smoke_tests:
  path: "smoke_tests/run.sh"
  timeout: 180
```

### A.4 Extension Package (Optional Dependencies)

```yaml
package_name: "extension-mcp-tools"
package_version: "0.5.2"
package_type: "extension"
status: "beta"

description: "Model Context Protocol integration (Claude, OpenAI tools)"
homepage: "https://docs.vitruvyan.io/extensions/mcp-tools"

compatibility:
  min_core_version: "1.0.0"
  max_core_version: "2.x.x"
  contracts_major: 1

dependencies:
  required:
    - "anthropic>=0.38.0"
  optional:
    - "openai>=1.0.0"

installation:
  method: "pip"
  package: "anthropic==0.38.0"
  feature_flag: "USE_MCP"

configuration:
  env_required:
    - ANTHROPIC_API_KEY
  env_optional:
    - OPENAI_API_KEY

smoke_tests:
  path: "vitruvyan_core/core/platform/mcp/tests/smoke/"
  timeout: 30
```

---

## Appendix B: Dependency Resolution Example

**Scenario**: Install `vertical-finance`

**Dependency tree**:
```
vertical-finance (1.0.0)
├── vitruvyan-core (>=1.0.0) → 1.2.0 installed ✅
├── service-neural-engine (>=2.0.0)
│   ├── vitruvyan-core (>=1.0.0) → 1.2.0 ✅ (shared)
│   ├── service-pattern-weavers (>=1.0.0)
│   │   └── vitruvyan-core (>=1.0.0) → 1.2.0 ✅ (shared)
│   └── postgres, redis → system ✅
└── extension-bloomberg-adapter (>=1.0.0) → OPTIONAL (skip)
```

**Install plan**:
1. Install `service-pattern-weavers` (1.1.0)
2. Install `service-neural-engine` (2.1.0)
3. Install `vertical-finance` (1.0.0)

**Estimated time**: 3 minutes (Docker pulls + smoke tests)

---

## Appendix C: Error Handling

### C.1 Incompatible Core Version

```bash
vit install babel_gardens

ERROR: Incompatible Core version
  Package: service-babel-gardens v1.2.0
  Requires: Core >=1.0.0, <=1.x.x
  Current: Core 2.0.0

Suggested actions:
  1. Downgrade Core: vit downgrade --target 1.9.0
  2. Wait for compatible package: vit search babel_gardens --channel beta
  3. Force install (unsafe): vit install babel_gardens --force

Exit code: 1
```

### C.2 Missing Dependencies

```bash
vit install neural_engine

ERROR: Missing dependencies
  Package: service-neural-engine v2.1.0
  Missing: service-pattern-weavers >=1.0.0

Suggested actions:
  1. Install dependencies automatically: vit install neural_engine --with-deps
  2. Install manually: vit install pattern_weavers && vit install neural_engine

Exit code: 1
```

### C.3 Port Conflict

```bash
vit install babel_gardens

ERROR: Port conflict
  Package: service-babel-gardens v1.2.0
  Port: 8004
  Already used by: service-custom-api (PID 12345)

Suggested actions:
  1. Stop conflicting service: docker stop service-custom-api
  2. Change port in manifest (advanced): vit install babel_gardens --port 8104

Exit code: 2
```

---

## Changelog

### v1.0 (Feb 20, 2026)

- Initial draft
- Package types defined (service, order, vertical, extension)
- Manifest schema specified
- CLI commands designed
- Integration with Update Manager defined
- Implementation phases outlined
