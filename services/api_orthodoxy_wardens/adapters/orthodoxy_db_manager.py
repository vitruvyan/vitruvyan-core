"""
Orthodoxy Wardens Database Manager
Handles PostgreSQL interactions for audit confessions and sacred records.

Uses PostgresAgent for connection management (env vars, no hardcoded credentials).
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import structlog

from core.agents.postgres_agent import PostgresAgent

logger = structlog.get_logger(__name__)


class OrthodoxyDatabaseManager:
    """
    Database manager for Orthodoxy Wardens.
    Handles confessions, audit findings, and sacred records.

    Delegates connection management to PostgresAgent (env vars:
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD).
    """
    
    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Initialize database manager.
        
        Args:
            connection_params: Dict with host, port, database, user, password.
                             If None, PostgresAgent reads from environment variables.
        """
        if connection_params:
            self.pg = PostgresAgent(
                host=connection_params.get("host"),
                port=str(connection_params.get("port", "5432")),
                dbname=connection_params.get("database"),
                user=connection_params.get("user"),
                password=connection_params.get("password")
            )
        else:
            self.pg = PostgresAgent()
    
    @property
    def connection(self):
        """Get active database connection (delegates to PostgresAgent)."""
        return self.pg.connection
    
    # =========================================================================
    # CONFESSION MANAGEMENT
    # =========================================================================
    
    async def create_confession(
        self,
        confession_id: str,
        service: str,
        event_type: str,
        payload: Dict[str, Any],
        assigned_warden: str = "confessor"
    ) -> Dict[str, Any]:
        """
        Create a new confession (audit request).
        
        Args:
            confession_id: Unique identifier
            service: Source service name
            event_type: Type of audit event
            payload: Event data (stored as JSONB)
            assigned_warden: Warden role responsible
        
        Returns:
            Confession record dict
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO confessions (
                        confession_id, service, event_type, payload, 
                        sacred_status, assigned_warden
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (confession_id, service, event_type, 
                     psycopg2.extras.Json(payload), 'pending', assigned_warden))
                
                self.connection.commit()
                result = dict(cur.fetchone())
                
                logger.info("📝 Confession created", 
                           confession_id=confession_id, 
                           service=service)
                
                return result
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"💀 Failed to create confession: {e}")
            raise
    
    async def get_confession_status(self, confession_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a confession.
        
        Args:
            confession_id: Unique confession identifier
        
        Returns:
            Confession dict or None if not found
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        confession_id,
                        sacred_status,
                        penance_progress,
                        divine_results,
                        assigned_warden,
                        created_at,
                        updated_at,
                        completed_at,
                        orthodoxy_score
                    FROM confessions
                    WHERE confession_id = %s
                """, (confession_id,))
                
                result = cur.fetchone()
                
                if result:
                    return dict(result)
                else:
                    logger.warning(f"⚠️ Confession not found", confession_id=confession_id)
                    return None
        
        except Exception as e:
            logger.error(f"💀 Failed to get confession status: {e}")
            raise
    
    async def update_confession_status(
        self,
        confession_id: str,
        sacred_status: str,
        orthodoxy_score: Optional[float] = None,
        divine_results: Optional[Dict[str, Any]] = None,
        penance_progress: Optional[float] = None
    ) -> bool:
        """
        Update confession status and results.
        
        Args:
            confession_id: Confession identifier
            sacred_status: New status (blessed, heretical, failed)
            orthodoxy_score: Validation score (0.0-1.0)
            divine_results: Audit results dict
            penance_progress: Progress percentage (0.0-1.0)
        
        Returns:
            True if updated successfully
        """
        try:
            with self.connection.cursor() as cur:
                update_fields = ["sacred_status = %s"]
                params = [sacred_status]
                
                if orthodoxy_score is not None:
                    update_fields.append("orthodoxy_score = %s")
                    params.append(orthodoxy_score)
                
                if divine_results is not None:
                    update_fields.append("divine_results = %s")
                    params.append(psycopg2.extras.Json(divine_results))
                
                if penance_progress is not None:
                    update_fields.append("penance_progress = %s")
                    params.append(penance_progress)
                
                # Add completed timestamp if status is terminal
                if sacred_status in ["blessed", "heretical", "failed"]:
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                params.append(confession_id)
                
                query = f"""
                    UPDATE confessions
                    SET {', '.join(update_fields)}
                    WHERE confession_id = %s
                """
                
                cur.execute(query, params)
                self.connection.commit()
                
                logger.info("✅ Confession updated", 
                           confession_id=confession_id, 
                           status=sacred_status)
                
                return cur.rowcount > 0
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"💀 Failed to update confession: {e}")
            raise
    
    async def get_recent_confessions(
        self, 
        limit: int = 10,
        event_type: Optional[str] = None,
        service: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent confessions with optional filters.
        
        Args:
            limit: Maximum records to return
            event_type: Filter by event type
            service: Filter by service name
        
        Returns:
            List of confession dicts
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if event_type:
                    where_clauses.append("event_type = %s")
                    params.append(event_type)
                
                if service:
                    where_clauses.append("service = %s")
                    params.append(service)
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                params.append(limit)
                
                query = f"""
                    SELECT *
                    FROM confessions
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"💀 Failed to get recent confessions: {e}")
            raise
    
    # =========================================================================
    # SACRED RECORDS (EVENT LOG)
    # =========================================================================
    
    async def log_sacred_record(
        self,
        event_type: str,
        service: Optional[str] = None,
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a sacred record (event).
        
        Args:
            event_type: Type of event
            service: Source service
            status: Event status
            details: Additional event data (JSONB)
        
        Returns:
            Record ID
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO sacred_records (event_type, service, status, details)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (event_type, service, status, 
                     psycopg2.extras.Json(details) if details else None))
                
                self.connection.commit()
                record_id = cur.fetchone()[0]
                
                logger.debug("📝 Sacred record logged", 
                            event_type=event_type, 
                            record_id=record_id)
                
                return record_id
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"💀 Failed to log sacred record: {e}")
            raise
    
    async def get_recent_records(
        self,
        limit: int = 10,
        event_type: Optional[str] = None,
        service: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent sacred records with filters.
        
        Args:
            limit: Maximum records
            event_type: Filter by event type
            service: Filter by service
        
        Returns:
            List of record dicts
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = []
                params = []
                
                if event_type:
                    where_clauses.append("event_type = %s")
                    params.append(event_type)
                
                if service:
                    where_clauses.append("service = %s")
                    params.append(service)
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                params.append(limit)
                
                query = f"""
                    SELECT *
                    FROM sacred_records
                    WHERE {where_sql}
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"💀 Failed to get recent records: {e}")
            raise
    
    # =========================================================================
    # AUDIT FINDINGS
    # =========================================================================
    
    async def add_audit_finding(
        self,
        confession_id: str,
        finding_type: str,
        severity: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add an audit finding to a confession.
        
        Args:
            confession_id: Related confession
            finding_type: Type (violation, warning, blessing)
            severity: Severity (critical, high, medium, low)
            message: Finding description
            context: Additional context (JSONB)
        
        Returns:
            Finding ID
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO audit_findings 
                    (confession_id, finding_type, severity, message, context)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (confession_id, finding_type, severity, message,
                     psycopg2.extras.Json(context) if context else None))
                
                self.connection.commit()
                finding_id = cur.fetchone()[0]
                
                logger.debug("📋 Audit finding added", 
                            confession_id=confession_id,
                            finding_type=finding_type)
                
                return finding_id
        
        except Exception as e:
            self.connection.rollback()
            logger.error(f"💀 Failed to add audit finding: {e}")
            raise
    
    async def get_confession_findings(
        self, 
        confession_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all audit findings for a confession.
        
        Args:
            confession_id: Confession identifier
        
        Returns:
            List of finding dicts
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM audit_findings
                    WHERE confession_id = %s
                    ORDER BY timestamp DESC
                """, (confession_id,))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"💀 Failed to get confession findings: {e}")
            raise
    
    # =========================================================================
    # HEALTH & DIAGNOSTICS
    # =========================================================================
    
    def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            True if connected and responsive
        """
        try:
            result = self.pg.fetch_scalar("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"💀 Database health check failed: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        self.pg.close()
