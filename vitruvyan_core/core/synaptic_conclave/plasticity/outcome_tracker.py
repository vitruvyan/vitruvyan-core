"""
Outcome Tracker — Links Decisions to Outcomes
==============================================

Tracks the results of consumer decisions for learning feedback.
PostgreSQL backend with async interface.

Sacred Order: Memory (Persistence Layer)

Author: Vitruvyan Core Team
Date: January 24, 2026
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.leo.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.plasticity import metrics as plasticity_metrics

logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    """
    Record of a decision outcome for learning.
    
    Attributes:
        decision_event_id: CognitiveEvent.id that made the decision
        outcome_type: Type of outcome (e.g., 'escalation_resolved', 'false_positive')
        outcome_value: Numeric success metric (0.0 = failure, 1.0 = success)
        consumer_name: Which consumer made the decision
        parameter_name: Which parameter was used (optional)
        parameter_value: Value of parameter at decision time (optional)
        metadata: Additional context
    """
    decision_event_id: str
    outcome_type: str
    outcome_value: float  # 0.0-1.0 scale
    consumer_name: str
    parameter_name: Optional[str] = None
    parameter_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate outcome_value range."""
        if not 0.0 <= self.outcome_value <= 1.0:
            raise ValueError(
                f"outcome_value must be 0.0-1.0, got {self.outcome_value}"
            )


