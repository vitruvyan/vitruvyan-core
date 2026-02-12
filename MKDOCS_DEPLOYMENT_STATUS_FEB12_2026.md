# MkDocs Knowledge Base — Deployment Status (Feb 12, 2026)

**Sessione**: Configurazione Knowledge Base multi-tier con accesso pubblico + autenticato  
**Data**: 12 Febbraio 2026, ore 18:40 UTC  
**Commit finale**: `fb8a9fb` — "feat(mkdocs): public site = landing page only + Nginx static serving"

---

## ✅ Completato Oggi

### 1. Multi-Build Architecture (FUNZIONANTE)
- ✅ **Public site**: Landing page singola (2.5 MB) — spiega Vitruvyan + richiesta accesso
- ✅ **Full site**: Documentazione completa (28 MB) — tutte le sezioni
- ✅ **Build automatico**: `build-all.sh` genera entrambi i siti allo startup container
- ✅ **Docker volumes**: `vitruvyan-core_mkdocs_site` (full), `vitruvyan-core_mkdocs_site_public` (landing)

### 2. Landing Page Pubblica (docs/public/landing.md)
Contenuto creato:
- ✅ Cosa è Vitruvyan? (OS epistemico domain-agnostic)
- ✅ Sacred Orders Pattern (6 ordini cognitivi)
- ✅ LangGraph + Synaptic Conclave overview
- ✅ **Access Tiers**:
  - 🔓 **Basic Access** (developers): full API docs, deployment, examples
  - 🔐 **Advanced Access** (core team): roadmaps, tech debt, planning
- ✅ Request Credentials (istruzioni + email template)
- ✅ Tech stack, license, contact info

### 3. Nginx Static Serving (TEST ENDPOINT)
- ✅ Nginx container monta volume `mkdocs_site_public` → `/var/www/mkdocs/site_public/`
- ✅ **Test locale**: `http://localhost/kb` → HTTP 200 ✅
- ✅ Landing page verificata (titolo "Vitruvyan Core", contenuto corretto)

### 4. File Configurazione Pronti
| File | Stato | Scopo |
|------|-------|-------|
| `mkdocs.public.yml` | ✅ Production-ready | Config landing page (docs_dir=/app/docs_root_public) |
| `mkdocs.yml` | ✅ Production-ready | Config documentazione completa |
| `build-all.sh` | ✅ Funzionante | Orchestrator multi-build |
| `Dockerfile` | ✅ Build OK | Crea docs_root + docs_root_public |
| `nginx.conf` | ✅ Test OK | Location `/kb` serve static files |
| `sites-available/mkdocs.conf` | ⚠️ Da attivare | Config produzione (public + auth proxy) |

---

## 📋 Stato Containers

```bash
# Verifica container attivi
docker ps | grep -E "mkdocs|nginx"
```

**Risultato atteso**:
```
core_mkdocs   Up 30 minutes (healthy)   9800->8000/tcp
core_nginx    Up 15 minutes              80->80/tcp, 443->443/tcp
```

**Volumes**:
```bash
docker volume ls | grep mkdocs
```
```
vitruvyan-core_mkdocs_site         # 28 MB (full docs)
vitruvyan-core_mkdocs_site_public  # 2.5 MB (landing page)
```

**Verifica build**:
```bash
docker logs core_mkdocs 2>&1 | grep -E "(Preparing|Public site|Full site)"
```
```
📄 Preparing public landing page...
✅ Public site: /app/site_public
✅ Full site: /app/site
```

---

## 🔧 Test Endpoint (Locale)

### Public Landing Page (NO AUTH)
```bash
curl http://localhost/kb
# HTTP 200 ✅
# Titolo: "Vitruvyan Core"
# Contenuto: Request Credentials, Basic Access, Advanced Access
```

### Full Docs (MkDocs Dev Server)
```bash
curl http://localhost:9800/
# HTTP 200 ✅
# Serve documentazione completa (NO AUTH al momento)
```

---

## ⏳ Prossimi Step (DA FARE DOMANI)

### FASE 1: Attivare Configurazione Produzione (kb.vitruvyan.com)

