"""
Simplified Audit Node for LangGraph Integration
Provides basic audit capabilities without external dependencies
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def audit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplified LangGraph audit node for basic monitoring
    Performs local auditing without requiring external audit service
    """
    
    try:
        # Determine audit type from state
        audit_type = state.get("audit_trigger", "graph_execution")
        node_context = state.get("current_node", "unknown")
        
        logger.info(f"🔍 Graph audit triggered: {audit_type} for node {node_context}")
        
        # Perform local audits based on trigger
        findings = []
        
        if audit_type == "pre_execution":
            findings.extend(_audit_pre_execution(state))
        elif audit_type == "post_execution":
            findings.extend(_audit_post_execution(state))
        elif audit_type == "error_recovery":
            findings.extend(_audit_error_recovery(state))
        elif audit_type == "performance_check":
            findings.extend(_audit_performance(state))
        else:
            # Default: comprehensive audit
            findings.extend(_audit_comprehensive(state))
        
        # Count findings by severity
        critical_findings = [f for f in findings if f["severity"] in ["critical", "high"]]
        
        # Log findings
        for finding in findings:
            severity_icon = "🚨" if finding["severity"] == "critical" else "⚠️" if finding["severity"] == "high" else "ℹ️"
            logger.info(f"{severity_icon} Audit finding: {finding['category']} - {finding['description']}")
        
        # Update state with audit results
        state["audit_session_id"] = f"local_{int(datetime.now().timestamp())}"
        state["audit_findings_count"] = len(findings)
        state["audit_critical_count"] = len(critical_findings)
        state["audit_timestamp"] = datetime.now().isoformat()
        state["audit_findings"] = findings
        
        # Log completion
        if critical_findings:
            logger.warning(f"🚨 {len(critical_findings)} critical findings detected in graph execution")
        
        logger.info(f"✅ Graph audit completed: {len(findings)} findings, {len(critical_findings)} critical")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Graph audit node failed: {e}")
        # Don't break the graph flow, just log the error
        state["audit_error"] = str(e)
        return state


def _audit_pre_execution(state: Dict[str, Any]) -> list:
    """Audit before sensitive operations"""
    findings = []
    
    # Check for dangerous intents
    intent = state.get("intent", "")
    if intent in ["system_shutdown", "delete_data", "admin_access"]:
        findings.append({
            "category": "security_violation",
            "severity": "critical", 
            "description": f"Dangerous intent detected: {intent}",
            "metadata": {"intent": intent, "prevention": "execution_blocked"}
        })
    
    # Check input validation
    input_text = state.get("input_text", "")
    if len(input_text) > 10000:  # Very long input
        findings.append({
            "category": "input_validation",
            "severity": "medium",
            "description": f"Excessively long input: {len(input_text)} characters",
            "metadata": {"input_length": len(input_text)}
        })
    
    # Check for suspicious patterns
    suspicious_keywords = ["DROP TABLE", "DELETE FROM", "exec(", "eval(", "__import__"]
    for keyword in suspicious_keywords:
        if keyword.lower() in input_text.lower():
            findings.append({
                "category": "injection_attempt",
                "severity": "high",
                "description": f"Suspicious keyword detected: {keyword}",
                "metadata": {"keyword": keyword, "input_text": input_text[:100]}
            })
    
    return findings


def _audit_post_execution(state: Dict[str, Any]) -> list:
    """Audit after node completion"""
    findings = []
    
    # Check for errors in execution
    if state.get("error"):
        findings.append({
            "category": "execution_error",
            "severity": "high",
            "description": f"Node execution failed: {state['error']}",
            "metadata": {"error": state["error"], "node": state.get("current_node")}
        })
    
    # Check response quality
    response = state.get("response", {})
    if not response or len(str(response)) < 10:
        findings.append({
            "category": "response_quality",
            "severity": "medium", 
            "description": "Empty or minimal response generated",
            "metadata": {"response_length": len(str(response))}
        })
    
    # Check for sensitive data in response
    response_str = str(response).lower()
    sensitive_patterns = ["password", "token", "secret", "key", "credential"]
    for pattern in sensitive_patterns:
        if pattern in response_str:
            findings.append({
                "category": "data_leak",
                "severity": "critical",
                "description": f"Potential sensitive data in response: {pattern}",
                "metadata": {"pattern": pattern}
            })
    
    return findings


def _audit_error_recovery(state: Dict[str, Any]) -> list:
    """Audit during error recovery"""
    findings = []
    
    error = state.get("error", "")
    if error:
        # Categorize error types
        if "timeout" in error.lower():
            findings.append({
                "category": "performance_timeout",
                "severity": "high",
                "description": f"Timeout error in graph execution: {error}",
                "metadata": {"error_type": "timeout"}
            })
        elif "memory" in error.lower():
            findings.append({
                "category": "high_memory_usage", 
                "severity": "critical",
                "description": f"Memory error in graph execution: {error}",
                "metadata": {"error_type": "memory"}
            })
        elif "connection" in error.lower():
            findings.append({
                "category": "connection_failure",
                "severity": "high",
                "description": f"Connection error in graph execution: {error}",
                "metadata": {"error_type": "connection"}
            })
    
    return findings


def _audit_performance(state: Dict[str, Any]) -> list:
    """Audit performance metrics"""
    findings = []
    
    # Check execution time if available
    execution_time = state.get("execution_time_ms", 0)
    if execution_time > 30000:  # 30 seconds
        findings.append({
            "category": "performance_slow",
            "severity": "medium",
            "description": f"Slow graph execution: {execution_time}ms",
            "metadata": {"execution_time": execution_time, "threshold": 30000}
        })
    
    # Check state size (potential memory issue)
    state_size = len(str(state))
    if state_size > 100000:  # 100KB state
        findings.append({
            "category": "large_state",
            "severity": "medium",
            "description": f"Large graph state detected: {state_size} bytes",
            "metadata": {"state_size": state_size}
        })
    
    return findings


def _audit_comprehensive(state: Dict[str, Any]) -> list:
    """Comprehensive audit combining all checks"""
    findings = []
    
    findings.extend(_audit_pre_execution(state))
    findings.extend(_audit_post_execution(state))
    findings.extend(_audit_performance(state))
    
    # Additional comprehensive checks
    route = state.get("route")
    if not route:
        findings.append({
            "category": "routing_failure",
            "severity": "medium",
            "description": "No route determined for graph execution",
            "metadata": {"state_keys": list(state.keys())}
        })
    
    # Check for missing critical fields
    required_fields = ["user_id", "input_text"]
    for field in required_fields:
        if not state.get(field):
            findings.append({
                "category": "missing_field",
                "severity": "low",
                "description": f"Missing required field: {field}",
                "metadata": {"field": field}
            })
    
    return findings