"""
DSE Service — Bus Adapter (LIVELLO 2)
======================================

Orchestrates LIVELLO 1 consumers + StreamBus.
This is the ONLY place where:
  1. LIVELLO 1 domain functions are called with real data.
  2. Events are published to the Synaptic Conclave (StreamBus).
  3. ML strategy records are injected (from persistence adapter).

FORBIDDEN here: business logic. Delegate everything to LIVELLO 1.

Last updated: Feb 26, 2026
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.synaptic_conclave.transport.streams import StreamBus

# LIVELLO 1 domain
from infrastructure.edge.dse.domain.schemas import (
    DesignPoint,
    KPIConfig,
    NormalizationProfile,
    OptimizationDirection,
    PolicySet,
    RunArtifact,
    RunContext,
)
from infrastructure.edge.dse.consumers.sampling import (
    latin_hypercube_sampling,
    cartesian_product_sampling,
)
from infrastructure.edge.dse.consumers.engine import run_dse
from infrastructure.edge.dse.governance.strategy import SamplingStrategySelector
from infrastructure.edge.dse.events.channels import DSEChannels

from .persistence import DSEPersistenceAdapter
from ..config import config

logger = logging.getLogger(__name__)


class DSEBusAdapter:
    """
    Bridges LIVELLO 1 (pure domain) ↔ LIVELLO 2 (infrastructure).

    Instantiated once at service startup.
    """

    def __init__(
        self,
        persistence: Optional[DSEPersistenceAdapter] = None,
        stream_bus: Optional[StreamBus] = None,
    ) -> None:
        self.persistence = persistence or DSEPersistenceAdapter()
        self.bus = stream_bus or StreamBus(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
        )
        self.selector = SamplingStrategySelector()

    # ------------------------------------------------------------------
    # Prepare
    # ------------------------------------------------------------------

    def prepare(
        self,
        weaver_context: Dict[str, Any],
        user_id: str,
        trace_id: str,
        trigger: str = "unknown",
    ) -> Dict[str, Any]:
        """
        1. Fetch ML historical record (if available).
        2. Decide sampling strategy (LIVELLO 1 — pure).
        3. Generate design points (LIVELLO 1 — pure).
        4. Publish dse.sampling.completed.
        Return summary dict.
        """
        logger.info("DSEBusAdapter.prepare trace_id=%s trigger=%s", trace_id, trigger)

        # Inject ML record (DB call belongs here, not in LIVELLO 1)
        ml_record = self.persistence.get_best_sampling_strategy()

        # Pure decision (LIVELLO 1)
        strategy, reason, confidence = self.selector.decide(weaver_context, ml_record)

        # Pure generation (LIVELLO 1)
        if strategy == "lhs":
            raw_points = latin_hypercube_sampling(
                weaver_context,
                num_samples=config.DEFAULT_NUM_SAMPLES,
                seed=config.DEFAULT_SEED,
            )
        else:
            raw_points = cartesian_product_sampling(weaver_context)

        # Convert to domain objects
        design_points = self._build_design_points(raw_points, weaver_context)

        # Publish event
        self._publish(DSEChannels.SAMPLING_COMPLETED, {
            "trace_id":            trace_id,
            "user_id":             user_id,
            "strategy":            strategy,
            "reason":              reason,
            "confidence":          confidence,
            "design_points_count": len(design_points),
            "trigger":             trigger,
            "timestamp":           datetime.utcnow().isoformat(),
        })

        logger.info(
            "Prepare complete: %d design points (strategy=%s, conf=%.2f)",
            len(design_points), strategy, confidence,
        )
        return {
            "design_points":        design_points,
            "strategy":             strategy,
            "confidence":           confidence,
            "design_points_count":  len(design_points),
        }

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def execute_run(
        self,
        design_points: List[DesignPoint],
        policy_set: PolicySet,
        normalization_profile: NormalizationProfile,
        run_context: RunContext,
        seed: int,
    ) -> RunArtifact:
        """
        Execute DSE compute engine (LIVELLO 1 — pure).
        Persist result + publish dse.run.completed.
        """
        start = time.time()
        artifact = run_dse(design_points, policy_set, normalization_profile, run_context, seed)
        elapsed_ms = (time.time() - start) * 1000

        logger.info(
            "DSE run complete: pareto=%d/%d  hash=%s… (%.1fms)",
            artifact.pareto_count, artifact.total_design_points,
            artifact.input_hash[:12], elapsed_ms,
        )

        # Persist audit record
        self.persistence.log_run({
            "trace_id":            run_context.trace_id,
            "user_id":             run_context.user_id,
            "use_case":            run_context.use_case,
            "strategy":            "run",
            "total_design_points": artifact.total_design_points,
            "pareto_count":        artifact.pareto_count,
            "input_hash":          artifact.input_hash,
            "seed":                artifact.seed,
            "schema_version":      artifact.schema_version,
        })

        # Publish events
        event_payload = {
            "trace_id":            run_context.trace_id,
            "user_id":             run_context.user_id,
            "pareto_count":        artifact.pareto_count,
            "total_design_points": artifact.total_design_points,
            "input_hash":          artifact.input_hash,
            "timestamp":           datetime.utcnow().isoformat(),
        }
        self._publish(DSEChannels.RUN_COMPLETED, event_payload)
        self._publish(DSEChannels.VAULT_ARCHIVE_REQUESTED, {
            **event_payload,
            "artifact_type": "dse_run",
        })

        return artifact

    # ------------------------------------------------------------------
    # Governance helpers
    # ------------------------------------------------------------------

    def request_governance(self, trace_id: str, design_points_count: int, strategy: str) -> None:
        self._publish(DSEChannels.GOVERNANCE_REQUESTED, {
            "trace_id":            trace_id,
            "design_points_count": design_points_count,
            "strategy":            strategy,
            "timestamp":           datetime.utcnow().isoformat(),
        })

    def log_rejection(self, trace_id: str, reason: str, rejected_by: Optional[str] = None) -> None:
        self.persistence.log_rejection(trace_id, reason, rejected_by)
        logger.warning("DSE run rejected: trace_id=%s reason=%s", trace_id, reason)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _publish(self, channel: str, payload: Dict[str, Any]) -> None:
        try:
            self.bus.publish(channel, json.dumps(payload, default=str))
            logger.debug("Published → %s", channel)
        except Exception as exc:
            logger.warning("StreamBus publish failed (%s): %s", channel, exc)

    @staticmethod
    def _build_design_points(
        raw_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[DesignPoint]:
        """Convert raw sampling output to domain DesignPoint objects."""
        result: List[DesignPoint] = []
        for i, raw in enumerate(raw_points):
            # Default numeric knobs derived from context tags
            knobs: Dict[str, Any] = {
                "compliance_threshold": round(0.3 + (i % 7) * 0.1, 2),
                "audit_frequency_days": 30 + (i % 4) * 30,
                "risk_tolerance":       round(0.1 + (i % 5) * 0.15, 2),
            }
            result.append(DesignPoint(
                design_id=i,
                knobs=knobs,
                tags={k: str(v) for k, v in raw.items()},
            ))
        return result
