# Configurazione nginx + SSL (Feb 2026)

## Stato attuale

✅ **Dashboard** (dashboard.vitruvyan.com) - ATTIVO con SSL  
✅ **Metrics** (metrics.vitruvyan.com) - ATTIVO con SSL  
✅ **Knowledge Base** (kb.vitruvyan.com) - ATTIVO con SSL  
✅ **Auth** (auth.vitruvyan.com) - ATTIVO con SSL (Keycloak)

## Certificati SSL esistenti

```
infrastructure/docker/monitoring/certbot/conf/live/
├── dashboard.vitruvyan.com/  ✅
├── metrics.vitruvyan.com/     ✅
├── kb.vitruvyan.com/          ✅
└── auth.vitruvyan.com/        ✅
```

## Architettura

- **nginx**: reverse proxy + gestione SSL (porta 80/443)
- **certbot**: richiesta/rinnovo certificati Let's Encrypt
- **Network**: 
  - `monitoring-net` (nginx ↔ certbot)
  - `core-net` (nginx ↔ services: grafana, prometheus, mkdocs)

## Servizi backend

- `core_grafana:3000` → dashboard.vitruvyan.com
- `core_prometheus:9090` → metrics.vitruvyan.com
- `core_mkdocs:8000` → kb.vitruvyan.com
- `core_keycloak:8080` → auth.vitruvyan.com

## Richiedere certificati

### 1) Verifica DNS
```bash
# Assicurati che kb.vitruvyan.com punti all'IP pubblico del server
dig kb.vitruvyan.com +short
```

### 2) Richiedi certificato SSL (singolo dominio)
```bash
cd infrastructure/docker/monitoring
./nginx/request-kb-cert.sh
./nginx/request-auth-cert.sh
```

### 3) Verifica
```bash
curl -I https://kb.vitruvyan.com
curl -I https://auth.vitruvyan.com/auth/
```

## Comandi utili

```bash
# Stato servizi
cd infrastructure/docker/monitoring
docker compose ps

# Log nginx
docker logs core_nginx --tail 50

# Test configurazione nginx
docker exec core_nginx nginx -t

# Rinnovo certificati manuale (rinnova tutti i domini)
./certbot/renew.sh

# Riavvio nginx (dopo modifica config)
docker compose restart nginx
```

## Note

- **Certbot**: usato per richieste/rinnovi con webroot su `/var/www/certbot`
- **Rinnovo automatico**: presente via cron (script `certbot/renew.sh`)
