# services/api_mcp/api/routes.py
"""MCP API routes."""

import time
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from schemas import ExecuteRequest, MCPResponse, get_tool_schemas
from tools import get_tool_executors, normalize_tool_request
from middleware import sacred_orders_middleware
from monitoring import mcp_requests_total, mcp_execution_duration

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "mercator_mcp_server", "version": "1.0.0",
        "description": "Model Context Protocol Bridge to Sacred Orders",
        "endpoints": {"tools": "/tools", "execute": "/execute", "health": "/health", "metrics": "/metrics"}
    }


@router.get("/health")
async def health():
    """Health check."""
    from middleware import get_stream_bus
    stream_bus = get_stream_bus()
    return {"status": "healthy", "service": "mercator_mcp_server", "bus": "connected" if stream_bus else "disconnected", "timestamp": datetime.utcnow().isoformat()}


@router.get("/tools")
async def get_tools():
    """Return OpenAI Function Calling compatible tool schemas."""
    tool_schemas = get_tool_schemas()
    logger.info("📋 Returning MCP tool schemas")
    return {"status": "success", "tools": tool_schemas, "total_tools": len(tool_schemas)}


@router.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """Execute MCP tool via Sacred Orders Middleware."""
    start_time = time.time()
    conclave_id = str(uuid.uuid4())
    requested_tool = request.tool
    args = request.args
    user_id = request.user_id
    tool_executors = get_tool_executors()
    resolved_tool, normalized_args = normalize_tool_request(requested_tool, args)
    
    logger.info(
        "🚀 MCP Execute: requested_tool=%s resolved_tool=%s user=%s conclave_id=%s",
        requested_tool,
        resolved_tool,
        user_id,
        conclave_id,
    )
    
    try:
        if resolved_tool not in tool_executors:
            mcp_requests_total.labels(tool=resolved_tool or requested_tool, status="error").inc()
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error": {
                        "code": "UNKNOWN_TOOL",
                        "message": f"Tool '{requested_tool}' not found",
                        "available_tools": list(tool_executors.keys()),
                    },
                },
            )
        
        executor = tool_executors[resolved_tool]
        result_data = await executor(normalized_args, user_id)
        result = {"status": "success", "tool": resolved_tool, "data": result_data}
        
        execution_time_ms = (time.time() - start_time) * 1000
        orthodoxy_status = await sacred_orders_middleware(
            resolved_tool,
            normalized_args,
            result,
            user_id,
            conclave_id,
            execution_time_ms,
        )
        
        mcp_requests_total.labels(tool=resolved_tool, status="success").inc()
        mcp_execution_duration.labels(tool=resolved_tool).observe(time.time() - start_time)
        
        response = MCPResponse(
            status="success",
            tool=resolved_tool,
            orthodoxy_status=orthodoxy_status,
            data=result_data,
            conclave_id=conclave_id,
            execution_time_ms=execution_time_ms,
            cached=False,
        )
        payload = response.model_dump()
        if resolved_tool != requested_tool:
            payload["requested_tool"] = requested_tool
            payload["resolved_tool"] = resolved_tool
        
        logger.info("✅ MCP Execute success: %s (%.2fms)", resolved_tool, execution_time_ms)
        return payload
    
    except ValueError as e:
        mcp_requests_total.labels(tool=resolved_tool or requested_tool, status="heretical").inc()
        logger.error(f"❌ Orthodoxy rejected: {e}")
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "tool": resolved_tool or requested_tool,
                "error": {"code": "ORTHODOXY_REJECTED", "message": str(e)},
                "orthodoxy_status": "heretical",
                "conclave_id": conclave_id,
                "execution_time_ms": (time.time() - start_time) * 1000,
            },
        )

    except HTTPException:
        raise
    
    except Exception as e:
        mcp_requests_total.labels(tool=resolved_tool or requested_tool, status="error").inc()
        logger.error(f"❌ MCP Execute failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "tool": resolved_tool or requested_tool,
                "error": {"code": "EXECUTION_FAILED", "message": str(e)},
                "conclave_id": conclave_id,
                "execution_time_ms": (time.time() - start_time) * 1000,
            },
        )


@router.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
