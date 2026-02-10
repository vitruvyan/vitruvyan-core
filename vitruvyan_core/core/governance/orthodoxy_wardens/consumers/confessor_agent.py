"""
Autonomous Audit Agent - LangGraph Implementation
NO CrewAI Dependencies - Pure Python + LangGraph
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, TypedDict
import json
from langgraph.graph import StateGraph, END

# Import your existing LLM interface
from core.llm.llm_interface import LLMInterface

# Import monitoring tools (NEW GOVERNANCE STRUCTURE)
from core.governance.orthodoxy_wardens.consumers.code_analyzer import CodeAnalyzer
# LEGACY: These 3 files moved to _legacy/ during FASE 0 refactoring (Feb 9, 2026)
# They will be eliminated entirely when confessor is rewritten as pure consumer (FASE 3)
from core.governance.orthodoxy_wardens._legacy.chronicler_agent import SystemMonitor
from core.governance.orthodoxy_wardens._legacy.docker_manager import DockerManager
from core.governance.orthodoxy_wardens._legacy.git_monitor import GitMonitor
from core.governance.orthodoxy_wardens.consumers.inquisitor_agent import ComplianceValidator
from core.governance.orthodoxy_wardens.consumers.penitent_agent import AutoCorrector
# TODO: disaster_prevention moved to different location - to be implemented
# from domains.trade.agents.disaster_prevention import get_disaster_prevention_agent

# Audit State definition
class AuditState(TypedDict):
    audit_id: str
    trigger_type: str
    analysis_results: Dict
    compliance_score: float
    healing_actions: List[Dict]
    auto_corrections: List[Dict]
    learning_insights: Dict
    notifications: List[Dict]
    status: str

class AutonomousAuditAgent:
    """
    Orchestrates comprehensive system audits using LangGraph workflow.
    
    **What it does**: 
    Coordinates all governance agents (SystemMonitor, ComplianceValidator, AutoCorrector) 
    to execute full audits of code changes, system health, and compliance violations. 
    Decides autonomously whether issues can be auto-corrected or require manual review.
    
    **How it works**:
    9-step LangGraph pipeline:
    1. trigger_analysis() - Determines audit scope (code_commit, scheduled, manual)
    2. analyze_code() - Static analysis of recent code changes via CodeAnalyzer
    3. monitor_system_health() - Collects metrics via SystemMonitor (CPU/memory/disk)
    4. validate_compliance() - Scans outputs via ComplianceValidator (regex + LLM)
    5. decide_action() - Decision engine: auto-correct vs escalate vs approve
    6. execute_auto_corrections() - Applies fixes via AutoCorrector (if approved)
    7. heal_system() - Restarts unhealthy containers, clears disk space
    8. send_notifications() - Alerts via Slack/PostgreSQL logs
    9. learn_from_audit() - Updates historical patterns for future audits
    
    **When to use**:
    - After Git commits (trigger_type='code_commit')
    - Scheduled health checks (every 10 minutes, trigger_type='scheduled')
    - Manual audit requests via API (trigger_type='manual')
    - After Neural Engine/VEE operations (trigger_type='output_validation')
    
    **Example**:
    ```python
    agent = AutonomousAuditAgent(config={
        "llm_interface": llm,
        "db_manager": db,
        "docker_manager": docker,
        "git_monitor": git
    })
    
    result = await agent.audit_workflow.ainvoke({
        "audit_id": "audit-123",
        "trigger_type": "code_commit",
        "repository": "vitruvyan-core",
        "commit_sha": "abc123"
    })
    
    # result contains:
    # - compliance_score: float (0-1)
    # - violations: List[Dict]
    # - auto_corrections: List[Dict]
    # - healing_actions: List[str]
    # - learning_insights: Dict
    ```
    
    **Dependencies**: Requires SystemMonitor, ComplianceValidator, AutoCorrector, 
    CodeAnalyzer, DockerManager, GitMonitor instances.
    
    **Output**: AuditState dataclass with full audit report and recommended actions.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM interface (your existing caching system)
        self.llm_interface = config.get("llm_interface")
        self.db_manager = config.get("db_manager")
        
        # Initialize monitoring tools
        self.code_analyzer = CodeAnalyzer()
        self.system_monitor = SystemMonitor()
        self.docker_manager = DockerManager()
        self.git_monitor = GitMonitor()
        self.compliance_validator = ComplianceValidator(self.llm_interface)
        self.auto_corrector = AutoCorrector()
        # TODO: disaster_prevention to be re-implemented in governance structure
        self.disaster_prevention = None  # Temporarily disabled
        
        # Setup LangGraph workflow
        self.setup_workflow()
        
        self.logger.info("Autonomous Audit Agent initialized")
    
    def setup_workflow(self):
        """
        Setup LangGraph workflow for autonomous audit process
        """
        workflow = StateGraph(AuditState)
        
        # Add all nodes
        workflow.add_node("trigger_analysis", self.analyze_trigger)
        workflow.add_node("code_analysis", self.analyze_code_changes)
        workflow.add_node("system_monitoring", self.monitor_system_health)
        workflow.add_node("compliance_check", self.validate_compliance)
        workflow.add_node("decision_engine", self.make_autonomous_decisions)
        workflow.add_node("auto_correction", self.execute_auto_corrections)
        workflow.add_node("system_healing", self.heal_system_issues)
        workflow.add_node("notification", self.send_notifications)
        workflow.add_node("learning", self.extract_learning_insights)
        
        # Define the flow
        workflow.set_entry_point("trigger_analysis")
        workflow.add_edge("trigger_analysis", "code_analysis")
        workflow.add_edge("code_analysis", "system_monitoring")
        workflow.add_edge("system_monitoring", "compliance_check")
        workflow.add_edge("compliance_check", "decision_engine")
        
        # Conditional routing based on severity
        workflow.add_conditional_edges(
            "decision_engine",
            self.route_based_on_severity,
            {
                "critical": "auto_correction",
                "high": "system_healing",
                "medium": "notification",
                "low": "learning"
            }
        )
        
        # All paths converge to notification and learning
        workflow.add_edge("auto_correction", "notification")
        workflow.add_edge("system_healing", "notification")
        workflow.add_edge("notification", "learning")
        workflow.add_edge("learning", END)
        
        # Compile the workflow
        self.workflow = workflow.compile()
        
        self.logger.info("LangGraph workflow compiled successfully")
    
    async def analyze_trigger(self, state: AuditState) -> AuditState:
        """
        Node 1: Analyze what triggered this audit cycle
        """
        trigger_type = state.get("trigger_type", "scheduled")
        audit_id = state.get("audit_id")
        
        self.logger.info(f"Analyzing trigger for audit {audit_id}: {trigger_type}")
        
        # Assess trigger severity and scope
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "trigger_source": trigger_type,
            "severity": self._assess_trigger_severity(trigger_type),
            "scope": await self._determine_audit_scope(trigger_type),
            "priority": self._calculate_priority(trigger_type)
        }
        
        # Initialize analysis results
        state["analysis_results"] = analysis
        state["status"] = "analyzing"
        
        self.logger.info(f"Trigger analysis complete: severity={analysis['severity']}, scope={len(analysis['scope'])}")
        
        return state
    
    async def analyze_code_changes(self, state: AuditState) -> AuditState:
        """
        Node 2: Analyze recent code changes for compliance and security issues
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Analyzing code changes for audit {audit_id}")
        
        try:
            # Get recent git changes
            changes = await self.git_monitor.get_recent_changes()
            
            # Analyze each change
            code_analysis = []
            total_risk_score = 0
            
            for change in changes:
                try:
                    analysis = await self.code_analyzer.analyze_change(change)
                    code_analysis.append(analysis)
                    
                    # Accumulate risk score
                    risk_score = self._extract_risk_score(analysis)
                    total_risk_score += risk_score
                    
                except Exception as e:
                    self.logger.error(f"Failed to analyze change {change.get('file_path', 'unknown')}: {e}")
                    code_analysis.append({
                        "file_path": change.get("file_path", "unknown"),
                        "error": str(e),
                        "risk_level": "unknown"
                    })
            
            # Calculate overall code risk
            avg_risk_score = total_risk_score / len(changes) if changes else 0
            
            state["analysis_results"]["code_changes"] = {
                "total_changes": len(changes),
                "analyzed_changes": len(code_analysis),
                "analysis": code_analysis,
                "overall_risk_score": avg_risk_score,
                "risk_level": self._categorize_risk_level(avg_risk_score)
            }
            
            self.logger.info(f"Code analysis complete: {len(changes)} changes, risk_level={self._categorize_risk_level(avg_risk_score)}")
            
        except Exception as e:
            self.logger.error(f"Code analysis failed for audit {audit_id}: {e}")
            state["analysis_results"]["code_changes"] = {
                "error": str(e),
                "risk_level": "error"
            }
        
        return state
    
    async def monitor_system_health(self, state: AuditState) -> AuditState:
        """
        Node 3: Monitor system health and performance
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Monitoring system health for audit {audit_id}")
        
        try:
            # Get system metrics
            health_metrics = await self.system_monitor.get_health_metrics()
            
            # Check container health
            container_health = await self.docker_manager.check_all_containers()
            
            # Check database performance
            db_metrics = await self.system_monitor.check_database_performance()
            
            # Assess overall system health
            overall_health = self._assess_system_health(health_metrics, container_health, db_metrics)
            
            state["analysis_results"]["system_health"] = {
                "metrics": health_metrics,
                "containers": container_health,
                "database": db_metrics,
                "overall_status": overall_health["status"],
                "health_score": overall_health["score"],
                "critical_issues": overall_health["critical_issues"]
            }
            
            self.logger.info(f"System health monitoring complete: status={overall_health['status']}, score={overall_health['score']}")
            
        except Exception as e:
            self.logger.error(f"System monitoring failed for audit {audit_id}: {e}")
            state["analysis_results"]["system_health"] = {
                "error": str(e),
                "overall_status": "error",
                "health_score": 0.0
            }
        
        return state
    
    async def validate_compliance(self, state: AuditState) -> AuditState:
        """
        Node 4: Validate financial compliance using LLM
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Validating compliance for audit {audit_id}")
        
        try:
            # Get recent financial outputs for compliance validation
            compliance_results = await self.compliance_validator.validate_recent_outputs()
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(compliance_results)
            
            state["compliance_score"] = compliance_score
            state["analysis_results"]["compliance"] = {
                "validation_results": compliance_results,
                "compliance_score": compliance_score,
                "compliance_level": self._categorize_compliance_level(compliance_score),
                "critical_violations": [r for r in compliance_results if r.get("severity") == "critical"]
            }
            
            self.logger.info(f"Compliance validation complete: score={compliance_score}, level={self._categorize_compliance_level(compliance_score)}")
            
        except Exception as e:
            self.logger.error(f"Compliance validation failed for audit {audit_id}: {e}")
            state["compliance_score"] = 0.0
            state["analysis_results"]["compliance"] = {
                "error": str(e),
                "compliance_score": 0.0,
                "compliance_level": "error"
            }
        
        return state
    
    async def make_autonomous_decisions(self, state: AuditState) -> AuditState:
        """
        Node 5: Make autonomous decisions based on all analysis
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Making autonomous decisions for audit {audit_id}")
        
        analysis = state["analysis_results"]
        compliance_score = state.get("compliance_score", 1.0)
        
        # Calculate overall risk score
        overall_risk = await self._calculate_overall_risk(analysis, compliance_score)
        
        # Determine autonomous actions based on risk
        actions = []
        if overall_risk >= 0.8:
            # Critical: Immediate action required + Emergency backup
            # TODO: Re-enable disaster prevention when re-implemented
            backup_id = None  # self.disaster_prevention.create_emergency_backup()
            actions = [
                {"action": "emergency_backup", "priority": "critical", "auto_execute": False, "backup_id": backup_id},  # Disabled until disaster_prevention restored
                {"action": "immediate_fix", "priority": "critical", "auto_execute": True},
                {"action": "alert_team", "priority": "critical", "auto_execute": True},
                {"action": "increase_monitoring", "priority": "high", "auto_execute": True}
            ]
            severity = "critical"
            
        elif overall_risk >= 0.6:
            # High: Schedule fixes and notify
            actions = [
                {"action": "schedule_fix", "priority": "high", "auto_execute": True},
                {"action": "notify_team", "priority": "high", "auto_execute": True},
                {"action": "container_health_check", "priority": "medium", "auto_execute": True}
            ]
            severity = "high"
            
        elif overall_risk >= 0.3:
            # Medium: Log and schedule review
            actions = [
                {"action": "log_issue", "priority": "medium", "auto_execute": True},
                {"action": "schedule_review", "priority": "medium", "auto_execute": False}
            ]
            severity = "medium"
            
        else:
            # Low: Continue monitoring
            actions = [
                {"action": "continue_monitoring", "priority": "low", "auto_execute": True}
            ]
            severity = "low"
        
        state["healing_actions"] = actions
        state["status"] = severity
        
        # Use LLM for additional decision insights
        if self.llm_interface:
            try:
                decision_prompt = self._create_decision_prompt(analysis, compliance_score, overall_risk)
                llm_insights = await self.llm_interface.get_completion(decision_prompt)
                
                state["analysis_results"]["llm_insights"] = {
                    "decision_analysis": llm_insights,
                    "prompt_used": decision_prompt[:200] + "..."  # Truncate for logging
                }
                
            except Exception as e:
                self.logger.error(f"LLM decision insights failed: {e}")
        
        self.logger.info(f"Autonomous decisions made: severity={severity}, actions={len(actions)}, risk={overall_risk:.2f}")
        
        return state
    
    def route_based_on_severity(self, state: AuditState) -> str:
        """
        Routing function: Route to appropriate node based on severity
        """
        severity = state.get("status", "low")
        self.logger.info(f"Routing audit {state.get('audit_id')} to {severity} severity path")
        return severity
    
    async def execute_auto_corrections(self, state: AuditState) -> AuditState:
        """
        Node 6a: Execute automatic corrections for critical issues
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Executing auto-corrections for audit {audit_id}")
        
        corrections = []
        
        for action_item in state.get("healing_actions", []):
            if action_item.get("auto_execute") and action_item["action"] in ["immediate_fix", "container_restart"]:
                try:
                    result = await self.auto_corrector.apply_fix(action_item, state["analysis_results"])
                    corrections.append(result)
                    self.logger.info(f"Auto-correction applied: {action_item['action']}")
                    
                except Exception as e:
                    self.logger.error(f"Auto-correction failed for {action_item['action']}: {e}")
                    corrections.append({
                        "action": action_item["action"],
                        "status": "failed",
                        "error": str(e)
                    })
        
        state["auto_corrections"] = corrections
        self.logger.info(f"Auto-corrections complete: {len(corrections)} corrections applied")
        
        return state
    
    async def heal_system_issues(self, state: AuditState) -> AuditState:
        """
        Node 6b: Heal system issues automatically
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Healing system issues for audit {audit_id}")
        
        healing_results = []
        system_health = state["analysis_results"].get("system_health", {})
        
        # INTELLIGENT: Restart only truly unhealthy containers with additional validation
        unhealthy_containers = system_health.get("containers", {}).get("unhealthy", [])
        self.logger.info(f"Found {len(unhealthy_containers)} potentially unhealthy containers: {unhealthy_containers}")
        
        for container in unhealthy_containers:
            # Additional validation before restart
            container_info = await self._validate_container_health(container)
            
            if container_info["needs_restart"]:
                try:
                    await self.docker_manager.restart_container(container)
                    healing_results.append({
                        "container": container,
                        "action": "restart",
                        "status": "success",
                        "message": f"Container restarted after validation: {container_info['reason']}"
                    })
                    self.logger.info(f"✅ Restarted container {container}: {container_info['reason']}")
                    
                except Exception as e:
                    healing_results.append({
                        "container": container,
                        "action": "restart", 
                        "status": "failed",
                        "message": f"Restart failed: {str(e)}"
                    })
                    self.logger.error(f"❌ Failed to restart {container}: {e}")
            else:
                healing_results.append({
                    "container": container,
                    "action": "skip_restart",
                    "status": "healthy_on_validation",
                    "message": f"Container skipped: {container_info['reason']}"
                })
                self.logger.info(f"⏭️ Skipped restart for {container}: {container_info['reason']}")
        
        # Clear disk space if needed
        if system_health.get("metrics", {}).get("disk_percent", 0) > 90:
            try:
                cleanup_result = await self.system_monitor.cleanup_disk_space()
                healing_results.append(cleanup_result)
                self.logger.info("Disk cleanup performed")
                
            except Exception as e:
                self.logger.error(f"Disk cleanup failed: {e}")
        
        state["healing_actions"] = healing_results
        self.logger.info(f"System healing complete: {len(healing_results)} healing actions performed")
        
        return state
    
    async def send_notifications(self, state: AuditState) -> AuditState:
        """
        Node 7: Send notifications based on audit results
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Sending notifications for audit {audit_id}")
        
        notifications = []
        status = state.get("status", "low")
        
        # Send Slack alert for critical/high issues
        if status in ["critical", "high"]:
            try:
                notification = await self._send_slack_alert(state)
                notifications.append(notification)
                self.logger.info("Slack alert sent")
                
            except Exception as e:
                self.logger.error(f"Slack notification failed: {e}")
                notifications.append({"type": "slack", "status": "failed", "error": str(e)})
        
        # Log audit completion to database
        try:
            await self._log_audit_completion(state)
            notifications.append({"type": "database_log", "status": "success"})
            
        except Exception as e:
            self.logger.error(f"Database logging failed: {e}")
        
        # Email notification for critical compliance violations
        compliance_score = state.get("compliance_score", 1.0)
        if compliance_score < 0.5:
            try:
                email_notification = await self._send_compliance_alert(state)
                notifications.append(email_notification)
                
            except Exception as e:
                self.logger.error(f"Email notification failed: {e}")
        
        state["notifications"] = notifications
        self.logger.info(f"Notifications sent: {len(notifications)} notifications")
        
        return state
    
    async def extract_learning_insights(self, state: AuditState) -> AuditState:
        """
        Node 8: Extract learning insights from this audit cycle
        """
        audit_id = state.get("audit_id")
        self.logger.info(f"Extracting learning insights for audit {audit_id}")
        
        try:
            insights = {
                "patterns_detected": await self._analyze_patterns(state),
                "effectiveness": await self._measure_actions_effectiveness(state),
                "recommendations": await self._generate_improvements(state),
                "timestamp": datetime.now().isoformat()
            }
            
            # Use LLM for deeper insights if available
            if self.llm_interface:
                try:
                    learning_prompt = self._create_learning_prompt(state)
                    llm_learning = await self.llm_interface.get_completion(learning_prompt)
                    insights["llm_learning"] = llm_learning
                    
                except Exception as e:
                    self.logger.error(f"LLM learning insights failed: {e}")
            
            state["learning_insights"] = insights
            
            # Save insights to database for future learning
            await self._save_learning_insights(audit_id, insights)
            
            self.logger.info(f"Learning insights extracted: {len(insights)} insights captured")
            
        except Exception as e:
            self.logger.error(f"Learning insights extraction failed: {e}")
            state["learning_insights"] = {"error": str(e)}
        
        # Mark audit as completed
        state["status"] = "completed"
        
        return state
    
    # Helper methods
    def _assess_trigger_severity(self, trigger_type: str) -> str:
        """Assess the severity of the trigger"""
        severity_map = {
            "git_push": "medium",
            "alert": "high", 
            "manual": "medium",
            "scheduled": "low",
            "compliance_violation": "critical",
            "system_failure": "critical"
        }
        return severity_map.get(trigger_type, "medium")
    
    async def _determine_audit_scope(self, trigger_type: str) -> List[str]:
        """Determine what components to audit based on trigger"""
        base_scope = ["code_changes", "system_health", "compliance"]
        
        if trigger_type == "git_push":
            return base_scope + ["recent_commits", "changed_files"]
        elif trigger_type == "alert":
            return base_scope + ["system_monitoring", "container_health"]
        elif trigger_type == "compliance_violation":
            return base_scope + ["financial_outputs", "regulatory_checks"]
        else:
            return base_scope
    
    def _calculate_priority(self, trigger_type: str) -> int:
        """Calculate numeric priority (1-10)"""
        priority_map = {
            "system_failure": 10,
            "compliance_violation": 9,
            "alert": 7,
            "git_push": 5,
            "manual": 5,
            "scheduled": 3
        }
        return priority_map.get(trigger_type, 5)
    
    def _extract_risk_score(self, analysis: Dict) -> float:
        """Extract numeric risk score from analysis"""
        if "error" in analysis:
            return 0.5  # Unknown risk
        
        risk_level = analysis.get("risk_level", "low")
        risk_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        return risk_map.get(risk_level, 0.5)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize numeric risk score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low"
    
    def _assess_system_health(self, health_metrics: Dict, container_health: Dict, db_metrics: Dict) -> Dict:
        """Assess overall system health"""
        critical_issues = []
        score = 1.0
        
        # Check CPU usage
        cpu_percent = health_metrics.get("cpu_percent", 0)
        if cpu_percent > 90:
            critical_issues.append(f"High CPU usage: {cpu_percent}%")
            score -= 0.3
        elif cpu_percent > 70:
            score -= 0.1
        
        # Check memory usage
        memory_percent = health_metrics.get("memory_percent", 0)
        if memory_percent > 90:
            critical_issues.append(f"High memory usage: {memory_percent}%")
            score -= 0.3
        elif memory_percent > 80:
            score -= 0.1
        
        # Check disk usage
        disk_percent = health_metrics.get("disk_percent", 0)
        if disk_percent > 95:
            critical_issues.append(f"Critical disk usage: {disk_percent}%")
            score -= 0.4
        elif disk_percent > 85:
            score -= 0.1
        
        # Check containers
        unhealthy_containers = container_health.get("unhealthy", [])
        if unhealthy_containers:
            critical_issues.append(f"Unhealthy containers: {len(unhealthy_containers)}")
            score -= 0.2 * len(unhealthy_containers)
        
        # Check database
        db_status = db_metrics.get("status", "unknown")
        if db_status == "error":
            critical_issues.append("Database connection error")
            score -= 0.5
        elif db_status == "slow":
            score -= 0.1
        
        # Determine status
        if score <= 0.3:
            status = "critical"
        elif score <= 0.6:
            status = "degraded"
        elif score <= 0.8:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "score": max(0.0, score),
            "critical_issues": critical_issues
        }
    
    def _calculate_compliance_score(self, compliance_results: List[Dict]) -> float:
        """Calculate overall compliance score"""
        if not compliance_results:
            return 1.0
        
        total_violations = len(compliance_results)
        critical_violations = len([r for r in compliance_results if r.get("severity") == "critical"])
        high_violations = len([r for r in compliance_results if r.get("severity") == "high"])
        
        # Weighted penalty
        score = 1.0
        score -= critical_violations * 0.3
        score -= high_violations * 0.1
        score -= (total_violations - critical_violations - high_violations) * 0.05
        
        return max(0.0, score)
    
    def _categorize_compliance_level(self, compliance_score: float) -> str:
        """Categorize compliance score"""
        if compliance_score >= 0.9:
            return "excellent"
        elif compliance_score >= 0.7:
            return "good"
        elif compliance_score >= 0.5:
            return "acceptable"
        else:
            return "poor"
    
    async def _calculate_overall_risk(self, analysis: Dict, compliance_score: float) -> float:
        """Calculate overall risk score from all analysis"""
        risk_factors = []
        
        # Code changes risk
        code_risk = analysis.get("code_changes", {}).get("overall_risk_score", 0.0)
        risk_factors.append(("code", code_risk, 0.3))
        
        # System health risk
        system_health = analysis.get("system_health", {})
        health_score = system_health.get("health_score", 1.0)
        system_risk = 1.0 - health_score
        risk_factors.append(("system", system_risk, 0.4))
        
        # Compliance risk
        compliance_risk = 1.0 - compliance_score
        risk_factors.append(("compliance", compliance_risk, 0.3))
        
        # Calculate weighted average
        total_risk = sum(risk * weight for _, risk, weight in risk_factors)
        
        return min(1.0, total_risk)
    
    def _create_decision_prompt(self, analysis: Dict, compliance_score: float, overall_risk: float) -> str:
        """Create prompt for LLM decision insights"""
        return f"""
