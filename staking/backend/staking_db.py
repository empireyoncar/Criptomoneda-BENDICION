"""PostgreSQL helpers for the staking module."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_connection():
    return psycopg2.connect(
        host=_env("STAKING_DB_HOST", "localhost"),
        port=int(_env("STAKING_DB_PORT", "5547")),
        dbname=_env("STAKING_DB_NAME", "staking_db"),
        user=_env("STAKING_DB_USER", "staking_user"),
        password=_env("STAKING_DB_PASSWORD", "staking_password"),
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


def run_execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with db_transaction() as cur:
        cur.execute(query, params)
        return cur.rowcount


def run_query_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with db_transaction() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def ensure_schema() -> None:
    for attempt in range(1, 11):
        try:
            run_execute(
                """
                CREATE TABLE IF NOT EXISTS stakes (
                    stake_id UUID PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    wallet VARCHAR(255) NOT NULL,
                    amount_bend BIGINT NOT NULL,
                    days INTEGER NOT NULL,
                    reward_don DOUBLE PRECISION NOT NULL,
                    transfer_tx_id VARCHAR(255) NOT NULL UNIQUE,
                    timestamp BIGINT NOT NULL,
                    end_timestamp BIGINT NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    finished_timestamp BIGINT,
                    cancelled_timestamp BIGINT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            run_execute("CREATE INDEX IF NOT EXISTS idx_stakes_user_id ON stakes(user_id)")
            run_execute("CREATE INDEX IF NOT EXISTS idx_stakes_wallet ON stakes(wallet)")
            run_execute("CREATE INDEX IF NOT EXISTS idx_stakes_status ON stakes(status)")
            run_execute("CREATE INDEX IF NOT EXISTS idx_stakes_end_timestamp ON stakes(end_timestamp)")
            return
        except Exception as exc:
            logger.warning("ensure_schema attempt %d/10 failed: %s", attempt, exc)
            if attempt == 10:
                raise
            time.sleep(3)