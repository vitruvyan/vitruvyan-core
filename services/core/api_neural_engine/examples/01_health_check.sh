#!/bin/bash
# 01_health_check.sh
# Test Neural Engine health endpoint
# 
# Usage: ./01_health_check.sh
# Expected: HTTP 200, status="healthy"

echo "🧠 Neural Engine Health Check"
echo "=============================="

curl -s http://localhost:9003/health | jq '.'

# Alternative: Check only status field
# curl -s http://localhost:9003/health | jq -r '.status'
