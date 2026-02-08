#!/bin/bash
# Screening with Filters Example
# Filter by group (GroupA) and use stratification

set -e

BASE_URL="${BASE_URL:-http://localhost:8003}"

echo "🔬 Testing Screening with Filters..."
echo "Profile: balanced"
echo "Filter: group = GroupA"
echo "Stratification: by_group"
echo "Top K: 5"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "filters": {
      "group": "GroupA"
    },
    "top_k": 5,
    "stratification_mode": "by_group"
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" -eq 200 ]; then
    echo "✅ Screening with filters completed (HTTP $http_code)"
    echo ""
    
    # Extract summary
    total=$(echo "$body" | jq -r '.total_entities_evaluated')
    processing_time=$(echo "$body" | jq -r '.processing_time_ms')
    
    echo "📊 Summary:"
    echo "   - Total entities evaluated: $total"
    echo "   - Processing time: ${processing_time}ms"
    echo "   - Filter applied: group=GroupA"
    echo ""
    echo "🏆 Top 5 Ranked Entities (GroupA only):"
    echo "$body" | jq '.ranked_entities[] | "   \(.rank). \(.entity_id) (bucket: \(.bucket), score: \(.composite_score | tonumber | . * 100 | round / 100))"' -r
    
    echo ""
    echo "📈 Profile Weights:"
    echo "$body" | jq '.profile_weights'
    
    echo ""
    echo "📈 Full Response:"
    echo "$body" | jq '.'
else
    echo "❌ Screening with filters failed (HTTP $http_code)"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    exit 1
fi
