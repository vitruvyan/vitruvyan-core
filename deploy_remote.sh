#!/bin/bash
# Deploy vitruvyan-core su VPS remota
# Target: vitruvyan@144.91.127.225

set -e

VPS_HOST="144.91.127.225"
VPS_USER="vitruvyan"
VPS_PASS="Vitruvyan1971"
REPO_URL="https://github.com/dbaldoni/vitruvyan-core.git"
DEPLOY_DIR="/opt/vitruvyan-core"

echo "🚀 Deployment vitruvyan-core su VPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Target: ${VPS_USER}@${VPS_HOST}"
echo ""

# Funzione per eseguire comandi remoti
remote_exec() {
    sshpass -p "${VPS_PASS}" ssh -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" "$@"
}

# 1. Test connessione
echo "1️⃣ Test connessione SSH..."
if remote_exec "echo 'Connesso!' && hostname"; then
    echo "✅ Connessione SSH riuscita"
else
    echo "❌ Errore connessione SSH"
    exit 1
fi

# 2. Verifica prerequisiti
echo -e "\n2️⃣ Verifica prerequisiti..."
remote_exec "command -v git >/dev/null 2>&1 || { echo 'git non installato'; exit 1; }" && echo "✅ Git disponibile"
remote_exec "command -v docker >/dev/null 2>&1 || { echo 'docker non installato'; exit 1; }" && echo "✅ Docker disponibile"

# 3. Clone repository
echo -e "\n3️⃣ Clone repository..."
remote_exec "
    if [ -d ${DEPLOY_DIR} ]; then
        echo '⚠️ Directory ${DEPLOY_DIR} esiste già, eseguo pull invece di clone'
        cd ${DEPLOY_DIR}
        git pull origin main
    else
        echo '📦 Clono repository in ${DEPLOY_DIR}...'
        sudo mkdir -p ${DEPLOY_DIR}
        sudo chown ${VPS_USER}:${VPS_USER} ${DEPLOY_DIR}
        git clone ${REPO_URL} ${DEPLOY_DIR}
        cd ${DEPLOY_DIR}
        git status
    fi
"

# 4. Verifica clone
echo -e "\n4️⃣ Verifica clone..."
remote_exec "
    cd ${DEPLOY_DIR}
    echo '📂 Directory:' && pwd
    echo '📊 File count:' && find . -type f | wc -l
    echo '🌿 Branch:' && git branch --show-current
    echo '📝 Last commit:' && git log -1 --oneline
    echo '✅ Clone verificato'
"

# 5. Verifica file critici
echo -e "\n5️⃣ Verifica file critici..."
remote_exec "
    cd ${DEPLOY_DIR}
    [ -f DEPLOYMENT_AGENT_PROMPT.md ] && echo '✅ DEPLOYMENT_AGENT_PROMPT.md presente' || echo '❌ DEPLOYMENT_AGENT_PROMPT.md MANCANTE'
    [ -f COGNITIVE_BUS_AUDIT_REPORT_FEB5_2026.md ] && echo '✅ COGNITIVE_BUS_AUDIT_REPORT presente' || echo '⚠️ Audit report non trovato'
    [ -d .github ] && echo '✅ .github/ presente' || echo '❌ .github/ MANCANTE'
    [ -d vitruvyan_core/core/foundation/cognitive_bus ] && echo '✅ Cognitive Bus presente' || echo '❌ Cognitive Bus MANCANTE'
"

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment completato!"
echo "📍 Repository clonato in: ${DEPLOY_DIR}"
echo ""
echo "🔍 Prossimi passi:"
echo "   1. Leggi DEPLOYMENT_AGENT_PROMPT.md"
echo "   2. Configura .env file"
echo "   3. Esegui docker compose up -d"
echo "   4. Lancia test suite E2E"
