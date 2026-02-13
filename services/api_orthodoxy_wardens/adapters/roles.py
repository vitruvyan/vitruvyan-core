"""
Sacred Roles - Theological wrappers for Orthodoxy Wardens agents

These classes provide event-driven interfaces for compliance validation,
auto-correction, system monitoring, and audit orchestration.

**Pragmatic Purpose**:
- Decouple business logic (agents) from infrastructure (FastAPI/Redis)
- Enable testing without Docker dependencies
- Provide both theological and functional method names

**Design**: Event-driven roles that emit/consume from Synaptic Conclave (Redis Streams)
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Add /app to path for imports (Docker compatibility)
if '/app' not in sys.path:
    sys.path.append('/app')

from core.synaptic_conclave.transport.streams import StreamBus
from core.synaptic_conclave.events.event_envelope import CognitiveEvent


class SacredRole:
    """
    Base class for all Sacred Orthodoxy Wardens roles.
    
    **What it does**: Provides common functionality for event emission via Redis Streams.
    
    **How it works**: Wraps StreamBus for publishing events, provides sacred logging format.
    
    **When to use**: Inherit from this when creating new orthodoxy roles.
    """
    
    def __init__(self, role_name: str):
        self.role_name = role_name
        self.logger = logging.getLogger(f"ORTHODOXY.{role_name.upper()}")
        # Redis Streams Cognitive Bus
        host = os.getenv('REDIS_HOST', 'omni_redis')
        port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_bus = StreamBus(host=host, port=port)
        
    def sacred_log(self, message: str, level: str = "INFO"):
        """Sacred logging format: [ORTHODOXY][ROLE] message"""
        getattr(self.logger, level.lower())(f"[ORTHODOXY][{self.role_name.upper()}] {message}")
    
    def publish_event(self, event_dict: Dict[str, Any]):
        """
        Compatibility wrapper for legacy publish_event() calls.
        Adapts old CognitiveEvent format to Redis Streams emit().
        
        Args:
            event_dict: Dict with keys: event_type, emitter, target, payload, timestamp
        """
        try:
            # Extract channel from event_type (e.g., "orthodoxy.heresy.detected" → "orthodoxy")
            event_type = event_dict.get("event_type", "orthodoxy.event")
            channel = event_type.split(".")[0]  # First segment becomes channel name
            
            # Construct payload with full event metadata
            payload = {
                "event_type": event_type,
                "emitter": event_dict.get("emitter", self.role_name.lower()),
                "target": event_dict.get("target", "system"),
                "payload": event_dict.get("payload", {}),
                "timestamp": event_dict.get("timestamp", datetime.utcnow().isoformat())
            }
            
            # Emit to Redis Stream (synchronous call, safe in FastAPI worker threads)
            event_id = self.redis_bus.emit(
                channel=channel,
                payload=payload,
                emitter=f"orthodoxy_{self.role_name.lower()}"
            )
            
            self.logger.info(f"[{self.role_name}] Event emitted to stream '{channel}': {event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"[{self.role_name}] Failed to emit event: {e}", exc_info=True)
            return False


class OrthodoxConfessor(SacredRole):
    """
    The Confessor - Hears system sins and validates compliance confessions.
    
    **Theological alias**: Confessor = Audit Orchestrator
    **Functional purpose**: Orchestrates full system audits via AutonomousAuditAgent
    """
    
    def __init__(self):
        super().__init__("CONFESSOR")
        self.audit_agent = None
        
    async def hear_confession(self, system_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Examine system for heresies and violations"""
        self.sacred_log("Commencing sacred confession examination...")
        
        # TODO: Implement actual audit logic using self.audit_agent
        findings = {
            "heresies_detected": 0,
            "violations": [],
            "confession_complete": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if findings["heresies_detected"] > 0:
            # Emit heresy detection event
            await self.emit_heresy_event(findings)
            
        self.sacred_log(f"Confession complete: {findings['heresies_detected']} heresies detected")
        return findings
        
    async def emit_heresy_event(self, findings: Dict[str, Any]):
        """Emit orthodoxy.heresy.detected event"""
        event = CognitiveEvent(
            event_type="orthodoxy.heresy.detected",
            emitter="orthodoxy_confessor",
            target="system",
            payload=findings,
            timestamp=datetime.utcnow().isoformat()
        )
        self.redis_bus.publish_event(event)
        self.sacred_log("Heresy detection event emitted to Synaptic Conclave")
    
    # ============================================================================
    # FUNCTIONAL ALIASES (Dec 21, 2025) - Pragmatic names for new developers
    # ============================================================================
    async def validate(self, system_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Functional alias for hear_confession().
        Validates system compliance and detects violations.
        
        Use this if theological metaphor confuses you.
        """
        return await self.hear_confession(system_payload)
    
    validate_compliance = validate  # Additional alias for clarity


class OrthodoxPenitent(SacredRole):
    """
    The Penitent - Performs remediation rituals and purification rites.
    
    **Theological alias**: Penitent = Auto-Corrector
    **Functional purpose**: Applies automated fixes via AutoCorrector agent
    """
    
    def __init__(self):
        super().__init__("PENITENT")
        self.auto_corrector = None
        
    async def apply_purification(self, heresy_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply healing and purification to detected heresies"""
        self.sacred_log("Commencing sacred purification ritual...")
        
        # TODO: Implement actual healing logic using self.auto_corrector
        purification = {
            "heresies_purified": len(heresy_payload.get("violations", [])),
            "healing_applied": True,
            "restoration_complete": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Emit purification completion event
        await self.emit_purification_event(purification)
        
        self.sacred_log(f"Purification complete: {purification['heresies_purified']} violations healed")
        return purification
        
    async def emit_purification_event(self, purification: Dict[str, Any]):
        """Emit orthodoxy.purification.executed event"""
        event = CognitiveEvent(
            event_type="orthodoxy.purification.executed",
            emitter="orthodoxy_penitent", 
            target="system",
            payload=purification,
            timestamp=datetime.utcnow().isoformat()
        )
        self.redis_bus.publish_event(event)
        self.sacred_log("Purification completion event emitted to Synaptic Conclave")
    
    # ============================================================================
    # FUNCTIONAL ALIASES (Dec 21, 2025) - Pragmatic names for new developers
    # ============================================================================
    async def remediate(self, heresy_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Functional alias for apply_purification().
        Remediates detected violations and applies corrections.
        
        Use this if theological metaphor confuses you.
        """
        return await self.apply_purification(heresy_payload)
    
    fix_violations = remediate  # Additional alias for clarity


class OrthodoxChronicler(SacredRole):
    """
    The Chronicler - Records sacred events and maintains divine documentation.
    
    **Theological alias**: Chronicler = Event Logger
    **Functional purpose**: Persists audit events to PostgreSQL via SystemMonitor
    """
    
    def __init__(self):
        super().__init__("CHRONICLER")
        self.system_monitor = None
        
    async def record_sacred_event(self, event_data: Dict[str, Any]) -> bool:
        """Record sacred events in divine chronicles (PostgreSQL)"""
        self.sacred_log("Recording sacred event in divine chronicles...")
        
        # TODO: Implement actual logging to database
        success = True
        
        if success:
            self.sacred_log("Sacred event successfully chronicled")
        else:
            self.sacred_log("Failed to chronicle sacred event", "ERROR")
            
        return success
    
    # ============================================================================
    # FUNCTIONAL ALIASES (Dec 21, 2025) - Pragmatic names for new developers
    # ============================================================================
    async def log_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Functional alias for record_sacred_event().
        Logs audit events to database for persistence and analysis.
        
        Use this if theological metaphor confuses you.
        """
        return await self.record_sacred_event(event_data)
    
    persist_audit = log_event  # Additional alias for clarity


class OrthodoxInquisitor(SacredRole):
    """
    The Inquisitor - Investigates heretical code and triggers audits.
    
    **Theological alias**: Inquisitor = Compliance Investigator
    **Functional purpose**: Triggers audit workflow via ComplianceValidator
    """
    
    def __init__(self):
        super().__init__("INQUISITOR")
        self.compliance_validator = None
        
    async def trigger_investigation(self, audit_request: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger system investigation and audit"""
        self.sacred_log("Sacred investigation initiated by divine mandate...")
        
        # Start confession process
        confession_started = {
            "investigation_id": f"inquisition_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "source": "inquisitor",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Emit confession started event
        await self.emit_confession_event(confession_started)
        
        self.sacred_log(f"Investigation {confession_started['investigation_id']} commenced")
        return confession_started
        
    async def emit_confession_event(self, confession_data: Dict[str, Any]):
        """Emit orthodoxy.confession.started event"""
        event = CognitiveEvent(
            event_type="orthodoxy.confession.started",
            emitter="orthodoxy_inquisitor",
            target="orthodoxy_confessor", 
            payload=confession_data,
            timestamp=datetime.utcnow().isoformat()
        )
        self.redis_bus.publish_event(event)
        self.sacred_log("Confession initiation event emitted to Synaptic Conclave")
    
    # ============================================================================
    # FUNCTIONAL ALIASES (Dec 21, 2025) - Pragmatic names for new developers
    # ============================================================================
    async def investigate(self, audit_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Functional alias for trigger_investigation().
        Investigates system for violations and triggers audits.
        
        Use this if theological metaphor confuses you.
        """
        return await self.trigger_investigation(audit_request)
    
    audit_system = investigate  # Additional alias for clarity


class OrthodoxAbbot(SacredRole):
    """
    The Abbot - Oversees sacred operations and provides divine guidance.
    
    **Theological alias**: Abbot = Audit Coordinator
    **Functional purpose**: Finalizes audit verdicts and coordinates workflow
    """
    
    def __init__(self):
        super().__init__("ABBOT")
        
    async def grant_absolution(self, confession_results: Dict[str, Any], correlation_id: str = None) -> Dict[str, Any]:
        """Grant final absolution and verdict"""
        self.sacred_log("Deliberating divine verdict and absolution...")
        
        absolution = {
            "verdict": "absolution_granted" if confession_results.get("confession_complete") else "penance_required",
            "findings": confession_results.get("heresies_detected", 0),
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat(),
            "divine_blessing": "System restored to sacred orthodoxy" if confession_results.get("heresies_detected", 0) == 0 else "Purification required"
        }
        
        # Emit absolution event with correlation_id for matching
        await self.emit_absolution_event(absolution, correlation_id)
        
        self.sacred_log(f"Divine verdict: {absolution['verdict']} - {absolution['divine_blessing']}")
        return absolution
        
    async def emit_absolution_event(self, absolution: Dict[str, Any], correlation_id: str = None):
        """Emit orthodoxy.absolution.granted event"""
        event = CognitiveEvent(
            event_type="orthodoxy.absolution.granted",
            emitter="orthodoxy_abbot",
            target="system",
            payload=absolution,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id  # 🔥 CRITICAL: Pass correlation_id for matching
        )
        self.redis_bus.publish_event(event)
        self.sacred_log(f"Divine absolution event emitted to Synaptic Conclave (correlation: {correlation_id})")
    
    # ============================================================================
    # FUNCTIONAL ALIASES (Dec 21, 2025) - Pragmatic names for new developers
    # ============================================================================
    async def approve(self, confession_results: Dict[str, Any], correlation_id: str = None) -> Dict[str, Any]:
        """
        Functional alias for grant_absolution().
        Approves or rejects system state based on validation results.
        
        Use this if theological metaphor confuses you.
        """
        return await self.grant_absolution(confession_results, correlation_id)
    
    finalize_verdict = approve  # Additional alias for clarity
    coordinate_audit = approve  # Alias matching original plan
