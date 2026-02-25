-- MCP Gateway Vault Keepers Schema
-- Sacred Orders archival table for MCP tool executions
-- Created: Feb 11, 2026 (Domain-Agnostic Refactoring)

-- Table: mcp_tool_calls
-- Purpose: Audit trail for all MCP tool executions with Sacred Orders validation status
CREATE TABLE IF NOT EXISTS mcp_tool_calls (
    conclave_id UUID PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    args JSONB NOT NULL,
    result JSONB NOT NULL,
    orthodoxy_status VARCHAR(20) NOT NULL CHECK (orthodoxy_status IN ('blessed', 'purified', 'heretical')),
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    execution_time_ms FLOAT,
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_user ON mcp_tool_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_tool ON mcp_tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_created ON mcp_tool_calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_orthodoxy ON mcp_tool_calls(orthodoxy_status);
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_conclave ON mcp_tool_calls(conclave_id);

-- Grant permissions
GRANT SELECT, INSERT ON mcp_tool_calls TO mercator_user;

-- Comment for documentation
COMMENT ON TABLE mcp_tool_calls IS 'MCP Gateway Vault Keepers audit trail - tracks all tool executions with Sacred Orders validation status (blessed/purified/heretical)';
COMMENT ON COLUMN mcp_tool_calls.conclave_id IS 'Unique UUID for this tool execution (Synaptic Conclave correlation ID)';
COMMENT ON COLUMN mcp_tool_calls.orthodoxy_status IS 'Sacred Orders validation result: blessed (valid), purified (warnings), heretical (rejected)';
COMMENT ON COLUMN mcp_tool_calls.args IS 'Tool input arguments (JSONB for domain-agnostic flexibility)';
COMMENT ON COLUMN mcp_tool_calls.result IS 'Tool output data (JSONB for domain-agnostic flexibility)';
