#!/bin/bash
# vitruvyan-core Stack Status Check
# Agnostic architecture deployment verification

echo "🔍 VITRUVYAN-CORE STACK STATUS CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Infrastructure Services
echo "📦 INFRASTRUCTURE (Base Layer)"
echo "───────────────────────────────────"
docker ps --filter "name=omni_redis" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
docker ps --filter "name=omni_postgres" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
docker ps --filter "name=omni_qdrant" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

# Sacred Orders
echo "🏛️ SACRED ORDERS (Cognitive Subsystems)"
echo "───────────────────────────────────"
docker ps --filter "name=omni_babel_gardens" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_api_embedding" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_memory_orders" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_vault_keepers" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_api_orthodoxy" --format "{{.Names}}\t{{.Status}}"
echo

# API Services
echo "🌐 API SERVICES (Orchestration Layer)"
echo "───────────────────────────────────"
docker ps --filter "name=omni_api_graph" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_api_crewai" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_codex_hunters" --format "{{.Names}}\t{{.Status}}"
docker ps --filter "name=omni_pattern_weavers" --format "{{.Names}}\t{{.Status}}"
echo

# Summary
echo "📊 SUMMARY"
echo "───────────────────────────────────"
TOTAL=$(docker ps -a --filter "name=omni_" --format "{{.Names}}" | wc -l)
RUNNING=$(docker ps --filter "name=omni_" --filter "status=running" --format "{{.Names}}" | wc -l)
HEALTHY=$(docker ps --filter "name=omni_" --filter "health=healthy" --format "{{.Names}}" | wc -l)

echo "Total containers: $TOTAL"
echo "Running: $RUNNING"
echo "Healthy: $HEALTHY"
echo

# Health checks
echo "🏥 HEALTH CHECKS"
echo "───────────────────────────────────"
echo "Testing Babel Gardens API..."
curl -sf http://localhost:9009/sacred-health && echo "✅ Babel Gardens: OK" || echo "❌ Babel Gardens: FAILED"

echo "Testing Embedding API..."
curl -sf http://localhost:9010/health && echo "✅ Embedding: OK" || echo "❌ Embedding: FAILED"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Status check completed at $(date)"
