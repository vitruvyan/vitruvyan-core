#!/bin/bash
# 01_health_check.sh
# Test Orthodoxy Wardens health endpoint
# 
# Usage: ./01_health_check.sh
# Expected: HTTP 200, sacred_status, blessing_level, listeners active

echo "🏛️ Orthodoxy Wardens Health Check"
echo "==================================="

curl -s http://localhost:9006/divine-health | jq '.'

# Alternative: Check only blessing level
# curl -s http://localhost:9006/divine-health | jq -r '.blessing_level'

# Alternative: Check Synaptic Conclave listeners
# curl -s http://localhost:9006/divine-health | jq '.synaptic_conclave'
