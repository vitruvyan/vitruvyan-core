#!/bin/bash
#
# Grafana Dashboard Quick Test — Verify All Metrics
# Tests all critical metrics used by Synaptic Bus dashboards
#

set -e

CONCLAVE_URL="http://localhost:9012"
EXPORTER_URL="http://localhost:9122"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Grafana Dashboard Metrics Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test Conclave API
echo -e "${YELLOW}📡 Testing Conclave API (port 9012)...${NC}"
if curl -s -f "$CONCLAVE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Conclave API reachable${NC}"
else
    echo -e "${RED}❌ Conclave API unreachable${NC}"
    exit 1
fi

# Test Redis Exporter
echo -e "${YELLOW}📊 Testing Redis Streams Exporter (port 9122)...${NC}"
if curl -s -f "$EXPORTER_URL/metrics" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis Exporter reachable${NC}"
else
    echo -e "${RED}❌ Redis Exporter unreachable${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Critical Metrics Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 1: Bus Health Score (Cognitive Stability Index panel)
echo -e "${YELLOW}Test 1: Bus Health Score${NC}"
BUS_HEALTH=$(curl -s "$CONCLAVE_URL/metrics" | grep "^bus_health_score{" | head -1 | awk '{print $2}')
if [ -n "$BUS_HEALTH" ]; then
    echo -e "${GREEN}✅ bus_health_score = $BUS_HEALTH${NC}"
    echo "   Components:"
    curl -s "$CONCLAVE_URL/metrics" | grep "^bus_health_score{" | head -6
else
    echo -e "${RED}❌ bus_health_score missing${NC}"
fi

# Test 2: Sacred Order Activity
echo -e "${YELLOW}Test 2: Sacred Order Activity${NC}"
SACRED_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "^sacred_order_activity{" | wc -l)
if [ "$SACRED_COUNT" -ge 6 ]; then
    echo -e "${GREEN}✅ $SACRED_COUNT Sacred Orders active${NC}"
    curl -s "$EXPORTER_URL/metrics" | grep "^sacred_order_activity{" | head -7
else
    echo -e "${RED}❌ Only $SACRED_COUNT Sacred Orders found (expected 6+)${NC}"
fi

echo ""

