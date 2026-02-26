"""
DSE Service — Persistence Adapter (LIVELLO 2)
==============================================

ONLY I/O point: PostgresAgent + QdrantAgent.
All DB operations pass through this module.
LIVELLO 1 domain code never accesses these agents directly.

Last updated: Feb 26, 2026
"""

import logging
from typing import Any, Dict, List, Optional

from core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class DSEPersistenceAdapter:
    """Wraps PostgresAgent for DSE-specific operations."""

    def __init__(self, postgres: Optional[PostgresAgent] = None) -> None:
        self.pg = postgres or PostgresAgent()

    # ------------------------------------------------------------------
    # ML strategy selection
    # ------------------------------------------------------------------

    def get_best_sampling_strategy(
        self,
        scenario_id: str = "SCN_BASE_01",
        metric: str = "score_fema",
    ) -> Optional[Dict[str, Any]]:
        """
        Query historical design points for the best-performing strategy.

        Returns dict with keys: sampling_plan, avg_score, sample_count
        or None if no historical data available.
        """
        try:
            rows = self.pg.fetch(
                """
                SELECT sampling_plan,
                       AVG(score_fema) AS avg_score,
                       COUNT(*)        AS sample_count
                FROM   dse_design_points
                WHERE  scenario_id = %s
                  AND  score_fema  IS NOT NULL
                GROUP  BY sampling_plan
                ORDER  BY avg_score DESC
                LIMIT  1
                """,
                (scenario_id,),
            )
            if rows:
                row = rows[0]
                return {
                    "sampling_plan": row["sampling_plan"],
                    "avg_score":     float(row["avg_score"]),
                    "sample_count":  int(row["sample_count"]),
                }
        except Exception as exc:
            logger.warning("DSEPersistence.get_best_sampling_strategy failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def log_run(self, run_data: Dict[str, Any]) -> None:
        """Persist a completed DSE run record for audit trail."""
        try:
            with self.pg.transaction():
                self.pg.execute(
                    """
                    INSERT INTO dse_runs
                        (trace_id, user_id, use_case, strategy, total_design_points,
                         pareto_count, input_hash, seed, schema_version, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (trace_id) DO NOTHING
                    """,
                    (
                        run_data.get("trace_id"),
                        run_data.get("user_id"),
                        run_data.get("use_case"),
                        run_data.get("strategy"),
                        run_data.get("total_design_points"),
                        run_data.get("pareto_count"),
                        run_data.get("input_hash"),
                        run_data.get("seed"),
                        run_data.get("schema_version", "1.0.0"),
                    ),
                )
        except Exception as exc:
            logger.warning("DSEPersistence.log_run failed: %s", exc)

    def log_rejection(self, trace_id: str, reason: str, rejected_by: Optional[str] = None) -> None:
        """Persist a Conclave governance rejection."""
        try:
            with self.pg.transaction():
                self.pg.execute(
                    """
                    INSERT INTO dse_rejections (trace_id, reason, rejected_by, created_at)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (trace_id, reason, rejected_by),
                )
        except Exception as exc:
            logger.warning("DSEPersistence.log_rejection failed: %s", exc)

    # ------------------------------------------------------------------
    # Schema bootstrap (idempotent)
    # ------------------------------------------------------------------

    def ensure_schema(self) -> None:
        """Create DSE tables if they do not exist (idempotent bootstrap)."""
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS dse_runs (
                trace_id            TEXT PRIMARY KEY,
                user_id             TEXT,
                use_case            TEXT,
                strategy            TEXT,
                total_design_points INTEGER,
                pareto_count        INTEGER,
                input_hash          TEXT,
                seed                INTEGER,
                schema_version      TEXT,
                created_at          TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS dse_rejections (
                id          BIGSERIAL PRIMARY KEY,
                trace_id    TEXT NOT NULL,
                reason      TEXT,
                rejected_by TEXT,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
            """,
        ]
        try:
            for stmt in ddl:
                self.pg.execute(stmt)
            logger.info("DSEPersistence: schema ensured")
        except Exception as exc:
            logger.warning("DSEPersistence.ensure_schema failed: %s", exc)
