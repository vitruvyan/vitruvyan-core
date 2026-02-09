#!/bin/bash
# 04_rank_by_feature.sh
# Test single-feature ranking (no profile weighting)
#
# Usage: ./04_rank_by_feature.sh
# Expected: Entities ranked by momentum feature only

echo "🧠 Neural Engine Single-Feature Ranking (Momentum)"
echo "===================================================="

curl -s -X POST http://localhost:9003/rank \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "momentum",
    "top_k": 5,
    "higher_is_better": true
  }' | jq '.ranked_entities[] | {rank, entity_id, raw_value, z_score}'

# Alternative: Rank by different feature
# "feature_name": "trend"
# "feature_name": "volatility"

# Alternative: Lower is better (for risk metrics)
# "higher_is_better": false
