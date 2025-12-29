#!/usr/bin/env python3
"""
Vitruvyan Codex Hunters - Expedition Planner Agent
==================================================

The Expedition Planner is a strategic scheduling agent within the Codex Hunters medieval 
data intelligence system. It replaces static cron jobs with intelligent, adaptive planning
based on:

- Database load patterns and performance metrics
- Historical inconsistency patterns and trends  
- System resource availability and constraints
- Priority-based expedition scheduling

This agent analyzes past expedition results, current database states, and system metrics
to optimize when and how healing expeditions should be triggered, ensuring maximum
efficiency and minimal system impact.

Author: Vitruvyan Development Team
Created: 2025-01-14
Phase: 3.3 - Strategic Planning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import statistics

from .base_hunter import BaseHunter, CodexEvent
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent


class ExpeditionPriority(Enum):
    """Priority levels for scheduled expeditions"""
    CRITICAL = 1    # Immediate execution required
    HIGH = 2        # Execute within 1 hour
    MEDIUM = 3      # Execute within 6 hours
    LOW = 4         # Execute within 24 hours
    MAINTENANCE = 5 # Execute during low-traffic periods


class ResourceType(Enum):
    """System resource types for monitoring"""
    CPU = "cpu_usage"
    MEMORY = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK = "network_load"
    DATABASE = "database_connections"


@dataclass
class ExpeditionSchedule:
    """Represents a scheduled expedition with all planning details"""
    expedition_id: str
    target_collection: str
    priority: ExpeditionPriority
    scheduled_time: datetime
    estimated_duration: int  # minutes
    resource_requirements: Dict[ResourceType, float]
    inconsistency_severity: float
    dependencies: List[str]  # Other expedition IDs this depends on
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SystemMetrics:
    """Current system performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_load: float
    database_connections: int
    active_expeditions: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class PerformancePattern:
    """Historical performance patterns for optimization"""
    hour_of_day: int
    day_of_week: int
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_response_time: float
    expedition_success_rate: float
    optimal_for_expeditions: bool


