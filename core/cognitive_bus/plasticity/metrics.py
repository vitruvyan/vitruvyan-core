"""
📊 Plasticity Metrics Module

Epistemic Order: LEARNING (Observability)

Prometheus metrics for plasticity system operations.
Tracks parameter adjustments, rollbacks, success rates, and learning cycles.

Phase 6: Plasticity System (Jan 24, 2026)

Metrics:
- plasticity_adjustment_total: Total parameter adjustments (applied)
- plasticity_adjustment_rejected_total: Rejected adjustments (out of bounds, disabled)
- plasticity_rollback_total: Total rollback operations
- plasticity_success_rate: Current success rate per consumer+parameter
- plasticity_learning_cycle_duration_seconds: Learning loop cycle duration
- plasticity_learning_cycles_total: Total learning cycles executed
- plasticity_parameters_adjustable: Number of adjustable parameters per consumer
- plasticity_parameters_disabled: Number of disabled parameters per consumer
- plasticity_outcome_recorded_total: Total outcomes recorded
- plasticity_adjustment_delta: Delta value of last adjustment (for trend analysis)
"""

from prometheus_client import Counter, Gauge, Histogram

# ========== ADJUSTMENT METRICS ==========

plasticity_adjustment_total = Counter(
    'vitruvyan_plasticity_adjustment_total',
    'Total number of parameter adjustments applied',
    ['consumer', 'parameter', 'reason']
)

plasticity_adjustment_rejected_total = Counter(
    'vitruvyan_plasticity_adjustment_rejected_total',
    'Total number of parameter adjustments rejected',
    ['consumer', 'parameter', 'reason']
)

plasticity_adjustment_delta = Gauge(
    'vitruvyan_plasticity_adjustment_delta',
    'Delta value of last adjustment (for trend analysis)',
    ['consumer', 'parameter']
)

# ========== ROLLBACK METRICS ==========

plasticity_rollback_total = Counter(
    'vitruvyan_plasticity_rollback_total',
    'Total number of rollback operations',
    ['consumer', 'parameter', 'steps']
)

# ========== SUCCESS RATE METRICS ==========

plasticity_success_rate = Gauge(
    'vitruvyan_plasticity_success_rate',
    'Current success rate (0.0-1.0) for consumer+parameter',
    ['consumer', 'parameter']
)

plasticity_outcome_recorded_total = Counter(
    'vitruvyan_plasticity_outcome_recorded_total',
    'Total number of outcomes recorded',
    ['consumer', 'parameter', 'outcome_type']
)

# ========== LEARNING LOOP METRICS ==========

