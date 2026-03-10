"""Neural Engine persistence adapter (service layer)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

try:
    from core.agents.postgres_agent import PostgresAgent
except ModuleNotFoundError:
    from vitruvyan_core.core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class NeuralEnginePersistence:
    """Persists screening runs in a generic JSON table."""

    def __init__(self, pg_agent: PostgresAgent | None = None):
        self._pg = pg_agent or PostgresAgent()
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._pg.execute(
            """
            CREATE TABLE IF NOT EXISTS neural_engine_runs (
                id BIGSERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                profile TEXT NOT NULL,
                top_k INT NOT NULL,
                stratification_mode TEXT NOT NULL,
                payload JSONB NOT NULL
            )
            """
        )

    def persist_screen_result(self, result: Dict[str, Any]) -> int | None:
        row = self._pg.fetch_one(
            """
            INSERT INTO neural_engine_runs (profile, top_k, stratification_mode, payload)
            VALUES (%s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            (
                result.get("profile", "unknown"),
                int(result.get("top_k", 0) or 0),
                result.get("stratification_mode", "global"),
                json.dumps(result),
            ),
        )
        run_id = int(row["id"]) if row and "id" in row else None
        if run_id is not None:
            logger.info("Persisted neural_engine run id=%s", run_id)
        return run_id