Analyze this audit situation and provide autonomous decision recommendations:

ANALYSIS SUMMARY:
- Code Changes Risk: {analysis.get('code_changes', {}).get('risk_level', 'unknown')}
- System Health: {analysis.get('system_health', {}).get('overall_status', 'unknown')}
- Compliance Score: {compliance_score:.2f}
- Overall Risk: {overall_risk:.2f}

CRITICAL ISSUES:
{json.dumps(analysis.get('system_health', {}).get('critical_issues', []), indent=2)}

COMPLIANCE VIOLATIONS:
{json.dumps(analysis.get('compliance', {}).get('critical_violations', []), indent=2)}

Based on this analysis, what autonomous actions should be taken immediately?
Focus on financial compliance and system stability.
Prioritize actions by severity and provide specific recommendations.
"""
    
    def _create_learning_prompt(self, state: Dict) -> str:
        """Create prompt for learning insights"""
        return f"""
Analyze this completed audit cycle and extract learning insights:

AUDIT RESULTS:
- Trigger Type: {state.get('trigger_type')}
- Final Status: {state.get('status')}
- Actions Taken: {len(state.get('healing_actions', []))}
- Corrections Applied: {len(state.get('auto_corrections', []))}

EFFECTIVENESS:
- Were the actions appropriate for the risk level?
- What patterns emerge from this audit?
- How can future audits be improved?

