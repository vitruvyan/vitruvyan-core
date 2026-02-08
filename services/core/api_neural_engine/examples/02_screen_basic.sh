#!/bin/bash
# Basic Screening Example
# Multi-factor screening with balanced profile

set -e

BASE_URL="${BASE_URL:-http://localhost:8003}"

echo "🔬 Testing Basic Screening..."
echo "Profile: balanced"
echo "Top K: 5"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "top_k": 5
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo "✅ Screening completed (HTTP $http_code)"
    echo ""
    
    # Extract summary
    total=$(echo "$body" | jq -r '.total_entities_evaluated')
    processing_time=$(echo "$body" | jq -r '.processing_time_ms')
    
    echo "📊 Summary:"
    echo "   - Total entities evaluated: $total"
    echo "   - Processing time: ${processing_time}ms"
    echo ""
    echo "🏆 Top 5 Ranked Entities:"
    echo "$body" | jq '.ranked_entities[] | "   \(.rank). \(.entity_id) (composite: \(.composite_score | tonumber | . * 100 | round / 100), percentile: \(.percentile | tonumber | . * 100 | round / 100)%)"' -r
    
    echo ""
    echo "📈 Full Response:"
    echo "$body" | jq '.'
else
    echo "❌ Screening failed (HTTP $http_code)"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    exit 1
fi