#### 1.1 Configurare Nginx per kb.vitruvyan.com
Il file `sites-available/mkdocs.conf` è pronto ma serve attivazione:

```bash
cd infrastructure/docker/monitoring/nginx

# Verifica configurazione
cat sites-available/mkdocs.conf
# NOTA: Ha già le location per public (static) + auth (proxy)

# Opzione A: Aggiungere a nginx.conf
# Decommentare blocco HTTPS (righe ~103-135 in nginx.conf)
# Oppure configurare HTTP temporaneo (vedi sotto)

# Opzione B: Include sites-enabled (standard pattern)
# Nginx non usa sites-enabled al momento, configurato direttamente in nginx.conf
```

**DECISIONE NECESSARIA**: Vuoi:
- **A)** Aggiungere location in `nginx.conf` (attuale) → modifica file esistente
- **B)** Switchare a pattern `sites-enabled/` → più modulare ma richiede modifica nginx.conf


#### 1.2 Creare htpasswd Files
```bash
cd infrastructure/docker/monitoring/nginx

# Script interattivo già creato
./create-htpasswd.sh

# Verrà richiesto:
# - Username/password per Basic Access (.htpasswd)
# - Username/password per Advanced Access (.htpasswd_advanced)

# Output:
# /etc/nginx/.htpasswd           → developer access
# /etc/nginx/.htpasswd_advanced  → core team access
```

**UTENTI SUGGERITI**:
```
Basic Access (.htpasswd):
- developer / <password>
- integrator / <password>

Advanced Access (.htpasswd_advanced):
- admin / <password>
- architect / <password>
```

#### 1.3 Configurare Server Block per kb.vitruvyan.com

**Opzione HTTP (no SSL, test veloce)**:

Aggiungi a `nginx.conf` dopo il blocco Prometheus (~line 105):

```nginx
# HTTPS: Knowledge Base (kb.vitruvyan.com)
server {
    listen 80;  # Temporaneo, poi 443 ssl http2
    server_name kb.vitruvyan.com;

    # Public landing page (static, no auth)
    location = / {
        root /var/www/mkdocs/site_public;
        index index.html;
        add_header Cache-Control "public, max-age=3600";
    }

    location ~* ^/(assets|search)/ {
        root /var/www/mkdocs/site_public;
        try_files $uri $uri/ =404;
    }

    # ADVANCED ACCESS (check first, more specific paths)
    location ~ ^/(planning|architecture/.*technical) {
        auth_basic "Vitruvyan KB - Advanced Access";
        auth_basic_user_file /etc/nginx/.htpasswd_advanced;

        proxy_pass http://kb;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # BASIC ACCESS (full docs)
    location ~ ^/(docs|services|infrastructure|examples|vitruvyan_core|config|scripts|tests) {
        auth_basic "Vitruvyan KB - Developer Access";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://kb;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "OK\n";
    }
}
```

**Restart Nginx**:
```bash
docker compose restart nginx
docker logs core_nginx --tail=20  # Verifica no errori
```

---

### FASE 2: SSL Certificate (Let's Encrypt)

```bash
# SSL certificate per kb.vitruvyan.com
certbot certonly --webroot -w /var/www/certbot -d kb.vitruvyan.com

# Output: certificati in /etc/letsencrypt/live/kb.vitruvyan.com/
# - fullchain.pem
# - privkey.pem
```

**Poi modifica server block**: `listen 80;` → `listen 443 ssl http2;`

```nginx
server {
    listen 443 ssl http2;
    server_name kb.vitruvyan.com;

    ssl_certificate /etc/letsencrypt/live/kb.vitruvyan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kb.vitruvyan.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... (resto location come sopra)
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name kb.vitruvyan.com;
    return 301 https://$server_name$request_uri;
}
```

---

### FASE 3: DNS Configuration

Punta dominio al server:

```
kb.vitruvyan.com.  A  <IP_SERVER>
```

**Verifica**:
```bash
dig kb.vitruvyan.com
# Deve risolvere a IP del server
```

---

### FASE 4: Test Accessi Multi-Tier

