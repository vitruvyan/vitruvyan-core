#!/bin/bash
# Script per ottenere certificati SSL con Let's Encrypt

set -e

DOMAINS=("dashboard.vitruvyan.com" "metrics.vitruvyan.com" "kb.vitruvyan.com")
EMAIL="admin@vitruvyan.com"  # Cambia con la tua email
STAGING=0  # Imposta a 1 per test con staging server

echo "🔐 Ottenimento certificati SSL Let's Encrypt"
echo "============================================="
echo ""

# Verifica che nginx sia in esecuzione
if ! docker ps | grep -q core_nginx; then
    echo "❌ Errore: nginx non in esecuzione"
    echo "Esegui: docker compose up -d nginx"
    exit 1
fi

# Per ogni dominio, richiedi il certificato
for DOMAIN in "${DOMAINS[@]}"; do
    echo "📜 Richiedendo certificato per: $DOMAIN"
    
    CERTBOT_ARGS="certonly --webroot -w /var/www/certbot"
    CERTBOT_ARGS="$CERTBOT_ARGS --email $EMAIL"
    CERTBOT_ARGS="$CERTBOT_ARGS -d $DOMAIN"
    CERTBOT_ARGS="$CERTBOT_ARGS --rsa-key-size 4096"
    CERTBOT_ARGS="$CERTBOT_ARGS --agree-tos"
    CERTBOT_ARGS="$CERTBOT_ARGS --non-interactive"
    
    if [ $STAGING -eq 1 ]; then
        CERTBOT_ARGS="$CERTBOT_ARGS --staging"
        echo "⚠️  Usando staging server (test)"
    fi
    
    docker compose run --rm certbot $CERTBOT_ARGS
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificato ottenuto per $DOMAIN"
    else
        echo "❌ Errore nell'ottenimento del certificato per $DOMAIN"
    fi
    echo ""
done

echo "🔄 Riavvio nginx per caricare i certificati..."
docker compose restart nginx

echo ""
echo "✅ Processo completato!"
echo ""
echo "📝 Prossimi passi:"
echo "1. Verifica che i certificati siano stati creati:"
echo "   ls -la monitoring/certbot/conf/live/"
echo ""
echo "2. Decommentare il redirect HTTPS in nginx.conf:"
echo "   - Rimuovi i commenti da 'location / { return 301 https://\$host\$request_uri; }'"
echo "   - Commenta il blocco 'Temporaneo: proxy diretto'"
echo ""
echo "3. Riavvia nginx:"
echo "   docker compose restart nginx"
echo ""
echo "🌐 I tuoi domini saranno accessibili via HTTPS:"
echo "   - https://dashboard.vitruvyan.com"
echo "   - https://metrics.vitruvyan.com"
