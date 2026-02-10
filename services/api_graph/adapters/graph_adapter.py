"""
Graph Orchestrator Adapter

Orchestrates LangGraph execution (request-response pattern).
NO event bus integration (graph is HTTP sync, not event-driven).

Layer: LIVELLO 2 (Service — orchestration)
"""

import logging
from typing import Dict, Any
from datetime import datetime

from core.orchestration.langgraph.graph_runner import run_graph_once, run_graph
from core.orchestration.langgraph.simple_graph_audit_monitor import get_simple_graph_monitor
from api_graph.config import settings

logger = logging.getLogger(__name__)


class GraphOrchestrationAdapter:
    """
    Adapter for orchestrating LangGraph execution.
    
    Responsibilities:
    - Execute graph with run_graph_once() (input_text, user_id)
    - Execute graph with run_graph() (raw dict payload)
    - Optional audit monitoring integration
    - Add execution metadata (timestamp, audit status)
    
    Pattern: Request-Response (HTTP sync, NOT event-driven)
    """
    
    def __init__(self):
        """Initialize graph adapter."""
        self.monitor = get_simple_graph_monitor()
        self.audit_enabled = settings.AUDIT_ENABLED
        
        logger.info(f"GraphOrchestrationAdapter initialized (audit={self.audit_enabled})")
    
    async def execute_graph(self, input_text: str, user_id: str) -> Dict[str, Any]:
        """
        Execute graph with input_text and user_id.
        
        Args:
            input_text: User input text to process
            user_id: User identifier
        
        Returns:
            Graph execution result with metadata
        """
        context = {"input_text": input_text, "user_id": user_id}
        
        try:
            if self.audit_enabled:
                # Execute with audit monitoring
                async with self.monitor.monitor_graph_execution(context):
                    result = run_graph_once(input_text, user_id=user_id)
                    result["audit_monitored"] = True
            else:
                # Execute without audit
                result = run_graph_once(input_text, user_id=user_id)
                result["audit_monitored"] = False
            
            # Add execution metadata
            result["execution_timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "execution_timestamp": datetime.now().isoformat(),
                "audit_monitored": self.audit_enabled
            }
    
    def execute_graph_dispatch(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with raw dispatch payload.
        
        Args:
            payload: Raw dict payload (used by dispatcher)
        
        Returns:
            Graph execution result
        """
        try:
            result = run_graph(payload)
            
            # Add metadata
            result["execution_timestamp"] = datetime.now().isoformat()
            result["audit_monitored"] = self.audit_enabled
            
            return result
            
        except Exception as e:
            logger.error(f"Graph dispatch execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "execution_timestamp": datetime.now().isoformat()
            }
    
    async def execute_graph_with_audit(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with explicit audit monitoring.
        Used by /graph/dispatch endpoint.
        
        Args:
            payload: Graph payload dict
        
        Returns:
            Result with audit metadata
        """
        import json
        
        async with self.monitor.monitor_graph_execution(payload):
            result = run_graph(payload)
            
            json_one_line = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            human = "Leonardo: grafo eseguito con audit monitoring. Se mancano slot chiave ti chiedo un chiarimento."
            
            return {
                "json": json_one_line,
                "human": human,
                "audit_monitored": True,
                "timestamp": datetime.now().isoformat()
            }
