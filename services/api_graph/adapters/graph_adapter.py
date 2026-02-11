"""
Graph Orchestrator Adapter

Orchestrates LangGraph execution (request-response pattern).
NO event bus integration (graph is HTTP sync, not event-driven).

Layer: LIVELLO 2 (Service — orchestration)
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from core.orchestration.langgraph.graph_runner import run_graph_once, run_graph
from core.orchestration.langgraph.graph_flow import build_graph, build_minimal_graph
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
        
        if settings.ENABLE_MINIMAL_GRAPH:
            self.graph = build_minimal_graph()
        else:
            self.graph = build_graph()
        
        logger.info(f"GraphOrchestrationAdapter initialized (audit={self.audit_enabled}, minimal={settings.ENABLE_MINIMAL_GRAPH})")
    
    async def execute_graph(self, input_text: str, user_id: str) -> Dict[str, Any]:
        """
        Execute graph with input_text and user_id.
        
        Args:
            input_text: User input text to process
            user_id: User identifier
        
        Returns:
            Graph execution result transformed to GraphResponseSchema
        """
        import json
        
        context = {"input_text": input_text, "user_id": user_id}
        
        try:
            if self.audit_enabled:
                # Execute with audit monitoring
                async with self.monitor.monitor_graph_execution(context):
                    raw_result = run_graph_once(input_text, user_id=user_id)
                    audit_monitored = True
            else:
                # Execute without audit
                raw_result = run_graph_once(input_text, user_id=user_id)
                audit_monitored = False
            
            # Transform core domain output → service API schema (GraphResponseSchema)
            return self._transform_to_api_schema(raw_result, audit_monitored)
            
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            # Return error in API schema format
            error_result = {
                "status": "error",
                "error": str(e),
                "narrative": f"Errore durante l'esecuzione del grafo: {str(e)}"
            }
            return self._transform_to_api_schema(error_result, self.audit_enabled)
    
    def execute_graph_dispatch(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with raw dispatch payload.
        
        Args:
            payload: Raw dict payload (used by dispatcher)
        
        Returns:
            Graph execution result transformed to GraphResponseSchema
        """
        try:
            raw_result = run_graph(payload)
            
            # Transform to API schema
            return self._transform_to_api_schema(raw_result, self.audit_enabled)
            
        except Exception as e:
            logger.error(f"Graph dispatch execution failed: {e}", exc_info=True)
            # Return error in API schema format
            error_result = {
                "status": "error",
                "error": str(e),
                "narrative": f"Errore durante l'esecuzione del grafo: {str(e)}"
            }
            return self._transform_to_api_schema(error_result, self.audit_enabled)
    
    async def execute_graph_with_audit(self, payload: dict) -> Dict[str, Any]:
        """
        Execute graph with explicit audit monitoring.
        Used by /graph/dispatch endpoint.
        
        Args:
            payload: Graph payload dict
        
        Returns:
            Result with audit metadata (GraphResponseSchema format)
        """
        async with self.monitor.monitor_graph_execution(payload):
            raw_result = run_graph(payload)
            
            # Transform to API schema with audit enabled
            return self._transform_to_api_schema(raw_result, audit_monitored=True)
    
    def _transform_to_api_schema(self, raw_result: Dict[str, Any], audit_monitored: bool) -> Dict[str, Any]:
        """
        Transform core graph output → API service schema (GraphResponseSchema).
        
        This is the adapter's responsibility: translate between domain layer (core)
        and service layer (API contracts).
        
        Args:
            raw_result: Raw graph runner output {narrative, action, intent, ...}
            audit_monitored: Whether audit monitoring was active
        
        Returns:
            {json, human, audit_monitored, execution_timestamp} (GraphResponseSchema)
        """
        # Extract human-readable message (primary field for UI)
        human_message = raw_result.get("narrative", "")
        
        # If no narrative, try alternative fields
        if not human_message:
            if "message" in raw_result:
                human_message = raw_result["message"]
            elif "error" in raw_result:
                human_message = f"Errore: {raw_result['error']}"
            elif "can_response" in raw_result and isinstance(raw_result["can_response"], dict):
                human_message = raw_result["can_response"].get("narrative", "Risposta non disponibile")
            else:
                human_message = "Risposta generata dal sistema"
        
        # Serialize full result as one-line JSON (for debugging/logging)
        json_one_line = json.dumps(raw_result, ensure_ascii=False, separators=(",", ":"))
        
        # Construct API-compliant response (GraphResponseSchema)
        return {
            "json": json_one_line,
            "human": human_message,
            "audit_monitored": audit_monitored,
            "execution_timestamp": datetime.now().isoformat()
        }
