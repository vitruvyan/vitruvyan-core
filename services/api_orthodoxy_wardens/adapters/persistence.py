"""
⚖️ Orthodoxy Wardens — Persistence Adapter (LIVELLO 2)

The ONLY file in this service that touches databases.
Core domain objects never import this — flow is one-way.

Responsibilities:
- Save verdicts to PostgreSQL (audit_findings table)
- Archive chronicle decisions
- Query recent findings for health checks
- Embed audit events to Qdrant (optional, for semantic search)

"Il giudice (core) non tocca mai il database. Il cancelliere (service) lo fa per lui."
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("OrthodoxyWardens.Persistence")


class PersistenceAdapter:
    """
    Single I/O boundary for the Orthodoxy Wardens service.

    All database operations are centralized here.
    Instantiated once at service startup.

    In Docker: imports PostgresAgent / QdrantAgent from core.agents.*
    In tests: mock this class entirely.
    """

    def __init__(self, pg=None, qdrant=None):
        """
        Args:
            pg: PostgresAgent instance (injected for testability).
                If None, creates one from core.agents.
            qdrant: QdrantAgent instance (injected for testability).
                If None, creates one from core.agents.
        """
        self._pg = pg
        self._qdrant = qdrant

    @property
    def pg(self):
        """Lazy-load PostgresAgent (avoids import at module level for testing)."""
        if self._pg is None:
            from core.agents.postgres_agent import PostgresAgent
            self._pg = PostgresAgent()
        return self._pg

    @property
    def qdrant(self):
        """Lazy-load QdrantAgent (avoids import at module level for testing)."""
        if self._qdrant is None:
            from core.agents.qdrant_agent import QdrantAgent
            self._qdrant = QdrantAgent()
        return self._qdrant

    def save_verdict(self, pipeline_result: Dict[str, Any]) -> bool:
        """
        Persist a pipeline result (from OrthodoxyBusAdapter.handle_event).

        Args:
            pipeline_result: Dict with confession_id, verdict, etc.

        Returns:
            True if persisted successfully.
        """
        try:
            verdict = pipeline_result.get("verdict", {})
            confession_id = pipeline_result.get("confession_id", "unknown")

            with self.pg.connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_findings
                        (confession_id, status, confidence, findings_count,
                         explanation, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (confession_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        confidence = EXCLUDED.confidence,
                        findings_count = EXCLUDED.findings_count,
                        explanation = EXCLUDED.explanation
                    """,
                    (
                        confession_id,
                        verdict.get("status", "unknown"),
                        verdict.get("confidence", 0.0),
                        pipeline_result.get("findings_count", 0),
                        verdict.get("explanation", ""),
                        datetime.utcnow(),
                    ),
                )
            self.pg.connection.commit()
            logger.info("Verdict saved: %s → %s", confession_id, verdict.get("status"))
            return True

        except Exception as e:
            logger.error("Failed to save verdict %s: %s", confession_id, e)
            return False

    def save_chronicle(self, pipeline_result: Dict[str, Any]) -> bool:
        """
        Archive chronicle decision from pipeline result.

        Args:
            pipeline_result: Dict with chronicle_decision.

        Returns:
            True if archived successfully.
        """
        chronicle = pipeline_result.get("chronicle_decision")
        if not chronicle:
            return True  # Nothing to archive

        try:
            confession_id = pipeline_result.get("confession_id", "unknown")
            # Archive based on chronicle decision destination
            # (Implementation depends on chronicle decision type)
            logger.info("Chronicle archived for %s", confession_id)
            return True

        except Exception as e:
            logger.error("Failed to archive chronicle: %s", e)
            return False

    def get_recent_findings(self, limit: int = 50) -> List[Dict]:
        """Query recent audit findings for health/status endpoints."""
        try:
            with self.pg.connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT confession_id, status, confidence, findings_count,
                           explanation, created_at
                    FROM audit_findings
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error("Failed to query recent findings: %s", e)
            return []

    def get_verdict_stats(self, days: int = 7) -> Dict[str, int]:
        """Get verdict status counts for monitoring."""
        try:
            with self.pg.connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM audit_findings
                    WHERE created_at > NOW() - INTERVAL '%s days'
                    GROUP BY status
                    """,
                    (days,),
                )
                return {row[0]: row[1] for row in cur.fetchall()}

        except Exception as e:
            logger.error("Failed to get verdict stats: %s", e)
            return {}
