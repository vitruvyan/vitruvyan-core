#!/bin/bash
# Single Feature Ranking Example
# Rank entities by momentum feature (z-score)

set -e

BASE_URL="${BASE_URL:-http://localhost:8003}"

echo "📊 Testing Single Feature Ranking..."
echo "Feature: momentum"
echo "Top K: 5"
echo "Higher is better: true"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "momentum",
    "top_k": 5,
    "higher_is_better": true
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo "✅ Ranking completed (HTTP $http_code)"
    echo ""
    
    # Extract summary
    feature=$(echo "$body" | jq -r '.feature_name')
    total=$(echo "$body" | jq -r '.total_entities_ranked')
    processing_time=$(echo "$body" | jq -r '.processing_time_ms')
    
    echo "📊 Summary:"
    echo "   - Feature: $feature"
    echo "   - Total entities ranked: $total"
    echo "   - Processing time: ${processing_time}ms"
    echo ""
    echo "🏆 Top 5 by Momentum Z-Score:"
    echo "$body" | jq '.ranked_entities[] | "   \(.rank). \(.entity_id) (z-score: \(.z_scores.momentum | tonumber | . * 100 | round / 100), percentile: \(.percentile | tonumber | . * 100 | round / 100)%)"' -r
    
    echo ""
    echo "📈 Full Response:"
    echo "$body" | jq '.'
else
    echo "❌ Ranking failed (HTTP $http_code)"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    exit 1
fi
