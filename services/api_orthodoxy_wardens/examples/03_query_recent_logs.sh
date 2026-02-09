#!/bin/bash
# 03_query_recent_logs.sh
# Query recent audit logs from PostgreSQL
#
# Usage: ./03_query_recent_logs.sh
# Expected: Last 10 audit events with event_type, service, status

echo "🏛️ Orthodoxy Wardens - Recent Audit Logs"
echo "=========================================="

curl -s "http://localhost:9006/sacred-records/recent?limit=10" | jq '.sacred_confessions[] | {timestamp: .created_at, event_type, service, status: .sacred_status}'

# Alternative: Filter by event type
# curl -s "http://localhost:9006/sacred-records/recent?event_type=audit_completed&limit=5"

# Alternative: Filter by service
# curl -s "http://localhost:9006/sacred-records/recent?service=neural_engine&limit=5"

# Alternative: Show full log details
# curl -s "http://localhost:9006/sacred-records/recent?limit=10" | jq '.'
