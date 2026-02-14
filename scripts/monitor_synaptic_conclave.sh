#!/bin/bash
# Synaptic Conclave Monitoring Script
# Check health of event bus infrastructure

set -e

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧠 SYNAPTIC CONCLAVE MONITORING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check Redis Status
echo -e "\n${COLOR_BLUE}1️⃣  Redis Streams Status${COLOR_RESET}"
if docker exec core_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "   ${COLOR_GREEN}✅ Redis is UP${COLOR_RESET}"
    
    # Get Redis version
    REDIS_VERSION=$(docker exec core_redis redis-cli INFO server | grep redis_version | cut -d: -f2 | tr -d '\r')
    echo "   Version: $REDIS_VERSION"
    
    # Count active streams
    STREAM_COUNT=$(docker exec core_redis redis-cli --scan --pattern "vitruvyan:*" | wc -l)
    echo "   Active streams: $STREAM_COUNT"
else
    echo -e "   ${COLOR_RED}❌ Redis is DOWN${COLOR_RESET}"
fi

# 2. Check Listeners
echo -e "\n${COLOR_BLUE}2️⃣  Sacred Order Listeners${COLOR_RESET}"
LISTENERS=(
    "core_orthodoxy_listener:8006:Orthodoxy Wardens"
    "core_vault_listener:8007:Vault Keepers"
    "core_codex_listener:8008:Codex Hunters"
    "core_babel_listener:8009:Babel Gardens"
    "core_pattern_weavers_listener:8011:Pattern Weavers"
    "core_conclave_listener:8012:Conclave Observatory"
    "core_memory_orders_listener:8016:Memory Orders"
)

HEALTHY=0
UNHEALTHY=0

for listener_info in "${LISTENERS[@]}"; do
    IFS=':' read -r container port name <<< "$listener_info"
    
    if docker inspect "$container" > /dev/null 2>&1; then
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
        
        if [ "$STATUS" = "healthy" ]; then
            echo -e "   ${COLOR_GREEN}✅${COLOR_RESET} $name ($container)"
            HEALTHY=$((HEALTHY + 1))
        elif [ "$STATUS" = "no-health-check" ]; then
            # Check if running
            IS_RUNNING=$(docker inspect --format='{{.State.Running}}' "$container")
            if [ "$IS_RUNNING" = "true" ]; then
                echo -e "   ${COLOR_YELLOW}⚠️${COLOR_RESET}  $name ($container) - Running (no health check)"
                HEALTHY=$((HEALTHY + 1))
            else
                echo -e "   ${COLOR_RED}❌${COLOR_RESET} $name ($container) - Stopped"
                UNHEALTHY=$((UNHEALTHY + 1))
            fi
        else
            echo -e "   ${COLOR_RED}❌${COLOR_RESET} $name ($container) - $STATUS"
            UNHEALTHY=$((UNHEALTHY + 1))
        fi
    else
        echo -e "   ${COLOR_RED}❌${COLOR_RESET} $name ($container) - Not found"
        UNHEALTHY=$((UNHEALTHY + 1))
    fi
done

echo ""
echo "   Summary: $HEALTHY healthy, $UNHEALTHY unhealthy"

# 3. Check Consumer Groups
echo -e "\n${COLOR_BLUE}3️⃣  Consumer Groups (sample)${COLOR_RESET}"
SAMPLE_STREAMS=(
    "vitruvyan:vault.archive.requested"
    "vitruvyan:memory.coherence.requested"
    "vitruvyan:babel.sentiment.completed"
)

for stream in "${SAMPLE_STREAMS[@]}"; do
    GROUPS=$(docker exec core_redis redis-cli XINFO GROUPS "$stream" 2>/dev/null | grep -c "name" || echo "0")
    PENDING=$(docker exec core_redis redis-cli XPENDING "$stream" "" 2>/dev/null | head -1 || echo "N/A")
    
    if [ "$GROUPS" -gt 0 ]; then
        echo -e "   ${COLOR_GREEN}✅${COLOR_RESET} $stream"
        echo "      Consumer groups: $GROUPS"
        echo "      Pending: $PENDING"
    else
        echo -e "   ${COLOR_YELLOW}⚠️${COLOR_RESET}  $stream - No consumer groups"
    fi
done

# 4. Check PostgreSQL
echo -e "\n${COLOR_BLUE}4️⃣  PostgreSQL Status${COLOR_RESET}"
if docker exec core_postgres pg_isready -U vitruvyan > /dev/null 2>&1; then
    echo -e "   ${COLOR_GREEN}✅ PostgreSQL is UP${COLOR_RESET}"
    
    # Check recent events
    RECENT_EVENTS=$(docker exec core_graph python3 -c "
from core.agents.postgres_agent import PostgresAgent
pg = PostgresAgent()
query = \"SELECT COUNT(*) as total FROM vault_archives WHERE created_at > NOW() - INTERVAL '1 hour'\"
result = pg.fetch(query)
print(result[0]['total'] if result else 0)
" 2>/dev/null)
    
    echo "   Recent events (1h): $RECENT_EVENTS"
else
    echo -e "   ${COLOR_RED}❌ PostgreSQL is DOWN${COLOR_RESET}"
fi

# 5. Stream Activity Monitor
echo -e "\n${COLOR_BLUE}5️⃣  Stream Activity (last 5 minutes)${COLOR_RESET}"
echo "   Checking for recent activity..."

# Count events in last 5 min by checking stream lengths and comparing with stored baseline
docker exec core_redis redis-cli --scan --pattern "vitruvyan:*" | head -10 | while read stream; do
    LEN=$(docker exec core_redis redis-cli XLEN "$stream" 2>/dev/null || echo "0")
    if [ "$LEN" -gt 0 ]; then
        echo "   • $stream: $LEN events in buffer"
    fi
done

# 6. Monitoring URLs
echo -e "\n${COLOR_BLUE}6️⃣  Monitoring Endpoints${COLOR_RESET}"
echo "   • Redis Exporter: http://localhost:9121/metrics"
echo "   • Redis Streams Exporter: http://localhost:9122/metrics"
echo "   • Grafana: http://localhost:3003/ (if enabled)"
echo "   • Prometheus: http://localhost:9090/ (if enabled)"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$UNHEALTHY" -eq 0 ]; then
    echo -e "  ${COLOR_GREEN}✅ SYNAPTIC CONCLAVE: HEALTHY${COLOR_RESET}"
else
    echo -e "  ${COLOR_RED}⚠️  SYNAPTIC CONCLAVE: $UNHEALTHY ISSUES DETECTED${COLOR_RESET}"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 For detailed metrics: docker logs core_redis_streams_exporter --tail=50"
echo "🔍 For listener logs: docker logs <listener_container> --tail=50"
echo ""
