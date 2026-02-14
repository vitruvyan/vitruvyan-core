"""PostgreSQL read adapter for reconciliation snapshots."""

from __future__ import annotations

from typing import Any, TypedDict

from core.agents.postgres_agent import PostgresAgent


class PgEntityRecord(TypedDict):
    """Minimal canonical record used by reconciliation flow."""

    id: str
    version: Any | None
    updated_at: str | None
    metadata: dict[str, Any]


class PgReader:
    """
    Read-only PostgreSQL adapter for canonical entity snapshots.

    This adapter intentionally contains no reconciliation logic.
    """

    def __init__(self, pg_agent: PostgresAgent | None = None):
        self.pg = pg_agent or PostgresAgent()

    def read_entities(
        self,
        table: str = "entities",
        limit: int = 1000,
        id_column: str = "id",
        version_column: str = "version",
        updated_at_column: str = "updated_at",
        metadata_columns: tuple[str, ...] = ("embedded",),
    ) -> tuple[PgEntityRecord, ...]:
        """Read canonical entity state with optional version metadata columns."""
        columns = self._table_columns(table)
        if id_column not in columns:
            return ()

        metadata_keys = tuple(
            col
            for col in metadata_columns
            if col in columns and col not in {id_column, version_column, updated_at_column}
        )

        select_parts = [f"{id_column}::text AS id"]
        select_parts.append(
            f"{version_column} AS version" if version_column in columns else "NULL AS version"
        )
        select_parts.append(
            f"{updated_at_column}::text AS updated_at"
            if updated_at_column in columns
            else "NULL AS updated_at"
        )
        select_parts.extend(f"{key} AS {key}" for key in metadata_keys)

        query = f"SELECT {', '.join(select_parts)} FROM {table} LIMIT %s;"
        rows = self.pg.fetch(query, (limit,))

        records: list[PgEntityRecord] = []
        for row in rows:
            metadata = {key: row.get(key) for key in metadata_keys}
            records.append(
                {
                    "id": str(row.get("id")),
                    "version": row.get("version"),
                    "updated_at": self._to_str_or_none(row.get("updated_at")),
                    "metadata": metadata,
                }
            )

        return tuple(records)

    def _table_columns(self, table: str) -> set[str]:
        """List table columns from information_schema for safe optional selects."""
        rows = self.pg.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s;
            """,
            (table,),
        )
        return {str(row.get("column_name")) for row in rows if row.get("column_name")}

    @staticmethod
    def _to_str_or_none(value: Any) -> str | None:
        return None if value is None else str(value)
