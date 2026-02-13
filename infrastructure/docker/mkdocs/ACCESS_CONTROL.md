# Knowledge Base — Access Control (Public / Internal / Advanced)

This repository ships a **reproducible, self-hosted** Knowledge Base deployment using:

- **MkDocs (Material)** in Docker for building/serving documentation
- **Nginx** as the enforcement point for access control + TLS

## Access Tiers

### 1) Public (no authentication)

- `/` → public landing page (English default)
- `/it/` → public landing page (Italian)

Served as **static files** from the `site_public` build output.

### 2) Internal (Basic Auth)

Protected via Nginx `auth_basic` (htpasswd).

- `/(it/)?docs/…`
- `/(it/)?(services|infrastructure|examples|vitruvyan_core|config|scripts|tests)/…`
- `/search/…` (protected to prevent search-index leakage)

### 3) Advanced (Basic Auth, separate credentials)

Protected via a separate htpasswd file:

- `/(it/)?docs/planning/…`
- `/(it/)?docs/architecture/<…technical…>/…`

## How It Works

1. The MkDocs container builds both sites:
   - `/app/site_public` (public landing)
   - `/app/site` (full/internal docs)
2. Nginx terminates TLS and:
   - serves public landing as **static**
   - proxies internal routes to the MkDocs server **only after auth**

## User Management (htpasswd)

Generate/update credentials from the repo:

```bash
./infrastructure/docker/monitoring/nginx/create-htpasswd.sh
docker compose -f infrastructure/docker/monitoring/docker-compose.yml restart nginx
```

> Keycloak/OIDC is optional and can be enabled later; Basic Auth is the current default.

## Verification (expected)

Anonymous:

- `GET /` → `200`
- `GET /docs/` → `401`
- `GET /search/search_index.json` → `401`

With credentials:

- `GET /docs/` → `200` (basic users)
- `GET /docs/planning/` → `401` unless advanced user
