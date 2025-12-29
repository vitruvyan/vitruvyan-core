"""
🛡️ THE CHAMBERLAIN - Simple Coordinator
=======================================
The Master Orchestrator of the Vault (NO CrewAI)

Direct coordinator of Keeper agents following the new architecture:
- Container-based service (vitruvyan_vault_keeper:8007)  
- FastAPI integration for LangGraph triggers
- Deterministic pipeline: Watcher→Compressor→Uploader→Verifier
- No LLM orchestration - pure procedural coordination

RESPONSIBILITIES:
- Direct coordination of Sentinel, Archivist, Courier
- Simple workflow execution without CrewAI complexity
- FastAPI service integration
- LangGraph REST trigger handling

ARCHITECTURE:
- Pipeline deterministica (NOT agentic reasoning)
- Container indipendente con fault isolation
- REST trigger da LangGraph con timeout

MOTTO: "Simplicitas et robustitas" (Simplicity and robustness)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
from enum import Enum

# NO CrewAI imports - simple coordination only
from .keeper import BaseKeeper, VaultEvent, BackupMode, VaultStatus, VaultConfig
from .sentinel import SentinelAgent
from .archivist import ArchivistAgent  
from .courier import CourierAgent

logger = logging.getLogger("VaultKeeper.ChamberlainAgent")

class WorkflowPhase(Enum):
    """Phases of backup workflow orchestration"""
    DETECTION = "detection"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    DELIVERY = "delivery"
    VERIFICATION = "verification"
    COMPLETION = "completion"

class ChamberlainAgent(BaseKeeper):
    """
    🛡️ The Chamberlain - Master Coordinator
    =======================================
    Simple orchestrator without CrewAI complexity
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        super().__init__(config)
        
        self.keeper_type = "ChamberlainAgent"
        self.motto = "Simplicitas et robustitas"
        self.logger.info("🛡️ The Chamberlain - Camerarius Magnus stands ready to guard the vault")
        
        # Initialize keeper agents directly (no CrewAI)
        self.sentinel: Optional[SentinelAgent] = None
        self.archivist: Optional[ArchivistAgent] = None
        self.courier: Optional[CourierAgent] = None
        
        # Simple coordination state
        self.current_workflow: Optional[str] = None
        self.workflow_phase: Optional[WorkflowPhase] = None
        self.workflow_start_time: Optional[datetime] = None
        
        # Performance metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_duration": 0.0
        }
        
        # Initialize keeper agents
        self._initialize_keepers()
        
        self.logger.info("🛡️ The Chamberlain assumes command - simple coordination ready")
    
    def _initialize_keepers(self):
        """Initialize all keeper agents for coordination"""
        try:
            self.logger.info("📋 Chamberlain initializing keeper agents...")
            
            # Initialize agents in sequence
            self.sentinel = SentinelAgent(self.config)
            self.archivist = ArchivistAgent(self.config)
            self.courier = CourierAgent(self.config)
            
            self.logger.info("✅ All keeper agents under Chamberlain command")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize keeper agents: {e}")
            raise
    
    async def execute_backup_workflow(self, mode: str = "incremental", trigger: Optional[str] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute coordinated backup workflow
        ==================================
        Simple deterministic pipeline without CrewAI
        """
        if context is None:
            context = {}
            
        workflow_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_workflow = workflow_id
        self.workflow_start_time = datetime.now()
        
        self.logger.info(f"🛡️ Chamberlain executing workflow {workflow_id}: mode={mode}, trigger={trigger}")
        
        try:
            # PHASE 1: DETECTION - Sentinel monitors
            self.workflow_phase = WorkflowPhase.DETECTION
            self.logger.info("🔍 Phase 1: Sentinel detection...")
            
            detection_result = await self._execute_detection()
            
            # PHASE 2: PREPARATION - Archivist prepares
            self.workflow_phase = WorkflowPhase.PREPARATION  
            self.logger.info("📚 Phase 2: Archivist preparation...")
            
            preparation_result = self._execute_preparation(mode, context)
            
            # PHASE 3: EXECUTION - Archivist creates backup
            self.workflow_phase = WorkflowPhase.EXECUTION
            self.logger.info("📦 Phase 3: Backup execution...")
            
            execution_result = self._execute_backup(mode, context)
            
            # PHASE 4: DELIVERY - Courier distributes
            self.workflow_phase = WorkflowPhase.DELIVERY
            self.logger.info("📮 Phase 4: Courier delivery...")
            
            delivery_result = self._execute_delivery(execution_result)
            
            # PHASE 5: VERIFICATION - Final checks
            self.workflow_phase = WorkflowPhase.VERIFICATION
            self.logger.info("✅ Phase 5: Verification...")
            
            verification_result = self._execute_verification(execution_result)
            
            # PHASE 6: COMPLETION - Workflow finished
            self.workflow_phase = WorkflowPhase.COMPLETION
            
            # Update metrics
            duration = (datetime.now() - self.workflow_start_time).total_seconds()
            self._update_metrics(success=True, duration=duration)
            
            result = {
                "success": True,
                "workflow_id": workflow_id,
                "mode": mode,
                "trigger": trigger,
                "duration": duration,
                "phases": {
                    "detection": detection_result,
                    "preparation": preparation_result,
                    "execution": execution_result,
                    "delivery": delivery_result,
                    "verification": verification_result
                },
                "message": "🛡️ Chamberlain workflow completed successfully"
            }
            
            self.logger.info(f"✅ Chamberlain workflow {workflow_id} completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            # Update metrics for failure
            duration = (datetime.now() - self.workflow_start_time).total_seconds() if self.workflow_start_time else 0
            self._update_metrics(success=False, duration=duration)
            
            self.logger.error(f"❌ Chamberlain workflow {workflow_id} failed: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "duration": duration,
                "phase": self.workflow_phase.value if self.workflow_phase else "unknown",
                "message": f"🛡️ Chamberlain workflow failed: {str(e)}"
            }
        finally:
            self.current_workflow = None
            self.workflow_phase = None
            self.workflow_start_time = None
    
    async def _execute_detection(self) -> Dict[str, Any]:
        """Phase 1: Sentinel detection"""
        try:
            # Use the async detect_changes method
            detection_result = await self.sentinel.detect_changes()
            return detection_result
        except Exception as e:
            self.logger.error(f"❌ Detection phase failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_preparation(self, mode: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Archivist preparation"""
        try:
            # Prepare backup environment
            archive_ready = self.archivist.prepare_archive_environment()
            space_available = self.archivist.check_available_space()
            
            return {
                "success": True,
                "archive_ready": archive_ready,
                "space_available_gb": space_available,
                "backup_mode": mode,
                "collections": list(self.archivist.collections.keys())
            }
        except Exception as e:
            self.logger.error(f"❌ Preparation phase failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_backup(self, mode: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Backup execution"""
        try:
            # Execute backup based on mode
            if mode == "incremental":
                result = self.archivist.create_incremental_backup()
            elif mode == "critical":  
                result = self.archivist.create_critical_backup()
            elif mode == "full_system":
                result = self.archivist.create_full_system_backup()
            elif mode == "disaster_recovery":
                result = self.archivist.create_disaster_recovery_backup()
            else:
                result = self.archivist.create_incremental_backup()  # default
            
            return {
                "success": result.get("success", False),
                "backup_path": result.get("backup_path"),
                "backup_size_mb": result.get("backup_size_mb", 0),
                "files_backed_up": result.get("files_backed_up", 0),
                "backup_id": result.get("backup_id")
            }
        except Exception as e:
            self.logger.error(f"❌ Backup execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_delivery(self, backup_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Courier delivery"""
        try:
            if not backup_result.get("success"):
                return {"success": False, "error": "No backup to deliver"}
            
            # Deliver backup via courier
            delivery_job = {
                "backup_path": backup_result.get("backup_path"),
                "backup_id": backup_result.get("backup_id"),
                "metadata": backup_result
            }
            
            result = self.courier.queue_delivery_job(delivery_job)
            
            return {
                "success": result.get("success", False),
                "delivery_channels": result.get("delivery_channels", []),
                "job_id": result.get("job_id"),
                "estimated_duration": result.get("estimated_duration", 0)
            }
        except Exception as e:
            self.logger.error(f"❌ Delivery phase failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_verification(self, backup_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5: Final verification"""
        try:
            if not backup_result.get("success"):
                return {"success": False, "error": "No backup to verify"}
            
            # Verify backup integrity
            backup_path = backup_result.get("backup_path")
            self.logger.info(f"🔍 Verifying backup at: {backup_path}")
            integrity_check = self.archivist.verify_backup_integrity(backup_path)
            
            self.logger.info(f"🔍 Integrity check result: {integrity_check}")
            
            return {
                "success": integrity_check.get("valid", False),
                "checksum_valid": integrity_check.get("checksum_valid", False),
                "size_valid": integrity_check.get("size_valid", False),
                "structure_valid": integrity_check.get("structure_valid", False)
            }
        except Exception as e:
            self.logger.error(f"❌ Verification phase failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_metrics(self, success: bool, duration: float):
        """Update performance metrics"""
        self.metrics["total_workflows"] += 1
        if success:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1
        
        # Update average duration
        total = self.metrics["total_workflows"]
        current_avg = self.metrics["average_duration"]
        self.metrics["average_duration"] = (current_avg * (total - 1) + duration) / total
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Chamberlain status"""
        return {
            "keeper_type": self.keeper_type,
            "motto": self.motto,
            "current_workflow": self.current_workflow,
            "workflow_phase": self.workflow_phase.value if self.workflow_phase else None,
            "keepers_ready": {
                "sentinel": self.sentinel is not None,
                "archivist": self.archivist is not None,
                "courier": self.courier is not None
            },
            "metrics": self.metrics,
            "vault_config": {
                "backup_mode": self.config.backup_mode,
                "backup_storage": self.config.backup_storage,
                "cloud_provider": self.config.cloud_provider
            }
        }
    
    def __str__(self) -> str:
        """String representation"""
        status = "ready" if all([self.sentinel, self.archivist, self.courier]) else "initializing"
        workflow = f", workflow: {self.current_workflow}" if self.current_workflow else ""
        return f"🛡️ The Chamberlain - Camerarius Magnus ({status}{workflow})"

# Compatibility alias for the old CrewAI-based system
VaultChamberlain = ChamberlainAgent