Provide insights for:
1. Pattern Recognition
2. Action Effectiveness
3. System Improvements
4. Compliance Enhancement
"""
    
    async def _analyze_patterns(self, state: Dict) -> Dict:
        """Analyze patterns in this audit"""
        patterns = {
            "trigger_patterns": state.get("trigger_type"),
            "risk_patterns": state.get("status"),
            "action_patterns": [action.get("action") for action in state.get("healing_actions", [])],
            "timing_patterns": datetime.now().hour  # Hour of day
        }
        return patterns
    
    async def _measure_actions_effectiveness(self, state: Dict) -> Dict:
        """Measure how effective the actions were"""
        effectiveness = {
            "auto_corrections": {
                "total": len(state.get("auto_corrections", [])),
                "successful": len([c for c in state.get("auto_corrections", []) if c.get("status") == "success"]),
                "effectiveness_rate": 0.0
            },
            "healing_actions": {
                "total": len(state.get("healing_actions", [])),
                "completed": len([h for h in state.get("healing_actions", []) if h.get("status") == "success"]),
                "effectiveness_rate": 0.0
            }
        }
        
        # Calculate effectiveness rates
        if effectiveness["auto_corrections"]["total"] > 0:
            effectiveness["auto_corrections"]["effectiveness_rate"] = \
                effectiveness["auto_corrections"]["successful"] / effectiveness["auto_corrections"]["total"]
        
        if effectiveness["healing_actions"]["total"] > 0:
            effectiveness["healing_actions"]["effectiveness_rate"] = \
                effectiveness["healing_actions"]["completed"] / effectiveness["healing_actions"]["total"]
        
        return effectiveness
    
    async def _generate_improvements(self, state: Dict) -> List[str]:
        """Generate improvement recommendations"""
        improvements = []
        
        # Check if actions were effective
        auto_corrections = state.get("auto_corrections", [])
        failed_corrections = [c for c in auto_corrections if c.get("status") == "failed"]
        
        if failed_corrections:
            improvements.append("Improve auto-correction mechanisms for failed actions")
        
        # Check compliance score
        compliance_score = state.get("compliance_score", 1.0)
        if compliance_score < 0.7:
            improvements.append("Enhance compliance validation rules")
        
        # Check system health patterns
        system_health = state.get("analysis_results", {}).get("system_health", {})
        critical_issues = system_health.get("critical_issues", [])
        
        if critical_issues:
            improvements.append("Implement proactive monitoring for detected critical issues")
        
        # Add general improvements
        improvements.extend([
            "Consider predictive analytics for issue prevention",
            "Enhance notification granularity",
            "Improve learning from audit patterns"
        ])
        
        return improvements
    
    async def _send_slack_alert(self, state: Dict) -> Dict:
        """Send Slack alert for critical issues"""
        webhook_url = self.config.get("notification_webhook")
        if not webhook_url:
            return {"type": "slack", "status": "skipped", "reason": "no_webhook"}
        
        try:
            import requests
            
            audit_id = state.get("audit_id")
            status = state.get("status")
            critical_issues = state.get("analysis_results", {}).get("system_health", {}).get("critical_issues", [])
            
            message = {
                "text": f"🚨 Vitruvyan Audit Alert - {status.upper()}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Audit ID:* {audit_id}\n*Status:* {status}\n*Critical Issues:* {len(critical_issues)}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Issues:*\n" + "\n".join([f"• {issue}" for issue in critical_issues[:5]])
                        }
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            return {"type": "slack", "status": "success", "response_code": response.status_code}
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {e}")
            return {"type": "slack", "status": "failed", "error": str(e)}
    
    async def _validate_container_health(self, container_name: str) -> Dict[str, any]:
        """
        Perform additional validation before restarting a container.
        Returns dict with 'needs_restart' boolean and 'reason' string.
        """
        try:
            # Get detailed container info
            container_info = await self.docker_manager.get_container_info(container_name)
            
            if not container_info:
                return {"needs_restart": True, "reason": "Container not found or stopped"}
            
            # Check if container is actually running
            if container_info.get("State", {}).get("Status") != "running":
                return {"needs_restart": True, "reason": f"Container status: {container_info.get('State', {}).get('Status', 'unknown')}"}
            
            # Check container uptime - don't restart if just started (< 2 minutes)
            started_at = container_info.get("State", {}).get("StartedAt")
            if started_at:
                from datetime import datetime, timezone
                import dateutil.parser
                
                start_time = dateutil.parser.parse(started_at)
                now = datetime.now(timezone.utc)
                uptime_seconds = (now - start_time).total_seconds()
                
                if uptime_seconds < 120:  # Less than 2 minutes
                    return {"needs_restart": False, "reason": f"Container recently started ({uptime_seconds:.0f}s ago)"}
            
            # Try to perform a health check via HTTP if it's an API container
            if any(port in container_name for port in ["api_", "8001", "8002", "8003", "8004", "8005", "8006"]):
                health_check_result = await self._perform_http_health_check(container_name)
                if health_check_result["healthy"]:
                    return {"needs_restart": False, "reason": f"HTTP health check passed: {health_check_result['response']}"}
            
            # Check resource usage - don't restart if CPU/Memory are reasonable
            stats = await self.docker_manager.get_container_stats(container_name)
            if stats:
                cpu_percent = stats.get("cpu_percent", 0)
                memory_percent = stats.get("memory_percent", 0)
                
                # If resource usage is normal, container is likely healthy
                if cpu_percent < 95 and memory_percent < 95:
                    return {"needs_restart": False, "reason": f"Resource usage normal (CPU: {cpu_percent:.1f}%, RAM: {memory_percent:.1f}%)"}
            
            # If we get here, container appears genuinely unhealthy
            return {"needs_restart": True, "reason": "Container failed all health validation checks"}
            
        except Exception as e:
            self.logger.error(f"Container validation error for {container_name}: {e}")
            # On validation error, err on the side of caution - don't restart
            return {"needs_restart": False, "reason": f"Validation error: {str(e)}"}
    
    async def _perform_http_health_check(self, container_name: str) -> Dict[str, any]:
        """Perform HTTP health check on API containers"""
        try:
            # Map container names to internal ports
            port_mapping = {
                "vitruvyan_api_graph": "8004",
                "vitruvyan_api_semantic": "8001", 
                "vitruvyan_api_neural": "8002",
                "vitruvyan_api_sentiment": "8003",
                "vitruvyan_api_crewai": "8005",
                "vitruvyan_api_craft": "8006"
            }
            
            port = port_mapping.get(container_name)
            if not port:
                return {"healthy": False, "response": "No port mapping found"}
            
            import requests
            
            # Try health endpoint with timeout
            url = f"http://{container_name}:{port}/health"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {"healthy": True, "response": f"HTTP {response.status_code}"}
            else:
                return {"healthy": False, "response": f"HTTP {response.status_code}"}
                        
        except requests.Timeout:
            return {"healthy": False, "response": "Health check timeout"}
        except Exception as e:
            return {"healthy": False, "response": f"Health check error: {str(e)}"}

    async def _send_compliance_alert(self, state: Dict) -> Dict:
        """Send compliance alert email"""
        # Placeholder for email notification
        return {"type": "email", "status": "not_implemented"}
    
    async def _log_audit_completion(self, state: Dict):
        """Log audit completion to database"""
        if self.db_manager:
            try:
                await self.db_manager.log_audit_completion(state)
            except Exception as e:
                self.logger.error(f"Database logging failed: {e}")
    
    async def _save_learning_insights(self, audit_id: str, insights: Dict):
        """Save learning insights to database"""
        if self.db_manager:
            try:
                await self.db_manager.save_learning_insights(audit_id, insights)
            except Exception as e:
                self.logger.error(f"Learning insights save failed: {e}")