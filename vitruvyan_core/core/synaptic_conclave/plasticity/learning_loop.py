"""
Learning Loop — Periodic Adaptive Learning
===========================================

Analyzes outcomes and proposes parameter adjustments automatically.
Runs as background task (daily by default).

Sacred Order: Reason (Adaptive Layer)

Author: Vitruvyan Core Team
Date: January 24, 2026
"""

import asyncio
import logging
import time
from typing import List, Any, Dict

from vitruvyan_core.core.synaptic_conclave.plasticity import metrics as plasticity_metrics

logger = logging.getLogger(__name__)


class PlasticityLearningLoop:
    """
    Periodic task that analyzes outcomes and proposes adjustments.
    
    Runs every N hours, checks success rates, proposes adaptations
    based on configured thresholds.
    
    Philosophy:
        - Daily adaptation (not real-time) prevents oscillation
        - 7-day lookback smooths variance
        - Small step sizes (0.05) prevent instability
        - Success rate thresholds (0.4-0.9) define action zones
    
    Usage:
        consumers = [narrative_engine, risk_guardian]
        loop = PlasticityLearningLoop(consumers, interval_hours=24)
        asyncio.create_task(loop.run())  # Start in background
    """
    
    def __init__(
        self, 
        consumers: List[Any],  # List[BaseConsumer] - avoid circular import
        interval_hours: int = 24,  # Daily by default
        success_threshold_low: float = 0.4,  # Too strict
        success_threshold_high: float = 0.9  # Too permissive
    ):
        """
        Initialize learning loop.
        
        Args:
            consumers: List of consumers with plasticity enabled
            interval_hours: Hours between adaptation cycles
            success_threshold_low: Trigger relaxation if below this
            success_threshold_high: Trigger tightening if above this
        """
        self.consumers = consumers
        self.interval = interval_hours
        self.success_low = success_threshold_low
        self.success_high = success_threshold_high
        self.running = False
        self.cycles_run = 0
        
        logger.info(
            f"PlasticityLearningLoop initialized: "
            f"{len(consumers)} consumers, interval={interval_hours}h, "
            f"thresholds=({success_threshold_low}, {success_threshold_high})"
        )
    
    async def run(self) -> None:
        """
        Start learning loop (runs indefinitely in background).
        
        Call this as: asyncio.create_task(loop.run())
        """
        self.running = True
        logger.info("🔄 Learning loop started")
        
        while self.running:
            try:
                await asyncio.sleep(self.interval * 3600)  # Convert hours to seconds
                await self._analyze_and_adapt()
                self.cycles_run += 1
            except asyncio.CancelledError:
                logger.info("Learning loop cancelled")
                break
            except Exception as e:
                logger.error(f"Learning loop error: {e}", exc_info=True)
                # Continue running despite errors
        
        logger.info(f"Learning loop stopped (ran {self.cycles_run} cycles)")
    
    async def stop(self) -> None:
        """Stop the learning loop."""
        self.running = False
        logger.info("Learning loop stopping...")
    
    async def run_once(self) -> Dict[str, Any]:
        """
        Run one adaptation cycle (for testing/manual triggering).
        
        Returns:
            Dict with adaptation results
        """
        return await self._analyze_and_adapt()
    
    async def _analyze_and_adapt(self) -> Dict[str, Any]:
        """
        Analyze outcomes and propose adjustments.
        
        For each consumer with plasticity:
        - Check success rate for each adjustable parameter
        - Propose adjustment if outside threshold range
        
        Returns:
            Dict with adaptation summary
        """
        logger.info("🧠 Learning cycle starting...")
        start_time = time.time()  # Start timing
        
        results = {
            "cycle": self.cycles_run,
            "consumers_analyzed": 0,
            "adjustments_proposed": 0,
            "adjustments_applied": 0,
            "adjustments_rejected": 0,
            "details": []
        }
        
        for consumer in self.consumers:
            if not consumer.plasticity:
                continue
            
            results["consumers_analyzed"] += 1
            consumer_name = consumer.__class__.__name__
            
            for param_name, bound in consumer.plasticity.bounds.items():
                # Skip disabled parameters
                if param_name in consumer.plasticity.disabled_parameters:
                    continue
                
                # Get success rate for last 7 days
                try:
                    success_rate = await consumer.outcome_tracker.get_success_rate(
                        consumer_name=consumer_name,
                        parameter_name=param_name,
                        lookback_hours=168  # 7 days
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to get success rate for "
                        f"{consumer_name}.{param_name}: {e}"
                    )
                    continue
                
                # Determine if adjustment needed
                adjustment_needed = False
                delta = 0.0
                reason = ""
                
                if success_rate < self.success_low:
                    # Too strict → relax threshold
                    adjustment_needed = True
                    # For thresholds: increase = more permissive
                    # For other params: decrease
                    delta = bound.step_size if "threshold" in param_name.lower() else -bound.step_size
                    reason = f"Low success rate: {success_rate:.2%} (too strict)"
                
                elif success_rate > self.success_high:
                    # Too permissive → tighten threshold
                    adjustment_needed = True
                    delta = -bound.step_size if "threshold" in param_name.lower() else bound.step_size
                    reason = f"High success rate: {success_rate:.2%} (can be stricter)"
                
                if adjustment_needed:
                    results["adjustments_proposed"] += 1
                    
                    logger.info(
                        f"📈 Proposing adjustment: {consumer_name}.{param_name} "
                        f"delta={delta:+.3f} (success_rate={success_rate:.2%})"
                    )
                    
                    # Propose adjustment
                    try:
                        result = await consumer.plasticity.propose_adjustment(
                            parameter=param_name,
                            delta=delta,
                            reason=reason,
                            success_rate=success_rate
                        )
                        
                        if result.action == "emit":
                            results["adjustments_applied"] += 1
                            logger.info(
                                f"✅ Adjustment applied: {consumer_name}.{param_name}"
                            )
                        elif result.action == "escalate":
                            results["adjustments_applied"] += 1
                            logger.info(
                                f"⚠️ Adjustment escalated (requires approval): "
                                f"{consumer_name}.{param_name}"
                            )
                        else:  # silence
                            results["adjustments_rejected"] += 1
                            logger.warning(
                                f"❌ Adjustment rejected: {consumer_name}.{param_name} "
                                f"(out of bounds or disabled)"
                            )
                        
                        results["details"].append({
                            "consumer": consumer_name,
                            "parameter": param_name,
                            "success_rate": success_rate,
                            "delta": delta,
                            "reason": reason,
                            "result": result.action
                        })
                    
                    except Exception as e:
                        logger.error(
                            f"Failed to apply adjustment for "
                            f"{consumer_name}.{param_name}: {e}"
                        )
                        results["adjustments_rejected"] += 1
        
        logger.info(
            f"🔄 Learning cycle complete: "
            f"{results['adjustments_applied']}/{results['adjustments_proposed']} applied"
        )
        
        # Record learning cycle metrics
        duration = time.time() - start_time
        plasticity_metrics.record_learning_cycle(
            duration_seconds=duration,
            adjustments_proposed=results['adjustments_proposed'],
            adjustments_applied=results['adjustments_applied'],
            adjustments_rejected=results['adjustments_rejected']
        )
        
        return results
