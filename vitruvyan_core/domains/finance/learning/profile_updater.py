"""
Finance learning profile updater.

Processes captured feedback events and updates user_learning_profile incrementally.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.agents.postgres_agent import PostgresAgent


logger = logging.getLogger(__name__)


class LearningProfileUpdater:
    """Incremental updater from user_feedback_events to user_learning_profile."""

    def __init__(self, batch_size: int = 500, postgres_agent: Optional[PostgresAgent] = None):
        self.batch_size = max(1, int(batch_size))
        self.postgres = postgres_agent or PostgresAgent()

    def run_once(self) -> Dict[str, int]:
        """
        Process pending events once.

        Returns:
            Summary counters.
        """
        users = self._pending_users()
        processed_users = 0
        processed_events = 0

        for user_id in users:
            processed_for_user = self._process_user(user_id)
            if processed_for_user > 0:
                processed_users += 1
                processed_events += processed_for_user

        summary = {
            "pending_users": len(users),
            "processed_users": processed_users,
            "processed_events": processed_events,
        }
        logger.info("LearningProfileUpdater run_once: %s", summary)
        return summary

    def _pending_users(self) -> List[str]:
        rows = self.postgres.fetch(
            """
            SELECT DISTINCT f.user_id
            FROM user_feedback_events f
            LEFT JOIN user_learning_profile p ON p.user_id = f.user_id
            WHERE f.id > COALESCE(p.last_processed_event_id, 0)
            ORDER BY f.user_id
            """
        )
        return [row["user_id"] for row in rows]

    def _process_user(self, user_id: str) -> int:
        profile = self._load_profile(user_id)
        last_processed_event_id = int(profile.get("last_processed_event_id", 0) or 0)
        total_processed = 0
        latest_feedback_at = profile.get("last_feedback_at")

        while True:
            events = self.postgres.fetch(
                """
                SELECT id, event_name, feedback_signal, feedback_value, payload, created_at
                FROM user_feedback_events
                WHERE user_id = %s
                  AND id > %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (user_id, last_processed_event_id, self.batch_size),
            )
            if not events:
                break

            profile, max_id, batch_latest_feedback_at = self._apply_events(profile, events)
            last_processed_event_id = max_id
            latest_feedback_at = batch_latest_feedback_at or latest_feedback_at
            total_processed += len(events)

            self._save_profile(
                user_id=user_id,
                profile=profile,
                last_processed_event_id=last_processed_event_id,
                last_feedback_at=latest_feedback_at,
            )

        return total_processed

    def _load_profile(self, user_id: str) -> Dict[str, Any]:
        row = self.postgres.fetch_one(
            """
            SELECT
                profile_version,
                inferred_risk_tolerance,
                preference_vector,
                behavior_metrics,
                model_overrides,
                last_processed_event_id,
                last_feedback_at
            FROM user_learning_profile
            WHERE user_id = %s
            """,
            (user_id,),
        )

        if not row:
            return {
                "profile_version": 1,
                "inferred_risk_tolerance": None,
                "preference_vector": {},
                "behavior_metrics": {},
                "model_overrides": {},
                "last_processed_event_id": 0,
                "last_feedback_at": None,
            }

        return {
            "profile_version": int(row.get("profile_version", 1) or 1),
            "inferred_risk_tolerance": row.get("inferred_risk_tolerance"),
            "preference_vector": row.get("preference_vector") or {},
            "behavior_metrics": row.get("behavior_metrics") or {},
            "model_overrides": row.get("model_overrides") or {},
            "last_processed_event_id": int(row.get("last_processed_event_id", 0) or 0),
            "last_feedback_at": row.get("last_feedback_at"),
        }

    def _apply_events(
        self,
        profile: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], int, Optional[datetime]]:
        behavior = profile.get("behavior_metrics") or {}
        prefs = profile.get("preference_vector") or {}
        overrides = profile.get("model_overrides") or {}

        ticker_affinity = prefs.setdefault("ticker_affinity", {})
        side_affinity = prefs.setdefault("side_affinity", {})
        risk_category_frequency = prefs.setdefault("risk_category_frequency", {})
        decision_frequency = prefs.setdefault("decision_frequency", {})
        risk_tolerance_signals = prefs.setdefault("risk_tolerance_signals", {})

        def inc(container: Dict[str, Any], key: str, amount: float = 1.0) -> None:
            container[key] = float(container.get(key, 0.0) or 0.0) + amount

        latest_created_at: Optional[datetime] = None
        max_id = 0

        for event in events:
            event_id = int(event["id"])
            max_id = max(max_id, event_id)
            latest_created_at = event.get("created_at") or latest_created_at

            event_name = str(event.get("event_name") or "")
            feedback_signal = str(event.get("feedback_signal") or "")
            payload = event.get("payload") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}

            inc(behavior, "feedback_events_total")

            if event_name == "shadow.order.executed":
                inc(behavior, "order_events_total")
                status = str(payload.get("status") or feedback_signal.replace("order_", ""))
                if status == "filled":
                    inc(behavior, "orders_filled")
                    ticker = str(payload.get("ticker") or "").upper()
                    if ticker:
                        inc(ticker_affinity, ticker, amount=1.0)
                elif status == "rejected":
                    inc(behavior, "orders_rejected")
                elif status in {"error", "execution_error"}:
                    inc(behavior, "order_errors")

                side = str(payload.get("side") or "").lower()
                if side in {"buy", "sell"}:
                    inc(side_affinity, side)

                risk_category = str(payload.get("risk_category") or "").lower()
                if risk_category:
                    inc(risk_category_frequency, risk_category)

            elif event_name == "shadow.trade.recommendation_generated":
                inc(behavior, "recommendation_events_total")
                decision = str(payload.get("decision") or "").lower()
                if decision:
                    inc(decision_frequency, decision)
                ticker = str(payload.get("ticker") or "").upper()
                if ticker:
                    inc(ticker_affinity, ticker, amount=0.2)

            elif event_name == "shadow.trade.recommendation_error":
                inc(behavior, "recommendation_errors")

            elif event_name == "portfolio.snapshot.requested":
                inc(behavior, "portfolio_views")

            elif event_name == "portfolio.history.requested":
                inc(behavior, "portfolio_history_views")

            elif event_name == "portfolio.constructed":
                inc(behavior, "portfolio_constructed")
                risk_tolerance = str(payload.get("risk_tolerance") or "").lower()
                if risk_tolerance:
                    inc(risk_tolerance_signals, risk_tolerance, amount=2.0)

            elif event_name == "portfolio.construction_error":
                inc(behavior, "portfolio_construction_errors")
                risk_tolerance = str(payload.get("risk_tolerance") or "").lower()
                if risk_tolerance:
                    inc(risk_tolerance_signals, risk_tolerance, amount=1.0)

            elif event_name == "portfolio.history_error":
                inc(behavior, "portfolio_history_errors")

        orders_filled = float(behavior.get("orders_filled", 0.0) or 0.0)
        orders_rejected = float(behavior.get("orders_rejected", 0.0) or 0.0)
        terminal_orders = orders_filled + orders_rejected
        if terminal_orders > 0:
            behavior["order_fill_rate"] = round(orders_filled / terminal_orders, 4)

        behavior["last_update_at"] = datetime.now(timezone.utc).isoformat()
        overrides["learning_worker_version"] = "v1"

        self._trim_top_n(ticker_affinity, limit=200)

        inferred_risk_tolerance = profile.get("inferred_risk_tolerance")
        if risk_tolerance_signals:
            inferred_risk_tolerance = max(
                risk_tolerance_signals.items(),
                key=lambda kv: float(kv[1]),
            )[0]

        profile["behavior_metrics"] = behavior
        profile["preference_vector"] = prefs
        profile["model_overrides"] = overrides
        profile["inferred_risk_tolerance"] = inferred_risk_tolerance
        return profile, max_id, latest_created_at

    @staticmethod
    def _trim_top_n(scores: Dict[str, Any], limit: int) -> None:
        if len(scores) <= limit:
            return
        top = sorted(scores.items(), key=lambda kv: float(kv[1]), reverse=True)[:limit]
        scores.clear()
        scores.update(top)

    def _save_profile(
        self,
        *,
        user_id: str,
        profile: Dict[str, Any],
        last_processed_event_id: int,
        last_feedback_at: Optional[datetime],
    ) -> None:
        self.postgres.execute(
            """
            INSERT INTO user_learning_profile (
                user_id,
                profile_version,
                inferred_risk_tolerance,
                preference_vector,
                behavior_metrics,
                model_overrides,
                last_processed_event_id,
                last_feedback_at,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET profile_version = user_learning_profile.profile_version + 1,
                inferred_risk_tolerance = EXCLUDED.inferred_risk_tolerance,
                preference_vector = EXCLUDED.preference_vector,
                behavior_metrics = EXCLUDED.behavior_metrics,
                model_overrides = EXCLUDED.model_overrides,
                last_processed_event_id = GREATEST(
                    user_learning_profile.last_processed_event_id,
                    EXCLUDED.last_processed_event_id
                ),
                last_feedback_at = EXCLUDED.last_feedback_at,
                updated_at = NOW()
            """,
            (
                user_id,
                int(profile.get("profile_version", 1) or 1),
                profile.get("inferred_risk_tolerance"),
                json.dumps(profile.get("preference_vector") or {}, default=str),
                json.dumps(profile.get("behavior_metrics") or {}, default=str),
                json.dumps(profile.get("model_overrides") or {}, default=str),
                int(last_processed_event_id),
                last_feedback_at,
            ),
        )
