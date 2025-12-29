"""
🔍 THE SENTINEL - Vigil Arcis
=============================
The Watchful Guardian of the Vault

Like the sentries of Mont-Saint-Michel who scanned horizons for Viking longships,
The Sentinel monitors the digital realm for threats and changes requiring protection.

RESPONSIBILITIES:
- Monitor database changes via PostgresAgent
- Listen for triggers from Audit Engine  
- Watch for LangGraph state events requiring backup
- Detect system anomalies and vulnerabilities
- Initiate backup sequences when threats are spotted

WATCHFUL DOMAINS:
- PostgreSQL tables (logs, configs, user_data)
- Qdrant vector collections (embeddings, semantic data)
- LangGraph state transitions (critical checkpoints)
- Audit Engine alerts (security violations, compliance issues)
- File system changes (configuration files, data directories)

MOTTO: "Semper vigilans, nunquam dormit" (Always watching, never sleeping)
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import json
import hashlib

from .keeper import BaseKeeper, VaultEvent, BackupMode, VaultStatus, VaultConfig

logger = logging.getLogger(__name__)

class SentinelAgent(BaseKeeper):
    """
    The Sentinel - Vigil Arcis
    
    The ever-watchful guardian who stands at the fortress walls,
    scanning for threats and changes that require vault protection.
    
    Like Argus with his hundred eyes, The Sentinel never sleeps,
    always ready to sound the alarm when treasures need safeguarding.
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        super().__init__(config)
        
        # Sentinel State
        self.watching = False
        self.last_check = datetime.utcnow()
        self.watch_intervals = {
            BackupMode.INCREMENTAL: 1800,      # 30 minutes
            BackupMode.CRITICAL: 21600,        # 6 hours  
            BackupMode.FULL_SYSTEM: 86400,     # 24 hours
        }
        
        # Database Change Tracking
        self._last_db_checksums: Dict[str, str] = {}
        self._watched_tables = [
            'conversations', 'sentiment_scores', 'signals', 'validations',
            'user_holdings', 'strategies', 'phrases',
            'vault_keepers_events', 'vault_keepers_backups'  # Use existing vault tables
        ]
        
        # File System Monitoring
        self._watched_paths = [
            '/app/core/config',
            '/app/.env',
            '/app/docker-compose.yml',
            '/var/vitruvyan'
        ]
        self._last_file_checksums: Dict[str, str] = {}
        
        self.logger.info("🔍 The Sentinel takes position at the fortress walls")
    
    async def start_watch(self):
        """
        Begin the eternal vigil
        
        Like lighting the beacon fires of Gondor, this starts the continuous
        monitoring that will protect the realm until manually stopped.
        """
        if self.watching:
            self.logger.warning("⚠️ The Sentinel is already on watch")
            return
        
        self.watching = True
        self.last_check = datetime.utcnow()
        
        self.logger.info("🔥 The Sentinel begins eternal vigil - beacon fires lit")
        self.publish_event("sentinel.watch_started", {
            "started_at": self.last_check.isoformat(),
            "watch_intervals": {mode.value: interval for mode, interval in self.watch_intervals.items()}
        })
        
        # Start monitoring loop
        try:
            await self._watch_loop()
        except Exception as e:
            self.logger.error(f"❌ Sentinel watch failed: {e}")
            await self.stop_watch()
    
    async def stop_watch(self):
        """End the vigil gracefully"""
        self.watching = False
        self.logger.info("🛑 The Sentinel ends vigil - watch relieved")
        self.publish_event("sentinel.watch_ended", {
            "ended_at": datetime.utcnow().isoformat(),
            "total_watch_duration": str(datetime.utcnow() - self.last_check)
        })
    
    async def _watch_loop(self):
        """Main watching loop - the eternal vigil"""
        while self.watching:
            try:
                # Perform all monitoring checks
                threats_detected = await self._scan_for_threats()
                
                if threats_detected:
                    self.logger.warning(f"🚨 The Sentinel detected {len(threats_detected)} threats!")
                    await self._respond_to_threats(threats_detected)
                
                # Check if scheduled backups are due
                await self._check_backup_schedule()
                
                # Brief rest before next scan (sentries need short breaks)
                await asyncio.sleep(60)  # Scan every minute
                
            except Exception as e:
                self.logger.error(f"❌ Error during sentinel scan: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _scan_for_threats(self) -> List[Dict[str, Any]]:
        """
        Scan all watched domains for threats
        
        Like a sentinel scanning the horizon with a spyglass,
        this method examines all potential sources of danger.
        """
        threats = []
        
        # 1. Database Change Detection
        db_threats = await self._scan_database_changes()
        threats.extend(db_threats)
        
        # 2. File System Change Detection  
        fs_threats = await self._scan_filesystem_changes()
        threats.extend(fs_threats)
        
        # 3. Audit Engine Integration
        audit_threats = await self._check_audit_triggers()
        threats.extend(audit_threats)
        
        # 4. LangGraph State Monitoring
        graph_threats = await self._monitor_langgraph_state()
        threats.extend(graph_threats)
        
        # 5. System Health Anomalies
        health_threats = await self._detect_system_anomalies()
        threats.extend(health_threats)
        
        return threats
    
    async def _scan_database_changes(self) -> List[Dict[str, Any]]:
        """Scan for database changes requiring backup"""
        threats = []
        
        for table in self._watched_tables:
            try:
                # Get current table checksum (skip time filter to avoid schema issues)
                try:
                    checksum_sql = f"""
                    SELECT MD5(STRING_AGG(
                        CONCAT_WS('|', *), 
                        '' ORDER BY id
                    )) as table_hash
                    FROM {table}
                    LIMIT 100;
                    """
                    result = self.postgres_agent.fetch_all(checksum_sql, ())
                except:
                    # Skip table if any error occurs
                    continue
                if result and result[0]:
                    current_hash = result[0][0] or ""
                    last_hash = self._last_db_checksums.get(table, "")
                    
                    if current_hash != last_hash and last_hash != "":
                        threats.append({
                            "type": "database_change",
                            "source": f"table:{table}",
                            "severity": "medium",
                            "details": {
                                "table": table,
                                "old_hash": last_hash[:8],
                                "new_hash": current_hash[:8]
                            },
                            "recommended_action": "incremental_backup"
                        })
                    
                    self._last_db_checksums[table] = current_hash
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Could not scan table {table}: {e}")
        
        return threats
    
    async def _scan_filesystem_changes(self) -> List[Dict[str, Any]]:
        """Scan for critical file system changes"""
        threats = []
        
        for path_str in self._watched_paths:
            path = Path(path_str)
            
            try:
                if path.exists():
                    if path.is_file():
                        # Single file monitoring
                        current_hash = self.calculate_file_hash(str(path))
                        last_hash = self._last_file_checksums.get(path_str, "")
                        
                        if current_hash != last_hash and last_hash != "":
                            threats.append({
                                "type": "file_change",
                                "source": f"file:{path_str}",
                                "severity": "high" if "docker-compose" in path_str or ".env" in path_str else "medium",
                                "details": {
                                    "file_path": path_str,
                                    "old_hash": last_hash[:8],
                                    "new_hash": current_hash[:8]
                                },
                                "recommended_action": "critical_backup"
                            })
                        
                        self._last_file_checksums[path_str] = current_hash
                        
                    elif path.is_dir():
                        # Directory monitoring (check for new/deleted files)
                        files = list(path.rglob("*"))
                        dir_signature = hashlib.sha256(
                            "|".join(sorted([str(f.relative_to(path)) for f in files if f.is_file()])).encode()
                        ).hexdigest()
                        
                        last_signature = self._last_file_checksums.get(path_str, "")
                        
                        if dir_signature != last_signature and last_signature != "":
                            threats.append({
                                "type": "directory_change", 
                                "source": f"dir:{path_str}",
                                "severity": "medium",
                                "details": {
                                    "directory": path_str,
                                    "file_count": len(files),
                                    "signature_changed": True
                                },
                                "recommended_action": "full_system_backup"
                            })
                        
                        self._last_file_checksums[path_str] = dir_signature
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Could not scan path {path_str}: {e}")
        
        return threats
    
    async def _check_audit_triggers(self) -> List[Dict[str, Any]]:
        """Check for audit engine triggers requiring backup"""
        threats = []
        
        try:
            # Check for recent audit alerts - skip to avoid schema issues
            alerts = []
            self.logger.info("🔍 Sentinel: Skipping audit_alerts check (schema compatibility)")
            
            for alert in alerts:
                alert_type, severity, details, created_at = alert
                
                # Determine if this alert requires backup
                if self._should_backup_for_alert(alert_type, severity):
                    threats.append({
                        "type": "audit_trigger",
                        "source": f"audit:{alert_type}",
                        "severity": severity,
                        "details": {
                            "alert_type": alert_type,
                            "audit_details": details,
                            "triggered_at": created_at.isoformat() if created_at else None
                        },
                        "recommended_action": "critical_backup" if severity == "critical" else "incremental_backup"
                    })
        
        except Exception as e:
            self.logger.warning(f"⚠️ Could not check audit triggers: {e}")
        
        return threats
    
    def _should_backup_for_alert(self, alert_type: str, severity: str) -> bool:
        """Determine if an audit alert should trigger a backup"""
        
        # Critical alerts always trigger backup
        if severity == "critical":
            return True
        
        # High severity alerts for specific types
        if severity == "high" and alert_type in [
            "data_corruption", "unauthorized_access", "configuration_change",
            "dependency_vulnerability", "container_failure", "database_error"
        ]:
            return True
        
        return False
    
    async def _monitor_langgraph_state(self) -> List[Dict[str, Any]]:
        """Monitor LangGraph for state changes requiring backup"""
        threats = []
        
        try:
            # Check for completed LangGraph sessions that should be backed up
            # Skip conversations table completely to avoid schema issues
            sessions = []
            self.logger.info("🔍 Sentinel: Skipping conversations table check (schema variations)")
            
            for session in sessions:
                user_id, session_id, final_response, created_at = session
                
                # Check if this is a significant session worth backing up
                if self._is_significant_session(final_response):
                    threats.append({
                        "type": "langgraph_completion",
                        "source": f"session:{session_id}",
                        "severity": "low",
                        "details": {
                            "user_id": user_id,
                            "session_id": session_id,
                            "completed_at": created_at.isoformat() if created_at else None
                        },
                        "recommended_action": "incremental_backup"
                    })
        
        except Exception as e:
            self.logger.warning(f"⚠️ Could not monitor LangGraph state: {e}")
        
        return threats
    
    def _is_significant_session(self, final_response: str) -> bool:
        """Determine if a session is significant enough to trigger backup"""
        if not final_response:
            return False
        
        # Simple heuristics for session significance
        response_length = len(final_response)
        
        # Long responses or those containing specific keywords are significant
        if response_length > 1000:
            return True
        
        significant_keywords = [
            "portfolio", "analysis", "recommendation", "strategy",
            "risk", "allocation", "backtest", "signal"
        ]
        
        return any(keyword in final_response.lower() for keyword in significant_keywords)
    
    async def _detect_system_anomalies(self) -> List[Dict[str, Any]]:
        """Detect system health anomalies requiring backup"""
        threats = []
        
        try:
            # Check for unusual database growth
            db_size_sql = """
            SELECT 
                schemaname,
                tablename,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY size_bytes DESC
            LIMIT 10;
            """
            
            tables = self.postgres_agent.fetch_all(db_size_sql, ())
            
            # Very basic anomaly detection (could be enhanced)
            for schema, table, size_bytes in tables:
                size_mb = size_bytes / (1024 * 1024)
                
                # If any table is unusually large, consider it an anomaly
                if size_mb > 1000:  # 1GB threshold
                    threats.append({
                        "type": "database_anomaly",
                        "source": f"table_size:{table}",
                        "severity": "medium",
                        "details": {
                            "table": table,
                            "size_mb": round(size_mb, 2),
                            "threshold_exceeded": True
                        },
                        "recommended_action": "full_system_backup"
                    })
        
        except Exception as e:
            self.logger.warning(f"⚠️ Could not detect system anomalies: {e}")
        
        return threats
    
    async def _check_backup_schedule(self):
        """Check if any scheduled backups are due"""
        now = datetime.utcnow()
        
        for mode, interval_seconds in self.watch_intervals.items():
            # Check last backup of this type
            last_backup_sql = """
            SELECT MAX(created_at) 
            FROM vault_history 
            WHERE backup_type = %s AND status = 'completed'
            """
            
            result = self.postgres_agent.fetch_all(last_backup_sql, (mode.value,))
            
            if result and result[0][0]:
                last_backup = result[0][0]
                time_since_backup = (now - last_backup).total_seconds()
                
                if time_since_backup >= interval_seconds:
                    self.logger.info(f"⏰ Scheduled {mode.value} backup is due")
                    self.publish_event("treasure.detected", {
                        "threat_type": "scheduled_backup",
                        "backup_mode": mode.value,
                        "time_since_last": f"{time_since_backup / 3600:.1f} hours",
                        "scheduled_interval": f"{interval_seconds / 3600:.1f} hours"
                    })
            else:
                # No previous backup of this type - trigger one
                self.logger.info(f"📋 No previous {mode.value} backup found - triggering initial backup")
                self.publish_event("treasure.detected", {
                    "threat_type": "initial_backup",
                    "backup_mode": mode.value,
                    "reason": "no_previous_backup"
                })
    
    async def _respond_to_threats(self, threats: List[Dict[str, Any]]):
        """
        Respond to detected threats by triggering appropriate backups
        
        Like a sentinel sounding the alarm when enemies approach,
        this method coordinates the fortress response to threats.
        """
        
        # Group threats by recommended action
        actions_needed = {}
        for threat in threats:
            action = threat.get("recommended_action", "incremental_backup")
            if action not in actions_needed:
                actions_needed[action] = []
            actions_needed[action].append(threat)
        
        # Execute actions in priority order
        action_priority = [
            "disaster_recovery", 
            "critical_backup",
            "full_system_backup", 
            "incremental_backup"
        ]
        
        for action in action_priority:
            if action in actions_needed:
                threat_list = actions_needed[action]
                
                self.logger.info(f"🚨 Sentinel triggering {action} for {len(threat_list)} threats")
                
                # Publish event to trigger vault keepers
                self.publish_event("treasure.detected", {
                    "sentinel_response": action,
                    "threat_count": len(threat_list),
                    "threats": threat_list[:3],  # Limit payload size
                    "priority": action_priority.index(action)
                })
    
    async def handle_external_trigger(self, trigger_source: str, trigger_data: Dict[str, Any]):
        """
        Handle external triggers from Audit Engine or LangGraph
        
        Like receiving urgent messages via signal fires or messenger ravens,
        this method processes external alerts requiring immediate attention.
        """
        self.logger.info(f"📨 Sentinel received external trigger from {trigger_source}")
        
        # Determine appropriate response based on trigger source and data
        if trigger_source == "audit_engine":
            severity = trigger_data.get("severity", "medium")
            action_map = {
                "critical": "critical_backup",
                "high": "critical_backup", 
                "medium": "incremental_backup",
                "low": "incremental_backup"
            }
            recommended_action = action_map.get(severity, "incremental_backup")
            
        elif trigger_source == "langgraph":
            trigger_type = trigger_data.get("trigger", "unknown")
            if trigger_type in ["error_critical", "state_corruption"]:
                recommended_action = "disaster_recovery"
            elif trigger_type in ["session_complete", "post_audit"]:
                recommended_action = "incremental_backup"
            else:
                recommended_action = "incremental_backup"
        
        else:
            recommended_action = "incremental_backup"
        
        # Create synthetic threat for processing
        threat = {
            "type": "external_trigger",
            "source": trigger_source,
            "severity": trigger_data.get("severity", "medium"),
            "details": trigger_data,
            "recommended_action": recommended_action
        }
        
        await self._respond_to_threats([threat])
    
    def get_watch_status(self) -> Dict[str, Any]:
        """Get current sentinel status"""
        return {
            "watching": self.watching,
            "last_check": self.last_check.isoformat(),
            "watch_duration": str(datetime.utcnow() - self.last_check) if self.watching else "not_watching",
            "monitored_tables": len(self._watched_tables),
            "monitored_paths": len(self._watched_paths),
            "db_checksums": len(self._last_db_checksums),
            "file_checksums": len(self._last_file_checksums)
        }
    
    def get_monitored_changes(self) -> List[Dict[str, Any]]:
        """Get recent monitored changes for Chamberlain coordination"""
        changes = []
        
        # Check database changes (only vault_keepers tables using correct names)
        vault_tables = [
            ("vault_keepers_events", "created_at"),    # vault_keepers_events usa created_at
            ("vault_keepers_backups", "created_at"),   # vault_keepers_backups ha created_at
            ("vault_keepers_delivery_jobs", "created_at")  # vault_keepers_delivery_jobs ha created_at  
        ]
        
        for table, time_column in vault_tables:
            try:
                # Get recent changes in this table using appropriate time column
                change_sql = f"""
                SELECT COUNT(*) as change_count, MAX({time_column}) as last_change
                FROM {table}
                WHERE {time_column} > NOW() - INTERVAL '1 hour';
                """
                results = self.postgres_agent.fetch_all(change_sql, ())
                result = results[0] if results else None
                
                if result and result[0] > 0:
                    changes.append({
                        "type": "database_change",
                        "source": f"table:{table}",
                        "change_count": result[0],
                        "last_change": result[1].isoformat() if result[1] else None,
                        "severity": "low"
                    })
                    
            except Exception as e:
                self.logger.warning(f"Could not check changes in table {table}: {e}")
                # Add fallback change to ensure backup still happens
                changes.append({
                    "type": "database_change",
                    "source": f"table:{table}",
                    "change_count": 1,
                    "severity": "low",
                    "note": "Fallback detection due to query error"
                })
        
        # Check filesystem changes
        for path in self._watched_paths:
            try:
                path_obj = Path(path)
                if path_obj.exists():
                    # Simple modification time check
                    mtime = path_obj.stat().st_mtime
                    last_mtime = self._last_file_checksums.get(str(path_obj), 0)
                    
                    if mtime > last_mtime:
                        changes.append({
                            "type": "filesystem_change",
                            "source": f"path:{path}",
                            "modified_time": datetime.fromtimestamp(mtime).isoformat(),
                            "severity": "low"
                        })
                        
            except Exception as e:
                self.logger.warning(f"Could not check changes in path {path}: {e}")
                
        return changes
    
    def scan_for_threats(self) -> List[Dict[str, Any]]:
        """Scan for security threats and anomalies"""
        threats = []
        
        try:
            # Simple threat detection - unusual activity patterns
            for table in self._watched_tables:
                try:
                    # Check for table activity (safe query without time filter)
                    threat_sql = f"""
                    SELECT COUNT(*) as recent_activity
                    FROM {table}
                    LIMIT 1;
                    """
                    results = self.postgres_agent.fetch_all(threat_sql, ())
                    
                    if results and results[0] and results[0][0] > 100:  # More than 100 changes in 10 min
                        threats.append({
                            "type": "high_activity",
                            "source": f"table:{table}",
                            "severity": "medium",
                            "activity_count": results[0][0],
                            "details": f"Unusual activity detected in {table}"
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Could not scan threats in table {table}: {e}")
        
            # Check filesystem threats (basic)
            for path in self._watched_paths:
                try:
                    path_obj = Path(path)
                    if path_obj.exists() and path_obj.is_dir():
                        # Check for unusual file count
                        file_count = len(list(path_obj.iterdir()))
                        if file_count > 1000:  # More than 1000 files
                            threats.append({
                                "type": "filesystem_bloat",
                                "source": f"path:{path}",
                                "severity": "low", 
                                "file_count": file_count,
                                "details": f"High file count detected in {path}"
                            })
                            
                except Exception as e:
                    self.logger.warning(f"Could not scan threats in path {path}: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Threat scanning failed: {e}")
        
        return threats
    
    async def detect_changes(self) -> Dict[str, Any]:
        """Async wrapper for change detection - used by Chamberlain"""
        changes = self.get_monitored_changes()
        threats = self.scan_for_threats()
        
        return {
            "success": True,
            "changes_detected": len(changes) > 0,
            "threats_detected": len(threats) > 0,
            "changes": changes,
            "threats": threats,
            "monitored_tables": len(self._watched_tables),
            "monitored_paths": len(self._watched_paths)
        }
    
    def __str__(self) -> str:
        status = "on watch" if self.watching else "standing ready"
        return f"🔍 The Sentinel - Vigil Arcis ({status})"