class ExpeditionPlanner(BaseHunter):
    """
    Expedition Planner Agent - Strategic Scheduling for Codex Hunters
    
    The Planner analyzes system performance, database load patterns, and historical
    expedition data to create optimal scheduling strategies for healing expeditions.
    It replaces static cron jobs with intelligent, adaptive planning that maximizes
    efficiency while minimizing system impact.
    """
    
    def __init__(self, postgres_agent: PostgresAgent, qdrant_agent: QdrantAgent):
        super().__init__()
        self.postgres_agent = postgres_agent
        self.qdrant_agent = qdrant_agent
        self.active_schedules: Dict[str, ExpeditionSchedule] = {}
        self.performance_history: List[SystemMetrics] = []
        self.performance_patterns: Dict[Tuple[int, int], PerformancePattern] = {}
        self.logger = logging.getLogger(__name__)
        
        # Planning configuration
        self.max_concurrent_expeditions = 3
        self.performance_window_hours = 24
        self.pattern_analysis_days = 30
        self.resource_thresholds = {
            ResourceType.CPU: 80.0,
            ResourceType.MEMORY: 85.0,
            ResourceType.DISK_IO: 70.0,
            ResourceType.NETWORK: 60.0,
            ResourceType.DATABASE: 90
        }
    
    async def activate(self) -> None:
        """Activate the Expedition Planner and begin strategic planning"""
        self.logger.info("🗓️ Expedition Planner activating - Strategic scheduling initiated")
        
        try:
            await self._load_historical_data()
            await self._analyze_performance_patterns()
            await self._initialize_scheduling_engine()
            
            # Emit activation event
            await self.emit_event(CodexEvent(
                event_type="planning.planner_activated",
                source="expedition_planner",
                data={
                    "timestamp": datetime.utcnow().isoformat(),
                    "performance_patterns_loaded": len(self.performance_patterns),
                    "active_schedules": len(self.active_schedules),
                    "status": "strategic_planning_active"
                }
            ))
            
            self.logger.info(f"✅ Planner activated with {len(self.performance_patterns)} patterns")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to activate Expedition Planner: {str(e)}")
            raise
    
    async def plan_expedition(self, collection: str, inconsistency_data: Dict[str, Any], 
                            priority: ExpeditionPriority = ExpeditionPriority.MEDIUM) -> ExpeditionSchedule:
        """
        Plan a new expedition with optimal scheduling
        
        Args:
            collection: Target collection for the expedition
            inconsistency_data: Data about detected inconsistencies
            priority: Priority level for the expedition
            
        Returns:
            ExpeditionSchedule: Planned expedition with optimal timing
        """
        self.logger.info(f"📋 Planning expedition for collection: {collection}")
        
        try:
            # Analyze inconsistency severity
            severity = self._calculate_inconsistency_severity(inconsistency_data)
            
            # Estimate resource requirements
            resource_reqs = await self._estimate_resource_requirements(collection, inconsistency_data)
            
            # Find optimal scheduling time
            optimal_time = await self._find_optimal_schedule_time(priority, resource_reqs)
            
            # Estimate duration based on historical data
            estimated_duration = await self._estimate_expedition_duration(collection, inconsistency_data)
            
            # Create expedition schedule
            expedition_schedule = ExpeditionSchedule(
                expedition_id=f"exp_{collection}_{int(time.time())}",
                target_collection=collection,
                priority=priority,
                scheduled_time=optimal_time,
                estimated_duration=estimated_duration,
                resource_requirements=resource_reqs,
                inconsistency_severity=severity,
                dependencies=[]
            )
            
            # Add to active schedules
            self.active_schedules[expedition_schedule.expedition_id] = expedition_schedule
            
            # Log to database
            await self._log_planned_expedition(expedition_schedule)
            
            # Emit planning event
            await self.emit_event(CodexEvent(
                event_type="planning.expedition_planned",
                source="expedition_planner",
                data={
                    "expedition_id": expedition_schedule.expedition_id,
                    "collection": collection,
                    "priority": priority.name,
                    "scheduled_time": optimal_time.isoformat(),
                    "severity": severity,
                    "estimated_duration": estimated_duration
                }
            ))
            
            self.logger.info(f"✅ Expedition planned - ID: {expedition_schedule.expedition_id}, "
                           f"Time: {optimal_time}, Duration: {estimated_duration}min")
            
            return expedition_schedule
            
        except Exception as e:
            self.logger.error(f"❌ Failed to plan expedition for {collection}: {str(e)}")
            raise
    
    async def get_next_expeditions(self, limit: int = 10) -> List[ExpeditionSchedule]:
        """Get the next expeditions to execute based on priority and timing"""
        current_time = datetime.utcnow()
        
        # Filter ready expeditions
        ready_expeditions = [
            schedule for schedule in self.active_schedules.values()
            if schedule.scheduled_time <= current_time
        ]
        
        # Sort by priority and scheduled time
        ready_expeditions.sort(key=lambda x: (x.priority.value, x.scheduled_time))
        
        return ready_expeditions[:limit]
    
    async def update_system_metrics(self, metrics: SystemMetrics) -> None:
        """Update current system performance metrics"""
        self.performance_history.append(metrics)
        
        # Maintain rolling window
        cutoff_time = datetime.utcnow() - timedelta(hours=self.performance_window_hours)
        self.performance_history = [
            m for m in self.performance_history if m.timestamp >= cutoff_time
        ]
        
        # Check if we need to reschedule based on resource constraints
        await self._check_resource_constraints(metrics)
    
    async def complete_expedition(self, expedition_id: str, success: bool, 
                                duration_minutes: int, metrics: Dict[str, Any]) -> None:
        """Mark an expedition as completed and update performance data"""
        if expedition_id not in self.active_schedules:
            self.logger.warning(f"⚠️ Unknown expedition completed: {expedition_id}")
            return
        
        schedule = self.active_schedules[expedition_id]
        
        # Log completion
        await self._log_expedition_completion(schedule, success, duration_minutes, metrics)
        
        # Update performance patterns
        await self._update_performance_patterns(schedule, success, duration_minutes)
        
        # Remove from active schedules
        del self.active_schedules[expedition_id]
        
        # Emit completion event
        await self.emit_event(CodexEvent(
            event_type="planning.expedition_completed",
            source="expedition_planner",
            data={
                "expedition_id": expedition_id,
                "success": success,
                "duration_minutes": duration_minutes,
                "collection": schedule.target_collection
            }
        ))
        
        self.logger.info(f"✅ Expedition {expedition_id} completed - Success: {success}")
    
    async def get_scheduling_recommendations(self) -> Dict[str, Any]:
        """Get current scheduling recommendations and system status"""
        current_time = datetime.utcnow()
        
        # Analyze current load
        current_metrics = self.performance_history[-1] if self.performance_history else None
        
        # Get performance patterns for current time
        current_pattern = self.performance_patterns.get(
            (current_time.hour, current_time.weekday()), None
        )
        
        # Count expeditions by priority
        priority_counts = {}
        for priority in ExpeditionPriority:
            priority_counts[priority.name] = sum(
                1 for s in self.active_schedules.values() if s.priority == priority
            )
        
        return {
            "current_time": current_time.isoformat(),
            "active_schedules": len(self.active_schedules),
            "ready_expeditions": len(await self.get_next_expeditions()),
            "system_load": {
                "cpu": current_metrics.cpu_usage if current_metrics else None,
                "memory": current_metrics.memory_usage if current_metrics else None,
                "database": current_metrics.database_connections if current_metrics else None
            },
            "current_pattern": {
                "optimal_for_expeditions": current_pattern.optimal_for_expeditions if current_pattern else None,
                "expected_success_rate": current_pattern.expedition_success_rate if current_pattern else None
            },
            "priority_distribution": priority_counts,
            "performance_patterns": len(self.performance_patterns)
        }
    
    # Private methods
    
    async def _load_historical_data(self) -> None:
        """Load historical expedition and performance data"""
        try:
            # Load recent system metrics
            query = """
            SELECT 
                created_at,
                cpu_usage,
                memory_usage,
                disk_io,
                network_load,
                database_connections,
                active_expeditions
            FROM system_metrics 
            WHERE created_at >= %s 
            ORDER BY created_at DESC
            LIMIT 1000
            """
            
            cutoff_date = datetime.utcnow() - timedelta(days=self.pattern_analysis_days)
            
            # Note: This assumes system_metrics table exists - in real implementation
            # we would create this table or use existing logging infrastructure
            self.logger.info("📊 Historical data loading would query system_metrics table")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load historical data: {str(e)}")
    
    async def _analyze_performance_patterns(self) -> None:
        """Analyze historical performance to identify optimal scheduling patterns"""
        if not self.performance_history:
            self.logger.info("📈 No performance history - using default patterns")
            self._create_default_patterns()
            return
        
        # Group metrics by hour and day of week
        pattern_data = {}
        
        for metrics in self.performance_history:
            hour = metrics.timestamp.hour
            day = metrics.timestamp.weekday()
            key = (hour, day)
            
            if key not in pattern_data:
                pattern_data[key] = []
            
            pattern_data[key].append({
                'cpu': metrics.cpu_usage,
                'memory': metrics.memory_usage,
                'network': metrics.network_load,
                'db_connections': metrics.database_connections
            })
        
        # Create performance patterns
        for (hour, day), data_points in pattern_data.items():
            if len(data_points) < 3:  # Need minimum data points
                continue
            
            avg_cpu = statistics.mean([d['cpu'] for d in data_points])
            avg_memory = statistics.mean([d['memory'] for d in data_points])
            avg_network = statistics.mean([d['network'] for d in data_points])
            
            # Determine if this time slot is optimal for expeditions
            optimal = (avg_cpu < 70 and avg_memory < 80 and avg_network < 50)
            
            pattern = PerformancePattern(
                hour_of_day=hour,
                day_of_week=day,
                avg_cpu_usage=avg_cpu,
                avg_memory_usage=avg_memory,
                avg_response_time=100.0,  # Default value
                expedition_success_rate=0.95 if optimal else 0.85,
                optimal_for_expeditions=optimal
            )
            
            self.performance_patterns[(hour, day)] = pattern
        
        self.logger.info(f"📈 Analyzed {len(self.performance_patterns)} performance patterns")
    
    def _create_default_patterns(self) -> None:
        """Create default performance patterns for initial operation"""
        # Create patterns for each hour/day combination
        for hour in range(24):
            for day in range(7):
                # Assume lower load during night hours and weekends
                is_night = hour < 6 or hour > 22
                is_weekend = day in [5, 6]  # Saturday, Sunday
                
                optimal = is_night or is_weekend
                
                pattern = PerformancePattern(
                    hour_of_day=hour,
                    day_of_week=day,
                    avg_cpu_usage=40.0 if optimal else 70.0,
                    avg_memory_usage=50.0 if optimal else 80.0,
                    avg_response_time=80.0 if optimal else 150.0,
                    expedition_success_rate=0.95 if optimal else 0.85,
                    optimal_for_expeditions=optimal
                )
                
                self.performance_patterns[(hour, day)] = pattern
    
    async def _initialize_scheduling_engine(self) -> None:
        """Initialize the scheduling engine with current system state"""
        self.logger.info("⚙️ Initializing scheduling engine")
        
        # Clear any expired schedules
        current_time = datetime.utcnow()
        expired_schedules = [
            exp_id for exp_id, schedule in self.active_schedules.items()
            if (current_time - schedule.created_at).days > 7  # Remove week-old schedules
        ]
        
        for exp_id in expired_schedules:
            del self.active_schedules[exp_id]
        
        self.logger.info(f"🗑️ Cleaned {len(expired_schedules)} expired schedules")
    
    def _calculate_inconsistency_severity(self, inconsistency_data: Dict[str, Any]) -> float:
        """Calculate severity score for inconsistency data"""
        # Extract key metrics
        missing_records = inconsistency_data.get('missing_records', 0)
        extra_records = inconsistency_data.get('extra_records', 0)
        total_records = inconsistency_data.get('total_records', 1)
        
        # Calculate severity as percentage of inconsistent records
        inconsistent_count = missing_records + extra_records
        severity = min(100.0, (inconsistent_count / total_records) * 100)
        
        return severity
    
    async def _estimate_resource_requirements(self, collection: str, 
                                           inconsistency_data: Dict[str, Any]) -> Dict[ResourceType, float]:
        """Estimate resource requirements for an expedition"""
        # Base requirements
        base_reqs = {
            ResourceType.CPU: 20.0,
            ResourceType.MEMORY: 15.0,
            ResourceType.DISK_IO: 30.0,
            ResourceType.NETWORK: 10.0,
            ResourceType.DATABASE: 5
        }
        
        # Scale based on inconsistency count
        missing_records = inconsistency_data.get('missing_records', 0)
        scale_factor = min(3.0, 1.0 + (missing_records / 1000.0))
        
        return {
            resource_type: base_value * scale_factor
            for resource_type, base_value in base_reqs.items()
        }
    
    async def _find_optimal_schedule_time(self, priority: ExpeditionPriority, 
                                        resource_reqs: Dict[ResourceType, float]) -> datetime:
        """Find the optimal time to schedule an expedition"""
        current_time = datetime.utcnow()
        
        # For critical priority, schedule immediately
        if priority == ExpeditionPriority.CRITICAL:
            return current_time
        
        # For high priority, schedule within 1 hour
        if priority == ExpeditionPriority.HIGH:
            return current_time + timedelta(minutes=15)
        
        # For other priorities, find optimal time slot
        optimal_time = current_time + timedelta(hours=1)
        
        # Look ahead for optimal time slots
        for hours_ahead in range(1, 25):  # Look up to 24 hours ahead
            check_time = current_time + timedelta(hours=hours_ahead)
            pattern = self.performance_patterns.get(
                (check_time.hour, check_time.weekday()), None
            )
            
            if pattern and pattern.optimal_for_expeditions:
                optimal_time = check_time
                break
        
        return optimal_time
    
    async def _estimate_expedition_duration(self, collection: str, 
                                         inconsistency_data: Dict[str, Any]) -> int:
        """Estimate expedition duration in minutes"""
        # Base duration
        base_duration = 15  # minutes
        
        # Scale based on missing records
        missing_records = inconsistency_data.get('missing_records', 0)
        
        if missing_records < 100:
            return base_duration
        elif missing_records < 1000:
            return base_duration * 2
        elif missing_records < 10000:
            return base_duration * 4
        else:
            return base_duration * 8
    
    async def _check_resource_constraints(self, metrics: SystemMetrics) -> None:
        """Check if current metrics require schedule adjustments"""
        # Check if any resources are over threshold
        over_threshold = []
        
        if metrics.cpu_usage > self.resource_thresholds[ResourceType.CPU]:
            over_threshold.append(ResourceType.CPU)
        
        if metrics.memory_usage > self.resource_thresholds[ResourceType.MEMORY]:
            over_threshold.append(ResourceType.MEMORY)
        
        if metrics.database_connections > self.resource_thresholds[ResourceType.DATABASE]:
            over_threshold.append(ResourceType.DATABASE)
        
        if over_threshold:
            await self._postpone_low_priority_expeditions(over_threshold)
    
    async def _postpone_low_priority_expeditions(self, constrained_resources: List[ResourceType]) -> None:
        """Postpone low priority expeditions due to resource constraints"""
        current_time = datetime.utcnow()
        postponed_count = 0
        
        for exp_id, schedule in list(self.active_schedules.items()):
            # Only postpone low and medium priority expeditions
            if schedule.priority in [ExpeditionPriority.LOW, ExpeditionPriority.MEDIUM]:
                # Check if expedition requires constrained resources
                requires_constrained = any(
                    schedule.resource_requirements.get(resource, 0) > 10
                    for resource in constrained_resources
                )
                
                if requires_constrained and schedule.scheduled_time <= current_time + timedelta(hours=1):
                    # Postpone by 2 hours
                    schedule.scheduled_time += timedelta(hours=2)
                    postponed_count += 1
        
        if postponed_count > 0:
            self.logger.info(f"⏰ Postponed {postponed_count} expeditions due to resource constraints")
    
    async def _log_planned_expedition(self, schedule: ExpeditionSchedule) -> None:
        """Log planned expedition to database"""
        try:
            # Create log_agent table if not exists and insert record
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS log_agent (
                        id SERIAL PRIMARY KEY,
                        agent_name TEXT,
                        action TEXT,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        collection_name TEXT
                    )
                """)
                
                details = {
                    "expedition_id": schedule.expedition_id,
                    "priority": schedule.priority.name,
                    "scheduled_time": schedule.scheduled_time.isoformat(),
                    "estimated_duration": schedule.estimated_duration,
                    "inconsistency_severity": schedule.inconsistency_severity
                }
                
                cur.execute("""
                    INSERT INTO log_agent (agent_name, action, details, timestamp, collection_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("expedition_planner", "expedition_planned", json.dumps(details), 
                     datetime.utcnow(), schedule.target_collection))
            
            self.postgres_agent.connection.commit()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not log planned expedition: {str(e)}")
    
    async def _log_expedition_completion(self, schedule: ExpeditionSchedule, success: bool,
                                       duration_minutes: int, metrics: Dict[str, Any]) -> None:
        """Log expedition completion to database"""
        try:
            with self.postgres_agent.connection.cursor() as cur:
                # Ensure log_agent table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS log_agent (
                        id SERIAL PRIMARY KEY,
                        agent_name TEXT,
                        action TEXT,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        collection_name TEXT
                    )
                """)
                
                details = {
                    "expedition_id": schedule.expedition_id,
                    "success": success,
                    "planned_duration": schedule.estimated_duration,
                    "actual_duration": duration_minutes,
                    "accuracy": abs(schedule.estimated_duration - duration_minutes) / schedule.estimated_duration,
                    "metrics": metrics
                }
                
                cur.execute("""
                    INSERT INTO log_agent (agent_name, action, details, timestamp, collection_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("expedition_planner", "expedition_completed", json.dumps(details),
                     datetime.utcnow(), schedule.target_collection))
            
            self.postgres_agent.connection.commit()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not log expedition completion: {str(e)}")
    
    async def _update_performance_patterns(self, schedule: ExpeditionSchedule, 
                                         success: bool, duration_minutes: int) -> None:
        """Update performance patterns based on expedition results"""
        execution_time = schedule.scheduled_time
        pattern_key = (execution_time.hour, execution_time.weekday())
        
        if pattern_key in self.performance_patterns:
            pattern = self.performance_patterns[pattern_key]
            
            # Update success rate using exponential moving average
            alpha = 0.1  # Learning rate
            current_success = 1.0 if success else 0.0
            pattern.expedition_success_rate = (
                alpha * current_success + (1 - alpha) * pattern.expedition_success_rate
            )
            
            self.logger.debug(f"📊 Updated pattern for {pattern_key}: "
                           f"success_rate={pattern.expedition_success_rate:.3f}")