# Package Manager — Sistema di Distribuzione Vitruvyan

> **Last updated**: Mar 14, 2026 18:30 UTC
> **Status**: Implemented — Local + Remote registry, 8 manifests, first published package (Oculus Prime v1.0.0)
> **CLI**: `vit install`, `vit remove`, `vit list`, `vit search`, `vit info`, `vit setup`
> **Architecture**: Registry (local + remote) → Resolver → Downloader → Installer → State

---

## Filosofia del Sistema

Il Package Manager di Vitruvyan è progettato come un **sistema di distribuzione a due livelli** ispirato ad apt/apk:

- **Core tier** — i componenti fondamentali dell'OS epistemico (Sacred Orders, Graph, Conclave, Agents) sono gestiti da `vit upgrade` e non sono installabili separatamente
- **Package tier** — servizi opzionali, verticali di dominio ed estensioni sono installabili via `vit install`

La distribuzione segue un modello **community + premium**:

| Tier | Accesso | Auth | Esempio |
|------|---------|------|---------|
| **community** | Download diretto da GitHub Releases | Nessuna | oculus-prime, neural-engine |
| **premium** | Download via VPS auth proxy con license token | `VIT_LICENSE_TOKEN` o `.vitruvyan/license.key` | frontier-odoo, frontier-sap |

---

## Quick Start

```bash
# Setup iniziale (wizard interattivo)
vit setup

# Cercare pacchetti disponibili (locali)
vit search engine
vit list --all

# Cercare anche nel remote registry
vit search frontier --remote

# Info dettagliate su un pacchetto
vit info neural_engine
vit info frontier-odoo        # fallback automatico al remote

# Installare un pacchetto locale
vit install neural_engine

# Installare un pacchetto remoto (download automatico)
vit install oculus-prime

# Installare un vertical con dipendenze opzionali
vit install vertical-finance --with-optional

# Rimuovere un pacchetto
vit remove mcp
vit remove mcp --purge       # rimuove anche i dati

# Stato installazioni
vit list
```

---

## Architettura — I Due Registri

### Registry Locale

Il registry locale scopre i manifest `.vit` presenti nel repo:

```
vitruvyan_core/core/platform/package_manager/
├── models.py                 # PackageManifest (frozen dataclass, ~30 campi)
│                             # InstalledPackage, InstallPlan
├── registry.py               # PackageRegistry — scopre .vit locali
│                             #   discover() → scansiona directory manifests
│                             #   get(name) → lookup multi-chiave
│                             #   search(query) → ricerca per nome/descrizione
├── resolver.py               # DependencyResolver — ordinamento topologico
│                             #   resolve() → InstallPlan con install_order
│                             #   Conflict detection (nomi, porte)
│                             #   System dep checks (docker, redis, postgres)
├── installer.py              # PackageInstaller — esecuzione installazione
│                             #   docker_compose → docker compose up -d --build
│                             #   script → esecuzione comandi init
│                             #   Health check polling post-install
├── state.py                  # PackageState — .vitruvyan/installed_packages.json
│                             #   Atomic writes (.tmp → os.replace)
├── remote.py                 # RemoteRegistry + PackageDownloader
│                             #   Fetch registry.json da GitHub
│                             #   Download .vit.tar.gz con SHA-256 verify
│                             #   License token per pacchetti premium
├── bootstrap.py              # Bootstrap iniziale
├── profiles.py               # Profili installazione (minimal/standard/full)
└── packages/
    ├── VIT_FORMAT_SPEC.md    # Specifica completa formato .vit
    └── manifests/            # Manifest builtin
        ├── order-babel-gardens.vit
        ├── service-graph.vit
        ├── service-neural-engine.vit
        ├── service-mcp.vit
        ├── service-edge-dse.vit
        ├── service-edge-oculus-prime.vit
        ├── vertical-finance.vit
        └── VERTICAL_TEMPLATE.vit
```

### Registry Remoto

