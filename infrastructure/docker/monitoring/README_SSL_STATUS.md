# Configurazione nginx + SSL (Feb 12, 2026)

## Stato attuale

✅ **Dashboard** (dashboard.vitruvyan.com) - ATTIVO con SSL  
✅ **Metrics** (metrics.vitruvyan.com) - ATTIVO con SSL  
⏸️ **Knowledge Base** (kb.vitruvyan.com) - PREPARATO, certificato SSL da richiedere

## Certificati SSL esistenti

```
infrastructure/docker/monitoring/certbot/conf/live/
├── dashboard.vitruvyan.com/  ✅
├── metrics.vitruvyan.com/     ✅
└── kb.vitruvyan.com/          ⏸️ (da creare)
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
- `core_mkdocs:8000` → kb.vitruvyan.com (⚠️ unhealthy, serve 404)

## Per attivare kb.vitruvyan.com

### Passo 1: Verifica DNS
```bash
# Assicurati che kb.vitruvyan.com punti all'IP pubblico del server
dig kb.vitruvyan.com +short
```

### Passo 2: Richiedi certificato SSL
```bash
cd infrastructure/docker/monitoring
./nginx/request-kb-cert.sh
```

### Passo 3: Abilita configurazione nginx
```bash
# Modifica infrastructure/docker/monitoring/nginx/nginx.conf
# Decommenta il blocco:
#   # HTTPS: Knowledge Base (kb) - Temporarily disabled

# Riavvia nginx
docker compose restart nginx
```

### Passo 4: Verifica
```bash
curl -I https://kb.vitruvyan.com
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

# Rinnovo certificati (cron consigliato ogni 60 giorni)
docker compose run --rm certbot renew

# Riavvio nginx (dopo modifica config)
docker compose restart nginx
```

## Note

- **Certbot**: container idle, usato solo per richieste/rinnovi manuali
- **Rinnovo automatico**: da implementare tramite cron (script `certbot/renew.sh`)
- **core_mkdocs**: attualmente unhealthy (404), da verificare configurazione mkdocs.yml
