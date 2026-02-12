"""
VEE Memory Adapter 3.0 — Schema-neutral explainability persistence.

Stores and retrieves explanations from PostgreSQL.
Schema is domain-agnostic:
  - entity_id VARCHAR(255) — fits any identifier scheme
  - domain_tag VARCHAR(100) — enables multi-domain coexistence
  - analysis_data JSONB — full analysis snapshot for audit

No Qdrant pseudo-embeddings. Semantic search should be handled by VSGS,
not by VEE memory (separation of concerns).
"""

import json
import logging
from datetime import datetime, timedelta
from dataclasses import asdict
from typing import Dict, List, Any, Optional

from .types import AnalysisResult, ExplanationLevels, HistoricalExplanation

logger = logging.getLogger(__name__)

# Safe import — PostgresAgent may not be available in unit tests
try:
    from core.agents.postgres_agent import PostgresAgent
except ImportError:
    PostgresAgent = None


class VEEMemoryAdapter:
    """Schema-neutral persistence for VEE explanations.

    Uses PostgresAgent for all I/O operations.
    Lazy connection — no DB access until first store/retrieve call.
    """

    TABLE = "vee_explanations_v3"

    def __init__(self, domain_tag: str = ""):
        self._pg = None
        self.domain_tag = domain_tag
        self.max_results = 5
        self.lookback_days = 90

    @property
    def pg(self):
        """Lazy PostgreSQL connection."""
        if self._pg is None and PostgresAgent is not None:
            try:
                self._pg = PostgresAgent()
                self._ensure_schema()
            except Exception as e:
                logger.warning(f"PostgreSQL unavailable: {e}")
        return self._pg

    # ── Public API ───────────────────────────────────────────────────────────

    def store(self, analysis: AnalysisResult,
              explanation: ExplanationLevels) -> bool:
        """Store an explanation with full analysis metadata."""
        if not self.pg:
            return False
        try:
            self.pg.execute(f"""
                INSERT INTO {self.TABLE} (
                    entity_id, domain_tag, summary, technical, detailed,
                    confidence, dominant_factor, direction,
                    metrics_count, overall_intensity, analysis_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                analysis.entity_id,
                self.domain_tag,
                explanation.summary,
                explanation.technical,
                explanation.detailed,
                analysis.overall_confidence,
                analysis.primary_factor,
                analysis.direction,
                analysis.metrics_count,
                analysis.overall_intensity,
                json.dumps(asdict(analysis), default=str),
            ))
            logger.debug(f"Stored explanation for {analysis.entity_id}")
            return True
        except Exception as e:
            logger.error(f"Store failed for {analysis.entity_id}: {e}")
            return False

    def retrieve(self, entity_id: str,
                 limit: Optional[int] = None) -> List[HistoricalExplanation]:
        """Retrieve historical explanations for an entity."""
        if not self.pg:
            return []
        try:
            limit = limit or self.max_results
            cutoff = datetime.now() - timedelta(days=self.lookback_days)

            params = [entity_id, cutoff, limit]
            domain_filter = ""
            if self.domain_tag:
                domain_filter = " AND domain_tag = %s"
                params = [entity_id, cutoff, self.domain_tag, limit]

            rows = self.pg.fetch(f"""
                SELECT id, entity_id, summary, technical, detailed,
                       created_at, confidence, dominant_factor, direction,
                       metrics_count, overall_intensity, domain_tag
                FROM {self.TABLE}
                WHERE entity_id = %s AND created_at >= %s{domain_filter}
                ORDER BY created_at DESC
                LIMIT %s
            """, tuple(params))

            return [self._row_to_historical(row) for row in (rows or [])]
        except Exception as e:
            logger.error(f"Retrieve failed for {entity_id}: {e}")
            return []

    def enrich(self, explanation: ExplanationLevels,
               historical: List[HistoricalExplanation]) -> ExplanationLevels:
        """Enrich explanation with historical context."""
        if not historical:
            return explanation
        try:
            most_recent = max(historical, key=lambda h: h.created_at)
            explanation.contextualized = (
                f"Consistent with {len(historical)} prior evaluations of "
                f"{explanation.entity_id}. Most recent "
                f"({most_recent.created_at.strftime('%Y-%m-%d')}) "
                f"highlighted {most_recent.dominant_factor} as dominant factor."
            )
            explanation.historical_reference = most_recent.summary
        except Exception as e:
            logger.warning(f"Enrichment failed: {e}")
        return explanation

    def get_trends(self, entity_id: str,
                   days: int = 30) -> Dict[str, Any]:
        """Analyze explanation trends for an entity."""
        if not self.pg:
            return {}
        try:
            cutoff = datetime.now() - timedelta(days=days)
            rows = self.pg.fetch(f"""
                SELECT dominant_factor, direction, confidence,
                       overall_intensity
                FROM {self.TABLE}
                WHERE entity_id = %s AND created_at >= %s
                ORDER BY created_at DESC
            """, (entity_id, cutoff))

            if not rows:
                return {}

            factors = [r[0] for r in rows]
            directions = [r[1] for r in rows if r[1]]
            confidences = [r[2] for r in rows if r[2]]
            intensities = [r[3] for r in rows if r[3]]

            return {
                "total": len(rows),
                "period_days": days,
                "top_factor": (max(set(factors), key=factors.count)
                               if factors else None),
                "top_direction": (max(set(directions), key=directions.count)
                                  if directions else None),
                "avg_confidence": (sum(confidences) / len(confidences)
                                   if confidences else 0),
                "avg_intensity": (sum(intensities) / len(intensities)
                                  if intensities else 0),
            }
        except Exception as e:
            logger.error(f"Trends failed for {entity_id}: {e}")
            return {}

    # ── Internals ────────────────────────────────────────────────────────────

    def _ensure_schema(self):
        """Create table if it doesn't exist."""
        try:
            self.pg.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE} (
                    id SERIAL PRIMARY KEY,
                    entity_id VARCHAR(255) NOT NULL,
                    domain_tag VARCHAR(100) DEFAULT '',
                    summary TEXT NOT NULL,
                    technical TEXT NOT NULL,
                    detailed TEXT NOT NULL,
                    confidence FLOAT DEFAULT 0.0,
                    dominant_factor VARCHAR(255),
                    direction VARCHAR(50),
                    metrics_count INTEGER DEFAULT 0,
                    overall_intensity FLOAT DEFAULT 0.0,
                    analysis_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.pg.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE}_entity "
                f"ON {self.TABLE}(entity_id)")
            self.pg.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE}_created "
                f"ON {self.TABLE}(created_at)")
        except Exception as e:
            logger.warning(f"Schema creation failed: {e}")

    def _row_to_historical(self, row) -> HistoricalExplanation:
        """Convert database row to HistoricalExplanation."""
        return HistoricalExplanation(
            id=row[0],
            entity_id=row[1],
            summary=row[2],
            technical=row[3],
            detailed=row[4],
            created_at=row[5],
            confidence=row[6] or 0.0,
            dominant_factor=row[7] or "",
            direction=row[8],
            metrics_count=row[9] or 0,
            overall_intensity=row[10] or 0.0,
            domain_tag=row[11] or "",
        )
