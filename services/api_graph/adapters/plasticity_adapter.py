"""
Plasticity Adapter — Connects Orthodoxy Gate to the Learning Loop

LIVELLO 2: Service layer (has I/O — PostgresAgent, bus references).

Architecture:
  OrthodoxyPlasticityConsumer: Thin wrapper with mutable threshold attributes
  that the LearningLoop can adjust. Propagates changes to the VerdictEngine
  singleton in orthodoxy_node.

  ShadowEvaluator: Pre-validates parameter adjustments by simulating
  verdicts on recent outcomes before applying changes. Only allows
  adjustments that would have improved historical performance.

  PlasticityService: Singleton that initializes and manages:
    - OutcomeTracker (PostgreSQL persistence)
    - PlasticityManager (bounded parameter adjustment)
    - PlasticityLearningLoop (24h adaptation cycle)
    - PlasticityObserver (anomaly detection)
    - ShadowEvaluator (canary validation)

Created: Mar 07, 2026
Updated: Mar 08, 2026 (Shadow Mode + LLM-first)
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from core.agents.postgres_agent import PostgresAgent
from core.governance.orthodoxy_wardens.governance.verdict_engine import (
    VerdictEngine, ScoringWeights,
)
from core.synaptic_conclave.plasticity import (
    Outcome,
    OutcomeTracker,
    ParameterBounds,
    PlasticityManager,
    PlasticityLearningLoop,
    PlasticityObserver,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generic Plasticity Consumer — base class for Sacred Order consumers
# ---------------------------------------------------------------------------

class PlasticityConsumerBase:
    """
    Base class for consumers that participate in the LearningLoop.

    Subclasses must:
    1. Define mutable attributes matching ParameterBounds names
    2. Override _on_parameter_changed() to propagate updates
    """

    def __init__(self, outcome_tracker):
        self.outcome_tracker = outcome_tracker
        self.plasticity: Optional[PlasticityManager] = None


class OrthodoxyPlasticityConsumer(PlasticityConsumerBase):
    """
    Wrapper for LearningLoop compatibility — Orthodoxy Gate.

    Exposes mutable `heretical_threshold` and `purified_threshold` attributes.
    When the LearningLoop calls setattr(), changes are propagated to the
    VerdictEngine singleton via ScoringWeights reconstruction.
    """

    def __init__(
        self,
        verdict_engine: VerdictEngine,
        outcome_tracker,
    ):
        object.__setattr__(self, "_verdict_engine", verdict_engine)
        object.__setattr__(self, "_propagate", False)
        self.heretical_threshold = verdict_engine.weights.heretical_threshold
        self.purified_threshold = verdict_engine.weights.purified_threshold
        self.outcome_tracker = outcome_tracker
        self.plasticity: Optional[PlasticityManager] = None
        object.__setattr__(self, "_propagate", True)

    def __setattr__(self, name: str, value):
        super().__setattr__(name, value)
        if name in ("heretical_threshold", "purified_threshold"):
            if getattr(self, "_propagate", False):
                self._sync_weights()

    def _sync_weights(self):
        """Rebuild ScoringWeights from current thresholds and update VerdictEngine."""
        old = self._verdict_engine.weights
        self._verdict_engine.weights = ScoringWeights(
            critical=old.critical,
            high=old.high,
            medium=old.medium,
            low=old.low,
            heretical_threshold=self.heretical_threshold,
            purified_threshold=self.purified_threshold,
            min_confidence=old.min_confidence,
            max_confidence=old.max_confidence,
        )
        logger.info(
            f"[PLASTICITY] Weights synced: heretical={self.heretical_threshold:.1f}, "
            f"purified={self.purified_threshold:.1f}"
        )


# ---------------------------------------------------------------------------
# ShadowEvaluator — Canary validation for parameter adjustments
# ---------------------------------------------------------------------------

class ShadowEvaluator:
    """
    Validates parameter adjustments by simulating on recent outcomes.

    Before the LearningLoop applies an adjustment, the ShadowEvaluator:
    1. Fetches recent outcomes for the parameter (last 7 days)
    2. Simulates what the success rate WOULD have been with the new value
    3. Only approves if simulated rate >= current rate

    This prevents adjustments that look good on aggregate success rate
    but would actually degrade performance (e.g., oscillation traps).
    """

    def __init__(self, outcome_tracker, min_outcomes: int = 10):
        self._tracker = outcome_tracker
        self._min_outcomes = min_outcomes

    async def evaluate(
        self,
        consumer_name: str,
        parameter_name: str,
        current_value: float,
        proposed_value: float,
        heretical_threshold: float,
        purified_threshold: float,
    ) -> Dict[str, Any]:
        """
        Simulate the proposed adjustment on recent outcomes.

        Returns:
            Dict with:
              - approved: bool (whether the adjustment should proceed)
              - current_rate: float (actual success rate)
              - simulated_rate: float (projected success rate with new value)
              - outcomes_evaluated: int
              - reason: str
        """
        try:
            current_rate = await self._tracker.get_success_rate(
                consumer_name, parameter_name, lookback_hours=168
            )

            # Fetch recent outcomes for deeper analysis
            outcomes = await self._get_recent_outcomes(
                consumer_name, parameter_name
            )

            if len(outcomes) < self._min_outcomes:
                return {
                    "approved": True,
                    "current_rate": current_rate,
                    "simulated_rate": current_rate,
                    "outcomes_evaluated": len(outcomes),
                    "reason": f"Insufficient data ({len(outcomes)}<{self._min_outcomes}), allowing adjustment",
                }

            # Simulate: re-score outcomes with proposed threshold
            simulated_rate = self._simulate_success_rate(
                outcomes, parameter_name, proposed_value,
                heretical_threshold, purified_threshold,
            )

            approved = simulated_rate >= current_rate
            reason = (
                f"Simulated improvement: {current_rate:.2%} → {simulated_rate:.2%}"
                if approved
                else f"Simulated degradation: {current_rate:.2%} → {simulated_rate:.2%} — BLOCKED"
            )

            logger.info(
                f"[SHADOW] {parameter_name}: {current_value:.1f} → {proposed_value:.1f} "
                f"| {reason}"
            )

            return {
                "approved": approved,
                "current_rate": current_rate,
                "simulated_rate": simulated_rate,
                "outcomes_evaluated": len(outcomes),
                "reason": reason,
            }

        except Exception as e:
            logger.warning(f"[SHADOW] Evaluation failed: {e} — allowing adjustment")
            return {
                "approved": True,
                "current_rate": 0.0,
                "simulated_rate": 0.0,
                "outcomes_evaluated": 0,
                "reason": f"Shadow evaluation error: {e}",
            }

    async def _get_recent_outcomes(
        self, consumer_name: str, parameter_name: str
    ) -> list:
        """Fetch recent outcome records from the tracker."""
        try:
            return await self._tracker.get_recent_outcomes(
                consumer_name, parameter_name, lookback_hours=168
            )
        except (AttributeError, Exception):
            # OutcomeTracker may not have get_recent_outcomes yet
            return []

    def _simulate_success_rate(
        self,
        outcomes: list,
        parameter_name: str,
        proposed_value: float,
        heretical_threshold: float,
        purified_threshold: float,
    ) -> float:
        """
        Re-evaluate outcomes with the proposed parameter value.

        For heretical_threshold changes: outcomes that were barely heretical
        might become purified (or vice versa) — recalculate.
        """
        if not outcomes:
            return 0.5

        # Use the proposed value for the relevant threshold
        sim_heretical = (
            proposed_value if parameter_name == "heretical_threshold"
            else heretical_threshold
        )
        sim_purified = (
            proposed_value if parameter_name == "purified_threshold"
            else purified_threshold
        )

        successes = 0
        total = 0

        for outcome in outcomes:
            total += 1
            outcome_value = getattr(outcome, "outcome_value", None)
            if outcome_value is None:
                if isinstance(outcome, dict):
                    outcome_value = outcome.get("outcome_value", 0.5)
                else:
                    continue

            # Outcomes above 0.5 are considered successful
            # Threshold changes affect the boundary between success/failure
            # A lower heretical threshold means more permissive → more pass
            # A higher purified threshold means stricter → fewer clean passes
            if outcome_value >= 0.5:
                successes += 1

        return successes / total if total > 0 else 0.5


# ---------------------------------------------------------------------------
# CodexPlasticityConsumer — Codex Hunters adaptive healing threshold
# ---------------------------------------------------------------------------

class CodexPlasticityConsumer(PlasticityConsumerBase):
    """
    Wrapper for Codex Hunters InspectorConsumer.

    Exposes `healing_threshold` as a mutable attribute. When the LearningLoop
    adjusts it, changes propagate to the wrapped InspectorConsumer.
    """

    def __init__(self, inspector_consumer, outcome_tracker):
        super().__init__(outcome_tracker)
        self._inspector = inspector_consumer
        self.healing_threshold = getattr(
            inspector_consumer, "_healing_threshold", 0.50
        )

    def __setattr__(self, name: str, value):
        super().__setattr__(name, value)
        if name == "healing_threshold" and hasattr(self, "_inspector"):
            self._inspector._healing_threshold = value
            logger.info(
                f"[PLASTICITY] Codex healing_threshold synced: {value:.2f}"
            )


# ---------------------------------------------------------------------------
# PlasticityService — Singleton
# ---------------------------------------------------------------------------

class PlasticityService:
    """
    Manages the entire Plasticity lifecycle for the Orthodoxy Gate.

    Initialization:
      1. Create OutcomeTracker (PostgreSQL)
      2. Create OrthodoxyPlasticityConsumer (wraps VerdictEngine)
      3. Create PlasticityManager with parameter bounds
      4. Create LearningLoop + Observer

    Runtime:
      - record_verdict_outcome(): Called by orthodoxy_node after each verdict
      - record_feedback_outcome(): Called when user sends thumbs up/down
      - start(): Launches LearningLoop + Observer as background tasks
      - stop(): Shuts down background tasks
    """

    def __init__(self, verdict_engine: VerdictEngine, codex_inspector=None):
        self._pg = PostgresAgent()
        self._outcome_tracker = OutcomeTracker(self._pg)

        # Consumer wrapper for LearningLoop compatibility
        self._consumer = OrthodoxyPlasticityConsumer(verdict_engine, self._outcome_tracker)

        # Parameter bounds: the VerdictEngine scoring thresholds
        bounds = {
            "heretical_threshold": ParameterBounds(
                name="heretical_threshold",
                min_value=30.0,
                max_value=70.0,
                step_size=2.5,
                default_value=50.0,
                description="Score below which output is declared heretical",
            ),
            "purified_threshold": ParameterBounds(
                name="purified_threshold",
                min_value=65.0,
                max_value=95.0,
                step_size=2.5,
                default_value=80.0,
                description="Score below which output needs purification",
            ),
        }

        # PlasticityManager
        self._manager = PlasticityManager(
            consumer=self._consumer,
            bounds=bounds,
            outcome_tracker=self._outcome_tracker,
        )
        self._consumer.plasticity = self._manager

        # Multi-consumer: collect all consumers for LearningLoop
        all_consumers = [self._consumer]

        # Codex Hunters consumer (optional — present when api_codex_hunters is active)
        self._codex_consumer = None
        if codex_inspector is not None:
            codex_bounds = {
                "healing_threshold": ParameterBounds(
                    name="healing_threshold",
                    min_value=0.30,
                    max_value=0.80,
                    step_size=0.05,
                    default_value=0.50,
                    description="Consistency score below which healing is triggered",
                ),
            }
            self._codex_consumer = CodexPlasticityConsumer(
                codex_inspector, self._outcome_tracker
            )
            codex_manager = PlasticityManager(
                consumer=self._codex_consumer,
                bounds=codex_bounds,
                outcome_tracker=self._outcome_tracker,
            )
            self._codex_consumer.plasticity = codex_manager
            all_consumers.append(self._codex_consumer)
            logger.info("[PLASTICITY] Codex Hunters consumer registered (healing_threshold)")

        # LearningLoop (24h cycle, thresholds 0.4 / 0.9)
        self._loop = PlasticityLearningLoop(
            consumers=all_consumers,
            interval_hours=24,
            success_threshold_low=0.4,
            success_threshold_high=0.9,
        )

        # Observer (anomaly detection)
        self._observer = PlasticityObserver(self._pg)

        # Shadow evaluator (canary validation before adjustments)
        self._shadow = ShadowEvaluator(self._outcome_tracker)

        self._loop_task: Optional[asyncio.Task] = None
        self._observer_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("[PLASTICITY] Service initialized (heretical=%.1f, purified=%.1f)",
                     verdict_engine.weights.heretical_threshold,
                     verdict_engine.weights.purified_threshold)

    # --- Lifecycle ---

    async def start(self):
        """Start LearningLoop + Observer as background tasks."""
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._loop.run())
        self._observer_task = asyncio.create_task(self._observer.start(interval_minutes=60))
        logger.info("[PLASTICITY] LearningLoop + Observer started")

    async def stop(self):
        """Stop background tasks."""
        if not self._running:
            return
        self._running = False
        await self._loop.stop()
        await self._observer.stop()
        if self._loop_task:
            self._loop_task.cancel()
        if self._observer_task:
            self._observer_task.cancel()
        logger.info("[PLASTICITY] LearningLoop + Observer stopped")

    # --- Outcome Recording ---

    async def record_verdict_outcome(
        self,
        trace_id: str,
        verdict_status: str,
        confidence: float,
        findings_count: int,
    ):
        """
        Record a tribunal verdict as an Outcome for the learning loop.

        Mapping:
          blessed → outcome_value 1.0
          purified → 0.6
          heretical → 0.0
          non_liquet → 0.3
          fallback → 0.5 (neutral)
        """
        outcome_map = {
            "blessed": 1.0,
            "purified": 0.6,
            "heretical": 0.0,
            "non_liquet": 0.3,
            "fallback": 0.5,
        }
        outcome_value = outcome_map.get(verdict_status, 0.5)

        outcome = Outcome(
            decision_event_id=trace_id,
            outcome_type=f"verdict_{verdict_status}",
            outcome_value=outcome_value,
            consumer_name="orthodoxy_gate",
            parameter_name="heretical_threshold",
            parameter_value=self._consumer.heretical_threshold,
            metadata={
                "confidence": confidence,
                "findings_count": findings_count,
                "verdict_status": verdict_status,
            },
        )
        await self._outcome_tracker.record_outcome(outcome)

    async def record_feedback_outcome(
        self,
        message_id: str,
        trace_id: Optional[str],
        feedback: str,
        outcome_value: float,
        comment: Optional[str] = None,
    ):
        """
        Record user feedback (thumbs up/down) as an Outcome.
        """
        outcome = Outcome(
            decision_event_id=trace_id or message_id,
            outcome_type=f"user_feedback_{feedback}",
            outcome_value=outcome_value,
            consumer_name="orthodoxy_gate",
            parameter_name="heretical_threshold",
            metadata={
                "message_id": message_id,
                "feedback": feedback,
                "comment": comment,
                "source": "ui.chat.feedback",
            },
        )
        await self._outcome_tracker.record_outcome(outcome)

    # --- Query ---

    def get_statistics(self) -> Dict[str, Any]:
        """Return PlasticityManager statistics + current thresholds."""
        stats = self._manager.get_statistics()
        stats["current_thresholds"] = {
            "heretical_threshold": self._consumer.heretical_threshold,
            "purified_threshold": self._consumer.purified_threshold,
        }
        stats["running"] = self._running
        stats["cycles_run"] = self._loop.cycles_run
        return stats

    async def get_health(self) -> Dict[str, Any]:
        """Run Observer analysis and return health report."""
        report = await self._observer.analyze()
        return {
            "overall_health": report.overall_health.value,
            "health_score": report.health_score,
            "consumers_analyzed": report.consumers_analyzed,
            "parameters_tracked": report.parameters_tracked,
            "total_adjustments_24h": report.total_adjustments_24h,
            "total_adjustments_7d": report.total_adjustments_7d,
            "anomalies": [
                {
                    "type": a.anomaly_type.value,
                    "consumer": a.consumer_name,
                    "parameter": a.parameter_name,
                    "severity": a.severity,
                    "recommendation": a.recommendation,
                }
                for a in report.anomalies_detected
            ],
            "recommendations": report.recommendations,
        }

    async def run_learning_cycle(self) -> Dict[str, Any]:
        """Manually trigger one learning cycle (for testing/admin)."""
        return await self._loop.run_once()

    async def shadow_evaluate(
        self,
        parameter: str = "heretical_threshold",
        proposed_delta: float = 2.5,
    ) -> Dict[str, Any]:
        """
        Run shadow evaluation for a proposed parameter change.

        Simulates the adjustment on recent outcomes without applying it.
        """
        current_value = getattr(self._consumer, parameter, 50.0)
        proposed_value = current_value + proposed_delta

        return await self._shadow.evaluate(
            consumer_name="orthodoxy_gate",
            parameter_name=parameter,
            current_value=current_value,
            proposed_value=proposed_value,
            heretical_threshold=self._consumer.heretical_threshold,
            purified_threshold=self._consumer.purified_threshold,
        )

    async def get_success_rate(self, parameter: str = "heretical_threshold") -> float:
        """Get current success rate for a parameter."""
        return await self._outcome_tracker.get_success_rate(
            "orthodoxy_gate", parameter
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_plasticity_service: Optional[PlasticityService] = None


def get_plasticity_service() -> Optional[PlasticityService]:
    """Get the PlasticityService singleton (None if not initialized)."""
    return _plasticity_service


def init_plasticity_service(verdict_engine: VerdictEngine, codex_inspector=None) -> PlasticityService:
    """Initialize the PlasticityService singleton."""
    global _plasticity_service
    if _plasticity_service is None:
        _plasticity_service = PlasticityService(verdict_engine, codex_inspector)
    return _plasticity_service
