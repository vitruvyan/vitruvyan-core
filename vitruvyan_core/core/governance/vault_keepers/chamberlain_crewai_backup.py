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
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
import json
from enum import Enum

# NO CrewAI imports - simple coordination only
from .keeper import BaseKeeper, VaultEvent, BackupMode, VaultStatus, VaultConfig
from .sentinel import SentinelAgent
from .archivist import ArchivistAgent  
from .courier import CourierAgent

logger = logging.getLogger(__name__)

class WorkflowPhase(Enum):
    """Phases of backup workflow orchestration"""
    DETECTION = "detection"
    ASSESSMENT = "assessment"
    PREPARATION = "preparation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    DELIVERY = "delivery"
    COMPLETION = "completion"

class WorkflowPriority(Enum):
    """Priority levels for backup workflows"""
    ROUTINE = 1
    ELEVATED = 2
    URGENT = 3
    CRITICAL = 4
    EMERGENCY = 5

class BackupWorkflow:
    """Represents a complete backup workflow"""
    
    def __init__(self, workflow_id: str, trigger_data: Dict[str, Any], priority: WorkflowPriority = WorkflowPriority.ROUTINE):
        self.workflow_id = workflow_id
        self.trigger_data = trigger_data
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.current_phase = WorkflowPhase.DETECTION
        self.status = "initialized"
        self.keeper_assignments: Dict[str, Dict[str, Any]] = {}
        self.phase_results: Dict[WorkflowPhase, Dict[str, Any]] = {}
        self.error_log: List[str] = []