# Test 3: Stream Lengths  
echo -e "${YELLOW}Test 3: Active Streams${NC}"
STREAM_COUNT=$(curl -s "$EXPORTER_URL/metrics" | grep "^stream_length{" | wc -l)
if [ "$STREAM_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ $STREAM_COUNT streams active${NC}"
    echo "Top 5 streams by size:"
    curl -s "$EXPORTER_URL/metrics" | grep "^stream_length{" | sort -t' ' -k2 -nr | head -5
else
    echo -e "${RED}❌ Only $STREAM_COUNT streams found${NC}"
fi

echo ""

# Test 4: Consumer Groups
echo -e "${YELLOW}Test 4: Consumer Groups${NC}"
CONSUMER_GROUPS=$(curl -s "$EXPORTER_URL/metrics" | grep "stream_consumer_lag{" | grep -o 'consumer_group="[^"]*"' | sort -u | wc -l)
if [ "$CONSUMER_GROUPS" -ge 5 ]; then
    echo -e "${GREEN}✅ $CONSUMER_GROUPS consumer groups active${NC}"
    curl -s "$EXPORTER_URL/metrics" | grep "stream_consumer_lag{" | grep -o 'consumer_group="[^"]*"' | sort -u
else
    echo -e "${RED}❌ Only $CONSUMER_GROUPS consumer groups found${NC}"
fi

echo ""

# Test 5: Event Emission (Scribe Writes)
echo -e "${YELLOW}Test 5: Scribe Write Total (API Emission)${NC}"
SCRIBE_TOTAL=$(curl -s "$CONCLAVE_URL/metrics" | grep "^scribe_write_total{" | awk '{sum+=$2} END {print sum}')
if [ -n "$SCRIBE_TOTAL" ] && [ "$SCRIBE_TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✅ scribe_write_total = $SCRIBE_TOTAL events${NC}"
else
    echo -e "${YELLOW}⚠️  scribe_write_total = 0 (simulator not running?)${NC}"
fi

echo ""

# Test 6: Cognitive Bus Events Total
echo -e "${YELLOW}Test 6: Cognitive Bus Events Total${NC}"
COG_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "^cognitive_bus_events_total{" | awk '{sum+=$2} END {print sum}')
if [ -n "$COG_TOTAL" ] && [ "$COG_TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✅ cognitive_bus_events_total = $COG_TOTAL events${NC}"
else
    echo -e "${RED}❌ cognitive_bus_events_total missing or zero${NC}"
fi

echo ""

# Test 7: Listener Consumed Total
echo -e "${YELLOW}Test 7: Listener Consumption${NC}"
LISTENER_TOTAL=$(curl -s "$EXPORTER_URL/metrics" | grep "^listener_consumed_total{" | awk '{sum+=$2} END {print sum}')
if [ -n "$LISTENER_TOTAL" ] && [ "$LISTENER_TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✅ listener_consumed_total = $LISTENER_TOTAL events${NC}"
else
    echo -e "${YELLOW}⚠️  listener_consumed_total = 0 (no active listeners?)${NC}"
fi

echo ""

# Test 8: Consumer Lag Health Check
echo -e "${YELLOW}Test 8: Consumer Lag Health${NC}"
BAD_LAG=$(curl -s "$EXPORTER_URL/metrics" | grep "^stream_consumer_lag{" | grep -v "0\.0$" | grep -E "e\\+0[0-9]{2}" | wc -l)
if [ "$BAD_LAG" -eq 0 ]; then
    echo -e "${GREEN}✅ All consumer lags are healthy${NC}"
else
    echo -e "${RED}❌ $BAD_LAG consumer groups have invalid lag values${NC}"
    echo "Affected groups:"
    curl -s "$EXPORTER_URL/metrics" | grep "^stream_consumer_lag{" | grep -v "0\.0$" | grep -E "e\\+0[0-9]{2}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Calculate pass rate
TESTS_PASSED=0
TEST_TOTAL=8

if [ -n "$BUS_HEALTH" ]; then ((TESTS_PASSED++)); fi
if [ "$SACRED_COUNT" -ge 6 ]; then ((TESTS_PASSED++)); fi
if [ "$STREAM_COUNT" -ge 10 ]; then ((TESTS_PASSED++)); fi
if [ "$CONSUMER_GROUPS" -ge 5 ]; then ((TESTS_PASSED++)); fi
if [ -n "$SCRIBE_TOTAL" ] && [ "$SCRIBE_TOTAL" -gt 0 ]; then ((TESTS_PASSED++)); fi
if [ -n "$COG_TOTAL" ] && [ "$COG_TOTAL" -gt 0 ]; then ((TESTS_PASSED++)); fi
if [ -n "$LISTENER_TOTAL" ] && [ "$LISTENER_TOTAL" -gt 0 ]; then ((TESTS_PASSED++)); fi
if [ "$BAD_LAG" -eq 0 ]; then ((TESTS_PASSED++)); fi

PASS_RATE=$((TESTS_PASSED * 100 / TEST_TOTAL))

if [ "$PASS_RATE" -ge 80 ]; then
    echo -e "${GREEN}✅ $TESTS_PASSED/$TEST_TOTAL tests passed ($PASS_RATE%)${NC}"
    echo -e "${GREEN}   Dashboard metrics are healthy!${NC}"
elif [ "$PASS_RATE" -ge 50 ]; then
    echo -e "${YELLOW}⚠️  $TESTS_PASSED/$TEST_TOTAL tests passed ($PASS_RATE%)${NC}"
    echo -e "${YELLOW}   Some dashboard panels may have issues${NC}"
else
    echo -e "${RED}❌ $TESTS_PASSED/$TEST_TOTAL tests passed ($PASS_RATE%)${NC}"
    echo -e "${RED}   Dashboard metrics need attention${NC}"
fi

echo ""
echo -e "${BLUE}📖 See full report: ${NC}docs/GRAFANA_DASHBOARD_DIAGNOSTICS_FEB16_2026.md"
echo ""
