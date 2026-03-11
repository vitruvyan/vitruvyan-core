# Installation

> **Last updated**: Mar 11, 2026 14:00 UTC

## Quick Start (One-Liner)

On a **fresh Ubuntu VPS** (24.04 LTS recommended), run:

```bash
curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh | bash
```

This single command will:

1. Install system prerequisites (git, python3, curl)
2. Clone the repository to `/opt/vitruvyan-core`
3. Make the `vit` command available system-wide
4. Launch the interactive setup wizard

The wizard then handles everything else: Docker installation, port configuration, environment setup, and infrastructure startup.

!!! tip "Review before running"
    If you prefer to inspect the script first:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh -o install.sh
    less install.sh
    bash install.sh
    ```

## Installation Options

| Method | Best for | Guide |
|--------|----------|-------|
| **One-liner** | Fresh VPS, quick deployment | This page |
| **Manual clone** | Developers, custom setups | [Local Setup](LOCAL.md) |
| **Docker only** | Pre-existing Docker host | [Docker Setup](DOCKER.md) |
| **Production** | Institutional deployment | [Production](PRODUCTION.md) |

## Installer Options

The installer script accepts environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `INSTALL_DIR` | `/opt/vitruvyan-core` | Where to clone the repository |
| `BRANCH` | `main` | Git branch to install |
| `SKIP_SETUP` | `0` | Set to `1` to skip the setup wizard |
| `REPO_URL` | `github.com/dbaldoni/vitruvyan-core` | Git repository URL |

Example with custom options:

```bash
INSTALL_DIR=/home/myuser/vitruvyan BRANCH=develop \
  curl -fsSL https://raw.githubusercontent.com/dbaldoni/vitruvyan-core/main/scripts/install.sh | bash
```

## What Gets Installed

The complete Vitruvyan OS stack consists of:

```
┌─────────────────────────────────────────────┐
│  Your VPS (Ubuntu)                          │
│                                             │
│  /opt/vitruvyan-core/        ← source code  │
│  /usr/local/bin/vit          ← CLI command  │
│                                             │
│  Docker containers:                         │
│  ├── core_redis      (Cognitive Bus)        │
│  ├── core_postgres   (Archivarium)          │
│  ├── core_qdrant     (Mnemosyne)            │
│  ├── core_graph      (LangGraph API)        │
│  ├── core_nginx      (Reverse Proxy)        │
│  └── ...services     (Sacred Orders)        │
└─────────────────────────────────────────────┘
```

## Post-Installation

After installation, verify with:

```bash
vit status          # System overview
vit doctor          # Detailed health check
```

## Next Steps

- [Requirements](REQUIREMENTS.md) — Hardware and OS requirements
- [Environment Variables](ENV_VARS.md) — Configuration reference
- [Health Checks](HEALTH_CHECKS.md) — Verification procedures

