"""
Plasticity Observer — Autonomous Learning Monitor
==================================================

Agente dedicato al monitoraggio continuo del sistema di apprendimento.
Rileva variazioni, cataloga pattern, fornisce metriche oggettive.

Sacred Order: Truth (Governance Layer)

Responsabilities:
1. Track all parameter adjustments over time
2. Detect anomalies (oscillation, drift, stagnation)
3. Compute objective health metrics
4. Generate learning quality reports
5. Alert on concerning patterns

Architecture:
    Observer ← PlasticityManager events
    Observer ← OutcomeTracker outcomes  
    Observer → PostgreSQL (observer_log)
    Observer → Prometheus (learning health metrics)
    Observer → Alerts (via Cognitive Bus)

Author: Vitruvyan Core Team
Date: January 26, 2026
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import statistics

from core.leo.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.events.event_envelope import CognitiveEvent
from vitruvyan_core.core.synaptic_conclave.plasticity import metrics as plasticity_metrics

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of learning anomalies."""
    OSCILLATION = "oscillation"      # Parameter bouncing up/down
    DRIFT = "drift"                  # Continuous movement in one direction
    STAGNATION = "stagnation"        # No learning despite poor outcomes
    INSTABILITY = "instability"      # Too many adjustments in short time
    DIVERGENCE = "divergence"        # Parameter approaching bounds
    FEEDBACK_LAG = "feedback_lag"    # Outcomes not affecting adjustments


class LearningHealth(Enum):
    """Overall learning system health."""
    HEALTHY = "healthy"              # Normal operation
    DEGRADED = "degraded"            # Minor issues detected
    CRITICAL = "critical"            # Major issues, intervention needed
    STALLED = "stalled"              # Learning effectively stopped


@dataclass
class AnomalyReport:
    """Report of detected anomaly."""
    anomaly_type: AnomalyType
    consumer_name: str
    parameter_name: str
    severity: float                  # 0.0-1.0, 1.0 = critical
    evidence: Dict[str, Any]         # Data supporting the detection
    detected_at: datetime = field(default_factory=datetime.utcnow)
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "consumer_name": self.consumer_name,
            "parameter_name": self.parameter_name,
            "severity": self.severity,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat(),
            "recommendation": self.recommendation
        }


@dataclass
class ParameterTrajectory:
    """Trajectory of a parameter over time."""
    consumer_name: str
    parameter_name: str
    values: List[Tuple[datetime, float]]  # (timestamp, value)
    adjustments: List[Tuple[datetime, float, float, str]]  # (ts, old, new, reason)
    success_rates: List[Tuple[datetime, float]]  # (timestamp, rate)
    
    @property
    def current_value(self) -> Optional[float]:
        if not self.values:
            return None
        return self.values[-1][1]
    
    @property
    def value_range(self) -> Tuple[float, float]:
        if not self.values:
            return (0.0, 0.0)
        vals = [v[1] for v in self.values]
        return (min(vals), max(vals))
    
    @property
    def adjustment_count(self) -> int:
        return len(self.adjustments)
    
    @property
    def net_direction(self) -> str:
        """Overall direction: 'increasing', 'decreasing', 'stable'."""
        if len(self.values) < 2:
            return "stable"
        
        deltas = [self.values[i][1] - self.values[i-1][1] 
                  for i in range(1, len(self.values))]
        
        positive = sum(1 for d in deltas if d > 0)
        negative = sum(1 for d in deltas if d < 0)
        
        if positive > negative * 2:
            return "increasing"
        elif negative > positive * 2:
            return "decreasing"
        return "stable"


