#!/bin/bash
# 03_screen_filters.sh
# Test screening with group filters (stratification)
#
# Usage: ./03_screen_filters.sh
# Expected: Entities filtered by group="GroupA", then ranked

echo "🧠 Neural Engine Screening with Group Filter"
echo "=============================================="

curl -s -X POST http://localhost:9003/screen \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "balanced",
    "top_k": 5,
    "filters": {
      "group": "GroupA"
    },
    "stratification_mode": "stratified"
  }' | jq '.ranked_entities[] | {rank, entity_id, group, composite_score}'

# Alternative: Filter by multiple criteria
# "filters": {"group": "GroupA", "min_volatility": 0.5}

# Alternative: Show stratification metadata
# ... | jq '.metadata.stratification'
