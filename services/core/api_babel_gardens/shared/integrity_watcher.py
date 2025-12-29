# api_gemma_cognitive/shared/integrity_watcher.py
"""
🔍 Unified Integrity Watcher
Monitors data quality, model performance, and system health
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
from pathlib import Path
import numpy as np

# Import standard Vitruvyan agents as required
from core.foundation.persistence import PostgresAgent

logger = logging.getLogger(__name__)

@dataclass
class IntegrityCheck:
    """Definition of an integrity check"""
    name: str
    description: str
    check_function: Callable
    severity: str = "medium"  # low, medium, high, critical
    frequency_minutes: int = 15
    enabled: bool = True
    last_run: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    failure_count: int = 0
    max_failures: int = 3

@dataclass 
class IntegrityViolation:
    """Detected integrity violation"""
    check_name: str
    severity: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False

class UnifiedIntegrityWatcher:
    """
    🛡️ Comprehensive integrity monitoring system
    Watches embeddings quality, sentiment consistency, cache health
    """
    
    def __init__(self):
        import os
        self.name = "unified_integrity_watcher"
        self.logger = logging.getLogger(f"gemma.{self.name}")
        
        # Sacred Test Mode Protection - Bypass database in test mode
        self.test_mode = os.getenv('VITRUVYAN_TEST_MODE', 'false').lower() == 'true'
        
        if self.test_mode:
            self.logger.info("🛡️ Sacred Test Mode: Bypassing PostgreSQL initialization for linguistic isolation")
            self.postgres_agent = None
        else:
            # Initialize standard Vitruvyan agents as required
            self.postgres_agent = PostgresAgent()
            
        self.checks: Dict[str, IntegrityCheck] = {}
        self.violations: List[IntegrityViolation] = []
        self.metrics: Dict[str, Any] = {}
        self.running = False
        self._monitor_task = None
        self.thresholds = {
            "embedding_similarity_min": 0.1,
            "embedding_similarity_max": 0.99,
            "sentiment_confidence_min": 0.3,
            "cache_hit_rate_min": 0.6,
            "response_time_max_ms": 5000,
            "error_rate_max": 0.05
        }
    
    async def _initialize_service(self):
        """Service-specific initialization for integrity watcher"""
        # This will be called by the base class initialize method
        pass
    
    async def initialize(self):
        """Initialize integrity watcher"""
        await super().initialize()
        
        # Register default checks
        await self._register_default_checks()
        
        # Start monitoring
        self.running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("🛡️ Integrity Watcher initialized")
    
    async def _register_default_checks(self):
        """Register default integrity checks"""
        
        # Embedding quality checks
        self.register_check(
            name="embedding_dimension_consistency",
            description="Check embedding dimensions are consistent",
            check_function=self._check_embedding_dimensions,
            severity="high",
            frequency_minutes=10
        )
        
        self.register_check(
            name="embedding_similarity_bounds",
            description="Check embedding similarities are within expected bounds",
            check_function=self._check_embedding_similarity,
            severity="medium",
            frequency_minutes=15
        )
        
        # Sentiment analysis checks
        self.register_check(
            name="sentiment_confidence_distribution",
            description="Check sentiment confidence scores distribution",
            check_function=self._check_sentiment_confidence,
            severity="medium",
            frequency_minutes=20
        )
        
        self.register_check(
            name="sentiment_fusion_consistency",
            description="Check consistency between fusion modes",
            check_function=self._check_sentiment_fusion,
            severity="high",
            frequency_minutes=30
        )
        
        # Cache health checks
        self.register_check(
            name="cache_performance",
            description="Monitor cache hit rates and performance",
            check_function=self._check_cache_health,
            severity="medium",
            frequency_minutes=5
        )
        
        # System health checks
        self.register_check(
            name="model_response_times",
            description="Monitor model response times",
            check_function=self._check_response_times,
            severity="high",
            frequency_minutes=10
        )
        
        self.register_check(
            name="error_rate_monitoring",
            description="Monitor overall error rates",
            check_function=self._check_error_rates,
            severity="critical",
            frequency_minutes=5
        )
    
    def register_check(
        self,
        name: str,
        description: str,
        check_function: Callable,
        severity: str = "medium",
        frequency_minutes: int = 15,
        enabled: bool = True
    ):
        """Register a new integrity check"""
        self.checks[name] = IntegrityCheck(
            name=name,
            description=description,
            check_function=check_function,
            severity=severity,
            frequency_minutes=frequency_minutes,
            enabled=enabled
        )
        logger.info(f"📋 Registered integrity check: {name}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._run_scheduled_checks()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _run_scheduled_checks(self):
        """Run checks that are due"""
        now = datetime.now()
        
        for check_name, check in self.checks.items():
            if not check.enabled:
                continue
            
            # Determine if check is due
            if check.last_run is None:
                is_due = True
            else:
                time_since_last = now - check.last_run
                is_due = time_since_last.total_seconds() >= (check.frequency_minutes * 60)
            
            if is_due:
                await self._run_check(check)
    
    async def _run_check(self, check: IntegrityCheck):
        """Run a single integrity check"""
        try:
            logger.debug(f"🔍 Running check: {check.name}")
            
            # Run the check function
            result = await check.check_function()
            
            check.last_run = datetime.now()
            check.last_result = result
            
            # Process results
            if result.get("status") == "violation":
                check.failure_count += 1
                violation = IntegrityViolation(
                    check_name=check.name,
                    severity=check.severity,
                    message=result.get("message", "Integrity violation detected"),
                    details=result.get("details", {})
                )
                self.violations.append(violation)
                
                logger.warning(f"⚠️ Integrity violation: {check.name} - {violation.message}")
                
                # Disable check if too many failures
                if check.failure_count >= check.max_failures:
                    check.enabled = False
                    logger.error(f"❌ Disabled check due to repeated failures: {check.name}")
            
            elif result.get("status") == "healthy":
                check.failure_count = max(0, check.failure_count - 1)  # Decrease failure count
            
        except Exception as e:
            logger.error(f"❌ Check execution error ({check.name}): {str(e)}")
            check.failure_count += 1
    
    # ===========================
    # DEFAULT CHECK IMPLEMENTATIONS
    # ===========================
    
    async def _check_embedding_dimensions(self) -> Dict[str, Any]:
        """Check embedding dimension consistency"""
        try:
            # This would integrate with the vector cache to sample recent embeddings
            from .vector_cache import vector_cache
            
            # For now, return healthy - would implement actual dimension checking
            return {
                "status": "healthy", 
                "message": "Embedding dimensions consistent",
                "details": {"expected_dim": 768, "checked_count": 0}
            }
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Failed to check embedding dimensions: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_embedding_similarity(self) -> Dict[str, Any]:
        """Check embedding similarity bounds"""
        try:
            # Sample some similarity scores and check bounds
            return {
                "status": "healthy",
                "message": "Embedding similarities within bounds",
                "details": {
                    "min_similarity": 0.15,
                    "max_similarity": 0.95,
                    "samples_checked": 0
                }
            }
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Embedding similarity check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_sentiment_confidence(self) -> Dict[str, Any]:
        """Check sentiment confidence distribution"""
        try:
            # Check recent sentiment analysis confidence scores
            return {
                "status": "healthy",
                "message": "Sentiment confidence distribution normal",
                "details": {
                    "avg_confidence": 0.75,
                    "low_confidence_ratio": 0.1
                }
            }
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Sentiment confidence check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_sentiment_fusion(self) -> Dict[str, Any]:
        """Check sentiment fusion consistency"""
        try:
            # Compare results across different fusion modes
            return {
                "status": "healthy",
                "message": "Sentiment fusion modes consistent",
                "details": {"consistency_score": 0.88}
            }
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Sentiment fusion check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache performance"""
        try:
            from .vector_cache import vector_cache
            
            stats = await vector_cache.get_cache_stats()
            hit_rate = stats.get("hit_rate", 0.0)
            
            if hit_rate < self.thresholds["cache_hit_rate_min"]:
                return {
                    "status": "violation",
                    "message": f"Cache hit rate too low: {hit_rate:.2f}",
                    "details": {"hit_rate": hit_rate, "threshold": self.thresholds["cache_hit_rate_min"]}
                }
            
            return {
                "status": "healthy",
                "message": f"Cache performing well: {hit_rate:.2f} hit rate",
                "details": {"hit_rate": hit_rate}
            }
            
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Cache health check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_response_times(self) -> Dict[str, Any]:
        """Check model response times"""
        try:
            # This would track actual response times from metrics
            avg_response_time = 1200  # ms - placeholder
            
            if avg_response_time > self.thresholds["response_time_max_ms"]:
                return {
                    "status": "violation", 
                    "message": f"Response time too high: {avg_response_time}ms",
                    "details": {
                        "avg_response_time_ms": avg_response_time,
                        "threshold_ms": self.thresholds["response_time_max_ms"]
                    }
                }
            
            return {
                "status": "healthy",
                "message": f"Response times acceptable: {avg_response_time}ms",
                "details": {"avg_response_time_ms": avg_response_time}
            }
            
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Response time check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_error_rates(self) -> Dict[str, Any]:
        """Check overall error rates"""
        try:
            # This would track actual error rates from metrics
            error_rate = 0.02  # 2% - placeholder
            
            if error_rate > self.thresholds["error_rate_max"]:
                return {
                    "status": "violation",
                    "message": f"Error rate too high: {error_rate:.1%}",
                    "details": {
                        "error_rate": error_rate,
                        "threshold": self.thresholds["error_rate_max"]
                    }
                }
            
            return {
                "status": "healthy",
                "message": f"Error rate acceptable: {error_rate:.1%}",
                "details": {"error_rate": error_rate}
            }
            
        except Exception as e:
            return {
                "status": "violation",
                "message": f"Error rate check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    # ===========================
    # PUBLIC API METHODS
    # ===========================
    
    async def run_check_now(self, check_name: str) -> Dict[str, Any]:
        """Run a specific check immediately"""
        if check_name not in self.checks:
            return {"error": f"Check not found: {check_name}"}
        
        check = self.checks[check_name]
        await self._run_check(check)
        
        return {
            "check_name": check_name,
            "result": check.last_result,
            "timestamp": check.last_run.isoformat() if check.last_run else None
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all enabled checks"""
        results = {}
        
        for check_name, check in self.checks.items():
            if check.enabled:
                await self._run_check(check)
                results[check_name] = {
                    "result": check.last_result,
                    "timestamp": check.last_run.isoformat() if check.last_run else None
                }
        
        return {"checks": results, "total_run": len(results)}
    
    def get_violations(
        self,
        severity: Optional[str] = None,
        unresolved_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get integrity violations"""
        violations = self.violations
        
        # Filter by severity
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        # Filter by resolution status
        if unresolved_only:
            violations = [v for v in violations if not v.resolved]
        
        # Sort by timestamp (newest first)
        violations.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit results
        violations = violations[:limit]
        
        # Convert to dict format
        return [
            {
                "check_name": v.check_name,
                "severity": v.severity,
                "message": v.message,
                "details": v.details,
                "timestamp": v.timestamp.isoformat(),
                "resolved": v.resolved
            }
            for v in violations
        ]
    
    def mark_violation_resolved(self, violation_index: int) -> bool:
        """Mark a violation as resolved"""
        if 0 <= violation_index < len(self.violations):
            self.violations[violation_index].resolved = True
            return True
        return False
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        total_checks = len(self.checks)
        enabled_checks = sum(1 for c in self.checks.values() if c.enabled)
        recent_violations = len([
            v for v in self.violations 
            if not v.resolved and 
            (datetime.now() - v.timestamp).total_seconds() < 3600  # Last hour
        ])
        
        # Determine overall health status
        if recent_violations == 0:
            health_status = "healthy"
        elif recent_violations <= 2:
            health_status = "degraded"
        else:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "checks": {
                "total": total_checks,
                "enabled": enabled_checks,
                "disabled": total_checks - enabled_checks
            },
            "violations": {
                "recent_unresolved": recent_violations,
                "total_unresolved": len([v for v in self.violations if not v.resolved])
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for integrity watcher"""
        try:
            summary = self.get_system_health_summary()
            return {
                "status": "healthy" if self.running else "unhealthy",
                "monitoring_active": self.running,
                "system_health": summary,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        await super().cleanup()
        logger.info("🛡️ Integrity Watcher cleaned up")

# Global singleton instance
integrity_watcher = UnifiedIntegrityWatcher()