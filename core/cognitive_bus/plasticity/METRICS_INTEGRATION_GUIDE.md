"""
Plasticity Metrics Integration Guide
=====================================

This file documents how to integrate Prometheus metrics into the plasticity system.

Phase 6: Plasticity System (Jan 24, 2026)

INTEGRATION POINTS:

1. PlasticityManager (core/cognitive_bus/plasticity/manager.py)
   - Import: from core.cognitive_bus.plasticity import metrics as plasticity_metrics
   
   - In propose_adjustment():
     * On success: plasticity_metrics.record_adjustment(consumer, parameter, delta, reason, applied=True)
     * On rejection: plasticity_metrics.record_adjustment(consumer, parameter, delta, reason, applied=False)
     * Update state: plasticity_metrics.update_parameter_state(consumer, parameter, value, min, max, disabled)
   
   - In rollback():
     * plasticity_metrics.record_rollback(consumer, parameter, steps)
     * plasticity_metrics.update_parameter_state(consumer, parameter, value, min, max, disabled)
   
   - In disable_plasticity()/enable_plasticity():
     * plasticity_metrics.update_consumer_parameters(consumer, adjustable_count, disabled_count)

2. OutcomeTracker (core/cognitive_bus/plasticity/outcome_tracker.py)
   - Import: from core.cognitive_bus.plasticity import metrics as plasticity_metrics
   
   - In record_outcome():
     * plasticity_metrics.record_outcome(consumer, parameter, outcome_type, outcome_value)
   
   - In get_success_rate():
     * plasticity_metrics.update_success_rate(consumer, parameter, success_rate)

3. LearningLoop (core/cognitive_bus/plasticity/learning_loop.py)
   - Import: from core.cognitive_bus.plasticity import metrics as plasticity_metrics
   - Import: import time
   
   - In _analyze_and_adapt():
     * start_time = time.time()
     * ... analysis logic ...
     * duration = time.time() - start_time
     * plasticity_metrics.record_learning_cycle(duration, proposed, applied, rejected)

PROMETHEUS QUERIES (for Grafana):

# Adjustment rate (per consumer)
rate(vitruvyan_plasticity_adjustment_total[5m])

# Rejection rate (should be low)
rate(vitruvyan_plasticity_adjustment_rejected_total[5m]) / 
  (rate(vitruvyan_plasticity_adjustment_total[5m]) + 
   rate(vitruvyan_plasticity_adjustment_rejected_total[5m]))

# Success rate (current)
vitruvyan_plasticity_success_rate

# Learning cycle duration (P95)
histogram_quantile(0.95, 
  rate(vitruvyan_plasticity_learning_cycle_duration_seconds_bucket[5m]))

# Parameter trends
vitruvyan_plasticity_parameter_value{consumer="NarrativeEngine", parameter="confidence_threshold"}

# Rollback rate (should be very low)
rate(vitruvyan_plasticity_rollback_total[1h])

# Error rate
rate(vitruvyan_plasticity_errors_total[5m])

GRAFANA DASHBOARD PANELS:

1. Adjustment Activity
   - Counter: Total adjustments (last 24h)
   - Graph: Adjustment rate over time (per consumer)
   - Stat: Rejection rate (should be <5%)

2. Success Rates
   - Gauge: Current success rate per consumer+parameter
   - Graph: Success rate trend over time

3. Learning Cycles
   - Counter: Total cycles (last 24h)
   - Graph: Cycle duration (P50, P95, P99)
   - Table: Last cycle results (proposed/applied/rejected)

4. Parameter Values
   - Graph: Parameter value over time (per consumer)
   - Table: Current values vs bounds (min/max)

5. Errors & Rollbacks
   - Counter: Total errors (last 24h)
   - Counter: Total rollbacks (last 24h)
   - Table: Recent errors by operation

ALERTING RULES:

# High rejection rate (>20%)
- alert: PlasticityHighRejectionRate
  expr: |
    rate(vitruvyan_plasticity_adjustment_rejected_total[5m]) / 
    (rate(vitruvyan_plasticity_adjustment_total[5m]) + 
     rate(vitruvyan_plasticity_adjustment_rejected_total[5m])) > 0.2
  for: 10m
  annotations:
    summary: "High plasticity adjustment rejection rate"

# Low success rate (<30%)
- alert: PlasticityLowSuccessRate
  expr: vitruvyan_plasticity_success_rate < 0.3
  for: 1h
  annotations:
    summary: "Low success rate detected for {{ $labels.consumer }}.{{ $labels.parameter }}"

# Frequent rollbacks (>5 per hour)
- alert: PlasticityFrequentRollbacks
  expr: rate(vitruvyan_plasticity_rollback_total[1h]) > 5
  for: 2h
  annotations:
    summary: "Frequent rollbacks for {{ $labels.consumer }}"

# Learning cycle errors
- alert: PlasticityLearningCycleErrors
  expr: rate(vitruvyan_plasticity_errors_total{operation="learning_cycle"}[5m]) > 0
  for: 10m
  annotations:
    summary: "Learning cycle errors detected"

# Long learning cycles (>60s)
- alert: PlasticitySlowLearningCycle
  expr: |
    histogram_quantile(0.95, 
      rate(vitruvyan_plasticity_learning_cycle_duration_seconds_bucket[5m])) > 60
  for: 30m
  annotations:
    summary: "Learning cycles taking >60s (P95)"

IMPLEMENTATION CHECKLIST:

[ ] 1. Metrics module created (metrics.py) ✅
[ ] 2. Import metrics in PlasticityManager
[ ] 3. Record adjustments (applied + rejected)
[ ] 4. Record rollbacks
[ ] 5. Update parameter state after changes
[ ] 6. Update consumer-level counts (adjustable/disabled)
[ ] 7. Import metrics in OutcomeTracker
[ ] 8. Record outcomes
[ ] 9. Update success rates
[ ] 10. Import metrics in LearningLoop
[ ] 11. Time learning cycles
[ ] 12. Record cycle results
[ ] 13. Export metrics in __init__.py
[ ] 14. Test metrics endpoint (/metrics)
[ ] 15. Create Grafana dashboard (Phase 7)
[ ] 16. Configure alerting rules (Phase 7)

TESTING COMMANDS:

# Check metrics endpoint
curl http://localhost:8004/metrics | grep plasticity

# Verify metric updates (after adjustment)
curl http://localhost:8004/metrics | grep vitruvyan_plasticity_adjustment_total

# Verify success rate updates
curl http://localhost:8004/metrics | grep vitruvyan_plasticity_success_rate

# Verify learning cycle metrics
curl http://localhost:8004/metrics | grep vitruvyan_plasticity_learning_cycle
"""
