#!/bin/bash
# Neural Engine Health Check Example
# Tests service health and dependency status

set -e

BASE_URL="${BASE_URL:-http://localhost:8003}"

echo "🔍 Testing Neural Engine Health..."
echo "Endpoint: ${BASE_URL}/health"
echo ""

response=$(curl -s -w "\n%{http_code}" "${BASE_URL}/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo "✅ Service is healthy (HTTP $http_code)"
    echo ""
    echo "Response:"
    echo "$body" | jq '.'
    
    # Extract key info
    status=$(echo "$body" | jq -r '.status')
    orchestrator=$(echo "$body" | jq -r '.dependencies.orchestrator')
    data_provider=$(echo "$body" | jq -r '.dependencies.data_provider')
    scoring_strategy=$(echo "$body" | jq -r '.dependencies.scoring_strategy')
    
    echo ""
    echo "📊 Service Status: $status"
    echo "   - Orchestrator: $orchestrator"
    echo "   - Data Provider: $data_provider"
    echo "   - Scoring Strategy: $scoring_strategy"
else
    echo "❌ Service unhealthy (HTTP $http_code)"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    exit 1
fi
