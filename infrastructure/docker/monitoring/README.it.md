# Monitoring Stack (Docker)

Questa cartella contiene lo stack **monitoring + reverse proxy** usato da Vitruvyan Core:

- Nginx (terminazione TLS + access control per la KB)
- Prometheus + Grafana
- Certbot (renewal Let’s Encrypt)

## Da leggere per primi

- Stato TLS / certificati: `infrastructure/docker/monitoring/README_SSL_STATUS.md`
- Config Nginx (KB + dashboards): `infrastructure/docker/monitoring/nginx/nginx.conf`
- Compose: `infrastructure/docker/monitoring/docker-compose.yml`

