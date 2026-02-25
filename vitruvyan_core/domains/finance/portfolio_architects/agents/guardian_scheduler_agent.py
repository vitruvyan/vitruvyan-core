#!/usr/bin/env python3
"""
Guardian Scheduler Agent
Sacred Order #7 - Mercator

Continuous service that schedules Guardian portfolio analysis.
Runs inside Docker container, no external cron needed.

Features:
- APScheduler for hourly execution
- Redis Cognitive Bus integration
- Prometheus metrics
- Health monitoring
- Graceful shutdown
"""
import os
import sys
import signal
import logging
import json
from datetime import datetime
from typing import Dict, List
import time
import redis

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from domains.finance.portfolio_architects.agents.portfolio_guardian_agent import (
    PortfolioGuardianAgent,
    GuardianInsight
)
from core.agents.postgres_agent import PostgresAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
guardian_runs_total = Counter(
    'guardian_scheduler_runs_total',
    'Total Guardian analysis runs',
    ['status']
)
guardian_insights_generated = Counter(
    'guardian_insights_generated_total',
    'Total insights generated',
    ['insight_type']
)
guardian_analysis_duration = Histogram(
    'guardian_analysis_duration_seconds',
    'Guardian analysis duration',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)
guardian_active_portfolios = Gauge(
    'guardian_active_portfolios',
    'Number of active portfolios monitored'
)
guardian_errors_total = Counter(
    'guardian_errors_total',
    'Total Guardian analysis errors',
    ['error_type']
)


class GuardianSchedulerAgent:
    """
    Continuous Guardian scheduler service.
    
    Responsibilities:
    - Schedule hourly portfolio analysis
    - Publish insights to Redis Cognitive Bus
    - Track execution metrics
    - Handle graceful shutdown
    """
    
    def __init__(self):
        self.postgres = PostgresAgent()
        self.guardian = PortfolioGuardianAgent(postgres_agent=self.postgres)
        
        # Simple Redis client (no complex Cognitive Bus)
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        self.scheduler = BlockingScheduler()
        self.is_running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        logger.info("🛡️ GuardianSchedulerAgent initialized (Sacred Order #7)")
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        logger.info(f"🛑 Received shutdown signal ({signum}), stopping scheduler...")
        self.is_running = False
        self.scheduler.shutdown(wait=True)
        logger.info("✅ Guardian Scheduler stopped gracefully")
        sys.exit(0)
    
    def get_active_users(self) -> List[str]:
        """
        Fetch all active users with portfolios.
        
        Returns:
            List[str]: User IDs with active portfolios
        """
        query = """
            SELECT DISTINCT sps.user_id
            FROM shadow_portfolio_snapshots sps
            JOIN shadow_cash_accounts sca ON sps.user_id = sca.user_id
            WHERE sps.is_latest = true
              AND sps.total_value > 0
            ORDER BY sps.user_id
        """
        
        with self.postgres.connection.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]
    
    def publish_insights_to_redis(self, user_id: str, insights: List[GuardianInsight]) -> None:
        """
        Publish insights to Redis Cognitive Bus for Telegram notifications.
        
        Args:
            user_id: User identifier
            insights: List of generated insights
        """
        for insight in insights:
            # Simplified event format for Telegram Bot
            event = {
                "event_type": "guardian.insight",
                "user_id": user_id,
                "insight_id": insight.insight_id,
                "insight_type": insight.insight_type,
                "severity": insight.severity,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to Redis channel
            self.redis.publish(
                "cognitive_bus:events",
                json.dumps(event)
            )
            
            # Track metrics
            guardian_insights_generated.labels(
                insight_type=insight.insight_type
            ).inc()
            
            logger.info(
                f"📢 Published insight to Redis - User: {user_id}, "
                f"Type: {insight.insight_type}, ID: {insight.insight_id}"
            )
    
    def analyze_all_portfolios(self):
        """
        Hourly job: Analyze all active portfolios.
        """
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info(f"🛡️ Guardian Hourly Analysis - Run ID: {run_id}")
        logger.info(f"⏰ Started at: {datetime.utcnow().isoformat()}")
        logger.info("=" * 60)
        
        try:
            # Fetch active users
            active_users = self.get_active_users()
            logger.info(f"📊 Active users: {len(active_users)}")
            guardian_active_portfolios.set(len(active_users))
            
            # Metrics
            total_insights = 0
            analyzed_users = 0
            errors = 0
            
            # Analyze each user
            for user_id in active_users:
                try:
                    logger.info(f"🔍 Analyzing portfolio - User: {user_id}")
                    
                    # Run Guardian analysis
                    with guardian_analysis_duration.time():
                        insights = self.guardian.analyze_portfolio(user_id=user_id)
                    
                    # Publish to Redis
                    if insights:
                        self.publish_insights_to_redis(user_id, insights)
                    
                    # Update metrics
                    analyzed_users += 1
                    total_insights += len(insights)
                    
                    logger.info(
                        f"✅ Analysis complete - User: {user_id}, "
                        f"Insights: {len(insights)}"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"❌ Error analyzing user {user_id}: {str(e)}",
                        exc_info=True
                    )
                    errors += 1
                    guardian_errors_total.labels(error_type="analysis_error").inc()
            
            # Track run metrics
            duration = time.time() - start_time
            guardian_runs_total.labels(status="success").inc()
            
            # Log final metrics
            logger.info("=" * 60)
            logger.info(f"🏁 Guardian Hourly Analysis Complete - Run ID: {run_id}")
            logger.info(f"📊 Analyzed: {analyzed_users}/{len(active_users)} users")
            logger.info(f"💡 Insights: {total_insights} generated")
            logger.info(f"❌ Errors: {errors}")
            logger.info(f"⏱️ Duration: {duration:.2f}s")
            logger.info(f"⏰ Completed at: {datetime.utcnow().isoformat()}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"💥 Fatal error in Guardian analysis: {str(e)}", exc_info=True)
            guardian_runs_total.labels(status="error").inc()
            guardian_errors_total.labels(error_type="fatal_error").inc()
    
    def start(self):
        """
        Start Guardian Scheduler service.
        
        Schedule:
        - Hourly analysis at minute 0 (e.g., 10:00, 11:00, 12:00)
        - Prometheus metrics on port 8022
        """
        logger.info("🚀 Starting Guardian Scheduler Agent...")
        
        # Start Prometheus metrics server
        metrics_port = int(os.getenv("GUARDIAN_METRICS_PORT", "8023"))
        start_http_server(metrics_port)
        logger.info(f"📊 Prometheus metrics server started on port {metrics_port}")
        
        # Schedule hourly Guardian analysis (every hour at minute 0)
        self.scheduler.add_job(
            func=self.analyze_all_portfolios,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id="guardian_hourly",
            name="Guardian Hourly Portfolio Analysis",
            replace_existing=True,
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        logger.info("⏰ Scheduled: Guardian analysis every hour at minute 0")
        
        # Run immediately on startup (optional, for testing)
        if os.getenv("GUARDIAN_RUN_ON_STARTUP", "false").lower() == "true":
            logger.info("🔄 Running initial analysis on startup...")
            self.analyze_all_portfolios()
        
        # Start scheduler
        logger.info("✅ Guardian Scheduler Agent ready")
        logger.info("🛡️ Monitoring active portfolios...")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Scheduler interrupted")


def main():
    """Main execution function"""
    try:
        scheduler_agent = GuardianSchedulerAgent()
        scheduler_agent.start()
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
