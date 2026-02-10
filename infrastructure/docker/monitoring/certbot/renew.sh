#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"

echo "[certbot-renew] $(date -Is) starting"

docker compose run --rm certbot \
  renew \
  --webroot -w /var/www/certbot \
  --config-dir /etc/letsencrypt \
  --work-dir /tmp/letsencrypt \
  --logs-dir /tmp/letsencrypt/logs

# Reload nginx to pick up renewed certs (if any)
docker compose exec -T nginx nginx -s reload || docker compose restart nginx

echo "[certbot-renew] $(date -Is) done"