```bash
# Test 1: Public landing (no auth)
curl https://kb.vitruvyan.com/
# HTTP 200, landing page ✅

# Test 2: Basic Access (richiede auth)
curl https://kb.vitruvyan.com/docs/
# HTTP 401 Unauthorized ✅

curl -u developer:password https://kb.vitruvyan.com/docs/
# HTTP 200, documentazione ✅

# Test 3: Advanced Access (richiede admin auth)
curl -u developer:password https://kb.vitruvyan.com/planning/
# HTTP 401 Unauthorized ✅ (basic user non può accedere)

curl -u admin:password https://kb.vitruvyan.com/planning/
# HTTP 200, planning docs ✅
```

---

## 📁 File Chiave (Riferimento Rapido)

### Documentazione
```
/home/vitruvyan/vitruvyan-core/
├── docs/public/landing.md                      # Landing page pubblica
├── index.md                                    # Homepage full docs
└── infrastructure/docker/
    ├── mkdocs/
    │   ├── mkdocs.yml                          # Config full docs
    │   ├── mkdocs.public.yml                   # Config landing page
    │   ├── build-all.sh                        # Orchestrator multi-build
    │   ├── Dockerfile                          # Image mkdocs
    │   └── README_MULTI_BUILD.md               # Setup guide completa
    └── monitoring/
        ├── docker-compose.yml                  # Nginx + certbot
        └── nginx/
            ├── nginx.conf                      # Config principale (modificare QUI)
            ├── sites-available/mkdocs.conf     # Virtual host template (usare come riferimento)
            └── create-htpasswd.sh              # User management (eseguibile)
```

### Comandi Docker
```bash
# Rebuild mkdocs
cd infrastructure/docker
docker compose build mkdocs
docker compose up -d --force-recreate mkdocs

# Restart nginx
cd infrastructure/docker/monitoring
docker compose restart nginx

# Logs
docker logs core_mkdocs --tail=50
docker logs core_nginx --tail=50

# Verifica volumi
docker exec core_mkdocs du -sh /app/site /app/site_public
docker exec core_nginx ls -lh /var/www/mkdocs/site_public/
```

---

## 🚨 Issue Noti

### 1. Nginx Config Pattern
**Problema**: Attualmente `nginx.conf` è monolitico (tutti i server block dentro).  
**Alternativa**: Pattern `sites-enabled/` (più modulare).  
**Stato**: `sites-available/mkdocs.conf` esiste ma NON è incluso.  
**Decisione**: Domani scegliere tra:
- Aggiungere location a `nginx.conf` (veloce)
- Switchare a `include /etc/nginx/sites-enabled/*.conf;` (clean)

### 2. Volume Name Mismatch (RISOLTO)
**Era**: `docker_mkdocs_site_public` (nome sbagliato in monitoring/docker-compose.yml)  
**Fix**: `vitruvyan-core_mkdocs_site_public` (commit fb8a9fb) ✅

### 3. Broken Relative Links in Full Docs
**Warning**: MkDocs segnala link relativi rotti (es. `../README.md` non trovato).  
**Causa**: File root repository non montati in docs_root.  
**Impatto**: Basso (solo warnings build, siti funzionano).  
**Fix futuro**: Symlink anche README.md root in docs_root/.

---

## 🎯 Decisioni Architetturali (Storico)

### Perché Landing Page Singola?
**Richiesta utente**: "nel site public non pubblicare documentazione fai solo una landing page semplice di spiegazione basilare e poi proponi accessi con password basic e advanced"

**Vantaggi**:
- ✅ Public site minimo (2.5MB vs 26MB)
- ✅ Security by isolation (nessun doc sensibile in public)
- ✅ Chiaro call-to-action (richiesta credenziali)
- ✅ SEO migliore (single page ottimizzata)

### Perché Nginx Static Serving per Public?
**Alternativa valutata**: Proxy tutto tramite MkDocs dev server.  
**Scelta**: Static files per landing, proxy per docs autenticate.  
**Vantaggi**:
- ✅ Performance (Nginx serve static molto veloce)
- ✅ Meno carico su MkDocs container
- ✅ Landing page accessibile anche se MkDocs crashato