class OutcomeTracker:
    """
    Tracks decision outcomes for learning feedback.
    
    Links consumer decisions (CognitiveEvent IDs) to their outcomes
    (success/failure metrics). Provides success rate analysis for
    parameter tuning.
    
    Architecture:
        - PostgreSQL backend via PostgresAgent
        - Async interface (asyncio.to_thread for sync operations)
        - 7-day default lookback window
        - Indexed by consumer_name, parameter_name, decision_event_id
    
    Usage:
        tracker = OutcomeTracker(postgres_agent)
        
        # Record outcome
        await tracker.record_outcome(Outcome(
            decision_event_id="evt-123",
            outcome_type="escalation_resolved",
            outcome_value=1.0,
            consumer_name="NarrativeEngine",
            parameter_name="confidence_threshold",
            parameter_value=0.6
        ))
        
        # Get success rate
        rate = await tracker.get_success_rate(
            "NarrativeEngine", 
            "confidence_threshold",
            lookback_hours=168  # 7 days
        )
    """
    
    def __init__(self, postgres: PostgresAgent):
        """
        Initialize outcome tracker.
        
        Args:
            postgres: PostgresAgent instance for database operations
        """
        self.postgres = postgres
        logger.info("OutcomeTracker initialized")
    
    async def record_outcome(self, outcome: Outcome) -> None:
        """
        Record a decision outcome to PostgreSQL.
        
        Args:
            outcome: Outcome dataclass with decision details
        
        Raises:
            RuntimeError: If database insert fails
        """
        query = """
            INSERT INTO plasticity_outcomes 
            (decision_event_id, outcome_type, outcome_value, consumer_name, 
             parameter_name, parameter_value, outcome_metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            await asyncio.to_thread(
                self._execute_insert,
                query,
                (
                    outcome.decision_event_id,
                    outcome.outcome_type,
                    outcome.outcome_value,
                    outcome.consumer_name,
                    outcome.parameter_name,
                    outcome.parameter_value,
                    json.dumps(outcome.metadata)
                )
            )
            logger.info(
                f"✅ Outcome recorded: {outcome.consumer_name}.{outcome.parameter_name} "
                f"outcome={outcome.outcome_value:.2f} ({outcome.outcome_type})"
            )
            
            # Record metrics
            if outcome.parameter_name:
                plasticity_metrics.record_outcome(
                    consumer=outcome.consumer_name,
                    parameter=outcome.parameter_name,
                    outcome_type=outcome.outcome_type,
                    outcome_value=outcome.outcome_value
                )
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            raise RuntimeError(f"Outcome recording failed: {e}") from e
    
    def _execute_insert(self, query: str, params: tuple) -> None:
        """Execute INSERT query synchronously (called via asyncio.to_thread)."""
        with self.postgres.connection.cursor() as cur:
            cur.execute(query, params)
            self.postgres.connection.commit()
    
    async def get_outcomes_for_parameter(
        self, 
        consumer_name: str, 
        parameter_name: str, 
        lookback_hours: int = 168  # 7 days default
    ) -> List[Outcome]:
        """
        Get recent outcomes for a specific parameter.
        
        Args:
            consumer_name: Name of consumer (e.g., 'NarrativeEngine')
            parameter_name: Parameter name (e.g., 'confidence_threshold')
            lookback_hours: Time window to query (default 168 = 7 days)
        
        Returns:
            List of Outcome objects, ordered by most recent first
        """
        query = """
            SELECT decision_event_id, outcome_type, outcome_value, 
                   consumer_name, parameter_name, parameter_value, outcome_metadata
            FROM plasticity_outcomes
            WHERE consumer_name = %s 
              AND parameter_name = %s
              AND recorded_at > NOW() - INTERVAL '%s hours'
            ORDER BY recorded_at DESC
        """
        
        try:
            rows = await asyncio.to_thread(
                self._execute_select,
                query,
                (consumer_name, parameter_name, lookback_hours)
            )
            
            outcomes = []
            for row in rows:
                # Handle metadata (already dict from JSONB, not string)
                metadata = row[6] if isinstance(row[6], dict) else json.loads(row[6]) if row[6] else {}
                outcomes.append(Outcome(
                    decision_event_id=row[0],
                    outcome_type=row[1],
                    outcome_value=row[2],
                    consumer_name=row[3],
                    parameter_name=row[4],
                    parameter_value=row[5],
                    metadata=metadata
                ))
            
            logger.debug(
                f"Retrieved {len(outcomes)} outcomes for "
                f"{consumer_name}.{parameter_name}"
            )
            return outcomes
        
        except Exception as e:
            logger.error(f"Failed to retrieve outcomes: {e}")
            return []
    
    def _execute_select(self, query: str, params: tuple) -> List[tuple]:
        """Execute SELECT query synchronously (called via asyncio.to_thread)."""
        with self.postgres.connection.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    async def get_success_rate(
        self, 
        consumer_name: str, 
        parameter_name: str, 
        lookback_hours: int = 168
    ) -> float:
        """
        Calculate success rate for a parameter (0.0-1.0).
        
        Success rate = average of outcome_value across all outcomes.
        
        Args:
            consumer_name: Name of consumer
            parameter_name: Parameter name
            lookback_hours: Time window (default 168 = 7 days)
        
        Returns:
            Success rate (0.0-1.0), or 0.5 if no data (neutral)
        """
        outcomes = await self.get_outcomes_for_parameter(
            consumer_name, parameter_name, lookback_hours
        )
        
        if not outcomes:
            logger.warning(
                f"No outcomes found for {consumer_name}.{parameter_name}, "
                f"returning neutral 0.5"
            )
            return 0.5  # Neutral if no data
        
        success_rate = sum(o.outcome_value for o in outcomes) / len(outcomes)
        
        logger.info(
            f"📊 Success rate for {consumer_name}.{parameter_name}: "
            f"{success_rate:.2%} (n={len(outcomes)})"
        )
        
        # Update metrics
        plasticity_metrics.update_success_rate(
            consumer=consumer_name,
            parameter=parameter_name,
            success_rate=success_rate
        )
        
        return success_rate
    
    async def get_recent_adjustments(
        self,
        consumer_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent parameter adjustments (for monitoring).
        
        Args:
            consumer_name: Name of consumer
            limit: Maximum number of results
        
        Returns:
            List of adjustment records with metadata
        """
        query = """
            SELECT parameter_name, parameter_value, outcome_type, 
                   outcome_value, recorded_at
            FROM plasticity_outcomes
            WHERE consumer_name = %s
            ORDER BY recorded_at DESC
            LIMIT %s
        """
        
        try:
            rows = await asyncio.to_thread(
                self._execute_select,
                query,
                (consumer_name, limit)
            )
            
            adjustments = []
            for row in rows:
                adjustments.append({
                    "parameter_name": row[0],
                    "parameter_value": row[1],
                    "outcome_type": row[2],
                    "outcome_value": row[3],
                    "recorded_at": row[4].isoformat() if row[4] else None
                })
            
            return adjustments
        
        except Exception as e:
            logger.error(f"Failed to retrieve adjustments: {e}")
            return []