@dataclass
class LearningHealthReport:
    """Comprehensive learning health report."""
    generated_at: datetime
    overall_health: LearningHealth
    health_score: float              # 0.0-1.0, 1.0 = perfect
    consumers_analyzed: int
    parameters_tracked: int
    total_adjustments_24h: int
    total_adjustments_7d: int
    anomalies_detected: List[AnomalyReport]
    trajectories: Dict[str, ParameterTrajectory]  # key: "consumer:parameter"
    recommendations: List[str]
    metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_health": self.overall_health.value,
            "health_score": self.health_score,
            "consumers_analyzed": self.consumers_analyzed,
            "parameters_tracked": self.parameters_tracked,
            "total_adjustments_24h": self.total_adjustments_24h,
            "total_adjustments_7d": self.total_adjustments_7d,
            "anomalies": [a.to_dict() for a in self.anomalies_detected],
            "trajectories": {k: {
                "current_value": v.current_value,
                "value_range": v.value_range,
                "adjustment_count": v.adjustment_count,
                "net_direction": v.net_direction
            } for k, v in self.trajectories.items()},
            "recommendations": self.recommendations,
            "metrics": self.metrics
        }


class PlasticityObserver:
    """
    Autonomous observer for plasticity system health.
    
    Monitors learning patterns, detects anomalies, provides objective metrics.
    Runs as background task, emits alerts via Cognitive Bus.
    
    Metrics Provided:
    - Learning Efficiency: adjustments_effective / adjustments_total
    - Stability Index: 1 - (oscillations_detected / adjustments_total)
    - Convergence Score: how close to optimal parameters
    - Feedback Responsiveness: correlation(outcomes, adjustments)
    - Drift Detection: magnitude of unidirectional movement
    
    Usage:
        observer = PlasticityObserver(postgres)
        await observer.start(interval_minutes=60)
        
        # Or manual analysis
        report = await observer.analyze()
    """
    
    # Detection thresholds
    OSCILLATION_THRESHOLD = 3       # Min reversals to detect oscillation
    OSCILLATION_WINDOW = 7          # Days to look back
    DRIFT_THRESHOLD = 0.8           # 80% same-direction adjustments = drift
    STAGNATION_DAYS = 14            # No adjustments for 14 days = stagnation
    INSTABILITY_THRESHOLD = 5       # More than 5 adjustments/day = instability
    DIVERGENCE_MARGIN = 0.1         # Within 10% of bound = divergence warning
    
    @staticmethod
    def _compare_datetime(ts: datetime, cutoff: datetime) -> bool:
        """Safely compare datetimes handling timezone-aware vs naive."""
        from datetime import timezone
        
        # Make both timezone-aware for comparison
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
            return ts > cutoff
        else:
            if cutoff.tzinfo is not None:
                cutoff = cutoff.replace(tzinfo=None)
            return ts > cutoff
    
    def __init__(self, postgres: PostgresAgent):
        """
        Initialize observer.
        
        Args:
            postgres: PostgresAgent for database operations
        """
        self.postgres = postgres
        self.running = False
        self._ensure_schema()
        
        logger.info("PlasticityObserver initialized")
    
    def _ensure_schema(self) -> None:
        """Ensure observer tables exist."""
        try:
            with self.postgres.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS plasticity_observer_log (
                        id SERIAL PRIMARY KEY,
                        generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        overall_health VARCHAR(20) NOT NULL,
                        health_score FLOAT NOT NULL,
                        consumers_analyzed INT NOT NULL,
                        parameters_tracked INT NOT NULL,
                        adjustments_24h INT NOT NULL,
                        adjustments_7d INT NOT NULL,
                        anomalies_count INT NOT NULL,
                        report_json JSONB NOT NULL
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_observer_log_generated 
                    ON plasticity_observer_log(generated_at DESC);
                    
                    CREATE TABLE IF NOT EXISTS plasticity_anomalies (
                        id SERIAL PRIMARY KEY,
                        detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        anomaly_type VARCHAR(30) NOT NULL,
                        consumer_name VARCHAR(100) NOT NULL,
                        parameter_name VARCHAR(100) NOT NULL,
                        severity FLOAT NOT NULL,
                        evidence JSONB NOT NULL,
                        recommendation TEXT,
                        resolved_at TIMESTAMPTZ,
                        resolution_notes TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_anomalies_unresolved 
                    ON plasticity_anomalies(detected_at DESC) 
                    WHERE resolved_at IS NULL;
                """)
                self.postgres.connection.commit()
        except Exception as e:
            logger.warning(f"Schema creation warning (may already exist): {e}")
            self.postgres.connection.rollback()
    
    async def start(self, interval_minutes: int = 60) -> None:
        """
        Start continuous monitoring.
        
        Args:
            interval_minutes: Analysis interval (default 60 min)
        """
        self.running = True
        logger.info(f"🔍 PlasticityObserver started (interval={interval_minutes}min)")
        
        while self.running:
            try:
                report = await self.analyze()
                await self._persist_report(report)
                await self._check_alerts(report)
                
                logger.info(
                    f"📊 Observer cycle complete: "
                    f"health={report.overall_health.value}, "
                    f"score={report.health_score:.2f}, "
                    f"anomalies={len(report.anomalies_detected)}"
                )
                
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("PlasticityObserver cancelled")
                break
            except Exception as e:
                logger.error(f"Observer error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Retry after 1 min on error
        
        self.running = False
        logger.info("PlasticityObserver stopped")
    
    async def stop(self) -> None:
        """Stop observer."""
        self.running = False
    
    async def analyze(self) -> LearningHealthReport:
        """
        Perform comprehensive learning analysis.
        
        Returns:
            LearningHealthReport with metrics and anomalies
        """
        now = datetime.utcnow()
        
        # Gather data
        trajectories = await self._build_trajectories()
        anomalies = await self._detect_anomalies(trajectories)
        metrics = await self._compute_metrics(trajectories)
        
        # Count adjustments
        adjustments_24h = await self._count_adjustments(hours=24)
        adjustments_7d = await self._count_adjustments(hours=168)
        
        # Determine health
        health_score = self._calculate_health_score(metrics, anomalies)
        overall_health = self._determine_health_level(health_score, anomalies)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies, metrics)
        
        return LearningHealthReport(
            generated_at=now,
            overall_health=overall_health,
            health_score=health_score,
            consumers_analyzed=len(set(t.consumer_name for t in trajectories.values())),
            parameters_tracked=len(trajectories),
            total_adjustments_24h=adjustments_24h,
            total_adjustments_7d=adjustments_7d,
            anomalies_detected=anomalies,
            trajectories=trajectories,
            recommendations=recommendations,
            metrics=metrics
        )
    
    async def _build_trajectories(self) -> Dict[str, ParameterTrajectory]:
        """Build parameter trajectories from historical data."""
        trajectories = {}
        
        # Query historical adjustments
        query = """
            SELECT 
                consumer_name,
                parameter_name,
                parameter_value,
                outcome_value,
                recorded_at
            FROM plasticity_outcomes
            WHERE recorded_at > NOW() - INTERVAL '30 days'
            ORDER BY recorded_at ASC
        """
        
        try:
            rows = await asyncio.to_thread(
                self._execute_query, query
            )
        except Exception as e:
            logger.warning(f"Failed to query trajectories: {e}")
            return trajectories
        
        # Group by consumer:parameter
        grouped: Dict[str, Dict[str, List]] = {}
        for row in rows:
            key = f"{row[0]}:{row[1]}"
            if key not in grouped:
                grouped[key] = {
                    "values": [],
                    "success_rates": []
                }
            
            if row[2] is not None:  # parameter_value
                grouped[key]["values"].append((row[4], row[2]))
            if row[3] is not None:  # outcome_value
                grouped[key]["success_rates"].append((row[4], row[3]))
        
        # Build trajectories
        for key, data in grouped.items():
            consumer, param = key.split(":", 1)
            trajectories[key] = ParameterTrajectory(
                consumer_name=consumer,
                parameter_name=param,
                values=data["values"],
                adjustments=[],  # Populated separately if needed
                success_rates=data["success_rates"]
            )
        
        return trajectories
    
    async def _detect_anomalies(
        self, 
        trajectories: Dict[str, ParameterTrajectory]
    ) -> List[AnomalyReport]:
        """Detect learning anomalies."""
        anomalies = []
        
        for key, traj in trajectories.items():
            # Check oscillation
            osc = self._detect_oscillation(traj)
            if osc:
                anomalies.append(osc)
            
            # Check drift
            drift = self._detect_drift(traj)
            if drift:
                anomalies.append(drift)
            
            # Check stagnation
            stag = self._detect_stagnation(traj)
            if stag:
                anomalies.append(stag)
            
            # Check feedback lag
            lag = self._detect_feedback_lag(traj)
            if lag:
                anomalies.append(lag)
        
        return anomalies
    
    def _detect_oscillation(self, traj: ParameterTrajectory) -> Optional[AnomalyReport]:
        """Detect parameter oscillation (bouncing up/down)."""
        if len(traj.values) < 4:
            return None
        
        # Get recent values (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=self.OSCILLATION_WINDOW)
        recent = [(t, v) for t, v in traj.values if self._compare_datetime(t, cutoff)]
        
        if len(recent) < 4:
            return None
        
        # Count direction reversals
        reversals = 0
        for i in range(2, len(recent)):
            prev_delta = recent[i-1][1] - recent[i-2][1]
            curr_delta = recent[i][1] - recent[i-1][1]
            
            if prev_delta * curr_delta < 0:  # Sign change
                reversals += 1
        
        if reversals >= self.OSCILLATION_THRESHOLD:
            severity = min(reversals / 10, 1.0)  # Cap at 1.0
            
            return AnomalyReport(
                anomaly_type=AnomalyType.OSCILLATION,
                consumer_name=traj.consumer_name,
                parameter_name=traj.parameter_name,
                severity=severity,
                evidence={
                    "reversals_detected": reversals,
                    "values_analyzed": len(recent),
                    "window_days": self.OSCILLATION_WINDOW,
                    "recent_values": [(t.isoformat(), v) for t, v in recent[-5:]]
                },
                recommendation=(
                    f"Consider increasing step_size or success thresholds for "
                    f"{traj.parameter_name} to reduce oscillation"
                )
            )
        
        return None
    
    def _detect_drift(self, traj: ParameterTrajectory) -> Optional[AnomalyReport]:
        """Detect continuous drift in one direction."""
        if len(traj.values) < 5:
            return None
        
        # Calculate direction of each change
        directions = []
        for i in range(1, len(traj.values)):
            delta = traj.values[i][1] - traj.values[i-1][1]
            if abs(delta) > 0.001:  # Ignore tiny changes
                directions.append(1 if delta > 0 else -1)
        
        if not directions:
            return None
        
        # Check for dominant direction
        positive_ratio = sum(1 for d in directions if d > 0) / len(directions)
        
        if positive_ratio >= self.DRIFT_THRESHOLD:
            return AnomalyReport(
                anomaly_type=AnomalyType.DRIFT,
                consumer_name=traj.consumer_name,
                parameter_name=traj.parameter_name,
                severity=positive_ratio,
                evidence={
                    "direction": "increasing",
                    "positive_ratio": positive_ratio,
                    "changes_analyzed": len(directions),
                    "value_range": traj.value_range
                },
                recommendation=(
                    f"Parameter {traj.parameter_name} shows continuous upward drift. "
                    f"Verify bounds are appropriate or outcomes are balanced."
                )
            )
        elif (1 - positive_ratio) >= self.DRIFT_THRESHOLD:
            return AnomalyReport(
                anomaly_type=AnomalyType.DRIFT,
                consumer_name=traj.consumer_name,
                parameter_name=traj.parameter_name,
                severity=1 - positive_ratio,
                evidence={
                    "direction": "decreasing",
                    "negative_ratio": 1 - positive_ratio,
                    "changes_analyzed": len(directions),
                    "value_range": traj.value_range
                },
                recommendation=(
                    f"Parameter {traj.parameter_name} shows continuous downward drift. "
                    f"Verify bounds are appropriate or outcomes are balanced."
                )
            )
        
        return None
    
    def _detect_stagnation(self, traj: ParameterTrajectory) -> Optional[AnomalyReport]:
        """Detect learning stagnation (no adjustments despite poor outcomes)."""
        if not traj.values or not traj.success_rates:
            return None
        
        # Check if any adjustments in last N days
        cutoff = datetime.utcnow() - timedelta(days=self.STAGNATION_DAYS)
        
        # Handle timezone-aware datetimes using helper
        recent_values = [(t, v) for t, v in traj.values if self._compare_datetime(t, cutoff)]
        
        if len(recent_values) >= 2:
            return None  # Not stagnant, has recent changes
        
        # Check if outcomes are poor (should trigger adjustment)
        recent_outcomes = [v for t, v in traj.success_rates if self._compare_datetime(t, cutoff)]
        
        if not recent_outcomes:
            return None
        
        avg_success = statistics.mean(recent_outcomes)
        
        # Stagnation if low success rate but no adjustments
        if avg_success < 0.5:  # Below 50% success
            return AnomalyReport(
                anomaly_type=AnomalyType.STAGNATION,
                consumer_name=traj.consumer_name,
                parameter_name=traj.parameter_name,
                severity=1.0 - avg_success,
                evidence={
                    "days_without_adjustment": self.STAGNATION_DAYS,
                    "average_success_rate": avg_success,
                    "outcomes_in_period": len(recent_outcomes)
                },
                recommendation=(
                    f"Parameter {traj.parameter_name} hasn't been adjusted in "
                    f"{self.STAGNATION_DAYS} days despite {avg_success:.1%} success rate. "
                    f"Check if learning loop is running or thresholds are too conservative."
                )
            )
        
        return None
    
    def _detect_feedback_lag(self, traj: ParameterTrajectory) -> Optional[AnomalyReport]:
        """Detect disconnect between outcomes and adjustments."""
        if len(traj.success_rates) < 10 or len(traj.values) < 3:
            return None
        
        # Simple correlation check: do adjustments follow outcome trends?
        # This is simplified; production would use proper time-series correlation
        
        outcome_trend = "stable"
        value_trend = traj.net_direction
        
        # Calculate outcome trend
        recent_outcomes = [v for t, v in traj.success_rates[-10:]]
        if len(recent_outcomes) >= 5:
            first_half = statistics.mean(recent_outcomes[:5])
            second_half = statistics.mean(recent_outcomes[5:])
            
            if second_half > first_half + 0.1:
                outcome_trend = "improving"
            elif second_half < first_half - 0.1:
                outcome_trend = "declining"
        
        # If outcomes declining but values not changing → feedback lag
        if outcome_trend == "declining" and value_trend == "stable":
            return AnomalyReport(
                anomaly_type=AnomalyType.FEEDBACK_LAG,
                consumer_name=traj.consumer_name,
                parameter_name=traj.parameter_name,
                severity=0.7,
                evidence={
                    "outcome_trend": outcome_trend,
                    "value_trend": value_trend,
                    "recent_outcomes": recent_outcomes[-5:]
                },
                recommendation=(
                    f"Outcomes for {traj.parameter_name} are declining but parameter "
                    f"is not adjusting. Check learning loop thresholds or frequency."
                )
            )
        
        return None
    
    async def _compute_metrics(
        self, 
        trajectories: Dict[str, ParameterTrajectory]
    ) -> Dict[str, float]:
        """Compute objective learning metrics."""
        metrics = {}
        
        if not trajectories:
            return {
                "learning_efficiency": 0.0,
                "stability_index": 1.0,
                "feedback_responsiveness": 0.0,
                "coverage": 0.0
            }
        
        # Learning Efficiency: ratio of effective adjustments
        # (adjustments that improved success rate)
        total_adjustments = sum(t.adjustment_count for t in trajectories.values())
        
        # Stability Index: 1 - (oscillations / total)
        oscillation_count = 0
        for traj in trajectories.values():
            if len(traj.values) >= 4:
                # Count reversals
                for i in range(2, len(traj.values)):
                    prev_d = traj.values[i-1][1] - traj.values[i-2][1]
                    curr_d = traj.values[i][1] - traj.values[i-1][1]
                    if prev_d * curr_d < 0:
                        oscillation_count += 1
        
        stability = 1.0 - (oscillation_count / max(total_adjustments, 1))
        stability = max(0.0, min(1.0, stability))
        
        metrics["stability_index"] = stability
        
        # Average success rate
        all_success = []
        for traj in trajectories.values():
            for _, rate in traj.success_rates:
                all_success.append(rate)
        
        metrics["average_success_rate"] = (
            statistics.mean(all_success) if all_success else 0.5
        )
        
        # Coverage: parameters with recent activity
        now = datetime.utcnow()
        active_params = 0
        for t in trajectories.values():
            if t.values:
                last_ts = t.values[-1][0]
                # Safe timezone comparison
                days_diff = self._compare_datetime(now, last_ts)
                if days_diff is not None and days_diff < 7:
                    active_params += 1
        metrics["coverage"] = active_params / max(len(trajectories), 1)
        
        # Trajectory diversity: how many different consumers
        consumers = set(t.consumer_name for t in trajectories.values())
        metrics["consumer_diversity"] = len(consumers)
        
        return metrics
    
    def _calculate_health_score(
        self, 
        metrics: Dict[str, float],
        anomalies: List[AnomalyReport]
    ) -> float:
        """Calculate overall health score (0.0-1.0)."""
        # Base score from metrics
        base_score = 0.0
        weight_sum = 0.0
        
        weights = {
            "stability_index": 0.3,
            "average_success_rate": 0.3,
            "coverage": 0.2
        }
        
        for metric, weight in weights.items():
            if metric in metrics:
                base_score += metrics[metric] * weight
                weight_sum += weight
        
        if weight_sum > 0:
            base_score /= weight_sum
        else:
            base_score = 0.5
        
        # Penalize for anomalies
        anomaly_penalty = sum(a.severity * 0.1 for a in anomalies)
        anomaly_penalty = min(anomaly_penalty, 0.5)  # Cap at 50% penalty
        
        return max(0.0, min(1.0, base_score - anomaly_penalty))
    
    def _determine_health_level(
        self, 
        score: float,
        anomalies: List[AnomalyReport]
    ) -> LearningHealth:
        """Determine health level from score and anomalies."""
        critical_anomalies = [a for a in anomalies if a.severity >= 0.8]
        
        if critical_anomalies:
            return LearningHealth.CRITICAL
        
        if score >= 0.8:
            return LearningHealth.HEALTHY
        elif score >= 0.5:
            return LearningHealth.DEGRADED
        elif score >= 0.2:
            return LearningHealth.STALLED
        else:
            return LearningHealth.CRITICAL
    
    def _generate_recommendations(
        self,
        anomalies: List[AnomalyReport],
        metrics: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # From anomalies
        for anomaly in anomalies:
            if anomaly.recommendation:
                recommendations.append(anomaly.recommendation)
        
        # From metrics
        if metrics.get("stability_index", 1.0) < 0.5:
            recommendations.append(
                "System stability is low. Consider increasing step_size values "
                "to reduce oscillation."
            )
        
        if metrics.get("average_success_rate", 0.5) < 0.4:
            recommendations.append(
                "Overall success rate is below 40%. Review learning thresholds "
                "and outcome recording accuracy."
            )
        
        if metrics.get("coverage", 1.0) < 0.3:
            recommendations.append(
                "Learning coverage is low. Many parameters haven't received "
                "recent feedback. Check if outcome recording is working."
            )
        
        return recommendations[:5]  # Limit to top 5
    
    async def _count_adjustments(self, hours: int) -> int:
        """Count adjustments in time window."""
        query = f"""
            SELECT COUNT(DISTINCT (consumer_name, parameter_name, recorded_at))
            FROM plasticity_outcomes
            WHERE recorded_at > NOW() - INTERVAL '{hours} hours'
            AND parameter_value IS NOT NULL
        """
        
        try:
            result = await asyncio.to_thread(self._execute_query, query)
            return result[0][0] if result else 0
        except Exception:
            return 0
    
    async def _persist_report(self, report: LearningHealthReport) -> None:
        """Persist report to database."""
        try:
            with self.postgres.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO plasticity_observer_log (
                        overall_health, health_score, consumers_analyzed,
                        parameters_tracked, adjustments_24h, adjustments_7d,
                        anomalies_count, report_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    report.overall_health.value,
                    report.health_score,
                    report.consumers_analyzed,
                    report.parameters_tracked,
                    report.total_adjustments_24h,
                    report.total_adjustments_7d,
                    len(report.anomalies_detected),
                    json.dumps(report.to_dict())
                ))
                self.postgres.connection.commit()
        except Exception as e:
            logger.error(f"Failed to persist report: {e}")
            self.postgres.connection.rollback()
        
        # Persist anomalies
        for anomaly in report.anomalies_detected:
            try:
                with self.postgres.connection.cursor() as cur:
                    cur.execute("""
                        INSERT INTO plasticity_anomalies (
                            anomaly_type, consumer_name, parameter_name,
                            severity, evidence, recommendation
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        anomaly.anomaly_type.value,
                        anomaly.consumer_name,
                        anomaly.parameter_name,
                        anomaly.severity,
                        json.dumps(anomaly.evidence),
                        anomaly.recommendation
                    ))
                    self.postgres.connection.commit()
            except Exception as e:
                logger.warning(f"Failed to persist anomaly: {e}")
                self.postgres.connection.rollback()
    
    async def _check_alerts(self, report: LearningHealthReport) -> None:
        """Emit alerts for critical issues."""
        if report.overall_health == LearningHealth.CRITICAL:
            logger.critical(
                f"🚨 PLASTICITY CRITICAL: health_score={report.health_score:.2f}, "
                f"anomalies={len(report.anomalies_detected)}"
            )
            
            # Could emit to Cognitive Bus here for alerting
            # await self._emit_alert(report)
        
        elif report.overall_health == LearningHealth.DEGRADED:
            logger.warning(
                f"⚠️ PLASTICITY DEGRADED: health_score={report.health_score:.2f}, "
                f"anomalies={len(report.anomalies_detected)}"
            )
    
    def _execute_query(self, query: str) -> List[tuple]:
        """Execute SQL query synchronously."""
        with self.postgres.connection.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    
    # =========================================================================
    # PUBLIC API — Metrics Queries
    # =========================================================================
    
    async def get_health_history(
        self, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get health history for trend analysis."""
        query = f"""
            SELECT generated_at, overall_health, health_score, anomalies_count
            FROM plasticity_observer_log
            WHERE generated_at > NOW() - INTERVAL '{days} days'
            ORDER BY generated_at DESC
        """
        
        try:
            rows = await asyncio.to_thread(self._execute_query, query)
            return [
                {
                    "generated_at": r[0].isoformat(),
                    "overall_health": r[1],
                    "health_score": r[2],
                    "anomalies_count": r[3]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []
    
    async def get_unresolved_anomalies(self) -> List[Dict[str, Any]]:
        """Get all unresolved anomalies."""
        query = """
            SELECT id, detected_at, anomaly_type, consumer_name, 
                   parameter_name, severity, recommendation
            FROM plasticity_anomalies
            WHERE resolved_at IS NULL
            ORDER BY severity DESC, detected_at DESC
        """
        
        try:
            rows = await asyncio.to_thread(self._execute_query, query)
            return [
                {
                    "id": r[0],
                    "detected_at": r[1].isoformat(),
                    "anomaly_type": r[2],
                    "consumer_name": r[3],
                    "parameter_name": r[4],
                    "severity": r[5],
                    "recommendation": r[6]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get anomalies: {e}")
            return []
    
    async def resolve_anomaly(
        self, 
        anomaly_id: int, 
        notes: str
    ) -> bool:
        """Mark anomaly as resolved."""
        try:
            with self.postgres.connection.cursor() as cur:
                cur.execute("""
                    UPDATE plasticity_anomalies
                    SET resolved_at = NOW(), resolution_notes = %s
                    WHERE id = %s AND resolved_at IS NULL
                """, (notes, anomaly_id))
                self.postgres.connection.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to resolve anomaly: {e}")
            self.postgres.connection.rollback()
            return False
