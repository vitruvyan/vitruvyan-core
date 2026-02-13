"""
Codex Hunters - Inspector Consumer
===================================

Pure cross-store consistency verification.
NO I/O — receives record counts and ID sets as input,
returns consistency scores, orphan lists, recommendations,
and healing decisions.

Restored from legacy inspector.py (commit 96d3c88, 699 lines)
as a domain-agnostic, I/O-free consumer following SACRED_ORDER_PATTERN.

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    CodexConfig,
    ConsistencyStatus,
    CollectionPairInput,
    CollectionConsistency,
    InspectionReport,
)

logger = logging.getLogger(__name__)

# ── Default thresholds (overridable via config) ──────────────────────────

DEFAULT_THRESHOLDS = {
    "excellent": 0.95,
    "good": 0.85,
    "poor": 0.70,
    "critical": 0.50,
}

DEFAULT_HEALING_THRESHOLD = 0.50  # trigger healing below this


class InspectorConsumer(BaseConsumer):
    """
    Cross-store consistency inspector.

    Given count/ID data from two mirrored stores (e.g. PostgreSQL ↔ Qdrant),
    computes:
    - Per-collection consistency scores
    - Orphan detection (IDs present in one store but not the other)
    - Status classification (excellent / good / poor / critical / empty)
    - Overall weighted score
    - Recommendations and healing decisions

    All computation is pure — no database access, no network calls.
    The LIVELLO 2 adapter is responsible for:
    - Fetching counts and ID sets from actual stores
    - Triggering healing expeditions when ``needs_healing`` is True
    """

    def __init__(
        self,
        config: CodexConfig = None,
        *,
        thresholds: Optional[Dict[str, float]] = None,
        healing_threshold: Optional[float] = None,
    ):
        super().__init__(config)
        self._thresholds = thresholds or dict(DEFAULT_THRESHOLDS)
        self._healing_threshold = (
            healing_threshold
            if healing_threshold is not None
            else DEFAULT_HEALING_THRESHOLD
        )
        # Running statistics (pure counters, no I/O)
        self._total_inspections = 0
        self._total_inconsistencies = 0
        self._consistency_scores: List[float] = []

    # ── Main entry point ─────────────────────────────────────────────────

    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Run a full consistency inspection.

        Expected input::

            {
                "collections": [
                    {
                        "collection_name": "my_collection",
                        "source_a_count": 150,
                        "source_b_count": 145,
                        "source_a_ids": ["id1", "id2", ...],   # optional
                        "source_b_ids": ["id1", "id3", ...],   # optional
                        "metadata": {}                         # optional
                    },
                    ...
                ]
            }

        Returns:
            ProcessResult with ``data["report"]`` containing an
            :class:`InspectionReport`.
        """
        start = datetime.utcnow()

        # ── validate ────────────────────────────────────────────────────
        errors = self.validate_input(data, ["collections"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)

        raw_collections = data["collections"]
        if not isinstance(raw_collections, list):
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=["'collections' must be a list"],
            )

        if len(raw_collections) == 0:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=["'collections' list is empty"],
            )

        # ── parse inputs ────────────────────────────────────────────────
        pairs: List[CollectionPairInput] = []
        parse_errors: List[str] = []
        for idx, raw in enumerate(raw_collections):
            try:
                pair = self._parse_pair(raw, idx)
                pairs.append(pair)
            except (KeyError, TypeError, ValueError) as exc:
                parse_errors.append(f"Collection [{idx}]: {exc}")

        if parse_errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=parse_errors)

        # ── compute per-collection consistency ──────────────────────────
        results: List[CollectionConsistency] = []
        warnings: List[str] = []
        for pair in pairs:
            cc = self._evaluate_pair(pair)
            results.append(cc)
            if cc.status in (ConsistencyStatus.POOR, ConsistencyStatus.CRITICAL):
                warnings.append(
                    f"{pair.collection_name}: {cc.status.value} "
                    f"(score={cc.consistency_score:.2%})"
                )

        # ── aggregate ───────────────────────────────────────────────────
        report = self._build_report(results)

        # ── bookkeeping ─────────────────────────────────────────────────
        self._total_inspections += 1
        self._consistency_scores.append(report.overall_score)
        if report.overall_status in (
            ConsistencyStatus.POOR,
            ConsistencyStatus.CRITICAL,
        ):
            self._total_inconsistencies += 1

        elapsed_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        self._record_success()

        return ProcessResult(
            success=True,
            data={
                "report": report,
                "report_dict": report.to_dict(),
            },
            warnings=warnings,
            processing_time_ms=elapsed_ms,
        )

    # ── Parse helpers ────────────────────────────────────────────────────

    @staticmethod
    def _parse_pair(raw: Dict[str, Any], idx: int) -> CollectionPairInput:
        """
        Parse a raw dict into a ``CollectionPairInput``.
        Raises on missing / invalid required fields.
        """
        name = raw.get("collection_name")
        if not name:
            raise ValueError(f"'collection_name' missing or empty")

        a_count = int(raw.get("source_a_count", 0))
        b_count = int(raw.get("source_b_count", 0))

        a_ids = [str(i) for i in raw.get("source_a_ids", [])]
        b_ids = [str(i) for i in raw.get("source_b_ids", [])]

        return CollectionPairInput(
            collection_name=name,
            source_a_count=a_count,
            source_b_count=b_count,
            source_a_ids=a_ids,
            source_b_ids=b_ids,
            metadata=raw.get("metadata", {}),
        )

    # ── Per-collection evaluation ────────────────────────────────────────

    def _evaluate_pair(self, pair: CollectionPairInput) -> CollectionConsistency:
        """
        Compute consistency for a single collection pair.
        """
        score = self._compute_score(pair.source_a_count, pair.source_b_count)
        status = self._classify(score, pair.source_a_count, pair.source_b_count)

        # Orphan detection (only when ID lists provided)
        orphans_a: List[str] = []
        orphans_b: List[str] = []
        if pair.source_a_ids or pair.source_b_ids:
            set_a = set(pair.source_a_ids)
            set_b = set(pair.source_b_ids)
            orphans_a = sorted(set_a - set_b)  # in A but not in B
            orphans_b = sorted(set_b - set_a)  # in B but not in A

        return CollectionConsistency(
            collection_name=pair.collection_name,
            source_a_count=pair.source_a_count,
            source_b_count=pair.source_b_count,
            consistency_score=score,
            status=status,
            orphans_a=orphans_a,
            orphans_b=orphans_b,
            metadata=pair.metadata,
        )

    # ── Scoring ──────────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(count_a: int, count_b: int) -> float:
        """
        Ratio-based consistency score.

        ``min(a, b) / max(a, b)`` — ranges from 0.0 to 1.0.
        Returns 1.0 when both counts are zero (vacuously consistent).
        """
        if count_a == 0 and count_b == 0:
            return 1.0
        larger = max(count_a, count_b)
        if larger == 0:
            return 1.0
        return min(count_a, count_b) / larger

    def _classify(
        self, score: float, count_a: int, count_b: int
    ) -> ConsistencyStatus:
        """
        Map a consistency score to a status label.
        """
        if count_a == 0 and count_b == 0:
            return ConsistencyStatus.EMPTY

        if score >= self._thresholds["excellent"]:
            return ConsistencyStatus.EXCELLENT
        if score >= self._thresholds["good"]:
            return ConsistencyStatus.GOOD
        if score >= self._thresholds["poor"]:
            return ConsistencyStatus.POOR
        if score >= self._thresholds["critical"]:
            return ConsistencyStatus.CRITICAL
        return ConsistencyStatus.CRITICAL  # below lowest threshold is still critical

    # ── Report aggregation ───────────────────────────────────────────────

    def _build_report(
        self, results: List[CollectionConsistency]
    ) -> InspectionReport:
        """
        Aggregate per-collection results into an overall inspection report.
        """
        if not results:
            return InspectionReport(
                overall_score=1.0,
                overall_status=ConsistencyStatus.EMPTY,
                collections=[],
                recommendations=["No collections to inspect."],
                needs_healing=False,
            )

        # Weighted average (weight = max count of each pair)
        total_weight = 0.0
        weighted_sum = 0.0
        for cc in results:
            weight = max(cc.source_a_count, cc.source_b_count, 1)
            weighted_sum += cc.consistency_score * weight
            total_weight += weight

        overall = weighted_sum / total_weight if total_weight > 0 else 1.0
        overall_status = self._classify(
            overall,
            sum(c.source_a_count for c in results),
            sum(c.source_b_count for c in results),
        )

        recommendations = self._generate_recommendations(overall, results)
        needs_healing = overall < self._healing_threshold

        return InspectionReport(
            overall_score=overall,
            overall_status=overall_status,
            collections=results,
            recommendations=recommendations,
            needs_healing=needs_healing,
        )

    # ── Recommendations ──────────────────────────────────────────────────

    def _generate_recommendations(
        self,
        overall: float,
        results: List[CollectionConsistency],
    ) -> List[str]:
        """
        Generate human-readable recommendations based on inspection results.
        """
        recs: List[str] = []

        # Overall assessment
        if overall >= self._thresholds["excellent"]:
            recs.append("Archives in excellent condition. No action required.")
        elif overall >= self._thresholds["good"]:
            recs.append(
                "Minor inconsistencies detected. Consider scheduling a "
                "healing expedition for affected collections."
            )
        elif overall >= self._thresholds["poor"]:
            recs.append(
                "Significant inconsistencies detected. Schedule a healing "
                "expedition within 24 hours."
            )
        else:
            recs.append(
                "CRITICAL: Severe data inconsistency. Immediate healing "
                "expedition required."
            )

        # Per-collection advice
        for cc in results:
            if cc.status == ConsistencyStatus.CRITICAL:
                recs.append(
                    f"  ⚠ {cc.collection_name}: CRITICAL "
                    f"(score={cc.consistency_score:.2%}, "
                    f"orphans_a={len(cc.orphans_a)}, "
                    f"orphans_b={len(cc.orphans_b)})"
                )
            elif cc.status == ConsistencyStatus.POOR:
                recs.append(
                    f"  ▲ {cc.collection_name}: poor consistency "
                    f"(score={cc.consistency_score:.2%})"
                )

        return recs

    # ── Statistics (pure counters) ───────────────────────────────────────

    def get_inspection_stats(self) -> Dict[str, Any]:
        """
        Return accumulated inspection statistics.
        """
        avg = (
            sum(self._consistency_scores) / len(self._consistency_scores)
            if self._consistency_scores
            else 0.0
        )
        return {
            **self.get_stats(),
            "total_inspections": self._total_inspections,
            "total_inconsistencies": self._total_inconsistencies,
            "average_consistency": round(avg, 4),
            "healing_threshold": self._healing_threshold,
            "thresholds": dict(self._thresholds),
        }
