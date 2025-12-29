-- MCP Tool Calls Table (Phase 1 - Sacred Orders Archival)
-- Vitruvyan-OS Model Context Protocol Integration
-- Date: December 27, 2025
--
-- Purpose: Archive ALL MCP tool calls for Sacred Orders audit trail
-- 100% archiving guarantee (blessed + heretical calls)

CREATE TABLE IF NOT EXISTS mcp_tool_calls (
    conclave_id UUID PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    args JSONB NOT NULL,
    result JSONB NOT NULL,
    orthodoxy_status VARCHAR(20) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance indexes for Sacred Orders queries
CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_user_id 
    ON mcp_tool_calls(user_id);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_tool_name 
    ON mcp_tool_calls(tool_name);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_created_at 
    ON mcp_tool_calls(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mcp_tool_calls_orthodoxy_status 
    ON mcp_tool_calls(orthodoxy_status);

-- Comments for Sacred Orders documentation
COMMENT ON TABLE mcp_tool_calls IS 'Sacred Orders archival for Model Context Protocol tool calls';
COMMENT ON COLUMN mcp_tool_calls.conclave_id IS 'UUID linking Sacred Orders events across tables';
COMMENT ON COLUMN mcp_tool_calls.orthodoxy_status IS 'blessed | heretical_zscore | heretical_composite | heretical_invalid';
COMMENT ON COLUMN mcp_tool_calls.args IS 'Original tool arguments (for replay/debugging)';
COMMENT ON COLUMN mcp_tool_calls.result IS 'Tool execution result (empty for heretical calls)';
