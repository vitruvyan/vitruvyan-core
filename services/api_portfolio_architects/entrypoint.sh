#!/bin/bash
# Portfolio Architects Multi-Service Entrypoint
# Starts both API service and Guardian Scheduler Agent

set -e

echo "🚀 Starting Portfolio Architects Services..."

# Start Guardian Scheduler in background
echo "🛡️ Starting Guardian Scheduler Agent..."
python3 -m domains.finance.portfolio_architects.agents.guardian_scheduler_agent &
GUARDIAN_PID=$!
echo "✅ Guardian Scheduler started (PID: $GUARDIAN_PID)"

# Start Learning Profile updater in background (optional)
LEARNING_PID=""
if [ "${LEARNING_PROFILE_UPDATER_ENABLED:-1}" != "0" ]; then
  echo "🧠 Starting Learning Profile Worker..."
  python3 -m api_portfolio_architects.learning_profile_worker &
  LEARNING_PID=$!
  echo "✅ Learning Profile Worker started (PID: $LEARNING_PID)"
else
  echo "🧠 Learning Profile Worker disabled"
fi

# Wait for Guardian to initialize
sleep 3

# Start API service in foreground
echo "🌐 Starting FastAPI service on port 8021..."
uvicorn api_portfolio_architects.main:app --host 0.0.0.0 --port 8021 &
API_PID=$!
echo "✅ API service started (PID: $API_PID)"

# Trap SIGTERM/SIGINT for graceful shutdown
_term() {
    echo "🛑 Received shutdown signal, stopping services..."
    kill -TERM "$GUARDIAN_PID" 2>/dev/null || true
    kill -TERM "$API_PID" 2>/dev/null || true
    if [ -n "$LEARNING_PID" ]; then
      kill -TERM "$LEARNING_PID" 2>/dev/null || true
      wait "$LEARNING_PID" 2>/dev/null || true
    fi
    wait "$GUARDIAN_PID" "$API_PID"
    echo "✅ Services stopped gracefully"
    exit 0
}

trap _term SIGTERM SIGINT

# Keep container running and monitor processes
echo "✅ Portfolio Architects services ready"
echo "   - API: http://localhost:8021"
echo "   - Guardian Metrics: http://localhost:8022"

# Wait for active processes
if [ -n "$LEARNING_PID" ]; then
  wait -n $GUARDIAN_PID $API_PID $LEARNING_PID
else
  wait -n $GUARDIAN_PID $API_PID
fi

# If one exits, kill the other
EXIT_CODE=$?
echo "⚠️ One service exited with code $EXIT_CODE, stopping remaining services..."
kill -TERM "$GUARDIAN_PID" "$API_PID" 2>/dev/null || true
if [ -n "$LEARNING_PID" ]; then
  kill -TERM "$LEARNING_PID" 2>/dev/null || true
  wait "$LEARNING_PID" 2>/dev/null || true
fi
wait "$GUARDIAN_PID" "$API_PID" 2>/dev/null || true

exit $EXIT_CODE
