#!/bin/bash
# Script di sviluppo locale rapido per Vitruvyan UI
# Uso: ./dev-local.sh

echo "🚀 Vitruvyan UI - Sviluppo Locale"
echo "================================="
echo ""
echo "📋 Configurazione attiva:"
echo "   - Backend: https://graph.vitruvyan.com"
echo "   - Keycloak: https://user.vitruvyan.com"
echo "   - Porta: 3000 (default Next.js)"
echo ""
echo "🔧 Comandi rapidi:"
echo "   Ctrl+C          → Ferma il server"
echo "   npm run build   → Build di produzione"
echo "   npm run lint    → Controlla il codice"
echo ""
echo "🌐 Frontend locale: http://localhost:3000"
echo "🌐 Frontend remoto: https://mercator.vitruvyan.com"
echo ""
echo "⚡ Avvio in 3 secondi..."
sleep 3

npm run dev