plasticity_learning_cycle_duration_seconds = Histogram(
    'vitruvyan_plasticity_learning_cycle_duration_seconds',
    'Time taken to complete a learning cycle (analysis + adaptation)',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

plasticity_learning_cycles_total = Counter(
    'vitruvyan_plasticity_learning_cycles_total',
    'Total number of learning cycles executed'
)

plasticity_learning_cycle_adjustments = Gauge(
    'vitruvyan_plasticity_learning_cycle_adjustments',
    'Number of adjustments in last learning cycle',
    ['status']  # 'proposed', 'applied', 'rejected'
)

# ========== PARAMETER STATE METRICS ==========

plasticity_parameters_adjustable = Gauge(
    'vitruvyan_plasticity_parameters_adjustable',
    'Number of adjustable parameters per consumer',
    ['consumer']
)

plasticity_parameters_disabled = Gauge(
    'vitruvyan_plasticity_parameters_disabled',
    'Number of disabled parameters per consumer',
    ['consumer']
)

plasticity_parameter_value = Gauge(
    'vitruvyan_plasticity_parameter_value',
    'Current value of adjustable parameter',
    ['consumer', 'parameter']
)

plasticity_parameter_bounds = Gauge(
    'vitruvyan_plasticity_parameter_bounds',
    'Parameter bounds (min/max)',
    ['consumer', 'parameter', 'bound_type']  # 'min' or 'max'
)

# ========== ERROR METRICS ==========

plasticity_errors_total = Counter(
    'vitruvyan_plasticity_errors_total',
    'Total plasticity operation errors',
    ['operation', 'error_type']
)


# ========== HELPER FUNCTIONS ==========

def record_adjustment(consumer: str, parameter: str, delta: float, reason: str, applied: bool):
    """
    Record adjustment metrics.
    
    Args:
        consumer: Consumer name
        parameter: Parameter name
        delta: Adjustment delta
        reason: Reason for adjustment
        applied: True if applied, False if rejected
    """
    if applied:
        plasticity_adjustment_total.labels(
            consumer=consumer,
            parameter=parameter,
            reason=reason
        ).inc()
        plasticity_adjustment_delta.labels(
            consumer=consumer,
            parameter=parameter
        ).set(delta)
    else:
        plasticity_adjustment_rejected_total.labels(
            consumer=consumer,
            parameter=parameter,
            reason=reason
        ).inc()


def record_rollback(consumer: str, parameter: str, steps: int):
    """
    Record rollback metrics.
    
    Args:
        consumer: Consumer name
        parameter: Parameter name
        steps: Number of steps rolled back
    """
    plasticity_rollback_total.labels(
        consumer=consumer,
        parameter=parameter,
        steps=str(steps)
    ).inc()


def record_outcome(consumer: str, parameter: str, outcome_type: str, outcome_value: float):
    """
    Record outcome metrics.
    
    Args:
        consumer: Consumer name
        parameter: Parameter name (can be None)
        outcome_type: Type of outcome
        outcome_value: Outcome value (0.0-1.0)
    """
    param_label = parameter if parameter else "all"
    
    plasticity_outcome_recorded_total.labels(
        consumer=consumer,
        parameter=param_label,
        outcome_type=outcome_type
    ).inc()


def update_success_rate(consumer: str, parameter: str, success_rate: float):
    """
    Update success rate gauge.
    
    Args:
        consumer: Consumer name
        parameter: Parameter name
        success_rate: Current success rate (0.0-1.0)
    """
    plasticity_success_rate.labels(
        consumer=consumer,
        parameter=parameter
    ).set(success_rate)


def update_parameter_state(consumer: str, parameter: str, value: float, 
                          min_value: float, max_value: float, disabled: bool):
    """
    Update parameter state metrics.
    
    Args:
        consumer: Consumer name
        parameter: Parameter name
        value: Current parameter value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        disabled: True if plasticity disabled for this parameter
    """
    plasticity_parameter_value.labels(
        consumer=consumer,
        parameter=parameter
    ).set(value)
    
    plasticity_parameter_bounds.labels(
        consumer=consumer,
        parameter=parameter,
        bound_type='min'
    ).set(min_value)
    
    plasticity_parameter_bounds.labels(
        consumer=consumer,
        parameter=parameter,
        bound_type='max'
    ).set(max_value)


def update_consumer_parameters(consumer: str, adjustable_count: int, disabled_count: int):
    """
    Update consumer-level parameter counts.
    
    Args:
        consumer: Consumer name
        adjustable_count: Number of adjustable parameters
        disabled_count: Number of disabled parameters
    """
    plasticity_parameters_adjustable.labels(
        consumer=consumer
    ).set(adjustable_count)
    
    plasticity_parameters_disabled.labels(
        consumer=consumer
    ).set(disabled_count)


def record_learning_cycle(duration_seconds: float, adjustments_proposed: int,
                          adjustments_applied: int, adjustments_rejected: int):
    """
    Record learning cycle metrics.
    
    Args:
        duration_seconds: Cycle duration
        adjustments_proposed: Total adjustments proposed
        adjustments_applied: Adjustments successfully applied
        adjustments_rejected: Adjustments rejected
    """
    plasticity_learning_cycle_duration_seconds.observe(duration_seconds)
    plasticity_learning_cycles_total.inc()
    
    plasticity_learning_cycle_adjustments.labels(status='proposed').set(adjustments_proposed)
    plasticity_learning_cycle_adjustments.labels(status='applied').set(adjustments_applied)
    plasticity_learning_cycle_adjustments.labels(status='rejected').set(adjustments_rejected)


def record_error(operation: str, error_type: str):
    """
    Record plasticity operation error.
    
    Args:
        operation: Operation type ('adjustment', 'rollback', 'outcome_tracking', 'learning_cycle')
        error_type: Error type (e.g., 'database_error', 'invalid_parameter', 'bounds_violation')
    """
    plasticity_errors_total.labels(
        operation=operation,
        error_type=error_type
    ).inc()
