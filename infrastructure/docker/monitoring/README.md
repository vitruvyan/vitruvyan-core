# Monitoring Stack (Docker)

This folder contains the **monitoring + reverse proxy** stack used by Vitruvyan Core:

- Nginx (TLS termination + access control for the KB)
- Prometheus + Grafana
- Certbot (Let’s Encrypt renewal)

## Start here

- TLS / certificate status: `infrastructure/docker/monitoring/README_SSL_STATUS.md`
- Nginx config (KB + dashboards): `infrastructure/docker/monitoring/nginx/nginx.conf`
- Compose file: `infrastructure/docker/monitoring/docker-compose.yml`

