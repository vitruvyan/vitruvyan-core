# Requirements

This page defines the **baseline requirements** to run Vitruvyan OS via Docker (KB + core services).

## Hardware baseline

These numbers assume a **single-node** deployment running the core stack (Redis, Postgres, Qdrant, Nginx, MkDocs, and the main APIs).

| Profile | CPU | RAM | Disk | Notes |
|---|---:|---:|---:|---|
| **Minimum (dev / small internal)** | 8 vCPU | 16 GB | 250 GB SSD | Works for demos and light usage. Expect tight memory headroom. |
| **Recommended (institutional / shared)** | 16 vCPU | 32 GB | 500 GB NVMe | Comfortable headroom for Qdrant + Postgres + logs + rebuilds. |
| **Heavy (multi-tenant / high ingestion)** | 32 vCPU | 64 GB | 1 TB NVMe | When embeddings + ingestion + retention grow continuously. |

Notes:
- Prefer **NVMe** over HDD (Qdrant and Postgres latency matters).
- Disk sizing depends on **retention** (events, audit, snapshots) and **vector growth**.

## Supported OS

- **Ubuntu 24.04 LTS** (recommended baseline)

Other Linux distros can work, but our reference paths and hardening notes assume Ubuntu.

## Required infrastructure services

Vitruvyan expects these components (containerized or managed equivalents):

- **PostgreSQL** (Archivarium) — structured storage, audit, metadata
- **Qdrant** (Mnemosyne) — vector storage for semantic retrieval
- **Redis** — Streams transport (Cognitive Bus) and coordination
- **Nginx** — reverse proxy, TLS termination, access control (Basic Auth today; Keycloak later)

## Required runtime

- **Docker Engine** + **Docker Compose**
- Ability to pull/build images (private registry access if applicable)

Optional but useful on the host:
- `curl`, `git`, `make`, `jq`
- `python3` (for local scripts and quick probes)

## Network requirements

### Inbound (from users)

- `80/tcp` (HTTP) and `443/tcp` (HTTPS) to Nginx

### Internal (container-to-container)

Services communicate inside the Docker network; avoid exposing internal ports publicly unless required.

### Outbound (from the server)

Depending on configuration, outbound access may be needed for:
- system package installs and container image pulls
- TLS certificate issuance/renewal (if using Let's Encrypt)
- optional LLM providers (if not fully self-hosted)

## DNS / TLS

- Stable hostname(s) for the KB (e.g. `kb.vitruvyan.com`)
- Valid TLS certificate (Nginx terminates TLS)

## Production hardening (recommended)

- Backups for PostgreSQL and Qdrant (snapshots + off-box storage)
- Log rotation and disk monitoring
- Firewall rules: expose only `80/443` publicly
- Separate nodes (optional): split DB/vector/bus from API tier when load grows
