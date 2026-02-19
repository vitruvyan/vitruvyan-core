#!/bin/bash
# Script di test per validare LangGraph 1.0.8 nel container isolato
# Data: 16 Febbraio 2026

set -e

CONTAINER_NAME="core_graph_test"
TEST_PORT="9099"
HEALTH_ENDPOINT="http://localhost:${TEST_PORT}/health"
DISPATCH_ENDPOINT="http://localhost:${TEST_PORT}/dispatch"

echo "=============================================="
echo " Test LangGraph 1.0.8 - Container Isolato"
echo "=============================================="
echo ""

# 1. Verifica immagine buildato
echo "1️⃣  Verifico immagine Docker..."
if docker images | grep -q "vitruvyan_api_graph_test"; then
    echo "   ✅ Immagine presente"
    docker images | grep graph_test | head -1
else
    echo "   ❌ Immagine NON trovata. Esegui prima:"
    echo "      docker compose -f infrastructure/docker/docker-compose.yml build vitruvyan_api_graph_test"
    exit 1
fi
echo ""

# 2. Rimuovi container precedente
echo "2️⃣  Rimuovo container precedente (se esiste)..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true
echo "   ✅ Container rimosso"
echo ""

# 3. Avvia container
echo "3️⃣  Avvio container di test..."
cd /home/vitruvyan/vitruvyan-core
docker compose -f infrastructure/docker/docker-compose.yml up -d vitruvyan_api_graph_test
echo "   ✅ Container avviato"
echo ""

# 4. Attendi startup
echo "4️⃣  Attendo startup container (15 secondi)..."
for i in {15..1}; do
    echo -ne "   ⏳ $i secondi...\r"
    sleep 1
done
echo "   ✅ Attesa completata                    "
echo ""

# 5. Verifica logs (ultimi 30 righe)
echo "5️⃣  Verifico logs container..."
echo "   --- ULTIMI 30 LOGS ---"
docker logs ${CONTAINER_NAME} --tail=30 2>&1 | sed 's/^/   │ /'
echo ""

# 6. Test health endpoint
echo "6️⃣  Test health endpoint..."
HTTP_CODE=$(curl -s -o /tmp/health_response.json -w "%{http_code}" ${HEALTH_ENDPOINT} 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Health check OK (HTTP ${HTTP_CODE})"
    echo "   Response:"
    cat /tmp/health_response.json | python3 -m json.tool 2>/dev/null | sed 's/^/   │ /' || cat /tmp/health_response.json | sed 's/^/   │ /'
else
    echo "   ❌ Health check FAILED (HTTP ${HTTP_CODE})"
    echo "   Response:"
    cat /tmp/health_response.json 2>/dev/null | sed 's/^/   │ /' || echo "   │ (vuoto)"
fi
echo ""

# 7. Verifica versione LangGraph installata
echo "7️⃣  Verifico versione LangGraph nel container..."
LANGGRAPH_VERSION=$(docker exec ${CONTAINER_NAME} pip show langgraph 2>/dev/null | grep "Version:" | awk '{print $2}')
if [ "$LANGGRAPH_VERSION" = "1.0.8" ]; then
    echo "   ✅ LangGraph versione: ${LANGGRAPH_VERSION}"
else
    echo "   ⚠️  LangGraph versione: ${LANGGRAPH_VERSION} (attesa 1.0.8)"
fi

# Verifica dipendenze correlate
echo "   Dipendenze correlate:"
docker exec ${CONTAINER_NAME} pip list 2>/dev/null | grep -E "(langgraph|alembic)" | sed 's/^/   │ /'
echo ""

# 8. Test dispatch endpoint (opzionale, solo se health OK)
if [ "$HTTP_CODE" = "200" ]; then
    echo "8️⃣  Test dispatch endpoint (richiesta semplice)..."
    DISPATCH_PAYLOAD='{"query": "test langgraph 1.0.8", "validated_entities": []}'
    
    DISPATCH_CODE=$(curl -s -o /tmp/dispatch_response.json -w "%{http_code}" \
        -X POST ${DISPATCH_ENDPOINT} \
        -H "Content-Type: application/json" \
        -d "$DISPATCH_PAYLOAD" 2>/dev/null || echo "000")
    
    if [ "$DISPATCH_CODE" = "200" ]; then
        echo "   ✅ Dispatch OK (HTTP ${DISPATCH_CODE})"
        echo "   Response (primi 500 caratteri):"
        cat /tmp/dispatch_response.json | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data, indent=2)[:500])" 2>/dev/null | sed 's/^/   │ /' || head -c 500 /tmp/dispatch_response.json | sed 's/^/   │ /'
    else
        echo "   ⚠️  Dispatch HTTP ${DISPATCH_CODE}"
        echo "   Response:"
        cat /tmp/dispatch_response.json 2>/dev/null | sed 's/^/   │ /' || echo "   │ (vuoto)"
    fi
else
    echo "8️⃣  Test dispatch SALTATO (health check fallito)"
fi
echo ""

# 9. Riepilogo
echo "=============================================="
echo " RIEPILOGO TEST"
echo "=============================================="
echo "Container:        ${CONTAINER_NAME}"
echo "Porta test:       ${TEST_PORT}"
echo "LangGraph:        ${LANGGRAPH_VERSION}"
echo "Health check:     $([ "$HTTP_CODE" = "200" ] && echo "✅ OK" || echo "❌ FAILED")"
echo ""
echo "Comandi utili:"
echo "  - Logs:         docker logs ${CONTAINER_NAME} -f"
echo "  - Stop:         docker stop ${CONTAINER_NAME}"
echo "  - Restart:      docker restart ${CONTAINER_NAME}"
echo "  - Health:       curl ${HEALTH_ENDPOINT}"
echo "  - Dispatch:     curl -X POST ${DISPATCH_ENDPOINT} -H 'Content-Type: application/json' -d '{\"query\":\"test\"}'"
echo ""

# Cleanup
rm -f /tmp/health_response.json /tmp/dispatch_response.json

echo "Test completati!"
