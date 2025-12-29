#!/usr/bin/env python3
"""
🏛️ EPOCH V - Orthodoxy Adaptation Listener

Listens for metrics.report.generated events from Prometheus Metrics Reader,
evaluates system coherence against thresholds, and invokes VARE adaptation
when incoherencies are detected.

This closes the EPOCH V cognitive loop:
Grafana → Prometheus → Metrics Reader → THIS LISTENER → VARE.adjust() → Vault

Author: Vitruvyan Development Team - EPOCH V  
Created: October 22, 2025
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Cognitive Bus integration
from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent

# VARE Engine integration
from core.cognitive.vitruvyan_proprietary.vare_engine import VAREEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ORTHODOXY_LISTENER] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class OrthodoxyAdaptationListener:
    """
    EPOCH V Orthodoxy Adaptation Listener
    
    Monitors system metrics and triggers VARE adaptations when
    coherence thresholds are violated.
    """
    
    def __init__(self):
        self.redis_bus = get_redis_bus()
        self.vare = VAREEngine()
        
        # Coherence thresholds (adjustable via config)
        self.thresholds = {
            'redis_memory_max_mb': 200,  # MB
            'redis_clients_min': 5,  # connections
            'container_memory_max_gb': 2,  # GB
            'redis_commands_min_rate': 1.0  # ops/sec
        }
        
        # Adaptation tracking
        self.adaptation_count = 0
        self.last_adaptation_time = None
        self.cooldown_seconds = 300  # 5 min cooldown between adaptations
        
        logger.info("🏛️ Orthodoxy Adaptation Listener initialized")
        logger.info(f"   Thresholds: {self.thresholds}")
    
    def start(self):
        """Start listening for metrics reports"""
        logger.info("🚀 Starting Orthodoxy Adaptation Listener...")
        
        # Ensure Redis connection
        if not self.redis_bus.is_connected():
            success = self.redis_bus.connect()
            if not success:
                logger.error("❌ Failed to connect to Redis Cognitive Bus")
                return
        
        # Subscribe to metrics reports
        self.redis_bus.subscribe("metrics.report.generated", self.handle_metrics_report)
        
        # Start listening loop
        if not self.redis_bus.is_listening:
            logger.info("👂 Starting Redis listening thread...")
            self.redis_bus.start_listening()
        
        logger.info("✅ Orthodoxy Adaptation Listener active")
        logger.info("   Waiting for metrics.report.generated events...")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(5)  # PHASE 5: Reduced CPU from 105.9% (was 1s loop)
        except KeyboardInterrupt:
            logger.info("\n👋 Listener stopped by user")
    
    def handle_metrics_report(self, event: CognitiveEvent):
        """
        Handle incoming metrics report from Prometheus Metrics Reader
        
        Args:
            event: CognitiveEvent with metrics payload
        """
        try:
            logger.info("\n" + "="*70)
            logger.info(f"📊 Metrics report received at {datetime.utcnow().strftime('%H:%M:%S')}")
            logger.info("="*70)
            
            payload = event.payload
            metrics = payload.get('metrics', {})
            summary = payload.get('summary', {})
            
            # Log summary
            logger.info(f"   Status: {summary.get('overall_status', 'unknown')}")
            logger.info(f"   Warnings: {summary.get('warnings', 0)}")
            logger.info(f"   Critical: {summary.get('critical_issues', 0)}")
            
            # Evaluate coherence
            incoherencies = self._evaluate_coherence(metrics)
            
            if incoherencies:
                logger.warning(f"⚠️ Detected {len(incoherencies)} incoherenc{'y' if len(incoherencies) == 1 else 'ies'}")
                
                # Check cooldown
                if self._is_cooldown_active():
                    logger.info(f"   ⏸️ Cooldown active, skipping adaptation")
                    return
                
                # Trigger adaptation
                self._trigger_adaptation(incoherencies, metrics)
            else:
                logger.info("✅ All metrics within coherence thresholds")
            
        except Exception as e:
            logger.error(f"❌ Error handling metrics report: {e}", exc_info=True)
    
    def _evaluate_coherence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate metrics against coherence thresholds
        
        Args:
            metrics: Dictionary of metric data
            
        Returns:
            Dictionary of incoherencies: {parameter: {metric, value, threshold, delta}}
        """
        incoherencies = {}
        
        # Check Redis memory
        redis_memory = metrics.get('redis_memory', {})
        if redis_memory.get('value') is not None:
            value_mb = redis_memory['value'] / (1024 * 1024)
            threshold_mb = self.thresholds['redis_memory_max_mb']
            
            if value_mb > threshold_mb:
                incoherencies['volatility_threshold'] = {
                    'metric': 'redis_memory',
                    'value': value_mb,
                    'threshold': threshold_mb,
                    'delta': -0.05,  # Reduce volatility sensitivity to lower memory usage
                    'reason': f'Redis memory {value_mb:.1f} MB exceeds threshold {threshold_mb} MB'
                }
                logger.warning(f"   ⚠️ Redis memory: {value_mb:.1f} MB > {threshold_mb} MB")
        
        # Check Redis clients
        redis_clients = metrics.get('redis_clients', {})
        if redis_clients.get('value') is not None:
            value = redis_clients['value']
            threshold = self.thresholds['redis_clients_min']
            
            if value < threshold:
                incoherencies['market_threshold'] = {
                    'metric': 'redis_clients',
                    'value': value,
                    'threshold': threshold,
                    'delta': +0.1,  # Increase market sensitivity to detect issues faster
                    'reason': f'Redis clients {value} below threshold {threshold}'
                }
                logger.warning(f"   ⚠️ Redis clients: {value} < {threshold}")
        
        # Check container memory
        container_memory = metrics.get('container_memory_total', {})
        if container_memory.get('value') is not None:
            value_gb = container_memory['value'] / (1024 * 1024 * 1024)
            threshold_gb = self.thresholds['container_memory_max_gb']
            
            if value_gb > threshold_gb:
                incoherencies['liquidity_threshold'] = {
                    'metric': 'container_memory_total',
                    'value': value_gb,
                    'threshold': threshold_gb,
                    'delta': -0.03,  # Reduce liquidity sensitivity
                    'reason': f'Container memory {value_gb:.2f} GB exceeds threshold {threshold_gb} GB'
                }
                logger.warning(f"   ⚠️ Container memory: {value_gb:.2f} GB > {threshold_gb} GB")
        
        # Check Redis command rate
        commands_rate = metrics.get('redis_commands_rate', {})
        if commands_rate.get('value') is not None:
            value = commands_rate['value']
            threshold = self.thresholds['redis_commands_min_rate']
            
            if value < threshold:
                # Low command rate might indicate system inactivity or issues
                logger.info(f"   ℹ️ Redis commands rate: {value:.2f} ops/sec < {threshold} ops/sec (info only)")
        
        return incoherencies
    
    def _is_cooldown_active(self) -> bool:
        """Check if cooldown period is still active"""
        if self.last_adaptation_time is None:
            return False
        
        elapsed = (datetime.utcnow() - self.last_adaptation_time).total_seconds()
        return elapsed < self.cooldown_seconds
    
    def _trigger_adaptation(self, incoherencies: Dict[str, Any], metrics: Dict[str, Any]):
        """
        Trigger VARE adaptation for detected incoherencies
        
        Args:
            incoherencies: Dictionary of parameter -> incoherency data
            metrics: Original metrics data
        """
        logger.info("\n🔧 TRIGGERING VARE ADAPTATION")
        logger.info("-" * 70)
        
        adaptations_applied = []
        
        for parameter, incoherence in incoherencies.items():
            logger.info(f"   Parameter: {parameter}")
            logger.info(f"   Reason: {incoherence['reason']}")
            logger.info(f"   Delta: {incoherence['delta']:+.3f}")
            
            # Apply adaptation via VARE
            success = self.vare.adjust(parameter, incoherence['delta'])
            
            if success:
                adaptations_applied.append({
                    'parameter': parameter,
                    'delta': incoherence['delta'],
                    'metric': incoherence['metric'],
                    'value': incoherence['value'],
                    'threshold': incoherence['threshold']
                })
                logger.info(f"   ✅ Adaptation applied successfully")
            else:
                logger.error(f"   ❌ Adaptation failed")
        
        # Update adaptation tracking
        self.adaptation_count += len(adaptations_applied)
        self.last_adaptation_time = datetime.utcnow()
        
        # Publish adaptation completed event to Vault
        if adaptations_applied:
            self._publish_adaptation_completed(adaptations_applied, metrics)
        
        logger.info("-" * 70)
        logger.info(f"✅ VARE adaptation cycle complete: {len(adaptations_applied)} adaptation(s) applied")
        logger.info(f"   Total adaptations: {self.adaptation_count}")
        logger.info(f"   Next adaptation allowed at: {datetime.utcnow() + timedelta(seconds=self.cooldown_seconds)}")
    
    def _publish_adaptation_completed(self, adaptations: List[Dict], metrics: Dict):
        """Publish adaptation completed event to Vault Keepers"""
        try:
            event = CognitiveEvent(
                event_type="vare.adaptation.completed",
                emitter="orthodoxy_adaptation_listener",
                target="vault_keepers",
                payload={
                    'adaptations': adaptations,
                    'metrics_snapshot': metrics,
                    'adaptation_count': self.adaptation_count,
                    'timestamp': datetime.utcnow().isoformat()
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info("   📡 Adaptation event published to Vault Keepers")
            else:
                logger.warning("   ⚠️ Failed to publish adaptation event")
                
        except Exception as e:
            logger.error(f"   ❌ Error publishing adaptation event: {e}")


def main():
    """Main entry point"""
    from datetime import timedelta
    
    logger.info("="*70)
    logger.info("🏛️  EPOCH V - ORTHODOXY ADAPTATION LISTENER")
    logger.info("="*70)
    logger.info("   Cognitive Loop: Metrics → Evaluation → VARE Adaptation → Vault")
    logger.info("="*70)
    
    # Create and start listener
    listener = OrthodoxyAdaptationListener()
    listener.start()


if __name__ == "__main__":
    main()
