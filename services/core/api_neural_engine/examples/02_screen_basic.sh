#!/bin/bash
# 02_screen_basic.sh
# Test basic screening with balanced profile
#
# Usage: ./02_screen_basic.sh
# Expected: 5 entities ranked by composite score

echo "🧠 Neural Engine Basic Screening (Balanced Profile)"
echo "====================================================="

curl -s -X POST http://localhost:9003/screen \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "top_k": 5,
    "stratification_mode": "global"
  }' | jq '.ranked_entities[] | {rank, entity_id, composite_score, percentile}'

# Alternative: Show only top 3
# ... | jq '.ranked_entities[:3]'

# Alternative: Show full response with metadata
# ... | jq '.'
