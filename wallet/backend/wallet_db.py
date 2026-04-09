"""PostgreSQL helpers for the wallet module."""

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
    """Create a PostgreSQL connection for the wallet service."""
    return psycopg2.connect(
        host=_env("WALLET_DB_HOST", "localhost"),
        port=int(_env("WALLET_DB_PORT", "5545")),
        dbname=_env("WALLET_DB_NAME", "wallet_db"),
        user=_env("WALLET_DB_USER", "wallet_user"),
        password=_env("WALLET_DB_PASSWORD", "wallet_password"),
        cursor_factory=RealDictCursor,
    )


@contextmanager
def db_transaction() -> Iterator[Any]:
    """Transaction context manager with commit and rollback safety."""
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
    """Run a SELECT query and return all rows as dicts."""
    with db_transaction() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def run_execute(query: str, params: tuple[Any, ...] = ()) -> int:
    """Run INSERT, UPDATE, or DELETE queries."""
    with db_transaction() as cur:
        cur.execute(query, params)
        return cur.rowcount


def ensure_schema() -> None:
    """Create wallet tables when they do not exist yet."""
    run_execute(
        """
        CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL UNIQUE,
            address VARCHAR(255) NOT NULL UNIQUE,
            public_key TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
