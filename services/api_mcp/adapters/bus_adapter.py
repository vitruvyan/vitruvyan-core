"""MCP Server — Bus Adapter (StreamBus integration for Sacred Orders)."""

import logging
from core.synaptic_conclave.transport.streams import StreamBus

logger = logging.getLogger(__name__)


class MCPBusAdapter:
    """Emit MCP events to Synaptic Conclave for Sacred Orders audit trail."""

    def __init__(self):
        try:
            self.bus = StreamBus()
            logger.info("StreamBus connected for MCP service")
        except Exception as e:
            logger.warning(f"StreamBus not available: {e}")
            self.bus = None

    def emit_tool_executed(self, tool_name: str, conclave_id: str, execution_time_ms: float, status: str):
        """Notify bus that an MCP tool was executed."""
        if not self.bus:
            return
        self.bus.emit("mcp.tool.executed", {
            "tool": tool_name,
            "conclave_id": conclave_id,
            "execution_time_ms": execution_time_ms,
            "status": status,
        })
