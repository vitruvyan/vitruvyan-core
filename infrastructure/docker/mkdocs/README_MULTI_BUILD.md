# MkDocs Multi-Build Architecture — Setup Guide

> **Last Updated**: February 12, 2026  
> **Architecture**: Multi-tier access control (Public / Authenticated / Advanced)  
> **Status**: Production-ready

## 🎯 Overview

Vitruvyan Knowledge Base con **3 livelli di accesso**:

| Level | Path | Authentication | Content |
|-------|------|----------------|---------|
| **Public** | `/public/` | ❌ None | Getting started, overview, charter |
| **Authenticated** | `/` | ✅ HTTP Basic Auth | Full documentation (services, infrastructure, tests) |
| **Advanced** | `/planning/`, `/architecture/technical-*` | ✅ Advanced htpasswd | Roadmaps, technical debt, refactoring plans |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Browser                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Nginx Reverse Proxy                                │
│  ┌──────────────────┬──────────────────┬──────────────────┐    │
│  │  /public/        │  /               │  /planning/      │    │
│  │  (no auth)       │  (htpasswd)      │  (htpasswd_adv)  │    │
│  └────────┬─────────┴────────┬─────────┴────────┬─────────┘    │
└───────────┼──────────────────┼──────────────────┼───────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│           MkDocs Container (core_mkdocs:8000)                   │
│  ┌───────────────────────┬────────────────────────────────┐    │
│  │  /app/site_public     │  /app/site                     │    │
│  │  (build public.yml)   │  (build full mkdocs.yml)       │    │
│  └───────────────────────┴────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Setup Instructions

### Step 1: Build Docker Image

```bash
cd infrastructure/docker
docker compose build mkdocs
```

**Cosa fa**:
- Installa Python 3.11 + MkDocs Material
- Copia `build-all.sh` script per multi-build
- Prepara directory `/app/site` e `/app/site_public`

### Step 2: Deploy MkDocs Container

```bash
docker compose up -d mkdocs
```

**Al startup**, il container esegue:
1. `/app/build-all.sh` → genera 2 siti:
   - `site_public/` (mkdocs.public.yml - solo public content)
   - `site/` (mkdocs.yml - full documentation)
2. `mkdocs serve` → hot-reload server su porta 8000

**Verifica**:
```bash
docker logs core_mkdocs --tail 30

# Expected output:
# ✅ Public site: /app/site_public
# ✅ Full site: /app/site
# INFO - [HH:MM:SS] Serving on http://0.0.0.0:8000/
```

### Step 3: Configure Nginx Authentication

```bash
# Entra nel container Nginx (o esegui su host se nginx installato)
cd infrastructure/docker/monitoring/nginx
chmod +x create-htpasswd.sh
./create-htpasswd.sh
```

**Interactive prompts**:
```
Create basic user 'developer':
New password: ********
Re-type password: ********

Create advanced user 'admin':
New password: ********
Re-type password: ********
```

**Output files**:
- `/etc/nginx/.htpasswd` → Basic users (full docs access)
- `/etc/nginx/.htpasswd_advanced` → Advanced users (planning/technical)

### Step 4: Configure Nginx Site

```bash
# Copia config nella directory nginx
cp monitoring/nginx/sites-available/mkdocs.conf monitoring/nginx/sites-enabled/

# Restart Nginx
docker compose restart nginx
```

### Step 5: Verify Access

```bash
# Public (no auth)
curl http://kb.vitruvyan.com/public/
# Expected: 200 OK (HTML homepage)

# Authenticated (requires credentials)
curl http://kb.vitruvyan.com/
# Expected: 401 Unauthorized

curl -u developer:password http://kb.vitruvyan.com/
# Expected: 200 OK (full documentation)

# Advanced (requires advanced credentials)
curl -u admin:password http://kb.vitruvyan.com/planning/
# Expected: 200 OK (planning docs)
```

## 🔧 Manual Multi-Build

Se vuoi rigenerare i siti manualmente:

```bash
# Entra nel container
docker exec -it core_mkdocs bash

# Esegui build script
/app/build-all.sh

# Output:
# ✅ Public site: 12M /app/site_public
# ✅ Full site: 45M /app/site
```

## 📝 Aggiungere Contenuto Pubblico

Modifica `mkdocs.public.yml`:

```yaml
nav:
  - Welcome: index.md
  - Getting Started:
    - Overview: docs/foundational/VITRUVYAN_OVERVIEW.md
    - New Public Page: docs/foundational/NEW_PAGE.md  # ← Add here
```

Poi rebuild:
```bash
docker restart core_mkdocs
```

## 🔐 Gestione Utenti

### Aggiungere utente basic

```bash
htpasswd /etc/nginx/.htpasswd nuovo_utente
```

### Aggiungere utente advanced

```bash
htpasswd /etc/nginx/.htpasswd_advanced nuovo_admin
```

### Rimuovere utente

```bash
htpasswd -D /etc/nginx/.htpasswd vecchio_utente
```

### Restart Nginx

```bash
docker compose restart nginx
```

## 📊 File Structure

```
infrastructure/docker/mkdocs/
├── Dockerfile                      # Python 3.11 + MkDocs + plugins
├── mkdocs.yml                      # FULL site config (authenticated)
├── mkdocs.public.yml               # PUBLIC site config (no auth)
├── build-all.sh                    # Multi-build orchestrator
├── requirements.txt                # Dependencies
└── README.md                       # This file

infrastructure/docker/monitoring/nginx/
├── sites-available/
│   └── mkdocs.conf                 # Nginx virtual host (multi-tier auth)
├── create-htpasswd.sh              # User management script
└── .htpasswd, .htpasswd_advanced   # Password files (generated)
```

## 🎯 Access Matrix

| User Type | `/public/` | `/` | `/services/` | `/planning/` |
|-----------|-----------|-----|--------------|--------------|
| **Anonymous** | ✅ | ❌ | ❌ | ❌ |
| **Basic (developer)** | ✅ | ✅ | ✅ | ❌ |
| **Advanced (admin)** | ✅ | ✅ | ✅ | ✅ |

## 🚀 Production Deployment

1. **DNS**: Point `kb.vitruvyan.com` A record to server IP
2. **SSL**: Enable HTTPS block in `mkdocs.conf` (uncomment)
3. **Certbot**: Run Let's Encrypt for SSL certificate
4. **Firewall**: Open ports 80, 443

```bash
# Get SSL certificate
certbot certonly --webroot -w /var/www/certbot -d kb.vitruvyan.com

# Reload Nginx with SSL config
docker compose restart nginx
```

---

**Status**: ✅ Multi-build architecture operational  
**URL**: https://kb.vitruvyan.com  
**Authentication**: HTTP Basic Auth + htpasswd