Il registry remoto risiede su GitHub: [`vitruvyan/vitruvyan-packages`](https://github.com/vitruvyan/vitruvyan-packages)

```
vitruvyan-packages/            # Repo GitHub
├── registry.json              # Indice di tutti i pacchetti pubblicati
├── README.md
└── (GitHub Releases)          # Asset: .vit.tar.gz + .sha256 per versione
```

**`registry.json`** — indice centrale:
```json
{
  "registry_version": "1.0.0",
  "base_url": "https://github.com/vitruvyan/vitruvyan-packages/releases/download",
  "packages": {
    "oculus-prime": {
      "display_name": "Oculus Prime",
      "description": "Multi-modal evidence ingestion...",
      "type": "service",
      "tier": "community",
      "license_required": false,
      "manifest_name": "service-edge-oculus-prime",
      "latest": "1.0.0",
      "versions": {
        "1.0.0": {
          "release_tag": "service-edge-oculus-prime-v1.0.0",
          "asset": "service-edge-oculus-prime-1.0.0.vit.tar.gz",
          "sha256": "f0867895f5b4958b..."
        }
      }
    }
  }
}
```

**Caching**: il registry.json viene cachato in `.vitruvyan/cache/registry_cache.json` con TTL di 1 ora. Se il remote è irraggiungibile, il client usa la cache scaduta come fallback.

---

## Flusso di Installazione

### Pacchetto Locale (già presente nel repo)

```
vit install neural_engine
  │
  ├── PackageRegistry.get("neural_engine")
  │   └── trovato in packages/manifests/service-neural-engine.vit ✓
  │
  ├── PackageState.is_installed() → no
  │
  ├── DependencyResolver.resolve()
  │   ├── Check system deps (docker, redis, postgres)
  │   ├── Check conflicts (nomi, porte)
  │   └── Topological sort → install_order
  │
  ├── Confirmation prompt → [Y/n]
  │
  └── PackageInstaller.install()
      ├── docker compose up -d --build neural_engine
      ├── Health check poll (http://localhost:9003/health)
      └── PackageState.add() → .vitruvyan/installed_packages.json
```

### Pacchetto Remoto (download dal registry GitHub)

```
vit install oculus-prime
  │
  ├── PackageRegistry.get("oculus-prime") → NOT FOUND
  │
  ├── Fallback: RemoteRegistry.fetch_index()
  │   └── GET registry.json da GitHub raw
  │
  ├── RemoteRegistry.get_package("oculus-prime") → trovato ✓
  │   ├── license_required: false (community)
  │   └── latest: "1.0.0"
  │
  ├── PackageDownloader.download_and_extract()
  │   ├── GET .vit.tar.gz da GitHub Release asset
  │   ├── SHA-256 checksum verification ✓
  │   ├── Path traversal protection ✓
  │   └── Extract → .vitruvyan/packages/oculus-prime-1.0.0/
  │
  ├── PackageRegistry(extra_paths=[extract_dir])
  │   └── Discover manifest.vit → PackageManifest
  │
  └── (prosegue come installazione locale)
```

### Pacchetto Premium (con license token)

```
vit install frontier-odoo
  │
  ├── (locale: not found) → (remoto: trovato)
  │   └── license_required: true
  │
  ├── read_license_token()
  │   ├── 1° check: $VIT_LICENSE_TOKEN env var
  │   └── 2° check: .vitruvyan/license.key file
  │
  ├── If no token → errore: "Set your license in .vitruvyan/license.key"
  │
  └── If token found:
      ├── Download via VPS auth proxy ($VIT_LICENSE_PROXY_URL)
      ├── HTTP 401 → "License required"
      ├── HTTP 403 → "License invalid or expired"
      └── HTTP 200 → extract + install
```

---

## Formato `.vit`

I manifest `.vit` sono file YAML che descrivono un pacchetto. Esempio completo:

```yaml
# Vitruvyan Package Manifest — Oculus Prime
package_name: service-edge-oculus-prime
package_version: "1.0.0"
package_type: service               # service|order|vertical|extension
status: stable                      # stable|beta|experimental|deprecated
tier: package                       # core|package
description: "Multi-modal evidence ingestion..."

sacred_order: Perception             # Sacred Order di appartenenza (opzionale)

compatibility:
  min_core_version: "1.15.0"
  max_core_version: "1.x.x"
  contracts_major: 1
  conflicts_with: []

dependencies:
  required:
    - "vitruvyan-core>=1.15.0"
  optional:
    - "service-neural-engine>=2.0.0"
  system:
    - docker
    - redis
    - postgres

installation:
  method: docker_compose             # docker_compose|script
  compose_service: edge_oculus_prime
  compose_file: infrastructure/docker/docker-compose.yml
  dockerfile: services/api_edge_oculus_prime/Dockerfile
  ports:
    - "9050:8050"
  env_required:
    - POSTGRES_PASSWORD
  env_optional:
    - LOG_LEVEL=INFO
    - GDRIVE_CREDENTIALS_FILE

health:
  endpoint: "http://localhost:9050/health"
  interval: 30
  timeout: 10

smoke_tests:
  path: smoke_tests/
  timeout: 120

uninstallation:
  preserve_data: true
  cleanup_streams: true
  cleanup_channels:
    - "oculus.ingest.completed"

ownership:
  team: core
  contact: dev@vitruvyan.io
```

### Tipi di Pacchetto

| Tipo | Descrizione | Metodo Install | Esempio |
|------|-------------|----------------|---------|
| **service** | Microservizio Docker standalone | docker_compose | service-neural-engine |
| **order** | Sacred Order (componente kernel) | docker_compose | order-babel-gardens |
| **vertical** | Meta-pacchetto dominio + servizi | script | vertical-finance |
| **extension** | Plugin/connettore per servizi esistenti | script | frontier-odoo (futuro) |

### Lookup Multi-Chiave

Un pacchetto `service-edge-oculus-prime` è raggiungibile con qualsiasi di questi nomi:

| Chiave | Esempio |
|--------|---------|
| `package_name` | `service-edge-oculus-prime` |
| `short_name` | `edge-oculus-prime` |
| `cli_name` | `edge_oculus_prime` |

Il registry converte automaticamente underscore → hyphen per la ricerca.

---

## Dependency Resolution

Il resolver usa **ordinamento topologico** (DFS) per determinare l'ordine di installazione:

```
vit install vertical-finance
→ Analisi dipendenze:
  ├── required: service-neural-engine (non installato → aggiungi)
  ├── optional: service-mcp, service-edge-dse (prompt interattivo)
  └── system: docker ✓, redis ✓, postgres ✓
→ Install order: [service-neural-engine, vertical-finance]
→ Conflitti: nessuno
```

**Conflict detection**:

- **Conflitti di nome** — pacchetti che dichiarano `conflicts_with: [altro-pacchetto]`
- **Conflitti di porta** — stessa porta host già occupata da un pacchetto installato

---

## Costruire e Pubblicare Pacchetti

### Build Script

```bash
# Costruire un singolo pacchetto
./scripts/build_package.sh service-edge-oculus-prime

# Costruire tutti i pacchetti
./scripts/build_package.sh --all
```

Output in `dist/`:
```
dist/
├── service-edge-oculus-prime-1.0.0.vit.tar.gz   # Tarball
├── service-edge-oculus-prime-1.0.0.sha256         # Checksum
├── service-neural-engine-2.1.0.vit.tar.gz
├── service-neural-engine-2.1.0.sha256
└── ...
```

Il tarball contiene:
```
manifest.vit                           # Manifest rinominato (standard)
service-edge-oculus-prime.vit          # Manifest originale preservato
```

### Pubblicazione su GitHub

```bash
# 1. Aggiornare registry.json in vitruvyan-packages
#    (aggiungere versione, SHA-256, release_tag)

# 2. Creare GitHub Release
gh release create "service-edge-oculus-prime-v1.0.0" \
  dist/service-edge-oculus-prime-1.0.0.vit.tar.gz \
  dist/service-edge-oculus-prime-1.0.0.sha256 \
  --repo vitruvyan/vitruvyan-packages \
  --title "Oculus Prime v1.0.0" \
  --notes "..."

# 3. Commit e push registry.json
cd vitruvyan-packages
git add registry.json && git commit -m "publish: oculus-prime v1.0.0"
git push origin main
```

### Automazione Jenkins (futuro)

Il Jenkinsfile rileva automaticamente quali servizi sono cambiati e può:

1. **Build automatico** dei tarball `.vit.tar.gz` per i servizi modificati
2. **Push** dei tarball come asset su GitHub Releases
3. **Aggiornamento** automatico di `registry.json`

---

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `VIT_REGISTRY_URL` | GitHub raw URL | URL del registry.json remoto |
| `VIT_RELEASE_BASE_URL` | GitHub Releases URL | Base URL per download asset |
| `VIT_LICENSE_PROXY_URL` | *(nessuno)* | URL del VPS auth proxy per pacchetti premium |
| `VIT_LICENSE_TOKEN` | *(nessuno)* | License token per pacchetti premium |

### File License

In alternativa alla variabile d'ambiente, il license token può risiedere in:
```
.vitruvyan/license.key      # nella root del repo
~/.vitruvyan/license.key    # nella home dell'utente
```

---

## State Management

I pacchetti installati sono tracciati in `.vitruvyan/installed_packages.json`:

```json
{
  "service-neural-engine": {
    "name": "service-neural-engine",
    "version": "2.1.0",
    "installed_at": "2026-03-14T18:30:00",
    "install_method": "docker_compose",
    "status": "active",
    "ports": ["9003:8003"]
  }
}
```

- **Atomic writes**: scrittura su file `.tmp` → `os.replace()` per prevenire corruzioni
- **Nessun database**: puro JSON su filesystem, zero dipendenze esterne

---

## Creare un Nuovo Vertical

1. Copiare `VERTICAL_TEMPLATE.vit` come `vertical-<dominio>.vit`
2. Compilare i campi specifici del dominio
3. Posizionare in `packages/manifests/`
4. Creare codice dominio sotto `vitruvyan_core/domains/<dominio>/`
5. Test: `vit info <dominio>`, `vit install <dominio>`

### Esempio: vertical-finance

```bash
$ vit install vertical-finance --with-optional

  Package: vertical-finance v1.0.0
  Type:    vertical (stable)

  Will install:
    + service-neural-engine v2.1.0
    + vertical-finance v1.0.0

  Optional packages:
    ? service-mcp v0.5.2
    ? service-edge-dse v1.0.0

  Domain components:
    - finance-intents: Finance intent detection configuration
    - finance-prompts: Finance-specific LLM prompts
    - finance-contracts: Finance domain contracts and rules
```

---

## Sicurezza

- **SHA-256 checksum** su ogni tarball scaricato — mismatch = abort
- **Path traversal protection** — i tarball con path assoluti o `../` vengono rifiutati
- **License token** — mai hardcodato, sempre via env var o file dedicato
- **No secrets nel codice** — URL, password, token sono sempre env vars
- **Atomic state writes** — prevengono corruzioni da crash/interruzioni

---

## Pacchetti Pubblicati

| Pacchetto | Versione | Tipo | Tier | Release |
|-----------|----------|------|------|---------|
| service-edge-oculus-prime | 1.0.0 | service | community | [GitHub Release](https://github.com/vitruvyan/vitruvyan-packages/releases/tag/service-edge-oculus-prime-v1.0.0) |

---

## Documentazione Correlata

- [Update Manager System](Update_Manager_System.md) — Sistema di aggiornamento core (`vit upgrade`)
- [Vertical Implementation Guide](Vertical_Implementation_Guide.md) — Costruire verticali di dominio
- [Package Manager Contract V1](../../contracts/platform/PACKAGE_MANAGER_SYSTEM_CONTRACT_V1.md) — Contratto binding per il package manager
- `.vit` Format Spec: `vitruvyan_core/core/platform/package_manager/packages/VIT_FORMAT_SPEC.md`
