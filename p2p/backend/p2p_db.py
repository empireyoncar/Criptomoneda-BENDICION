"""PostgreSQL connection and transaction helpers for the P2P module."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import RealDictCursor


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_connection():
    """Create a new PostgreSQL connection."""
    return psycopg2.connect(
        host=_env("P2P_DB_HOST", "localhost"),
        port=int(_env("P2P_DB_PORT", "5432")),
        dbname=_env("P2P_DB_NAME", "p2p_db"),
        user=_env("P2P_DB_USER", "p2p_user"),
        password=_env("P2P_DB_PASSWORD", "p2p_password"),
        cursor_factory=RealDictCursor,
    )


@contextmanager
def db_transaction() -> Iterator[Any]:
    """Transaction context manager with commit/rollback safety."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_query(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Run SELECT query and return all rows."""
    with db_transaction() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def run_execute(query: str, params: tuple[Any, ...] = ()) -> int:
    """Run INSERT/UPDATE/DELETE and return affected row count."""
    with db_transaction() as cur:
        cur.execute(query, params)
        return cur.rowcount


def health_check() -> bool:
    """Return True when DB is reachable and responsive."""
    try:
        rows = run_query("SELECT 1 AS ok")
        return bool(rows and rows[0].get("ok") == 1)
    except Exception:
        return False
