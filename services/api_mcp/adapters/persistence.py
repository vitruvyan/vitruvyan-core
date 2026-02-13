"""MCP Server — Persistence Adapter."""

import logging
from core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class MCPPersistenceAdapter:
    """Persistence operations for MCP audit trail."""

    def __init__(self):
        try:
            self.pg = PostgresAgent()
            logger.info("PostgresAgent connected for MCP service")
        except Exception as e:
            logger.warning(f"PostgresAgent not available: {e}")
            self.pg = None

    def log_execution(self, conclave_id: str, tool_name: str, user_id: str, status: str, execution_time_ms: float):
        """Log MCP tool execution to PostgreSQL."""
        if not self.pg:
            return
        self.pg.execute(
            "INSERT INTO mcp_executions (conclave_id, tool, user_id, status, execution_time_ms) VALUES (%s, %s, %s, %s, %s)",
            (conclave_id, tool_name, user_id, status, execution_time_ms),
        )
