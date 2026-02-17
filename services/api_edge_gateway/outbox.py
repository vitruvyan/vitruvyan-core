from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .contracts import EdgeEnvelopeStored


@dataclass(frozen=True)
class OutboxRecord:
    id: int
    envelope: EdgeEnvelopeStored
    attempts: int
    created_utc: str
    last_attempt_utc: str | None


class SQLiteOutbox:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edge_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    envelope_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_utc TEXT NOT NULL,
                    last_attempt_utc TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_edge_outbox_status ON edge_outbox(status)"
            )
            conn.commit()

    def enqueue(self, envelope: EdgeEnvelopeStored) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO edge_outbox (envelope_json, status, attempts, created_utc)
                VALUES (?, 'pending', 0, ?)
                """,
                (envelope.model_dump_json(), now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def fetch_pending(self, limit: int) -> List[OutboxRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, envelope_json, attempts, created_utc, last_attempt_utc
                FROM edge_outbox
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        records: List[OutboxRecord] = []
        for row in rows:
            envelope = EdgeEnvelopeStored.model_validate_json(row["envelope_json"])
            records.append(
                OutboxRecord(
                    id=row["id"],
                    envelope=envelope,
                    attempts=row["attempts"],
                    created_utc=row["created_utc"],
                    last_attempt_utc=row["last_attempt_utc"],
                )
            )
        return records

    def mark_attempt(self, record_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE edge_outbox
                SET attempts = attempts + 1, last_attempt_utc = ?
                WHERE id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), record_id),
            )
            conn.commit()

    def mark_sent(self, record_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE edge_outbox SET status = 'sent' WHERE id = ?", (record_id,))
            conn.commit()

    def mark_pending(self, record_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE edge_outbox SET status = 'pending' WHERE id = ?", (record_id,))
            conn.commit()

    def pending_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM edge_outbox WHERE status = 'pending'"
            ).fetchone()
            return int(row["c"])

    def sent_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM edge_outbox WHERE status = 'sent'").fetchone()
            return int(row["c"])
