#!/bin/bash
# Script per richiedere il certificato SSL per auth.vitruvyan.com (Keycloak)
# Esegui da: infrastructure/docker/monitoring/

set -e

DOMAIN="auth.vitruvyan.com"
EMAIL="admin@vitruvyan.com"

echo "🔐 Richiedendo certificato SSL per ${DOMAIN}..."
echo ""

if ! docker ps | grep -q core_nginx; then
  echo "❌ Errore: nginx non in esecuzione"
  echo "Esegui: docker compose up -d nginx"
  exit 1
fi

docker compose run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  --email "${EMAIL}" \
  -d "${DOMAIN}" \
  --rsa-key-size 4096 \
  --agree-tos \
  --non-interactive

echo ""
echo "✅ Certificato ottenuto per ${DOMAIN}"
echo ""
echo "📝 Prossimi passi:"
echo "1. Abilitare il blocco HTTPS in nginx.conf:"
echo "   - file: infrastructure/docker/monitoring/nginx/nginx.conf"
echo "   - sezione: 'HTTPS: Keycloak (Auth)'"
echo ""
echo "2. Riavviare nginx:"
echo "   docker compose restart nginx"
echo ""
echo "3. Verificare:"
echo "   https://${DOMAIN}/auth/"
