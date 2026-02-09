#!/bin/bash
# 06_prometheus_metrics.sh
# Test Prometheus metrics endpoint
#
# Usage: ./06_prometheus_metrics.sh
# Expected: Prometheus-formatted metrics (counters, histograms, gauges)

echo "🧠 Neural Engine Prometheus Metrics"
echo "===================================="

# Get all metrics
curl -s http://localhost:9003/metrics

echo ""
echo ""
echo "📊 Filtered Neural Engine Metrics:"
echo "=================================="

# Filter only neural_engine_* metrics
curl -s http://localhost:9003/metrics | grep "^neural_engine_"

# Alternative: Show only screening metrics
# curl -s http://localhost:9003/metrics | grep "screening"

# Alternative: Show only HTTP request metrics
# curl -s http://localhost:9003/metrics | grep "http_request"
