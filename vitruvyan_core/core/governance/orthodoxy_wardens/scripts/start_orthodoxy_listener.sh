#!/bin/bash
# EPOCH V - Orthodoxy Adaptation Listener Startup Script

cd /home/caravaggio/vitruvyan
export PYTHONPATH=/home/caravaggio/vitruvyan

nohup python3 core/cognitive_bus/orthodoxy_adaptation_listener.py > logs/orthodoxy_listener.log 2>&1 &
PID=$!
echo "✅ Orthodoxy Listener started with PID: $PID"
echo $PID > logs/orthodoxy_listener.pid
