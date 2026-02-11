# services/api_mcp/api/routes.py
"""MCP API routes."""

import time
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from schemas import TOOL_SCHEMAS, ExecuteRequest, MCPResponse
from tools import TOOL_EXECUTORS
from middleware import sacred_orders_middleware

logger = logging.getLogger(__name__)

router = APIRouter()

# Prometheus metrics
mcp_requests_total = Counter('vitruvyan_mcp_requests_total', 'Total MCP tool requests', ['tool', 'status'])
mcp_execution_duration = Histogram('vitruvyan_mcp_execution_duration_seconds', 'MCP execution duration', ['tool'])


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "vitruvyan_mcp_server", "version": "1.0.0",
        "description": "Model Context Protocol Bridge to Sacred Orders",
        "endpoints": {"tools": "/tools", "execute": "/execute", "health": "/health", "metrics": "/metrics"}
    }


@router.get("/health")
async def health():
    """Health check."""
    from middleware import get_stream_bus
    stream_bus = get_stream_bus()
    return {"status": "healthy", "service": "vitruvyan_mcp_server", "bus": "connected" if stream_bus else "disconnected", "timestamp": datetime.utcnow().isoformat()}


@router.get("/tools")
async def get_tools():
    """Return OpenAI Function Calling compatible tool schemas."""
    logger.info("📋 Returning MCP tool schemas")
    return {"status": "success", "tools": TOOL_SCHEMAS, "total_tools": len(TOOL_SCHEMAS)}


@router.post("/execute")
async def execute_tool(request: ExecuteRequest):
    """Execute MCP tool via Sacred Orders Middleware."""
    start_time = time.time()
    conclave_id = str(uuid.uuid4())
    tool_name = request.tool
    args = request.args
    user_id = request.user_id
    
    logger.info(f"🚀 MCP Execute: tool={tool_name}, user={user_id}, conclave_id={conclave_id}")
    
    try:
        if tool_name not in TOOL_EXECUTORS:
            mcp_requests_total.labels(tool=tool_name, status="error").inc()
            raise HTTPException(status_code=400, detail={"status": "error", "error": {"code": "UNKNOWN_TOOL", "message": f"Tool '{tool_name}' not found", "available_tools": list(TOOL_EXECUTORS.keys())}})
        
        executor = TOOL_EXECUTORS[tool_name]
        result_data = await executor(args, user_id)
        result = {"status": "success", "tool": tool_name, "data": result_data}
        
        orthodoxy_status = await sacred_orders_middleware(tool_name, args, result, user_id, conclave_id)
        execution_time_ms = (time.time() - start_time) * 1000
        
        mcp_requests_total.labels(tool=tool_name, status="success").inc()
        mcp_execution_duration.labels(tool=tool_name).observe(time.time() - start_time)
        
        response = MCPResponse(status="success", tool=tool_name, orthodoxy_status=orthodoxy_status, data=result_data, conclave_id=conclave_id, execution_time_ms=execution_time_ms, cached=False)
        
        logger.info(f"✅ MCP Execute success: {tool_name} ({execution_time_ms:.2f}ms)")
        return response.model_dump()
    
    except ValueError as e:
        mcp_requests_total.labels(tool=tool_name, status="heretical").inc()
        logger.error(f"❌ Orthodoxy rejected: {e}")
        return JSONResponse(status_code=422, content={"status": "error", "tool": tool_name, "error": {"code": "ORTHODOXY_REJECTED", "message": str(e)}, "orthodoxy_status": "heretical", "conclave_id": conclave_id, "execution_time_ms": (time.time() - start_time) * 1000})
    
    except Exception as e:
        mcp_requests_total.labels(tool=tool_name, status="error").inc()
        logger.error(f"❌ MCP Execute failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "tool": tool_name, "error": {"code": "EXECUTION_FAILED", "message": str(e)}, "conclave_id": conclave_id, "execution_time_ms": (time.time() - start_time) * 1000})


@router.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
