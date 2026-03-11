# Local Setup (Manual Installation)

> **Last updated**: Mar 11, 2026 14:00 UTC

Step-by-step guide for installing Vitruvyan OS manually, without the one-liner installer.

## Prerequisites

- **Ubuntu 24.04 LTS** (or compatible Debian-based distro)
- **Python 3.10+** (`python3 --version`)
- **git** and **curl**

```bash
# Install prerequisites if missing
sudo apt update && sudo apt install -y git curl python3
```

## Step 1: Clone the Repository

```bash
# Clone to your preferred location
git clone https://github.com/dbaldoni/vitruvyan-core.git
cd vitruvyan-core
```

## Step 2: Make `vit` Available

The `vit` CLI works directly from the repo — no `pip install` required:

```bash
# Option A: symlink to PATH (recommended)
sudo ln -s "$(pwd)/vit" /usr/local/bin/vit

# Option B: add repo to PATH in ~/.bashrc
echo "export PATH=\"$(pwd):\$PATH\"" >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
vit --help
```

## Step 3: Run the Setup Wizard

```bash
vit setup
```

The wizard guides you through 5 steps:

| Step | What it does |
|------|-------------|
| **1. Prerequisites** | Checks Python, git, Docker — offers to install Docker if missing |
| **2. Ports** | Configure host ports (standard: 6379, 5432, 6333, 6334 — or custom) |
| **3. Profile** | Choose an installation profile (minimal, standard, finance, full, custom) |
| **4. Environment** | Collect API keys and passwords (OpenAI, PostgreSQL, etc.) |
| **5. Install** | Install selected packages and start infrastructure containers |

## Step 4: Verify

```bash
# Check system status
vit status

# Verify Docker containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Non-Interactive Mode

For automated deployments (CI/CD, Ansible, etc.):

```bash
# Install with minimal profile, no prompts
vit setup --profile minimal --yes

# Or just run prerequisite checks
vit setup --check

# Or just generate .env file
vit setup --env-only
```

## Custom Ports

If standard ports conflict with existing services, the wizard lets you choose alternatives. Ports are configured as `HOST_*` variables in `infrastructure/docker/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_REDIS_PORT` | 6379 | Redis host port |
| `HOST_POSTGRES_PORT` | 5432 | PostgreSQL host port |
| `HOST_QDRANT_REST_PORT` | 6333 | Qdrant REST API host port |
| `HOST_QDRANT_GRPC_PORT` | 6334 | Qdrant gRPC host port |

These only affect the **host-side** port mapping. Services communicate internally via the Docker network using standard ports.

## Troubleshooting

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
# Log out and back in, then retry
```

**Port already in use:**
```bash
# Find what's using a port
sudo lsof -i :6379
# Choose a different port during setup
```

**Re-run setup:**
```bash
vit setup  # Safe to re-run — preserves existing .env values
```

