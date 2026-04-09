"""PostgreSQL helpers for the usuarios module."""

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
    return psycopg2.connect(
        host=_env("USERS_DB_HOST", "localhost"),
        port=int(_env("USERS_DB_PORT", "5546")),
        dbname=_env("USERS_DB_NAME", "users_db"),
        user=_env("USERS_DB_USER", "users_user"),
        password=_env("USERS_DB_PASSWORD", "users_password"),
        cursor_factory=RealDictCursor,
    )


@contextmanager
def db_transaction() -> Iterator[Any]:
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
    with db_transaction() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
