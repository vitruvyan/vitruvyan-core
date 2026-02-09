#!/bin/bash
# Pattern Weavers Service Startup Script
# Starts both API service and Redis listener

set -e

export PYTHONUNBUFFERED=1

echo "🕸️ Starting Pattern Weavers Services..."
echo "=========================================="

# Start Redis listener in background with explicit output
echo "Starting Redis Cognitive Bus listener..."
python3 -u -c "from core.pattern_weavers.redis_listener import main; main()" 2>&1 &
LISTENER_PID=$!

# Give listener time to connect
sleep 2

# Start API service
echo "Starting FastAPI service on port 8017..."
python3 -m uvicorn docker.services.api_pattern_weavers.main:app --host 0.0.0.0 --port 8017 &
API_PID=$!

# Wait for both processes
echo "✅ Pattern Weavers services started"
echo "   API PID: $API_PID"
echo "   Listener PID: $LISTENER_PID"

# Trap signals to shutdown gracefully
trap "kill $LISTENER_PID $API_PID; exit" SIGINT SIGTERM

# Wait for either process to exit
wait -n

# If one exits, kill the other
kill $LISTENER_PID $API_PID 2>/dev/null || true
