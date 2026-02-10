# services/api_mcp/errors.py
"""MCP Error classes (opaque to LLM, transparent for logging/audit)."""


class MCPError(Exception):
    """Base class for all MCP errors (never shown to LLM)."""
    
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)
    
    def to_llm_response(self) -> dict:
        """Return sanitized error for LLM (no Sacred Orders details)."""
        return {"error": {"code": self.error_code, "message": self.message}}


class MCPToolError(MCPError):
    """Tool execution failed (API down, invalid args, etc.)."""
    
    def __init__(self, message: str):
        super().__init__(message, "TOOL_EXECUTION_ERROR")


class MCPGovernanceError(MCPError):
    """Sacred Orders blocked (Orthodoxy rejected, Sentinel blocked)."""
    
    def __init__(self, message: str):
        super().__init__(message, "INVALID_DATA")


class MCPSystemError(MCPError):
    """Internal system error (database down, Redis unreachable)."""
    
    def __init__(self, message: str):
        super().__init__(message, "SYSTEM_ERROR")
