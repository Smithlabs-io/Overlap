"""
PostgreSQL access for Overlap.

Connections come from a psycopg pool built from `DATABASE_URL`. The schema is
not created here: it comes from the migrations in `overlap/db/migrations`,
applied with dbmate, and `check_schema()` refuses to start against a database
that is behind.

Everything talks to the pool through a few helpers (`get_cursor`,
`transaction`, `execute_*`). That keeps the pool behind one seam, so moving to
an async driver later touches this module and its callers, not every query.
"""
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.numeric import Int2Dumper
from psycopg_pool import ConnectionPool

from overlap import config
from overlap.core.logging import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"


def required_schema_version() -> str:
    """Newest migration shipped with this code (its filename prefix)."""
    versions = [f.name.split("_", 1)[0] for f in MIGRATIONS_DIR.glob("*.sql")]
    if not versions:
        raise RuntimeError(f"No migrations found in {MIGRATIONS_DIR}")
    return max(versions)


# =============================================================================
# Connection Management
# =============================================================================

class _BoolAsInt(Int2Dumper):
    """Send Python bools as 0/1. Flag columns are INTEGER, and Postgres won't cast a boolean."""

    def dump(self, obj):
        return super().dump(int(obj))


def _configure(conn: psycopg.Connection) -> None:
    conn.adapters.register_dumper(bool, _BoolAsInt)


_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()

# Set while a thread is inside transaction(), so nested helper calls reuse
# that connection and see its uncommitted writes.
_tx = threading.local()


def get_pool() -> ConnectionPool:
    """Return the shared pool, opening it on first use."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                if not config.DATABASE_URL:
                    raise RuntimeError("DATABASE_URL is not set")
                _pool = ConnectionPool(
                    config.DATABASE_URL,
                    min_size=config.DB_POOL_MIN,
                    max_size=config.DB_POOL_MAX,
                    kwargs={"autocommit": True, "row_factory": dict_row},
                    configure=_configure,
                    open=True,
                )
                _pool.wait()
                logger.info("Database pool opened")
    return _pool


def close_connection() -> None:
    """Close the pool."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None
            logger.info("Database pool closed")


@contextmanager
def get_cursor() -> Generator[psycopg.Cursor, None, None]:
    """
    Cursor in autocommit mode. Rows come back as dicts.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE guild_id = %s", (gid,))
            results = cursor.fetchall()
    """
    conn = getattr(_tx, "conn", None)
    if conn is not None:
        with conn.cursor() as cursor:
            yield cursor
        return
    with get_pool().connection() as conn:
        with conn.cursor() as cursor:
            yield cursor


@contextmanager
def transaction() -> Generator[psycopg.Cursor, None, None]:
    """
    Cursor inside a transaction. Commits on success, rolls back on exception.

    Usage:
        with transaction() as cursor:
            cursor.execute("INSERT INTO ...")
            cursor.execute("UPDATE ...")
    """
    if getattr(_tx, "conn", None) is not None:
        with get_cursor() as cursor:  # already inside a transaction: join it
            yield cursor
        return
    with get_pool().connection() as conn:
        _tx.conn = conn
        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    yield cursor
        finally:
            _tx.conn = None


# =============================================================================
# Schema Check
# =============================================================================

def get_schema_version() -> Optional[str]:
    """Latest applied migration version, or None if none have run."""
    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT MAX(version) AS version FROM schema_migrations")
            row = cursor.fetchone()
            return row["version"] if row else None
    except psycopg.errors.UndefinedTable:
        return None


def check_schema() -> None:
    """
    Stop startup if the database schema is behind what this code needs.

    Raises RuntimeError with the fix. The required version is the newest
    migration shipped in overlap/db/migrations, so there is no version
    constant to keep in step by hand.
    """
    required = required_schema_version()
    current = get_schema_version()
    if current is None or current < required:
        raise RuntimeError(
            f"Database schema is out of date (have {current}, need {required}). "
            "Apply the migrations (`dbmate up`, see overlap/db/README.md) and restart."
        )
    logger.info(f"Database schema OK (version {current})")


def cutoff_text(days: int) -> str:
    """UTC timestamp `days` ago, in the same text format `overlap_now()` writes."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# Utility Functions
# =============================================================================

def execute_query(query: str, params: tuple = ()) -> list:
    """Run a SELECT and return all rows (dicts)."""
    with get_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_one(query: str, params: tuple = ()) -> Optional[dict]:
    """Run a SELECT and return the first row (dict) or None."""
    with get_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def execute_write(query: str, params: tuple = ()) -> int:
    """Run an INSERT/UPDATE/DELETE and return the number of affected rows."""
    with get_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount


def row_to_dict(row: Optional[dict]) -> Optional[dict]:
    """Rows are already dicts; kept so callers stay unchanged."""
    return dict(row) if row is not None else None


def rows_to_dicts(rows: list) -> list:
    return [dict(row) for row in rows]
