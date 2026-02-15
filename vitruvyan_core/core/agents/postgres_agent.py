"""
PostgresAgent — Domain-Agnostic Database Interface

This is the CORE database agent. It provides ONLY generic connection
and query capabilities. Each vertical defines its own schema and 
domain-specific methods.

Usage:
    from core.agents.postgres_agent import PostgresAgent
    
    pg = PostgresAgent()
    
    # Generic execute (CREATE, INSERT, UPDATE, DELETE)
    pg.execute("CREATE TABLE IF NOT EXISTS entities (...)")
    pg.execute("INSERT INTO entities (id, name) VALUES (%s, %s)", ("E1", "Example"))
    
    # Generic fetch (SELECT)
    rows = pg.fetch("SELECT * FROM entities WHERE id = %s", ("E1",))
    row = pg.fetch_one("SELECT * FROM entities WHERE id = %s", ("E1",))
    
    # Transaction support
    with pg.transaction():
        pg.execute("INSERT ...")
        pg.execute("UPDATE ...")
    # Auto-commit on success, auto-rollback on error

Each vertical should:
1. Create its own schema (tables, indexes) on first run
2. Extend PostgresAgent with domain-specific methods if needed
3. Use environment variables for connection (POSTGRES_HOST, etc.)
"""

import os
import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool as pg_pool

# NOTE: Configuration via environment variables only.
# load_dotenv() is called in service entrypoints (main.py), not in core modules.

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level connection pool (shared by all PostgresAgent instances)
# ---------------------------------------------------------------------------
_pool: Optional[pg_pool.ThreadedConnectionPool] = None
_pool_db_params: Optional[Dict[str, str]] = None


def _get_pool(db_params: Dict[str, str]) -> pg_pool.ThreadedConnectionPool:
    """Get or create a module-level threaded connection pool."""
    global _pool, _pool_db_params

    # Reuse existing pool if params haven't changed
    if _pool is not None and not _pool.closed and _pool_db_params == db_params:
        return _pool

    min_conn = int(os.getenv("POSTGRES_POOL_MIN", "2"))
    max_conn = int(os.getenv("POSTGRES_POOL_MAX", "10"))

    _pool = pg_pool.ThreadedConnectionPool(
        minconn=min_conn,
        maxconn=max_conn,
        **db_params,
    )
    _pool_db_params = db_params
    logger.info(
        "PostgreSQL pool created: %s:%s/%s (min=%d, max=%d)",
        db_params.get("host"), db_params.get("port"),
        db_params.get("dbname"), min_conn, max_conn,
    )
    return _pool


class PostgresAgent:
    """
    Domain-agnostic PostgreSQL interface.
    
    Provides generic CRUD operations. Schema is NOT defined here —
    each vertical creates its own tables.
    """
    
    def __init__(self, 
                 host: str = None,
                 port: str = None,
                 dbname: str = None,
                 user: str = None,
                 password: str = None):
        """
        Initialize connection using params or environment variables.
        
        Uses a module-level ThreadedConnectionPool for efficient 
        connection reuse.  Pool size is controlled by:
            POSTGRES_POOL_MIN (default 2)
            POSTGRES_POOL_MAX (default 10)
        
        Environment variables (fallback):
            POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, 
            POSTGRES_USER, POSTGRES_PASSWORD
        """
        self.db_params = {
            "host": host or os.getenv("POSTGRES_HOST", "localhost"),
            "port": port or os.getenv("POSTGRES_PORT", "5432"),
            "dbname": dbname or os.getenv("POSTGRES_DB", "vitruvyan"),
            "user": user or os.getenv("POSTGRES_USER"),
            "password": password or os.getenv("POSTGRES_PASSWORD"),
        }
        
        self._pool = _get_pool(self.db_params)
        self._connection = None
    
    def _get_conn(self):
        """Get a connection from the pool (or reuse the held one)."""
        if self._connection is None or self._connection.closed:
            self._connection = self._pool.getconn()
        return self._connection

    def _put_conn(self):
        """Return the held connection to the pool."""
        if self._connection is not None and not self._connection.closed:
            self._pool.putconn(self._connection)
            self._connection = None
    
    @property
    def connection(self):
        """Get active connection from pool, reconnect if needed."""
        return self._get_conn()
    
    def execute(self, sql: str, params: Tuple = None) -> bool:
        """
        Execute a SQL statement (CREATE, INSERT, UPDATE, DELETE).
        
        Args:
            sql: SQL statement with %s placeholders
            params: Tuple of parameters
            
        Returns:
            True on success, False on error
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(sql, params)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Execute error: {e}\nSQL: {sql[:200]}")
            return False
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> bool:
        """
        Execute a SQL statement for multiple rows (batch insert).
        
        Args:
            sql: SQL statement with %s placeholders
            params_list: List of tuples with parameters
            
        Returns:
            True on success, False on error
        """
        try:
            with self.connection.cursor() as cur:
                cur.executemany(sql, params_list)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Execute many error: {e}")
            return False
    
    def fetch(self, sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows as list of dicts.
        
        Args:
            sql: SELECT statement
            params: Query parameters
            
        Returns:
            List of dicts (empty list on error)
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Fetch error: {e}")
            return []
    
    def fetch_one(self, sql: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row as dict.
        
        Args:
            sql: SELECT statement
            params: Query parameters
            
        Returns:
            Dict or None
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Fetch one error: {e}")
            return None
    
    def fetch_scalar(self, sql: str, params: Tuple = None) -> Any:
        """
        Fetch a single value.
        
        Args:
            sql: SELECT statement returning single value
            params: Query parameters
            
        Returns:
            Value or None
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Fetch scalar error: {e}")
            return None

    def fetch_paginated(
        self,
        sql: str,
        params: Tuple = None,
        page_size: int = 500,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Fetch rows in pages using a server-side cursor.

        Avoids loading the entire result set into memory — essential
        for large tables.  Yields lists of ``page_size`` dicts.

        Args:
            sql: SELECT statement
            params: Query parameters
            page_size: Rows per page (default 500)

        Yields:
            List[Dict] — one page at a time
        """
        cur_name = f"pg_paginated_{id(self)}_{os.getpid()}"
        try:
            with self.connection.cursor(name=cur_name, cursor_factory=RealDictCursor) as cur:
                cur.itersize = page_size
                cur.execute(sql, params)
                while True:
                    rows = cur.fetchmany(page_size)
                    if not rows:
                        break
                    yield [dict(r) for r in rows]
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Fetch paginated error: {e}")
            return
    
    @contextmanager
    def transaction(self):
        """
        Transaction context manager.
        
        Usage:
            with pg.transaction():
                pg.execute("INSERT ...")
                pg.execute("UPDATE ...")
            # Auto-commit on success, auto-rollback on error
        """
        try:
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        result = self.fetch_one(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            (table_name,)
        )
        return result.get("exists", False) if result else False
    
    def close(self):
        """Return connection to the pool."""
        self._put_conn()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Convenience function for quick queries
def get_postgres() -> PostgresAgent:
    """Get a PostgresAgent instance (uses shared connection pool)."""
    return PostgresAgent()