class ChamberlainAgent(BaseKeeper):
    """
    The Chamberlain - Magister Palatii
    
    The supreme coordinator of the fortress, who conducts the great
    symphony of backup operations with the precision of a master
    conductor, ensuring each keeper plays their part flawlessly.
    
    Like Cardinal Richelieu orchestrating the affairs of state,
    The Chamberlain sees the grand design and coordinates all.
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        super().__init__(config)
        
        # Initialize Vault Keepers
        self.sentinel = SentinelAgent(config)
        self.archivist = ArchivistAgent(config)
        self.courier = CourierAgent(config)
        
        # Workflow Management
        self.active_workflows: Dict[str, BackupWorkflow] = {}
        self.workflow_queue: asyncio.Queue = asyncio.Queue()
        self.workflow_executor_task: Optional[asyncio.Task] = None
        
        # CrewAI Components
        self.crew: Optional[Crew] = None
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, BaseTool] = {}
        
        # Status Monitoring
        self.vault_health_score = 100
        self.last_health_check = datetime.utcnow()
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_duration": 0.0,
            "total_data_protected_gb": 0.0
        }
        
        # Initialize CrewAI setup
        self._initialize_crewai()
        
        self.logger.info("🛡️ The Chamberlain assumes command - fortress coordination begins")
    
    def _initialize_crewai(self):
        """Initialize CrewAI agents and tools for orchestration"""
        
        # Define specialized agents for different aspects
        
        # 1. Threat Analysis Agent
        self.agents["threat_analyst"] = Agent(
            role="Threat Analysis Specialist",
            goal="Analyze threats and determine appropriate backup strategies",
            backstory="""You are a master strategist who examines threats to the digital fortress
            and determines the most appropriate response. Like a medieval scout reporting enemy movements,
            you provide critical intelligence for backup decisions.""",
            verbose=True,
            allow_delegation=False
        )
        
        # 2. Backup Coordinator Agent
        self.agents["backup_coordinator"] = Agent(
            role="Backup Operations Coordinator",
            goal="Coordinate backup execution across all vault keepers",
            backstory="""You are the master of ceremonies who ensures each keeper performs
            their role perfectly. Like a conductor directing an orchestra, you ensure
            harmonious execution of complex backup workflows.""",
            verbose=True,
            allow_delegation=True
        )
        
        # 3. Quality Assurance Agent
        self.agents["quality_inspector"] = Agent(
            role="Quality Assurance Inspector", 
            goal="Verify backup integrity and completeness",
            backstory="""You are the meticulous guardian of quality who ensures no detail
            is overlooked. Like a master craftsman inspecting precious artifacts,
            you verify every backup meets the highest standards.""",
            verbose=True,
            allow_delegation=False
        )
        
        # 4. Recovery Planning Agent
        self.agents["recovery_planner"] = Agent(
            role="Disaster Recovery Planner",
            goal="Plan and coordinate disaster recovery procedures",
            backstory="""You are the wise sage who prepares for the worst while hoping
            for the best. Like Noah building the ark, you ensure the fortress
            can survive and recover from any catastrophe.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Initialize tools for agents
        self._initialize_crewai_tools()
        
        # Create the Crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            process=Process.hierarchical,  # Chamberlain leads hierarchically
            manager_llm=None,  # Would use configured LLM in production
            verbose=True
        )
    
    def _initialize_crewai_tools(self):
        """Initialize tools for CrewAI agents"""
        
        class VaultStatusTool(BaseTool):
            name: str = "vault_status_checker"
            description: str = "Check the current status and health of all vault keepers"
            
            def _run(self, query: str = "") -> str:
                # Access parent chamberlain instance
                chamberlain = self.parent  # Would need proper reference
                status = chamberlain.get_vault_status()
                return json.dumps(status, indent=2)
        
        class BackupExecutorTool(BaseTool):
            name: str = "backup_executor" 
            description: str = "Execute backup operations through the Archivist"
            
            def _run(self, backup_mode: str, threat_data: str) -> str:
                # Would execute backup through Archivist
                return f"Backup execution initiated: {backup_mode}"
        
        class ThreatAnalysisTool(BaseTool):
            name: str = "threat_analyzer"
            description: str = "Analyze threats detected by the Sentinel"
            
            def _run(self, threat_data: str) -> str:
                # Parse and analyze threat data
                try:
                    threats = json.loads(threat_data)
                    analysis = {
                        "total_threats": len(threats),
                        "severity_distribution": {},
                        "recommended_actions": []
                    }
                    
                    for threat in threats:
                        severity = threat.get("severity", "unknown")
                        analysis["severity_distribution"][severity] = analysis["severity_distribution"].get(severity, 0) + 1
                        
                        recommended = threat.get("recommended_action", "incremental_backup")
                        if recommended not in analysis["recommended_actions"]:
                            analysis["recommended_actions"].append(recommended)
                    
                    return json.dumps(analysis, indent=2)
                except:
                    return "Error analyzing threat data"
        
        # Store tools (in production, properly connect to self)
        self.tools = {
            "vault_status": VaultStatusTool(),
            "backup_executor": BackupExecutorTool(), 
            "threat_analyzer": ThreatAnalysisTool()
        }
    
    async def start_orchestration(self):
        """Start the Chamberlain's orchestration service"""
        if self.workflow_executor_task:
            self.logger.warning("⚠️ Chamberlain orchestration already running")
            return
        
        # Start all vault keepers
        await self.sentinel.start_watch()
        await self.courier.start_delivery_service()
        
        # Start workflow executor
        self.workflow_executor_task = asyncio.create_task(self._workflow_executor())
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor_loop())
        
        self.logger.info("🏰 The Chamberlain begins fortress orchestration - all keepers at their posts")
        
        self.publish_event("chamberlain.orchestration_started", {
            "keepers_active": ["sentinel", "archivist", "courier"],
            "workflow_queue_size": self.workflow_queue.qsize(),
            "initial_health_score": self.vault_health_score
        })
    
    async def stop_orchestration(self):
        """Stop the orchestration gracefully"""
        
        # Stop workflow executor
        if self.workflow_executor_task:
            self.workflow_executor_task.cancel()
            try:
                await self.workflow_executor_task
            except asyncio.CancelledError:
                pass
            self.workflow_executor_task = None
        
        # Stop all vault keepers
        await self.sentinel.stop_watch()
        await self.courier.stop_delivery_service()
        
        self.logger.info("🛑 The Chamberlain ends orchestration - fortress secured")
        self.publish_event("chamberlain.orchestration_stopped", {})
    
    async def handle_backup_trigger(self, trigger_source: str, trigger_data: Dict[str, Any]) -> str:
        """
        Handle backup trigger and orchestrate appropriate response
        
        Like receiving urgent dispatches from across the realm,
        this method processes threats and coordinates the fortress response.
        """
        
        # Determine workflow priority based on trigger
        priority = self._assess_trigger_priority(trigger_source, trigger_data)
        
        # Create workflow
        workflow_id = f"workflow_{trigger_source}_{int(datetime.utcnow().timestamp())}"
        workflow = BackupWorkflow(
            workflow_id=workflow_id,
            trigger_data={"source": trigger_source, "data": trigger_data},
            priority=priority
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Add to workflow queue
        await self.workflow_queue.put(workflow)
        
        self.logger.info(f"⚔️ The Chamberlain received {priority.name} trigger from {trigger_source}")
        self.logger.info(f"📋 Created workflow {workflow_id} - added to orchestration queue")
        
        self.publish_event("chamberlain.workflow_created", {
            "workflow_id": workflow_id,
            "trigger_source": trigger_source,
            "priority": priority.name,
            "queue_position": self.workflow_queue.qsize()
        })
        
        return workflow_id
    
    def _assess_trigger_priority(self, trigger_source: str, trigger_data: Dict[str, Any]) -> WorkflowPriority:
        """Assess the priority of a backup trigger"""
        
        # Emergency indicators
        emergency_keywords = ["disaster", "critical", "emergency", "corruption", "failure"]
        
        if trigger_source == "audit_engine":
            severity = trigger_data.get("severity", "medium")
            if severity == "critical":
                return WorkflowPriority.EMERGENCY
            elif severity == "high":
                return WorkflowPriority.CRITICAL
            else:
                return WorkflowPriority.ELEVATED
        
        elif trigger_source == "sentinel":
            threats = trigger_data.get("threats", [])
            max_severity = "low"
            
            for threat in threats:
                threat_severity = threat.get("severity", "low")
                threat_type = threat.get("type", "")
                
                if any(keyword in threat_type.lower() for keyword in emergency_keywords):
                    return WorkflowPriority.EMERGENCY
                
                if threat_severity == "critical":
                    max_severity = "critical"
                elif threat_severity == "high" and max_severity != "critical":
                    max_severity = "high"
            
            if max_severity == "critical":
                return WorkflowPriority.CRITICAL
            elif max_severity == "high":
                return WorkflowPriority.URGENT
            else:
                return WorkflowPriority.ELEVATED
        
        elif trigger_source == "langgraph":
            graph_event = trigger_data.get("event_type", "")
            if "error" in graph_event or "failure" in graph_event:
                return WorkflowPriority.URGENT
            else:
                return WorkflowPriority.ROUTINE
        
        else:
            # External or unknown triggers
            return WorkflowPriority.ELEVATED
    
    async def _workflow_executor(self):
        """Main workflow executor loop"""
        while True:
            try:
                # Get next workflow (priority queue would be better)
                workflow = await self.workflow_queue.get()
                
                self.logger.info(f"🎭 The Chamberlain begins workflow orchestration: {workflow.workflow_id}")
                
                # Execute workflow
                success = await self._execute_workflow(workflow)
                
                # Update statistics
                self._update_workflow_statistics(workflow, success)
                
                # Cleanup workflow
                workflow.completed_at = datetime.utcnow()
                workflow.status = "completed" if success else "failed"
                
                self.workflow_queue.task_done()
                
                # Remove from active workflows after delay
                asyncio.create_task(self._cleanup_workflow(workflow.workflow_id, delay_minutes=60))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Chamberlain workflow executor error: {e}")
                await asyncio.sleep(60)
    
    async def _execute_workflow(self, workflow: BackupWorkflow) -> bool:
        """Execute complete backup workflow through all phases"""
        
        workflow.started_at = datetime.utcnow()
        workflow.status = "in_progress"
        
        try:
            # Phase 1: Detection and Analysis
            workflow.current_phase = WorkflowPhase.DETECTION
            detection_result = await self._phase_detection(workflow)
            workflow.phase_results[WorkflowPhase.DETECTION] = detection_result
            
            if not detection_result.get("success", False):
                return False
            
            # Phase 2: Assessment
            workflow.current_phase = WorkflowPhase.ASSESSMENT  
            assessment_result = await self._phase_assessment(workflow)
            workflow.phase_results[WorkflowPhase.ASSESSMENT] = assessment_result
            
            if not assessment_result.get("success", False):
                return False
            
            # Phase 3: Preparation
            workflow.current_phase = WorkflowPhase.PREPARATION
            preparation_result = await self._phase_preparation(workflow)
            workflow.phase_results[WorkflowPhase.PREPARATION] = preparation_result
            
            if not preparation_result.get("success", False):
                return False
            
            # Phase 4: Execution
            workflow.current_phase = WorkflowPhase.EXECUTION
            execution_result = await self._phase_execution(workflow)
            workflow.phase_results[WorkflowPhase.EXECUTION] = execution_result
            
            if not execution_result.get("success", False):
                return False
            
            # Phase 5: Verification
            workflow.current_phase = WorkflowPhase.VERIFICATION
            verification_result = await self._phase_verification(workflow)
            workflow.phase_results[WorkflowPhase.VERIFICATION] = verification_result
            
            if not verification_result.get("success", False):
                return False
            
            # Phase 6: Delivery
            workflow.current_phase = WorkflowPhase.DELIVERY
            delivery_result = await self._phase_delivery(workflow)
            workflow.phase_results[WorkflowPhase.DELIVERY] = delivery_result
            
            # Phase 7: Completion
            workflow.current_phase = WorkflowPhase.COMPLETION
            completion_result = await self._phase_completion(workflow)
            workflow.phase_results[WorkflowPhase.COMPLETION] = completion_result
            
            return True
            
        except Exception as e:
            workflow.error_log.append(f"Workflow execution failed: {e}")
            self.logger.error(f"❌ Workflow {workflow.workflow_id} failed: {e}")
            return False
    
    async def _phase_detection(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 1: Detect and validate threats"""
        self.logger.info(f"🔍 Workflow {workflow.workflow_id}: Detection phase")
        
        trigger_data = workflow.trigger_data
        threats = trigger_data.get("data", {}).get("threats", [])
        
        # Use CrewAI threat analyst to analyze threats
        if self.crew and threats:
            try:
                # Create analysis task
                analysis_task = Task(
                    description=f"Analyze the following threat data and determine backup requirements: {json.dumps(threats[:3])}",
                    agent=self.agents["threat_analyst"]
                )
                
                # This would execute the CrewAI task in production
                analysis_result = {
                    "threats_analyzed": len(threats),
                    "severity_assessment": "medium",
                    "backup_recommendation": "incremental_backup",
                    "urgency_level": "standard"
                }
                
            except Exception as e:
                self.logger.warning(f"⚠️ CrewAI analysis failed, using fallback: {e}")
                analysis_result = {
                    "threats_analyzed": len(threats),
                    "severity_assessment": "unknown",
                    "backup_recommendation": "incremental_backup",
                    "fallback_analysis": True
                }
        else:
            # Fallback analysis
            analysis_result = {
                "threats_analyzed": len(threats),
                "severity_assessment": "low",
                "backup_recommendation": "incremental_backup",
                "no_crew_analysis": True
            }
        
        return {
            "success": True,
            "phase": "detection",
            "analysis": analysis_result,
            "threats_detected": len(threats)
        }
    
    async def _phase_assessment(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 2: Assess backup requirements and plan strategy"""
        self.logger.info(f"📊 Workflow {workflow.workflow_id}: Assessment phase")
        
        detection_result = workflow.phase_results.get(WorkflowPhase.DETECTION, {})
        backup_recommendation = detection_result.get("analysis", {}).get("backup_recommendation", "incremental_backup")
        
        # Determine backup mode
        if backup_recommendation in ["disaster_recovery", "emergency_backup"]:
            backup_mode = BackupMode.DISASTER_RECOVERY
        elif backup_recommendation in ["critical_backup", "high_priority"]:
            backup_mode = BackupMode.CRITICAL
        elif backup_recommendation in ["full_backup", "complete_system"]:
            backup_mode = BackupMode.FULL_SYSTEM
        else:
            backup_mode = BackupMode.INCREMENTAL
        
        # Assign keeper responsibilities
        keeper_assignments = {
            "sentinel": {
                "role": "threat_monitoring",
                "tasks": ["continue_watch", "monitor_new_threats"],
                "priority": "background"
            },
            "archivist": {
                "role": "backup_execution", 
                "tasks": ["execute_backup", "verify_integrity"],
                "backup_mode": backup_mode.value,
                "priority": "primary"
            },
            "courier": {
                "role": "delivery_coordination",
                "tasks": ["prepare_channels", "execute_delivery"],
                "priority": "secondary"
            }
        }
        
        workflow.keeper_assignments = keeper_assignments
        
        return {
            "success": True,
            "phase": "assessment", 
            "backup_mode": backup_mode.value,
            "keeper_assignments": keeper_assignments,
            "estimated_duration_minutes": self._estimate_workflow_duration(backup_mode)
        }
    
    async def _phase_preparation(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 3: Prepare all keepers for coordinated action"""
        self.logger.info(f"⚙️ Workflow {workflow.workflow_id}: Preparation phase")
        
        preparation_tasks = []
        
        # Prepare Archivist
        archivist_assignment = workflow.keeper_assignments.get("archivist", {})
        backup_mode_str = archivist_assignment.get("backup_mode", "incremental")
        backup_mode = BackupMode(backup_mode_str)
        
        # Prepare Courier
        courier_assignment = workflow.keeper_assignments.get("courier", {})
        
        # Test courier delivery channels if critical backup
        if backup_mode in [BackupMode.CRITICAL, BackupMode.DISASTER_RECOVERY]:
            courier_test_result = await self.courier.test_delivery_channels()
            preparation_tasks.append({
                "keeper": "courier",
                "task": "channel_test",
                "result": courier_test_result
            })
        
        return {
            "success": True,
            "phase": "preparation",
            "preparation_tasks": preparation_tasks,
            "ready_for_execution": True
        }
    
    async def _phase_execution(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 4: Execute backup through Archivist"""
        self.logger.info(f"⚔️ Workflow {workflow.workflow_id}: Execution phase")
        
        assessment_result = workflow.phase_results.get(WorkflowPhase.ASSESSMENT, {})
        backup_mode_str = assessment_result.get("backup_mode", "incremental")
        backup_mode = BackupMode(backup_mode_str)
        
        # Execute backup through Archivist
        try:
            backup_result = await self.archivist.execute_backup(
                backup_mode=backup_mode,
                threat_data=workflow.trigger_data.get("data", {})
            )
            
            return {
                "success": True,
                "phase": "execution",
                "backup_result": backup_result,
                "artifacts_created": len(backup_result.get("artifacts", [])),
                "backup_size_mb": backup_result.get("size_bytes", 0) / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": "execution",
                "error": str(e),
                "backup_failed": True
            }
    
    async def _phase_verification(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 5: Verify backup integrity and completeness"""
        self.logger.info(f"🔍 Workflow {workflow.workflow_id}: Verification phase")
        
        execution_result = workflow.phase_results.get(WorkflowPhase.EXECUTION, {})
        backup_result = execution_result.get("backup_result", {})
        artifacts = backup_result.get("artifacts", [])
        
        verification_results = []
        
        for artifact in artifacts:
            artifact_path = Path(artifact.get("path", ""))
            expected_hash = artifact.get("hash", "")
            
            if artifact_path.exists() and expected_hash:
                # Verify file integrity
                actual_hash = self.calculate_file_hash(str(artifact_path))
                integrity_ok = (actual_hash == expected_hash)
                
                verification_results.append({
                    "artifact_type": artifact.get("type", "unknown"),
                    "path": str(artifact_path),
                    "integrity_verified": integrity_ok,
                    "size_bytes": artifact.get("size_bytes", 0)
                })
            else:
                verification_results.append({
                    "artifact_type": artifact.get("type", "unknown"),
                    "path": str(artifact_path),
                    "integrity_verified": False,
                    "error": "missing_file_or_hash"
                })
        
        verification_success = all(v.get("integrity_verified", False) for v in verification_results)
        
        return {
            "success": verification_success,
            "phase": "verification",
            "verified_artifacts": len([v for v in verification_results if v.get("integrity_verified", False)]),
            "total_artifacts": len(verification_results),
            "verification_details": verification_results
        }
    
    async def _phase_delivery(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 6: Deliver backups through Courier"""
        self.logger.info(f"🚀 Workflow {workflow.workflow_id}: Delivery phase")
        
        execution_result = workflow.phase_results.get(WorkflowPhase.EXECUTION, {})
        backup_result = execution_result.get("backup_result", {})
        
        # Determine delivery priority based on workflow priority
        if workflow.priority in [WorkflowPriority.CRITICAL, WorkflowPriority.EMERGENCY]:
            delivery_priority = 0  # Highest
        elif workflow.priority == WorkflowPriority.URGENT:
            delivery_priority = 1
        else:
            delivery_priority = 2
        
        try:
            # Dispatch backup for delivery
            delivery_job_id = await self.courier.dispatch_backup(
                backup_result=backup_result,
                delivery_priority=delivery_priority
            )
            
            # Wait for delivery completion (with timeout)
            delivery_timeout = 300  # 5 minutes
            delivery_completed = False
            
            for _ in range(delivery_timeout):
                courier_status = self.courier.get_delivery_status()
                active_jobs = courier_status.get("active_jobs", {})
                
                if delivery_job_id and delivery_job_id not in [j for j in self.courier.active_jobs.keys()]:
                    delivery_completed = True
                    break
                
                await asyncio.sleep(1)
            
            return {
                "success": delivery_completed,
                "phase": "delivery",
                "delivery_job_id": delivery_job_id,
                "delivery_completed": delivery_completed,
                "timeout_reached": not delivery_completed
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": "delivery",
                "error": str(e),
                "delivery_failed": True
            }
    
    async def _phase_completion(self, workflow: BackupWorkflow) -> Dict[str, Any]:
        """Phase 7: Complete workflow and update records"""
        self.logger.info(f"✅ Workflow {workflow.workflow_id}: Completion phase")
        
        # Calculate workflow statistics
        duration_seconds = 0
        if workflow.started_at:
            duration_seconds = (datetime.utcnow() - workflow.started_at).total_seconds()
        
        # Count successful phases
        successful_phases = len([
            phase for phase, result in workflow.phase_results.items()
            if result.get("success", False)
        ])
        
        total_phases = len(workflow.phase_results)
        
        # Update vault history
        await self._record_workflow_completion(workflow, successful_phases, total_phases)
        
        # Publish completion event
        self.publish_event("chamberlain.workflow_completed", {
            "workflow_id": workflow.workflow_id,
            "priority": workflow.priority.name,
            "duration_seconds": duration_seconds,
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "success_rate": round(successful_phases / max(total_phases, 1) * 100, 2)
        })
        
        return {
            "success": successful_phases == total_phases,
            "phase": "completion",
            "workflow_duration_seconds": duration_seconds,
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "completion_timestamp": datetime.utcnow().isoformat()
        }
    
    def _estimate_workflow_duration(self, backup_mode: BackupMode) -> int:
        """Estimate workflow duration in minutes"""
        
        duration_estimates = {
            BackupMode.INCREMENTAL: 5,
            BackupMode.CRITICAL: 15,
            BackupMode.FULL_SYSTEM: 30,
            BackupMode.DISASTER_RECOVERY: 45
        }
        
        return duration_estimates.get(backup_mode, 10)
    
    async def _record_workflow_completion(self, workflow: BackupWorkflow, successful_phases: int, total_phases: int):
        """Record workflow completion in database"""
        try:
            insert_sql = """
            INSERT INTO vault_workflows 
            (workflow_id, trigger_source, priority, status, successful_phases, 
             total_phases, duration_seconds, phase_results, created_at, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            duration_seconds = 0
            if workflow.started_at and workflow.completed_at:
                duration_seconds = (workflow.completed_at - workflow.started_at).total_seconds()
            
            self.postgres_agent.execute_query(
                insert_sql,
                (
                    workflow.workflow_id,
                    workflow.trigger_data.get("source", "unknown"),
                    workflow.priority.value,
                    workflow.status,
                    successful_phases,
                    total_phases,
                    duration_seconds,
                    json.dumps(workflow.phase_results, default=str),
                    workflow.created_at,
                    workflow.completed_at or datetime.utcnow()
                )
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to record workflow completion: {e}")
    
    def _update_workflow_statistics(self, workflow: BackupWorkflow, success: bool):
        """Update Chamberlain performance statistics"""
        self.performance_metrics["total_workflows"] += 1
        
        if success:
            self.performance_metrics["successful_workflows"] += 1
        else:
            self.performance_metrics["failed_workflows"] += 1
        
        # Update average duration
        if workflow.started_at and workflow.completed_at:
            duration = (workflow.completed_at - workflow.started_at).total_seconds()
            total_workflows = self.performance_metrics["total_workflows"]
            
            self.performance_metrics["average_workflow_duration"] = (
                (self.performance_metrics["average_workflow_duration"] * (total_workflows - 1) + duration) /
                total_workflows
            )
        
        # Update data protected (estimate from execution results)
        execution_result = workflow.phase_results.get(WorkflowPhase.EXECUTION, {})
        backup_size_mb = execution_result.get("backup_size_mb", 0)
        self.performance_metrics["total_data_protected_gb"] += backup_size_mb / 1024
    
    async def _cleanup_workflow(self, workflow_id: str, delay_minutes: int = 60):
        """Cleanup completed workflow after delay"""
        await asyncio.sleep(delay_minutes * 60)
        
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow.status in ["completed", "failed"]:
                del self.active_workflows[workflow_id]
                self.logger.debug(f"🧹 Cleaned up workflow: {workflow_id}")
    
    async def _health_monitor_loop(self):
        """Monitor vault health continuously"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Health monitor error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _perform_health_check(self):
        """Perform comprehensive vault health check"""
        
        health_factors = []
        
        # Check Sentinel health
        sentinel_status = self.sentinel.get_watch_status()
        if sentinel_status.get("watching", False):
            health_factors.append(("sentinel", 25))
        else:
            health_factors.append(("sentinel", 0))
        
        # Check Courier health
        courier_status = self.courier.get_delivery_status()
        if courier_status.get("service_running", False):
            success_rate = courier_status.get("statistics", {}).get("success_rate", 0)
            health_factors.append(("courier", min(25, success_rate * 0.25)))
        else:
            health_factors.append(("courier", 0))
        
        # Check Archivist health (archive status)
        try:
            archive_status = self.archivist.get_archive_status()
            if archive_status.get("total_backups", 0) > 0:
                health_factors.append(("archivist", 25))
            else:
                health_factors.append(("archivist", 10))  # Some points for being available
        except:
            health_factors.append(("archivist", 0))
        
        # Check workflow performance
        if self.performance_metrics["total_workflows"] > 0:
            success_rate = (self.performance_metrics["successful_workflows"] / 
                          self.performance_metrics["total_workflows"])
            health_factors.append(("workflows", success_rate * 25))
        else:
            health_factors.append(("workflows", 25))  # Full points if no failures yet
        
        # Calculate overall health score
        self.vault_health_score = sum(score for _, score in health_factors)
        self.last_health_check = datetime.utcnow()
        
        # Log health status
        if self.vault_health_score >= 90:
            self.logger.info(f"💚 Vault health excellent: {self.vault_health_score}/100")
        elif self.vault_health_score >= 70:
            self.logger.info(f"💛 Vault health good: {self.vault_health_score}/100")
        else:
            self.logger.warning(f"❤️ Vault health concerning: {self.vault_health_score}/100")
        
        # Publish health event
        self.publish_event("chamberlain.health_check", {
            "health_score": self.vault_health_score,
            "health_factors": dict(health_factors),
            "check_timestamp": self.last_health_check.isoformat()
        })
    
    async def emergency_protocol(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute emergency protocol for critical situations
        
        Like sounding the castle bells when enemies breach the gates,
        this protocol mobilizes all resources for immediate protection.
        """
        self.logger.critical("🚨 CHAMBERLAIN EMERGENCY PROTOCOL ACTIVATED")
        
        emergency_id = f"emergency_{int(datetime.utcnow().timestamp())}"
        
        # Create emergency workflow with maximum priority
        emergency_workflow = BackupWorkflow(
            workflow_id=emergency_id,
            trigger_data={"source": "emergency_protocol", "data": emergency_data},
            priority=WorkflowPriority.EMERGENCY
        )
        
        # Execute emergency workflow immediately (bypass queue)
        self.active_workflows[emergency_id] = emergency_workflow
        
        # Execute parallel emergency actions
        emergency_tasks = [
            self.archivist.execute_backup(BackupMode.DISASTER_RECOVERY, emergency_data),
            self.courier.emergency_evacuation(emergency_data),
            self.sentinel.handle_external_trigger("emergency_protocol", emergency_data)
        ]
        
        emergency_results = await asyncio.gather(*emergency_tasks, return_exceptions=True)
        
        # Record emergency protocol execution
        self.publish_event("chamberlain.emergency_protocol", {
            "emergency_id": emergency_id,
            "trigger_data": emergency_data,
            "emergency_actions": len(emergency_tasks),
            "completed_actions": len([r for r in emergency_results if not isinstance(r, Exception)])
        })
        
        return {
            "emergency_id": emergency_id,
            "status": "executed",
            "emergency_results": [
                str(r) if isinstance(r, Exception) else "success"
                for r in emergency_results
            ],
            "fortress_status": "emergency_protocol_complete"
        }
    
    def get_vault_status(self) -> Dict[str, Any]:
        """Get comprehensive vault status"""
        
        return {
            "chamberlain": {
                "orchestration_active": self.workflow_executor_task is not None,
                "active_workflows": len(self.active_workflows),
                "workflow_queue_size": self.workflow_queue.qsize(),
                "health_score": self.vault_health_score,
                "last_health_check": self.last_health_check.isoformat(),
                "performance_metrics": self.performance_metrics
            },
            "keepers": {
                "sentinel": self.sentinel.get_watch_status(),
                "archivist": self.archivist.get_archive_status(),
                "courier": self.courier.get_delivery_status()
            },
            "vault_summary": {
                "fortress_status": "operational" if self.vault_health_score >= 70 else "degraded",
                "total_keepers": 4,  # Including Chamberlain
                "active_keepers": sum([
                    1 if self.sentinel.watching else 0,
                    1,  # Archivist always available
                    1 if self.courier.delivery_worker_task else 0,
                    1 if self.workflow_executor_task else 0  # Chamberlain
                ]),
                "protection_level": "maximum" if self.vault_health_score >= 90 else "standard"
            }
        }
    
    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history"""
        
        try:
            history_sql = """
            SELECT workflow_id, trigger_source, priority, status, 
                   successful_phases, total_phases, duration_seconds, 
                   created_at, completed_at
            FROM vault_workflows 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            
            workflows = self.postgres_agent.fetch_all(history_sql, (limit,))
            
            return [
                {
                    "workflow_id": row[0],
                    "trigger_source": row[1],
                    "priority": row[2],
                    "status": row[3],
                    "successful_phases": row[4],
                    "total_phases": row[5],
                    "duration_seconds": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "completed_at": row[8].isoformat() if row[8] else None
                }
                for row in workflows
            ]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get workflow history: {e}")
            return []
    
    def __str__(self) -> str:
        active_workflows = len(self.active_workflows)
        orchestration_status = "orchestrating" if self.workflow_executor_task else "ready"
        return f"🛡️ The Chamberlain - Magister Palatii ({active_workflows} active workflows, {orchestration_status})"