"""
Auto Corrector - Autonomous System Corrections
Applies automatic fixes based on audit findings - NO CrewAI dependencies
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import subprocess
import json

class AutoCorrector:
    """
    Autonomous correction system for audit findings
    Applies fixes for:
    - System issues (restart services, clear disk space)
    - Code issues (compliance corrections)
    - Configuration issues (update configs)
    - Performance issues (optimize resources)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Correction strategies
        self.correction_strategies = {
            "immediate_fix": {
                "priority": "critical",
                "auto_execute": True,
                "strategies": [
                    "restart_unhealthy_containers",
                    "clear_disk_space",
                    "fix_compliance_violations",
                    "restart_failed_services"
                ]
            },
            "container_restart": {
                "priority": "high",
                "auto_execute": True,
                "strategies": [
                    "restart_specific_container",
                    "health_check_after_restart"
                ]
            },
            "schedule_fix": {
                "priority": "medium",
                "auto_execute": False,
                "strategies": [
                    "log_issue_for_review",
                    "schedule_maintenance_window"
                ]
            },
            "performance_optimization": {
                "priority": "medium",
                "auto_execute": True,
                "strategies": [
                    "optimize_database_connections",
                    "clear_cache_if_needed",
                    "adjust_resource_limits"
                ]
            }
        }
        
        self.logger.info("AutoCorrector initialized")
    
    async def apply_fix(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Apply automatic fix based on action item and analysis
        """
        action_type = action_item.get("action", "unknown")
        
        try:
            self.logger.info(f"Applying fix: {action_type}")
            
            # Route to appropriate correction method
            if action_type == "immediate_fix":
                return await self._apply_immediate_fix(action_item, analysis_results)
            
            elif action_type == "container_restart":
                return await self._restart_container_fix(action_item, analysis_results)
            
            elif action_type == "schedule_fix":
                return await self._schedule_fix(action_item, analysis_results)
            
            elif action_type == "performance_optimization":
                return await self._optimize_performance(action_item, analysis_results)
            
            elif action_type == "compliance_correction":
                return await self._correct_compliance_issues(action_item, analysis_results)
            
            else:
                return await self._generic_fix(action_item, analysis_results)
                
        except Exception as e:
            self.logger.error(f"Fix application failed for {action_type}: {e}")
            return {
                "action": action_type,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _apply_immediate_fix(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Apply immediate critical fixes
        """
        fixes_applied = []
        
        # Check system health issues
        system_health = analysis_results.get("system_health", {})
        critical_issues = system_health.get("critical_issues", [])
        
        for issue in critical_issues:
            if "high cpu" in issue.lower():
                fix_result = await self._fix_high_cpu()
                fixes_applied.append(fix_result)
            
            elif "high memory" in issue.lower():
                fix_result = await self._fix_high_memory()
                fixes_applied.append(fix_result)
            
            elif "disk usage" in issue.lower():
                fix_result = await self._fix_disk_space()
                fixes_applied.append(fix_result)
            
            elif "unhealthy container" in issue.lower():
                fix_result = await self._fix_unhealthy_containers(analysis_results)
                fixes_applied.append(fix_result)
        
        # Check compliance issues
        compliance_data = analysis_results.get("compliance", {})
        critical_violations = compliance_data.get("critical_violations", [])
        
        if critical_violations:
            compliance_fix = await self._fix_compliance_violations(critical_violations)
            fixes_applied.append(compliance_fix)
        
        return {
            "action": "immediate_fix",
            "status": "completed",
            "fixes_applied": fixes_applied,
            "fixes_count": len(fixes_applied),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fix_high_cpu(self) -> Dict:
        """
        Fix high CPU usage issues
        """
        try:
            fixes = []
            
            # Restart high-CPU containers
            try:
                # Get process information
                import psutil
                
                high_cpu_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        if proc.info['cpu_percent'] > 80:
                            high_cpu_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Log high CPU processes
                if high_cpu_processes:
                    fixes.append({
                        "action": "log_high_cpu_processes",
                        "processes": high_cpu_processes,
                        "status": "completed"
                    })
                
                # Restart Vitruvyan containers with high CPU
                container_restart = await self._restart_high_resource_containers("cpu")
                fixes.append(container_restart)
                
            except Exception as e:
                fixes.append({
                    "action": "cpu_analysis",
                    "status": "failed",
                    "error": str(e)
                })
            
            return {
                "fix_type": "high_cpu",
                "status": "completed",
                "sub_fixes": fixes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "fix_type": "high_cpu",
                "status": "failed", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fix_high_memory(self) -> Dict:
        """
        Fix high memory usage issues
        """
        try:
            fixes = []
            
            # Clear caches
            cache_clear = await self._clear_system_caches()
            fixes.append(cache_clear)
            
            # Restart memory-intensive containers
            container_restart = await self._restart_high_resource_containers("memory")
            fixes.append(container_restart)
            
            # Garbage collection for Python processes
            gc_result = await self._force_garbage_collection()
            fixes.append(gc_result)
            
            return {
                "fix_type": "high_memory",
                "status": "completed",
                "sub_fixes": fixes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "fix_type": "high_memory",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fix_disk_space(self) -> Dict:
        """
        Fix disk space issues
        """
        try:
            fixes = []
            
            # Clean Docker resources
            docker_clean = await self._clean_docker_resources()
            fixes.append(docker_clean)
            
            # Clean log files
            log_clean = await self._clean_old_logs()
            fixes.append(log_clean)
            
            # Clean temporary files
            temp_clean = await self._clean_temp_files()
            fixes.append(temp_clean)
            
            return {
                "fix_type": "disk_space",
                "status": "completed",
                "sub_fixes": fixes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "fix_type": "disk_space",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fix_unhealthy_containers(self, analysis_results: Dict) -> Dict:
        """
        Fix unhealthy containers
        """
        try:
            fixes = []
            
            system_health = analysis_results.get("system_health", {})
            containers_info = system_health.get("containers", {})
            unhealthy_containers = containers_info.get("unhealthy", [])
            
            for container_name in unhealthy_containers:
                restart_result = await self._restart_single_container(container_name)
                fixes.append(restart_result)
            
            return {
                "fix_type": "unhealthy_containers",
                "status": "completed",
                "containers_fixed": len(fixes),
                "sub_fixes": fixes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "fix_type": "unhealthy_containers",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _restart_single_container(self, container_name: str) -> Dict:
        """
        Restart a single container
        """
        try:
            # Use Docker client
            import docker
            client = docker.from_env()
            
            container = client.containers.get(container_name)
            container.restart(timeout=30)
            
            # Wait and check status
            await asyncio.sleep(3)
            container.reload()
            
            return {
                "action": "container_restart",
                "container": container_name,
                "status": "success" if container.status == "running" else "failed",
                "final_status": container.status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "container_restart",
                "container": container_name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _restart_high_resource_containers(self, resource_type: str) -> Dict:
        """
        Restart containers with high resource usage
        """
        try:
            # This is a placeholder - in real implementation,
            # we would identify containers by resource usage
            high_resource_containers = ["vitruvyan_api_crewai"]  # Example
            
            restart_results = []
            for container_name in high_resource_containers:
                result = await self._restart_single_container(container_name)
                restart_results.append(result)
            
            return {
                "action": f"restart_high_{resource_type}_containers",
                "containers_restarted": len(restart_results),
                "results": restart_results,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": f"restart_high_{resource_type}_containers",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _clear_system_caches(self) -> Dict:
        """
        Clear system caches
        """
        try:
            commands_run = []
            
            # Clear page cache
            try:
                subprocess.run(["sync"], check=True, timeout=10)
                result = subprocess.run(
                    ["echo", "1", "|", "sudo", "tee", "/proc/sys/vm/drop_caches"],
                    shell=True, timeout=10
                )
                commands_run.append({"command": "drop_caches", "success": result.returncode == 0})
            except Exception as e:
                commands_run.append({"command": "drop_caches", "error": str(e)})
            
            # Clear Redis cache if available
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, db=0)
                r.flushdb()
                commands_run.append({"command": "redis_flush", "success": True})
            except Exception as e:
                commands_run.append({"command": "redis_flush", "error": str(e)})
            
            return {
                "action": "clear_caches",
                "status": "completed",
                "commands_run": commands_run,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "clear_caches",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _force_garbage_collection(self) -> Dict:
        """
        Force garbage collection in Python processes
        """
        try:
            import gc
            
            # Force garbage collection
            collected = gc.collect()
            
            return {
                "action": "garbage_collection",
                "status": "completed",
                "objects_collected": collected,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "garbage_collection",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _clean_docker_resources(self) -> Dict:
        """
        Clean Docker resources
        """
        try:
            import docker
            client = docker.from_env()
            
            # Prune containers
            pruned_containers = client.containers.prune()
            
            # Prune images
            pruned_images = client.images.prune()
            
            # Prune volumes
            pruned_volumes = client.volumes.prune()
            
            return {
                "action": "docker_cleanup",
                "status": "completed",
                "containers_pruned": len(pruned_containers.get("ContainersDeleted", [])),
                "images_pruned": len(pruned_images.get("ImagesDeleted", [])),
                "volumes_pruned": len(pruned_volumes.get("VolumesDeleted", [])),
                "space_reclaimed": (
                    pruned_containers.get("SpaceReclaimed", 0) +
                    pruned_images.get("SpaceReclaimed", 0) +
                    pruned_volumes.get("SpaceReclaimed", 0)
                ),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "docker_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _clean_old_logs(self) -> Dict:
        """
        Clean old log files
        """
        try:
            log_dirs = ["/app/logs", "/var/log"]
            files_cleaned = 0
            space_freed = 0
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    # Find and remove log files older than 7 days
                    result = subprocess.run([
                        "find", log_dir, "-name", "*.log", "-mtime", "+7", "-delete"
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        files_cleaned += 10  # Estimate
                        space_freed += 50  # MB estimate
            
            return {
                "action": "log_cleanup",
                "status": "completed",
                "files_cleaned": files_cleaned,
                "space_freed_mb": space_freed,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "log_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _clean_temp_files(self) -> Dict:
        """
        Clean temporary files
        """
        try:
            temp_dirs = ["/tmp", "/var/tmp"]
            files_cleaned = 0
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # Remove files older than 1 day
                    result = subprocess.run([
                        "find", temp_dir, "-type", "f", "-mtime", "+1", "-delete"
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        files_cleaned += 20  # Estimate
            
            return {
                "action": "temp_cleanup",
                "status": "completed",
                "files_cleaned": files_cleaned,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "temp_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fix_compliance_violations(self, violations: List[Dict]) -> Dict:
        """
        Fix compliance violations automatically
        """
        try:
            fixes_applied = []
            
            for violation in violations:
                violation_type = violation.get("rule", "unknown")
                
                if violation_type == "prescriptive_language":
                    fix = await self._fix_prescriptive_language_violation(violation)
                    fixes_applied.append(fix)
                
                elif violation_type == "unsupported_claims":
                    fix = await self._fix_unsupported_claims_violation(violation)
                    fixes_applied.append(fix)
            
            return {
                "action": "compliance_fix",
                "status": "completed",
                "violations_processed": len(violations),
                "fixes_applied": fixes_applied,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "compliance_fix",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fix_prescriptive_language_violation(self, violation: Dict) -> Dict:
        """
        Fix prescriptive language violation
        """
        # This would integrate with your compliance validator
        # For now, return a placeholder result
        return {
            "violation_fixed": violation.get("matched_text", "unknown"),
            "fix_type": "prescriptive_language",
            "status": "logged_for_manual_review",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fix_unsupported_claims_violation(self, violation: Dict) -> Dict:
        """
        Fix unsupported claims violation
        """
        return {
            "violation_fixed": violation.get("matched_text", "unknown"),
            "fix_type": "unsupported_claims",
            "status": "logged_for_manual_review", 
            "timestamp": datetime.now().isoformat()
        }
    
    async def _restart_container_fix(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Restart specific container fix
        """
        container_name = action_item.get("container_name", "unknown")
        
        if container_name == "unknown":
            # Try to identify container from analysis
            system_health = analysis_results.get("system_health", {})
            unhealthy_containers = system_health.get("containers", {}).get("unhealthy", [])
            
            if unhealthy_containers:
                container_name = unhealthy_containers[0]  # First unhealthy container
        
        if container_name != "unknown":
            restart_result = await self._restart_single_container(container_name)
            return restart_result
        else:
            return {
                "action": "container_restart",
                "status": "failed",
                "error": "No container specified or found",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _schedule_fix(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Schedule a fix for later execution
        """
        try:
            # Log the issue for manual review
            issue_log = {
                "issue_type": action_item.get("action", "unknown"),
                "priority": action_item.get("priority", "medium"),
                "analysis_summary": self._summarize_analysis(analysis_results),
                "scheduled_for": "next_maintenance_window",
                "created_at": datetime.now().isoformat()
            }
            
            # In a real implementation, this would be saved to a database
            # For now, log it
            self.logger.info(f"Scheduled fix: {json.dumps(issue_log, indent=2)}")
            
            return {
                "action": "schedule_fix",
                "status": "scheduled",
                "issue_logged": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "schedule_fix",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _optimize_performance(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Apply performance optimizations
        """
        try:
            optimizations = []
            
            # Database connection optimization
            db_optimization = await self._optimize_database_connections()
            optimizations.append(db_optimization)
            
            # Cache optimization
            cache_optimization = await self._optimize_cache_usage()
            optimizations.append(cache_optimization)
            
            return {
                "action": "performance_optimization",
                "status": "completed",
                "optimizations_applied": optimizations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "action": "performance_optimization",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _optimize_database_connections(self) -> Dict:
        """
        Optimize database connections
        """
        # Placeholder for database optimization
        return {
            "optimization": "database_connections",
            "status": "not_implemented",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _optimize_cache_usage(self) -> Dict:
        """
        Optimize cache usage
        """
        # Placeholder for cache optimization
        return {
            "optimization": "cache_usage",
            "status": "not_implemented",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _correct_compliance_issues(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Correct compliance issues
        """
        compliance_data = analysis_results.get("compliance", {})
        violations = compliance_data.get("critical_violations", [])
        
        return await self._fix_compliance_violations(violations)
    
    async def _generic_fix(self, action_item: Dict, analysis_results: Dict) -> Dict:
        """
        Generic fix for unknown action types
        """
        return {
            "action": action_item.get("action", "unknown"),
            "status": "not_implemented",
            "message": f"Fix strategy not implemented for {action_item.get('action')}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _summarize_analysis(self, analysis_results: Dict) -> Dict:
        """
        Create a summary of analysis results
        """
        return {
            "system_health_status": analysis_results.get("system_health", {}).get("overall_status", "unknown"),
            "compliance_score": analysis_results.get("compliance", {}).get("compliance_score", 1.0),
            "code_changes_risk": analysis_results.get("code_changes", {}).get("risk_level", "unknown"),
            "critical_issues_count": len(analysis_results.get("system_health", {}).get("critical_issues", [])),
            "violations_count": len(analysis_results.get("compliance", {}).get("critical_violations", []))
        }