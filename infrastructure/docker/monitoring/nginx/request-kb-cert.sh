#!/bin/bash
# Script per richiedere il certificato SSL per kb.vitruvyan.com
# Esegui da: infrastructure/docker/monitoring/

set -e

echo "🔐 Richiedendo certificato SSL per kb.vitruvyan.com..."
echo ""

# Verifica che nginx sia in esecuzione
if ! docker ps | grep -q core_nginx; then
    echo "❌ Errore: nginx non in esecuzione"
    echo "Esegui: docker compose up -d"
    exit 1
fi

# Richiedi il certificato
docker compose run --rm --entrypoint certbot certbot certonly \
    --webroot \
    -w /var/www/certbot \
    --email admin@vitruvyan.com \
    -d kb.vitruvyan.com \
    --rsa-key-size 4096 \
    --agree-tos \
    --non-interactive

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Certificato ottenuto per kb.vitruvyan.com"
    echo ""
    echo "📝 Prossimi passi:"
    echo "1. Decommentare il blocco HTTPS per kb in nginx.conf"
    echo "   (cerca 'HTTPS: Knowledge Base (kb) - Temporarily disabled')"
    echo ""
    echo "2. Riavviare nginx:"
    echo "   docker compose restart nginx"
    echo ""
    echo "3. Verificare:"
    echo "   https://kb.vitruvyan.com"
else
    echo ""
    echo "❌ Errore nell'ottenimento del certificato"
    echo ""
    echo "Verifica che:"
    echo "- Il dominio kb.vitruvyan.com punti al tuo server"
    echo "- La porta 80 sia accessibile dall'esterno"
    echo "- nginx risponda su http://kb.vitruvyan.com/.well-known/acme-challenge/"
fi
