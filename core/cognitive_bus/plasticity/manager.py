"""
Plasticity Manager — Governed Parameter Adjustments
===================================================

Manages bounded, auditable, reversible parameter adjustments for consumers.

Sacred Order: Truth (Governance Layer)

Key Principles:
1. All adjustments bounded by (min, max)
2. All adjustments logged as events
3. All adjustments reversible (rollback)
4. Adjustments require governance approval (optional)
5. No unbounded learning possible

Author: Vitruvyan Core Team
Date: January 24, 2026
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

from core.cognitive_bus.event_envelope import CognitiveEvent
from core.cognitive_bus.consumers.base_consumer import ProcessResult
from core.cognitive_bus.plasticity.outcome_tracker import OutcomeTracker
from core.cognitive_bus.plasticity import metrics as plasticity_metrics

logger = logging.getLogger(__name__)


@dataclass
class ParameterBounds:
    """
    Defines an adjustable parameter with safety bounds.
    
    Attributes:
        name: Parameter name (must match consumer attribute)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        step_size: Minimum adjustment increment (for discretization)
        default_value: Default/initial value
        description: Human-readable description
    """
    name: str
    min_value: float
    max_value: float
    step_size: float
    default_value: float
    description: str
    
    def __post_init__(self):
        """Validate bounds are sensible."""
        if self.min_value >= self.max_value:
            raise ValueError(
                f"Invalid bounds for {self.name}: "
                f"min ({self.min_value}) >= max ({self.max_value})"
            )
        
        if self.step_size <= 0:
            raise ValueError(
                f"Invalid step_size for {self.name}: {self.step_size} <= 0"
            )
        
        if not (self.min_value <= self.default_value <= self.max_value):
            raise ValueError(
                f"Default value {self.default_value} not in bounds "
                f"[{self.min_value}, {self.max_value}] for {self.name}"
            )


@dataclass
class Adjustment:
    """
    Record of a parameter adjustment.
    
    Immutable record for audit trail and rollback capability.
    """
    timestamp: datetime
    parameter: str
    old_value: float
    new_value: float
    reason: str
    success_rate: float        # Trigger metric (e.g., 0.85)
    event_id: str              # CognitiveEvent ID for adjustment
    
    @property
    def delta(self) -> float:
        """Calculate adjustment delta."""
        return self.new_value - self.old_value


class PlasticityManager:
    """
    Governed learning manager with bounded adjustments.
    
    Manages parameter tuning for a consumer with the following guarantees:
    - All adjustments stay within (min, max) bounds
    - All adjustments logged as CognitiveEvents
    - All adjustments reversible via rollback()
    - Governance approval optional (for CRITICAL consumers)
    - Plasticity can be disabled per-parameter
    
    Architecture:
        - Stateful history (List[Adjustment])
        - Bounded adjustments (ParameterBounds enforcement)
        - Event emission (plasticity.adjustment, plasticity.rollback)
        - Optional governance (require_approval flag)
    
    Usage:
        bounds = {
            "confidence_threshold": ParameterBounds(
                name="confidence_threshold",
                min_value=0.4,
                max_value=0.9,
                step_size=0.05,
                default_value=0.6,
                description="Minimum confidence for non-escalation"
            )
        }
        
        manager = PlasticityManager(
            consumer=narrative_engine,
            bounds=bounds,
            outcome_tracker=tracker,
            require_approval=False
        )
        
        # Propose adjustment
        result = await manager.propose_adjustment(
            parameter="confidence_threshold",
            delta=0.05,
            reason="Low success rate",
            success_rate=0.35
        )
        
        if result.action == "emit":
            print("Adjustment applied!")
        
        # Rollback if needed
        await manager.rollback(steps=1)
    """
    
    def __init__(
        self, 
        consumer: Any,  # BaseConsumer, but avoid circular import
        bounds: Dict[str, ParameterBounds],
        outcome_tracker: OutcomeTracker,
        require_approval: bool = False
    ):
        """
        Initialize plasticity manager.
        
        Args:
            consumer: Consumer instance (must have attributes matching bounds)
            bounds: Dict of parameter_name → ParameterBounds
            outcome_tracker: OutcomeTracker for learning feedback
            require_approval: If True, emit governance request instead of applying
        """
        self.consumer = consumer
        self.bounds = bounds
        self.tracker = outcome_tracker
        self.require_approval = require_approval
        self.history: List[Adjustment] = []
        self.disabled_parameters: Set[str] = set()
        
        logger.info(
            f"PlasticityManager initialized for {consumer.__class__.__name__} "
            f"({len(bounds)} adjustable parameters, approval={require_approval})"
        )
        
        # Initialize metrics
        self._update_consumer_metrics()
    
    async def propose_adjustment(
        self, 
        parameter: str, 
        delta: float,
        reason: str,
        success_rate: float
    ) -> ProcessResult:
        """
        Propose parameter adjustment.
        
        Validates bounds, applies adjustment, emits event.
        
        Args:
            parameter: Parameter name (must exist in self.bounds)
            delta: Adjustment amount (can be negative)
            reason: Human-readable reason for adjustment
            success_rate: Trigger metric (for audit)
        
        Returns:
            ProcessResult:
                - emit: Adjustment applied successfully
                - escalate: Adjustment requires governance approval
                - silence: Adjustment rejected (out of bounds or disabled)
        """
        # 1. Validate parameter exists
        if parameter not in self.bounds:
            logger.warning(
                f"⚠️ Unknown parameter: {parameter} (available: {list(self.bounds.keys())})"
            )
            plasticity_metrics.record_adjustment(
                consumer=self.consumer.__class__.__name__,
                parameter=parameter,
                delta=delta,
                reason="unknown_parameter",
                applied=False
            )
            return ProcessResult.silence()
        
        if parameter in self.disabled_parameters:
            logger.info(f"🚫 Plasticity disabled for {parameter}")
            plasticity_metrics.record_adjustment(
                consumer=self.consumer.__class__.__name__,
                parameter=parameter,
                delta=delta,
                reason="disabled",
                applied=False
            )
            return ProcessResult.silence()
        
        # 2. Calculate new value
        bound = self.bounds[parameter]
        
        if not hasattr(self.consumer, parameter):
            logger.error(
                f"❌ Consumer {self.consumer.__class__.__name__} "
                f"missing attribute: {parameter}"
            )
            return ProcessResult.silence()
        
        current = getattr(self.consumer, parameter)
        new_value = current + delta
        
        # Snap to step_size (discretize)
        new_value = round(new_value / bound.step_size) * bound.step_size
        
        # 3. Check bounds
        if not (bound.min_value <= new_value <= bound.max_value):
            logger.warning(
                f"⛔ Adjustment rejected: {self.consumer.__class__.__name__}.{parameter} "
                f"{current:.3f} → {new_value:.3f} out of bounds "
                f"[{bound.min_value}, {bound.max_value}]"
            )
            plasticity_metrics.record_adjustment(
                consumer=self.consumer.__class__.__name__,
                parameter=parameter,
                delta=delta,
                reason="out_of_bounds",
                applied=False
            )
            return ProcessResult.silence()
        
        # 4. Record adjustment
        adjustment = Adjustment(
            timestamp=datetime.utcnow(),
            parameter=parameter,
            old_value=current,
            new_value=new_value,
            reason=reason,
            success_rate=success_rate,
            event_id=str(uuid.uuid4())
        )
        self.history.append(adjustment)
        
        # 5. Apply adjustment
        setattr(self.consumer, parameter, new_value)
        
        # 5a. Record metrics
        plasticity_metrics.record_adjustment(
            consumer=self.consumer.__class__.__name__,
            parameter=parameter,
            delta=delta,
            reason=reason,
            applied=True
        )
        plasticity_metrics.update_parameter_state(
            consumer=self.consumer.__class__.__name__,
            parameter=parameter,
            value=new_value,
            min_value=bound.min_value,
            max_value=bound.max_value,
            disabled=False
        )
        
        # 6. Emit adjustment event
        event = CognitiveEvent(
            id=adjustment.event_id,
            type="plasticity.adjustment",
            correlation_id=str(uuid.uuid4()),
            causation_id="",
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source=self.consumer.__class__.__name__,
            payload={
                "parameter": parameter,
                "old_value": current,
                "new_value": new_value,
                "delta": delta,
                "actual_delta": new_value - current,  # After discretization
                "reason": reason,
                "success_rate": success_rate,
                "bounds": {
                    "min": bound.min_value,
                    "max": bound.max_value,
                    "step": bound.step_size
                },
                "description": bound.description
            },
            metadata={
                "require_approval": self.require_approval,
                "history_length": len(self.history)
            }
        )
        
        logger.info(
            f"✅ Plasticity adjustment applied: {self.consumer.__class__.__name__}.{parameter} "
            f"{current:.3f} → {new_value:.3f} (delta={delta:.3f}, reason={reason})"
        )
        
        # 7. Return result
        if self.require_approval:
            return ProcessResult.escalate(
                reason=(
                    f"Plasticity adjustment requires approval: "
                    f"{self.consumer.__class__.__name__}.{parameter} "
                    f"{current:.3f} → {new_value:.3f}"
                ),
                confidence=0.8
            )
        else:
            return ProcessResult.emit(event, confidence=1.0)
    
    async def rollback(self, steps: int = 1) -> ProcessResult:
        """
        Undo the last N adjustments.
        
        Restores exact previous values and emits rollback events.
        
        Args:
            steps: Number of adjustments to undo (default 1)
        
        Returns:
            ProcessResult with rollback events
        """
        if steps <= 0:
            logger.warning(f"Invalid rollback steps: {steps}")
            return ProcessResult.silence()
        
        rollback_events = []
        
        for _ in range(steps):
            if not self.history:
                logger.warning("No adjustments to rollback")
                break
            
            adj = self.history.pop()
            setattr(self.consumer, adj.parameter, adj.old_value)
            
            # Record rollback metrics
            plasticity_metrics.record_rollback(
                consumer=self.consumer.__class__.__name__,
                parameter=adj.parameter,
                steps=1
            )
            
            # Update parameter state
            bound = self.bounds.get(adj.parameter)
            if bound:
                plasticity_metrics.update_parameter_state(
                    consumer=self.consumer.__class__.__name__,
                    parameter=adj.parameter,
                    value=adj.old_value,
                    min_value=bound.min_value,
                    max_value=bound.max_value,
                    disabled=(adj.parameter in self.disabled_parameters)
                )
            
            event = CognitiveEvent(
                id=str(uuid.uuid4()),
                type="plasticity.rollback",
                correlation_id=adj.event_id,  # Link to original adjustment
                causation_id=adj.event_id,
                trace_id=adj.event_id,
                timestamp=datetime.utcnow(),
                source=self.consumer.__class__.__name__,
                payload={
                    "parameter": adj.parameter,
                    "restored_value": adj.old_value,
                    "discarded_value": adj.new_value,
                    "original_reason": adj.reason,
                    "original_timestamp": adj.timestamp.isoformat()
                },
                metadata={}
            )
            rollback_events.append(event)
            
            logger.info(
                f"↩️ Rollback: {self.consumer.__class__.__name__}.{adj.parameter} "
                f"{adj.new_value:.3f} → {adj.old_value:.3f}"
            )
        
        if rollback_events:
            return ProcessResult.emit_many(rollback_events, confidence=1.0)
        else:
            return ProcessResult.silence()
    
    def disable_plasticity(self, parameter: str) -> None:
        """
        Disable plasticity for a specific parameter.
        
        Parameter will not be adjustable until re-enabled.
        
        Args:
            parameter: Parameter name to disable
        """
        self.disabled_parameters.add(parameter)
        logger.info(
            f"🚫 Plasticity disabled for "
            f"{self.consumer.__class__.__name__}.{parameter}"
        )
        self._update_consumer_metrics()
    
    def enable_plasticity(self, parameter: str) -> None:
        """
        Re-enable plasticity for a parameter.
        
        Args:
            parameter: Parameter name to enable
        """
        self.disabled_parameters.discard(parameter)
        logger.info(
            f"✅ Plasticity enabled for "
            f"{self.consumer.__class__.__name__}.{parameter}"
        )
        self._update_consumer_metrics()
    
    def get_current_value(self, parameter: str) -> Optional[float]:
        """Get current value of parameter."""
        if not hasattr(self.consumer, parameter):
            return None
        return getattr(self.consumer, parameter)
    
    def get_adjustment_history(self, parameter: Optional[str] = None) -> List[Adjustment]:
        """
        Get adjustment history.
        
        Args:
            parameter: Filter by parameter name (optional)
        
        Returns:
            List of Adjustment objects, most recent first
        """
        history = list(reversed(self.history))  # Most recent first
        if parameter:
            history = [adj for adj in history if adj.parameter == parameter]
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get plasticity statistics for monitoring.
        
        Returns:
            Dict with adjustment counts, parameter states, etc.
        """
        stats = {
            "total_adjustments": len(self.history),
            "adjustable_parameters": len(self.bounds),
            "disabled_parameters": len(self.disabled_parameters),
            "require_approval": self.require_approval,
            "consumer_name": self.consumer.__class__.__name__,
            "parameters": {}
        }
        
        for param, bound in self.bounds.items():
            current = self.get_current_value(param)
            param_adjustments = [
                adj for adj in self.history if adj.parameter == param
            ]
            
            stats["parameters"][param] = {
                "current_value": current,
                "default_value": bound.default_value,
                "bounds": [bound.min_value, bound.max_value],
                "step_size": bound.step_size,
                "adjustments_count": len(param_adjustments),
                "disabled": param in self.disabled_parameters
            }
        
        return stats
    
    def _update_consumer_metrics(self) -> None:
        """
        Update consumer-level metrics (adjustable/disabled counts).
        Called after __init__, disable_plasticity, enable_plasticity.
        """
        plasticity_metrics.update_consumer_parameters(
            consumer=self.consumer.__class__.__name__,
            adjustable_count=len(self.bounds) - len(self.disabled_parameters),
            disabled_count=len(self.disabled_parameters)
        )
