# services/api_mcp/schemas/models.py
"""Pydantic request/response models for MCP API."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    """MCP tool execution request."""
    tool: str = Field(..., description="Tool name (e.g., 'screen_entities')")
    args: Dict[str, Any] = Field(..., description="Tool arguments")
    user_id: str = Field(..., description="User ID for audit trail")


class MCPResponse(BaseModel):
    """Standard MCP response format."""
    status: str = Field(..., description="'success' or 'error'")
    tool: str = Field(..., description="Tool name")
    orthodoxy_status: Optional[str] = Field(None, description="Orthodoxy validation status")
    data: Optional[Dict[str, Any]] = Field(None, description="Tool result data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if status='error'")
    conclave_id: str = Field(..., description="Synaptic Conclave UUID")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    cached: bool = Field(False, description="Whether result was cached")
