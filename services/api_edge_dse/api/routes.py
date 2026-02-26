"""
DSE Service — HTTP Routes (LIVELLO 2)
======================================

Thin endpoints: validate → delegate to bus_adapter → return.
Zero business logic here.

Endpoints:
    POST /run_dse                — Execute DSE compute (stateless)
    POST /dse/prepare            — Prepare design points from Pattern Weavers context
    POST /dse/run_from_context   — Full synchronous pipeline (LangGraph entry point)
    POST /dse/log_rejection      — Log a Conclave governance rejection
    GET  /health                 — Service health

Last updated: Feb 26, 2026
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..adapters.bus_adapter import DSEBusAdapter
from ..config import config
from ..models.schemas import (
    LogRejectionRequest,
    PrepareDSERequest,
    PrepareDSEResponse,
    RunDSERequest,
    RunDSEResponse,
    RunFromContextRequest,
    RunFromContextResponse,
)
from infrastructure.edge.dse.domain.schemas import (
    DesignPoint,
    KPIConfig,
    NormalizationProfile,
    OptimizationDirection,
    PolicySet,
    RunContext,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazily initialized adapter (set by main.py on startup)
_adapter: DSEBusAdapter = None  # type: ignore[assignment]


def get_adapter() -> DSEBusAdapter:
    if _adapter is None:
        raise RuntimeError("DSEBusAdapter not initialized")
    return _adapter


def set_adapter(adapter: DSEBusAdapter) -> None:
    global _adapter
    _adapter = adapter


# ---------------------------------------------------------------------------
# POST /run_dse
# ---------------------------------------------------------------------------

@router.post("/run_dse", response_model=RunDSEResponse)
async def run_dse_endpoint(request: RunDSERequest, adapter: DSEBusAdapter = Depends(get_adapter)):
    """Execute Design Space Exploration (stateless pure compute)."""
    logger.info("/run_dse: %d design_points", len(request.design_points))
    start = time.time()
    try:
        dps = [
            DesignPoint(
                design_id=dp["design_id"],
                knobs=dp["knobs"],
                constraints=dp.get("constraints", {}),
                tags=dp.get("tags", {}),
            )
            for dp in request.design_points
        ]
        kpi_cfgs = [
            KPIConfig(
                kpi_name=k["kpi_name"],
                min_value=k["min_value"],
                max_value=k["max_value"],
                direction=OptimizationDirection(k["direction"]),
                weight=k.get("weight", 1.0),
            )
            for k in request.normalization_profile["kpi_configs"]
        ]
        profile = NormalizationProfile(
            profile_name=request.normalization_profile.get("profile_name", "default"),
            kpi_configs=kpi_cfgs,
        )
        policy = PolicySet(
            policy_name=request.policy_set.get("policy_name", "default"),
            optimization_objective=request.policy_set.get("optimization_objective", "maximize"),
            doctrine_weights=request.policy_set.get("doctrine_weights", {}),
        )
        ctx = RunContext(
            user_id=request.run_context.get("user_id", "unknown"),
            trace_id=request.run_context.get("trace_id", "unknown"),
            use_case=request.run_context.get("use_case", "unknown"),
            metadata=request.run_context.get("metadata", {}),
        )
        artifact = adapter.execute_run(dps, policy, profile, ctx, request.seed)
        elapsed = (time.time() - start) * 1000
        return RunDSEResponse(
            status="success",
            data={
                "pareto_frontier":      artifact.pareto_frontier,
                "ranking_dottrinale":   artifact.ranking_dottrinale,
                "input_hash":           artifact.input_hash,
                "seed":                 artifact.seed,
                "schema_version":       artifact.schema_version,
                "asof":                 artifact.asof.isoformat(),
                "total_design_points":  artifact.total_design_points,
                "pareto_count":         artifact.pareto_count,
            },
            execution_time_ms=elapsed,
        )
    except Exception as exc:
        logger.error("/run_dse failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /dse/prepare
# ---------------------------------------------------------------------------

@router.post("/dse/prepare", response_model=PrepareDSEResponse)
async def prepare_dse_endpoint(request: PrepareDSERequest, adapter: DSEBusAdapter = Depends(get_adapter)):
    """Prepare design points from Pattern Weavers context."""
    logger.info("/dse/prepare trace_id=%s trigger=%s", request.trace_id, request.trigger)
    try:
        result = adapter.prepare(
            weaver_context=request.weaver_context,
            user_id=request.user_id,
            trace_id=request.trace_id,
            trigger=request.trigger,
        )
        return PrepareDSEResponse(
            status="success",
            design_points_count=result["design_points_count"],
            strategy=result["strategy"],
            confidence=result["confidence"],
            trace_id=request.trace_id,
        )
    except Exception as exc:
        logger.error("/dse/prepare failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /dse/log_rejection
# ---------------------------------------------------------------------------

@router.post("/dse/log_rejection")
async def log_rejection_endpoint(request: LogRejectionRequest, adapter: DSEBusAdapter = Depends(get_adapter)):
    """Log a Conclave governance rejection."""
    logger.info("/dse/log_rejection trace_id=%s reason=%s", request.trace_id, request.reason)
    adapter.log_rejection(request.trace_id, request.reason, request.rejected_by)
    return {"status": "logged", "trace_id": request.trace_id}


# ---------------------------------------------------------------------------
# POST /dse/run_from_context  (LangGraph synchronous entry point)
# ---------------------------------------------------------------------------

@router.post("/dse/run_from_context", response_model=RunFromContextResponse)
async def run_from_context_endpoint(
    request: RunFromContextRequest,
    adapter: DSEBusAdapter = Depends(get_adapter),
):
    """
    Full synchronous DSE pipeline from a Pattern Weavers weaver_context.

    Called by the LangGraph dse_node. Single call → prepare + sample + Pareto
    + dottrinale ranking + persist + StreamBus events.
    """
    logger.info(
        "/dse/run_from_context trace_id=%s user_id=%s",
        request.trace_id, request.user_id,
    )
    try:
        result = adapter.run_from_context(
            weaver_context=request.weaver_context,
            user_id=request.user_id,
            trace_id=request.trace_id,
            seed=request.seed,
            use_case=request.use_case,
        )
        return RunFromContextResponse(
            status="success",
            trace_id=request.trace_id,
            total_design_points=result["total_design_points"],
            pareto_count=result["pareto_count"],
            strategy=result["strategy"],
            confidence=result["confidence"],
            input_hash=result["input_hash"],
            asof=result["asof"],
            top_designs=result["ranking_dottrinale"][:3],
            artifact={
                "pareto_frontier":    result["pareto_frontier"],
                "ranking_dottrinale": result["ranking_dottrinale"],
            },
        )
    except Exception as exc:
        logger.error("/dse/run_from_context failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {
        "status":    "healthy",
        "service":   config.SERVICE_NAME,
        "version":   config.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }
