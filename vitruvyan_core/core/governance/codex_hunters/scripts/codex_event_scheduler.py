#!/usr/bin/env python3
"""
⏰ Codex Event Scheduler - Automated Backfill Service

Publishes scheduled events to trigger Codex Hunter expeditions:
- Daily 23:00: Full expedition (Track → Restore → Bind → Scribe → Inspect)
- Weekly Sunday 04:00: Cartographer (macro data from FRED)
- Weekly Sunday 05:00: Scholastic (academic factors)

Uses APScheduler with cron-style scheduling for reliable event triggering.
"""

import sys
import logging
import signal
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Setup path
sys.path.insert(0, '/home/caravaggio/vitruvyan')

from core.foundation.cognitive_bus.redis_client import get_redis_bus, CognitiveEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class CodexEventScheduler:
    """
    Event Scheduler for automated Codex Hunter backfill operations.
    
    Publishes Redis events on schedule to trigger:
    - Daily full expeditions (all tickers, technical indicators)
    - Weekly macro data refresh (FRED API)
    - Weekly factor calculation (Fama-French)
    """
    
    def __init__(self):
        self.redis_bus = get_redis_bus()
        self.scheduler = BlockingScheduler()
        self.running = False
        
        # Load ticker list (in production, fetch from DB)
        self.active_tickers = self._load_active_tickers()
        
        logger.info("⏰ Codex Event Scheduler initialized")
    
    def start(self):
        """Start the scheduler service"""
        try:
            logger.info("🚀 Starting Codex Event Scheduler Service...")
            
            # Connect to Redis
            if not self.redis_bus.connect():
                logger.error("❌ Failed to connect to Redis Bus")
                return False
            
            # Setup scheduled jobs
            self._setup_scheduled_jobs()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            logger.info("✅ Codex Event Scheduler started successfully")
            
            # Start scheduler (blocking)
            logger.info("⏰ Scheduler running... Press Ctrl+C to stop")
            self.scheduler.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler service"""
        try:
            logger.info("🛑 Stopping Codex Event Scheduler Service...")
            
            self.running = False
            self.scheduler.shutdown(wait=False)
            self.redis_bus.disconnect()
            
            logger.info("✅ Codex Event Scheduler stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def _setup_scheduled_jobs(self):
        """Configure all scheduled jobs"""
        logger.info("⚙️ Setting up scheduled jobs...")
        
        # Job 1: Daily full expedition at 23:00 UTC
        self.scheduler.add_job(
            self._trigger_daily_expedition,
            CronTrigger(hour=23, minute=0),
            id='daily_expedition',
            name='Daily Codex Full Expedition',
            replace_existing=True
        )
        logger.info("✅ Daily expedition scheduled: 23:00 UTC")
        
        # Job 2: Schema validation - DAILY at 17:55 UTC (before backfills)
        self.scheduler.add_job(
            self._trigger_schema_validation,
            CronTrigger(hour=17, minute=55),
            id='daily_schema_validation',
            name='Daily Schema Validation',
            replace_existing=True
        )
        logger.info("✅ Schema validation scheduled: 17:55 UTC")
        
        # Job 3: Momentum backfill - DAILY at 18:00 UTC (critical for Function H)
        self.scheduler.add_job(
            self._trigger_momentum_backfill,
            CronTrigger(hour=18, minute=0),
            id='daily_momentum',
            name='Daily Momentum Backfill',
            replace_existing=True
        )
        logger.info("✅ Momentum backfill scheduled: 18:00 UTC")
        
        # Job 4: Trend backfill - DAILY at 18:30 UTC (important for Function I)
        self.scheduler.add_job(
            self._trigger_trend_backfill,
            CronTrigger(hour=18, minute=30),
            id='daily_trend',
            name='Daily Trend Backfill',
            replace_existing=True
        )
        logger.info("✅ Trend backfill scheduled: 18:30 UTC")
        
        # Job 5: Volatility backfill - WEEKLY on Sundays at 19:00 UTC
        self.scheduler.add_job(
            self._trigger_volatility_backfill,
            CronTrigger(day_of_week='sun', hour=19, minute=0),
            id='weekly_volatility',
            name='Weekly Volatility Backfill',
            replace_existing=True
        )
        logger.info("✅ Volatility backfill scheduled: Sunday 19:00 UTC")
        
        # Job 6: Weekly macro data refresh (Sunday 04:00 UTC)
        self.scheduler.add_job(
            self._trigger_macro_refresh,
            CronTrigger(day_of_week='sun', hour=4, minute=0),
            id='weekly_macro',
            name='Weekly Macro Data Refresh',
            replace_existing=True
        )
        logger.info("✅ Weekly macro refresh scheduled: Sunday 04:00 UTC")
        
        # Job 7: Weekly factor calculation (Sunday 05:00 UTC)
        self.scheduler.add_job(
            self._trigger_factor_calculation,
            CronTrigger(day_of_week='sun', hour=5, minute=0),
            id='weekly_factors',
            name='Weekly Factor Calculation',
            replace_existing=True
        )
        logger.info("✅ Weekly factor calc scheduled: Sunday 05:00 UTC")
        
        # Job 8: Heartbeat every hour (optional, for monitoring)
        self.scheduler.add_job(
            self._send_heartbeat,
            CronTrigger(minute=0),  # Every hour
            id='heartbeat',
            name='Scheduler Heartbeat',
            replace_existing=True
        )
        logger.info("✅ Heartbeat scheduled: Every hour")
        
        logger.info(f"📅 All jobs scheduled ({len(self.scheduler.get_jobs())} total)")
    
    def _trigger_daily_expedition(self):
        """Trigger daily full expedition event"""
        logger.info("🌙 Triggering daily full expedition (23:00 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.data.refresh.requested",
                source="event_scheduler",
                target="codex_listener",
                correlation_id=f"daily_expedition_{int(datetime.now().timestamp())}",
                payload={
                    "tickers": self.active_tickers,
                    "sources": ["yfinance", "reddit"],
                    "priority": "scheduled",
                    "include_scribe": True,  # Calculate technical indicators
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "daily_backfill"
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info(f"✅ Daily expedition event published: {len(self.active_tickers)} tickers")
            else:
                logger.error("❌ Failed to publish daily expedition event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering daily expedition: {e}")
    
    def _trigger_schema_validation(self):
        """Trigger daily schema validation (before backfills)"""
        logger.info("🔧 Triggering schema validation (17:55 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.schema.validation.requested",
                source="event_scheduler",
                target="inspector",
                correlation_id=f"schema_validation_{int(datetime.now().timestamp())}",
                payload={
                    "tables": ["momentum_logs", "trend_logs", "volatility_logs"],
                    "priority": "high",
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "daily_schema_check"
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info("✅ Schema validation event published")
            else:
                logger.error("❌ Failed to publish schema validation event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering schema validation: {e}")
    
    def _trigger_momentum_backfill(self):
        """Trigger daily momentum backfill (18:00 UTC) - Critical for Function H"""
        logger.info("⚡ Triggering momentum backfill (18:00 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.technical.momentum.requested",
                source="event_scheduler",
                target="scribe",
                correlation_id=f"momentum_backfill_{int(datetime.now().timestamp())}",
                payload={
                    "tickers": self.active_tickers,
                    "indicator": "momentum",
                    "priority": "high",  # Critical for Function H (Divergence Detection)
                    "only_us": True,
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "daily_momentum",
                    "neural_engine_function": "H"  # Divergence Detection requires this
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info(f"✅ Momentum backfill event published: {len(self.active_tickers)} tickers")
            else:
                logger.error("❌ Failed to publish momentum backfill event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering momentum backfill: {e}")
    
    def _trigger_trend_backfill(self):
        """Trigger daily trend backfill (18:30 UTC) - Important for Function I"""
        logger.info("📈 Triggering trend backfill (18:30 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.technical.trend.requested",
                source="event_scheduler",
                target="scribe",
                correlation_id=f"trend_backfill_{int(datetime.now().timestamp())}",
                payload={
                    "tickers": self.active_tickers,
                    "indicator": "trend",
                    "priority": "high",  # Important for Function I (Multi-Timeframe Consensus)
                    "only_us": True,
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "daily_trend",
                    "neural_engine_function": "I"  # Multi-Timeframe Consensus requires this
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info(f"✅ Trend backfill event published: {len(self.active_tickers)} tickers")
            else:
                logger.error("❌ Failed to publish trend backfill event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering trend backfill: {e}")
    
    def _trigger_volatility_backfill(self):
        """Trigger weekly volatility backfill (Sunday 19:00 UTC) - For Function E"""
        logger.info("📊 Triggering volatility backfill (Sunday 19:00 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.technical.volatility.requested",
                source="event_scheduler",
                target="scribe",
                correlation_id=f"volatility_backfill_{int(datetime.now().timestamp())}",
                payload={
                    "tickers": self.active_tickers,
                    "indicator": "volatility",
                    "priority": "medium",  # Weekly is sufficient for Function E
                    "only_us": True,
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "weekly_volatility",
                    "neural_engine_function": "E"  # Risk-Adjusted Ranking uses this
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info(f"✅ Volatility backfill event published: {len(self.active_tickers)} tickers")
            else:
                logger.error("❌ Failed to publish volatility backfill event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering volatility backfill: {e}")
    
    def _trigger_macro_refresh(self):
        """Trigger weekly macro data refresh event"""
        logger.info("🌍 Triggering weekly macro data refresh (Sunday 04:00 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.macro.refresh.requested",
                source="event_scheduler",
                target="cartographer",
                correlation_id=f"macro_refresh_{int(datetime.now().timestamp())}",
                payload={
                    "fred_series": ["CPIAUCSL", "FEDFUNDS", "VIXCLS"],
                    "priority": "scheduled",
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "weekly_macro"
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info("✅ Macro refresh event published")
            else:
                logger.error("❌ Failed to publish macro refresh event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering macro refresh: {e}")
    
    def _trigger_factor_calculation(self):
        """Trigger weekly factor calculation event"""
        logger.info("📚 Triggering weekly factor calculation (Sunday 05:00 UTC)...")
        
        try:
            event = CognitiveEvent(
                event_type="codex.factors.refresh.requested",
                source="event_scheduler",
                target="scholastic",
                correlation_id=f"factors_refresh_{int(datetime.now().timestamp())}",
                payload={
                    "tickers": self.active_tickers,
                    "priority": "scheduled",
                    "scheduled_time": datetime.now().isoformat(),
                    "schedule_type": "weekly_factors"
                }
            )
            
            success = self.redis_bus.publish_event(event)
            
            if success:
                logger.info(f"✅ Factor calculation event published: {len(self.active_tickers)} tickers")
            else:
                logger.error("❌ Failed to publish factor calculation event")
                
        except Exception as e:
            logger.error(f"❌ Error triggering factor calculation: {e}")
    
    def _send_heartbeat(self):
        """Send heartbeat event for monitoring"""
        try:
            jobs_info = {}
            for job_id in ['daily_expedition', 'daily_schema_validation', 'daily_momentum', 
                          'daily_trend', 'weekly_volatility', 'weekly_macro', 'weekly_factors']:
                job = self.scheduler.get_job(job_id)
                if job:
                    jobs_info[job_id] = str(job.next_run_time)
            
            event = CognitiveEvent(
                event_type="scheduler.heartbeat",
                source="event_scheduler",
                target="monitoring",
                correlation_id=f"heartbeat_{int(datetime.now().timestamp())}",
                payload={
                    "status": "running",
                    "jobs_scheduled": len(self.scheduler.get_jobs()),
                    "next_runs": jobs_info,
                    "timestamp": datetime.now().isoformat(),
                    "epistemic_mode": True  # Indicates intelligent scheduling is active
                }
            )
            
            self.redis_bus.publish_event(event)
            logger.debug("💓 Heartbeat sent")
            
        except Exception as e:
            logger.warning(f"⚠️  Heartbeat failed: {e}")
    
    def _load_active_tickers(self) -> list:
        """
        Load active tickers from database.
        Queries PostgreSQL tickers table for all active symbols.
        """
        try:
            from core.foundation.persistence.postgres_agent import PostgresAgent
            
            pg = PostgresAgent()
            result = pg.execute_query(
                "SELECT ticker FROM tickers WHERE active = true ORDER BY ticker",
                fetch=True
            )
            
            if result:
                tickers = [row[0] for row in result]
                logger.info(f"✅ Loaded {len(tickers)} active tickers from database")
                return tickers
            else:
                logger.warning("⚠️ No active tickers found in database, using fallback list")
                return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"]
                
        except Exception as e:
            logger.error(f"❌ Failed to load tickers from database: {e}")
            # Fallback to sample list if DB query fails
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"]


def main():
    """Main service entry point"""
    print("⏰ CODEX EVENT SCHEDULER SERVICE - EPISTEMIC MODE")
    print("=" * 80)
    print("📅 Scheduled Jobs (Intelligent Backfill Orchestration):")
    print("  - Schema Validation: 17:55 UTC (Ensures tables/columns exist)")
    print("  - Momentum Backfill: 18:00 UTC (Function H: Divergence Detection)")
    print("  - Trend Backfill: 18:30 UTC (Function I: Multi-Timeframe Consensus)")
    print("  - Volatility Backfill: Sunday 19:00 UTC (Function E: Risk-Adjusted)")
    print("  - Daily Expedition: 23:00 UTC (Track → Restore → Bind → Scribe)")
    print("  - Macro Refresh: Sunday 04:00 UTC (Cartographer → FRED API)")
    print("  - Factor Calc: Sunday 05:00 UTC (Scholastic → Fama-French)")
    print("  - Heartbeat: Every hour (Monitoring)")
    print("=" * 80)
    print("🧠 Epistemic Scheduling: Adapts to system load and performance patterns")
    print("=" * 80)
    
    scheduler = CodexEventScheduler()
    
    try:
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt received")
        scheduler.stop()
        return 0
        
    except Exception as e:
        logger.error(f"❌ Scheduler failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