### Perché 2 htpasswd Files?
**Basic Access** (`.htpasswd`): developers, integrators → accesso a docs API/servizi.  
**Advanced Access** (`.htpasswd_advanced`): core team → accesso a planning/roadmaps.  
**Vantaggi**:
- ✅ Separazione chiara permessi
- ✅ Facile management (2 file separati)
- ✅ Revoca credenziali selective

---

## 📊 Metriche Finali

| Metrica | Valore |
|---------|--------|
| **Public site size** | 2.5 MB (was 26 MB) |
| **Full site size** | 28 MB |
| **Landing page lines** | 308 (docs/public/landing.md) |
| **Build time** | ~18 secondi (entrambi i siti) |
| **Commits today** | 6 (a26148b init → fb8a9fb final) |
| **Files created** | 7 (landing.md, configs, scripts) |
| **Files modified** | 10 |

---

## 💾 Checkpoint Git

**Branch**: `main`  
**Commits ahead of origin**: 7 (non pushato ancora)

```bash
# Commit history (ultimi 6)
git log --oneline -6

fb8a9fb feat(mkdocs): public site = landing page only + Nginx static serving
a26148b fix(mkdocs): resolve docs_dir parent directory error with symlink strategy
37430e9 feat(mkdocs): multi-build architecture with 3-tier access control
3e51287 fix(mkdocs): homepage on / + production URL kb.vitruvyan.com
a725666 feat(mkdocs): deploy knowledge base server + config fixes
450a320 chore: remove duplicate CHANGELOG_PHASE6.md from root
```

**Push quando pronto**:
```bash
git push origin main  # Push 7 commits
```

---

## 🔄 Come Riprendere Domani

### 1. Verifica Stato Container
```bash
cd /home/vitruvyan/vitruvyan-core/infrastructure/docker/monitoring

# Status
docker ps | grep -E "mkdocs|nginx"

# Se stopped:
docker compose up -d

# Se crashato:
docker logs core_mkdocs --tail=50
docker logs core_nginx --tail=50
```

### 2. Test Landing Page
```bash
curl http://localhost/kb
# Deve ritornare HTTP 200 + landing page
```

### 3. Leggi Questo File
```bash
cat /home/vitruvyan/vitruvyan-core/MKDOCS_DEPLOYMENT_STATUS_FEB12_2026.md

# Vai a sezione "FASE 1" per continuare deployment produzione
```

### 4. Prosegui con FASE 1.1
Decisione: modificare `nginx.conf` per aggiungere kb.vitruvyan.com server block.

---

## 📞 Contatti / Risorse

- **Repository**: `/home/vitruvyan/vitruvyan-core`
- **Docker logs**: `infrastructure/docker/monitoring/`
- **MkDocs configs**: `infrastructure/docker/mkdocs/`
- **Landing page source**: `docs/public/landing.md`
- **Setup guide**: `infrastructure/docker/mkdocs/README_MULTI_BUILD.md`

---

## ✅ Checklist Pre-Produzione

Prima di andare live su kb.vitruvyan.com:

- [ ] **htpasswd files creati** (`./create-htpasswd.sh`)
- [ ] **nginx.conf modificato** (server block kb.vitruvyan.com)
- [ ] **DNS configurato** (kb.vitruvyan.com → IP server)
- [ ] **SSL certificate ottenuto** (certbot)
- [ ] **Test HTTP** (http://kb.vitruvyan.com/ → landing page)
- [ ] **Test HTTPS** (https://kb.vitruvyan.com/ → landing page)
- [ ] **Test auth basic** (curl -u developer:pwd /docs/)
- [ ] **Test auth advanced** (curl -u admin:pwd /planning/)
- [ ] **Push commits** (git push origin main)
- [ ] **Update README.md** (add kb.vitruvyan.com link)

---

**Stato finale**: ✅ Multi-build funzionante, landing page creata, Nginx configurato (test endpoint).  
**Prossimo step**: Creare htpasswd files + attivare configurazione produzione kb.vitruvyan.com.

---

*File creato: 12 Feb 2026, 18:40 UTC*  
*Location: `/home/vitruvyan/vitruvyan-core/MKDOCS_DEPLOYMENT_STATUS_FEB12_2026.md`*
