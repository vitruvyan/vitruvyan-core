"""
🗺️ CODEX HUNTER - BASE HUNTER
================================
Foundation class for all Codex Hunters with shared expedition logic

The Codex Hunters are digital archaeologists tracking lost data across
the financial dark ages, preserving knowledge for future generations.

Features:
- PostgresAgent and QdrantAgent integration
- Expedition event publishing to Cognitive Bus
- Discovery logging and monitoring
- Helper methods for codex operations
- Standard error handling
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json

# Import standard agents
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent

logger = logging.getLogger(__name__)


class CodexEvent:
    """Standard event structure for Codex Hunter expeditions"""
    
    def __init__(
        self,
        event_type: str,
        hunter: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        self.hunter = hunter
        self.payload = payload
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert expedition event to dictionary"""
        return {
            "event_type": self.event_type,
            "hunter": self.hunter,
            "payload": self.payload,
            "context": {
                **self.context,
                "timestamp": self.timestamp
            }
        }
    
    def to_json(self) -> str:
        """Convert expedition event to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class BaseHunter(ABC):
    """
    🗺️ Base class for all Codex Hunters
    
    The foundation of every expedition. Hunters track lost financial codices
    across distributed archives, preserving data for future analysis.
    
    Provides:
    - Database connectivity (PostgreSQL Archive + Qdrant Vault)
    - Expedition event publishing
    - Discovery logging infrastructure
    - Common codex operations
    - Standard error handling
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base codex hunter
        
        Args:
            name: Hunter name (e.g., "Tracker", "Restorer", "Binder")
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        
        # Initialize database agents (archives)
        try:
            self.postgres_agent = PostgresAgent()
            logger.info(f"✅ {self.name}: PostgreSQL Archive connected")
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to connect PostgreSQL Archive: {e}")
            self.postgres_agent = None
        
        try:
            self.qdrant_agent = QdrantAgent()
            logger.info(f"✅ {self.name}: Qdrant Vault connected")
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to connect Qdrant Vault: {e}")
            self.qdrant_agent = None
        
        # Expedition event queue for batch publishing
        self.event_queue: List[CodexEvent] = []
        
        # Hunter statistics
        self.stats = {
            "operations_executed": 0,
            "operations_failed": 0,
            "events_published": 0,
            "records_processed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info(f"🤖 {self.name} initialized successfully")
    
    def save_record(self, table: str, record: Dict[str, Any]) -> bool:
        """
        Save a single record to PostgreSQL using existing agent methods
        
        Args:
            table: Target table name ('sentiment_scores', 'phrases', etc.)
            record: Record data as dictionary
            
        Returns:
            bool: Success status
        """
        try:
            if not self.postgres_agent:
                logger.error(f"❌ {self.name}: PostgresAgent not available")
                return False
            
            # Use specific PostgresAgent methods based on table
            success = False
            
            if table == "sentiment_scores":
                success = self.postgres_agent.insert_sentiment(
                    entity_id=record.get("entity_id", ""),
                    reddit=record.get("reddit_score", 0.0),
                    google=record.get("google_score", 0.0),
                    combined=record.get("combined_score", 0.0),
                    tag=record.get("sentiment_tag", "neutral"),
                    reddit_titles=record.get("reddit_titles", []),
                    google_titles=record.get("google_titles", []),
                    timeframe=record.get("timeframe", "daily")
                )
            elif table == "phrases":
                success = self.postgres_agent.insert_phrase(
                    text=record.get("phrase_text", ""),
                    source=record.get("source", "unknown"),
                    language=record.get("language", "en"),
                    created_at=record.get("created_at"),
                    embedded=record.get("embedded", False)
                )
            elif table == "signals":
                success = self.postgres_agent.insert_signal(
                    entity_id=record.get("entity_id", ""),
                    pattern=record.get("pattern", ""),
                    confidence=record.get("confidence", 0.0),
                    source=record.get("source", "codex_hunters"),
                    timeframe=record.get("timeframe", "daily")
                )
            else:
                logger.warning(f"⚠️ {self.name}: Unsupported table '{table}' - using generic connection")
                # Fallback: direct connection usage for unsupported tables
                with self.postgres_agent.connection.cursor() as cur:
                    columns = list(record.keys())
                    placeholders = ["%s"] * len(columns)
                    query = f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT DO NOTHING
                    """
                    cur.execute(query, list(record.values()))
                self.postgres_agent.connection.commit()
                success = True
            
            if success:
                self.stats["records_processed"] += 1
                logger.debug(f"✅ {self.name}: Saved record to {table}")
            else:
                self.stats["operations_failed"] += 1
                logger.error(f"❌ {self.name}: Failed to save record to {table}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to save record to {table}: {e}")
            self.stats["operations_failed"] += 1
            return False
    
    def save_batch(self, table: str, records: List[Dict[str, Any]]) -> int:
        """
        Save multiple records to PostgreSQL using existing agent methods
        
        Args:
            table: Target table name ('sentiment_scores', 'phrases', etc.)
            records: List of record dictionaries
            
        Returns:
            int: Number of records successfully saved
        """
        if not records:
            return 0
        
        saved_count = 0
        
        try:
            if not self.postgres_agent:
                logger.error(f"❌ {self.name}: PostgresAgent not available")
                return 0
            
            # Process each record using specific methods
            for record in records:
                if self.save_record(table, record):
                    saved_count += 1
            
            logger.info(f"✅ {self.name}: Saved {saved_count}/{len(records)} records to {table}")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to save batch to {table}: {e}")
            self.stats["operations_failed"] += 1
            return saved_count
    
    def log_event(self, event_type: str, payload: Dict[str, Any], severity: str = "info") -> None:
        """
        Log an event (currently to console, database logging TODO)
        
        Args:
            event_type: Type of event (e.g., "codex.discovered")
            payload: Event data
            severity: Event severity (info, warning, error, critical)
        """
        try:
            event = CodexEvent(
                event_type=event_type,
                hunter=self.name,
                payload=payload,
                context={"severity": severity}
            )
            
            # Log to console (TODO: add database persistence when event_log table is ready)
            logger.info(f"📝 {self.name}: Event {event_type} | {severity} | {json.dumps(payload, default=str)[:100]}")
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to log event: {e}")
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], severity: str = "info") -> None:
        """
        Publish event to Cognitive Bus (currently logs + queues)
        
        Args:
            event_type: Type of event
            payload: Event data
            severity: Event severity
        """
        try:
            event = CodexEvent(
                event_type=event_type,
                hunter=self.name,
                payload=payload,
                context={"severity": severity}
            )
            
            # Add to queue for batch publishing
            self.event_queue.append(event)
            
            # Log event
            self.log_event(event_type, payload, severity)
            
            # TODO: Publish to Redis/Kafka when Cognitive Bus is ready
            # self.cognitive_bus.publish(event)
            
            self.stats["events_published"] += 1
            
            logger.debug(f"📡 {self.name}: Published event {event_type}")
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to publish event: {e}")
    
    def flush_event_queue(self) -> int:
        """
        Flush queued events (batch publish)
        
        Returns:
            int: Number of events flushed
        """
        count = len(self.event_queue)
        
        if count > 0:
            logger.info(f"🔄 {self.name}: Flushing {count} queued events")
            
            # TODO: Batch publish to Cognitive Bus
            # for event in self.event_queue:
            #     self.cognitive_bus.publish(event)
            
            self.event_queue.clear()
        
        return count
    
    def flush_events(self) -> int:
        """Alias for flush_event_queue() for backward compatibility"""
        return self.flush_event_queue()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics
        
        Returns:
            dict: Agent statistics
        """
        stats = self.stats.copy()
        stats["uptime_seconds"] = (
            datetime.now() - datetime.fromisoformat(stats["start_time"])
        ).total_seconds()
        return stats
    
    def reset_stats(self) -> None:
        """Reset agent statistics"""
        self.stats = {
            "operations_executed": 0,
            "operations_failed": 0,
            "events_published": 0,
            "records_processed": 0,
            "start_time": datetime.now().isoformat()
        }
        logger.info(f"🔄 {self.name}: Statistics reset")
    
    def is_healthy(self) -> bool:
        """
        Check if agent is healthy
        
        Returns:
            bool: Health status
        """
        try:
            # Check database connections
            pg_healthy = self.postgres_agent is not None
            qdrant_healthy = self.qdrant_agent is not None
            
            # Check error rate
            total_ops = self.stats["operations_executed"] + self.stats["operations_failed"]
            error_rate = (
                self.stats["operations_failed"] / total_ops
                if total_ops > 0
                else 0
            )
            
            # Healthy if connections OK and error rate < 20%
            healthy = pg_healthy and qdrant_healthy and error_rate < 0.2
            
            return healthy
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Health check failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            dict: Health check results with status, database status, error rate, uptime
        """
        try:
            # Check overall health
            healthy = self.is_healthy()
            
            # Database status
            db_status = {
                "postgres": "connected" if self.postgres_agent else "disconnected",
                "qdrant": "connected" if self.qdrant_agent else "disconnected"
            }
            
            # Calculate error rate
            total_ops = self.stats["operations_executed"] + self.stats["operations_failed"]
            error_rate = (
                self.stats["operations_failed"] / total_ops * 100
                if total_ops > 0
                else 0.0
            )
            
            # Calculate uptime
            uptime = (
                datetime.now() - datetime.fromisoformat(self.stats["start_time"])
            ).total_seconds()
            
            return {
                "status": "healthy" if healthy else "unhealthy",
                "database_status": db_status,
                "error_rate": round(error_rate, 1),
                "uptime_seconds": round(uptime, 2),
                "operations": {
                    "executed": self.stats["operations_executed"],
                    "failed": self.stats["operations_failed"],
                    "records_processed": self.stats["records_processed"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "uptime_seconds": 0,
                "error_rate": 100.0
            }
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Main execution method - must be implemented by subclasses
        
        Returns:
            Any: Agent-specific result
        """
        pass
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<{self.__class__.__name__}(name='{self.name}', healthy={self.is_healthy()})>"
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        try:
            # Flush any pending events
            self.flush_event_queue()
            
            # Note: PostgresAgent and QdrantAgent don't have close() methods
            # They manage their own connections
            
            logger.info(f"🛑 {self.name}: Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Cleanup error: {e}")
        
        return False  # Don't suppress exceptions