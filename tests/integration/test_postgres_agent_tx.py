"""
Integration Test — PostgresAgent transaction commit + rollback.

Uses a mock psycopg2 connection pool to verify execute, fetch,
fetch_one, and transaction semantics without a running PostgreSQL.

Markers: integration
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from contextlib import contextmanager

from core.agents.postgres_agent import PostgresAgent


@pytest.fixture(autouse=True)
def reset_pool():
    """Reset the module-level pool between tests."""
    import core.agents.postgres_agent as pg_mod
    original_pool = pg_mod._pool
    original_params = pg_mod._pool_db_params
    pg_mod._pool = None
    pg_mod._pool_db_params = None
    yield
    pg_mod._pool = original_pool
    pg_mod._pool_db_params = original_params


@pytest.fixture
def mock_conn():
    """Create a mock psycopg2 connection."""
    conn = MagicMock()
    conn.closed = False
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


@pytest.fixture
def pg(mock_conn):
    """Create a PostgresAgent with mocked pool."""
    conn, cursor = mock_conn
    mock_pool = MagicMock()
    mock_pool.closed = False
    mock_pool.getconn.return_value = conn

    with patch("core.agents.postgres_agent._get_pool", return_value=mock_pool):
        agent = PostgresAgent(
            host="localhost", port="5432", dbname="test",
            user="test", password="test",
        )
        agent._connection = conn
    return agent, conn, cursor


class TestExecute:
    """PostgresAgent.execute() — CREATE/INSERT/UPDATE/DELETE."""

    def test_execute_success_returns_true(self, pg):
        agent, conn, cursor = pg
        result = agent.execute("INSERT INTO t (id) VALUES (%s)", ("1",))
        assert result is True
        conn.commit.assert_called_once()

    def test_execute_error_returns_false_and_rolls_back(self, pg):
        agent, conn, cursor = pg
        cursor.execute.side_effect = Exception("SQL error")
        result = agent.execute("BAD SQL")
        assert result is False
        conn.rollback.assert_called()


class TestFetch:
    """PostgresAgent.fetch() — SELECT multiple rows."""

    def test_fetch_returns_list_of_dicts(self, pg):
        agent, conn, cursor = pg
        cursor.fetchall.return_value = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        rows = agent.fetch("SELECT * FROM t")
        assert len(rows) == 2
        assert rows[0]["id"] == 1

    def test_fetch_error_returns_empty_list(self, pg):
        agent, conn, cursor = pg
        cursor.execute.side_effect = Exception("Query failed")
        rows = agent.fetch("SELECT 1")
        assert rows == []


class TestFetchOne:
    """PostgresAgent.fetch_one() — SELECT single row."""

    def test_fetch_one_returns_dict(self, pg):
        agent, conn, cursor = pg
        cursor.fetchone.return_value = {"id": 1, "value": "test"}
        row = agent.fetch_one("SELECT * FROM t WHERE id = %s", (1,))
        assert row == {"id": 1, "value": "test"}

    def test_fetch_one_no_result_returns_none(self, pg):
        agent, conn, cursor = pg
        cursor.fetchone.return_value = None
        row = agent.fetch_one("SELECT * FROM t WHERE id = %s", (999,))
        assert row is None


class TestTransaction:
    """PostgresAgent.transaction() — context manager commit/rollback."""

    def test_transaction_commits_on_success(self, pg):
        agent, conn, cursor = pg
        with agent.transaction():
            agent.execute("INSERT INTO t VALUES (%s)", ("1",))

        # transaction() calls commit at the end
        assert conn.commit.call_count >= 1

    def test_transaction_rolls_back_on_exception(self, pg):
        agent, conn, cursor = pg

        with pytest.raises(ValueError, match="bad data"):
            with agent.transaction():
                agent.execute("INSERT INTO t VALUES (%s)", ("1",))
                raise ValueError("bad data")

        conn.rollback.assert_called()


class TestTableExists:
    """PostgresAgent.table_exists() check."""

    def test_table_exists_returns_true(self, pg):
        agent, conn, cursor = pg
        cursor.fetchone.return_value = {"exists": True}
        assert agent.table_exists("events") is True

    def test_table_not_found_returns_false(self, pg):
        agent, conn, cursor = pg
        cursor.fetchone.return_value = {"exists": False}
        assert agent.table_exists("nonexistent") is False
