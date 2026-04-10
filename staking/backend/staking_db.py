"""PostgreSQL helpers for the staking module."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import Json, RealDictCursor

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
            run_execute(
                """
                CREATE TABLE IF NOT EXISTS stake_rewards (
                    id BIGSERIAL PRIMARY KEY,
                    stake_id UUID NOT NULL UNIQUE REFERENCES stakes(stake_id) ON DELETE CASCADE,
                    user_id VARCHAR(255) NOT NULL,
                    wallet VARCHAR(255),
                    reward_don DOUBLE PRECISION NOT NULL,
                    transfer_tx_id VARCHAR(255),
                    timestamp BIGINT NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    paid_timestamp BIGINT,
                    last_error TEXT,
                    last_attempt_timestamp BIGINT,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            run_execute("CREATE INDEX IF NOT EXISTS idx_stake_rewards_status ON stake_rewards(status)")
            run_execute("CREATE INDEX IF NOT EXISTS idx_stake_rewards_user_id ON stake_rewards(user_id)")
            run_execute(
                """
                CREATE TABLE IF NOT EXISTS stake_payouts (
                    payout_id UUID PRIMARY KEY,
                    stake_id UUID NOT NULL UNIQUE REFERENCES stakes(stake_id) ON DELETE CASCADE,
                    user_id VARCHAR(255) NOT NULL,
                    wallet VARCHAR(255),
                    amount DOUBLE PRECISION NOT NULL,
                    asset VARCHAR(32) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    created_timestamp BIGINT NOT NULL,
                    paid_timestamp BIGINT NOT NULL,
                    source VARCHAR(64),
                    reward_record_timestamp BIGINT,
                    transfer_tx_id VARCHAR(255),
                    don_api JSONB,
                    idempotency_key VARCHAR(255) UNIQUE,
                    support_note TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            run_execute("CREATE INDEX IF NOT EXISTS idx_stake_payouts_user_id ON stake_payouts(user_id)")
            run_execute("CREATE INDEX IF NOT EXISTS idx_stake_payouts_status ON stake_payouts(status)")
            return
        except Exception as exc:
            logger.warning("ensure_schema attempt %d/10 failed: %s", attempt, exc)
            if attempt == 10:
                raise
            time.sleep(3)


def list_rewards() -> list[dict[str, Any]]:
    return run_query(
        """
        SELECT stake_id::text AS stake_id, user_id, wallet, reward_don, transfer_tx_id, timestamp,
               status, paid_timestamp, last_error, last_attempt_timestamp, attempt_count
        FROM stake_rewards
        ORDER BY timestamp ASC, id ASC
        """
    )


def list_pending_rewards() -> list[dict[str, Any]]:
    return run_query(
        """
        SELECT stake_id::text AS stake_id, user_id, wallet, reward_don, transfer_tx_id, timestamp,
               status, paid_timestamp, last_error, last_attempt_timestamp, attempt_count
        FROM stake_rewards
        WHERE status = 'pending'
        ORDER BY timestamp ASC, id ASC
        """
    )


def create_reward(reward: dict[str, Any]) -> int:
    return run_execute(
        """
        INSERT INTO stake_rewards (
            stake_id, user_id, wallet, reward_don, transfer_tx_id, timestamp,
            status, paid_timestamp, last_error, last_attempt_timestamp, attempt_count
        )
        VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stake_id) DO NOTHING
        """,
        (
            reward["stake_id"],
            reward["user_id"],
            reward.get("wallet"),
            float(reward.get("reward_don", 0)),
            reward.get("transfer_tx_id"),
            int(reward["timestamp"]),
            reward.get("status", "pending"),
            reward.get("paid_timestamp"),
            reward.get("last_error"),
            reward.get("last_attempt_timestamp"),
            int(reward.get("attempt_count", 0)),
        ),
    )


def mark_reward_paid(stake_id: str, paid_timestamp: int) -> int:
    return run_execute(
        """
        UPDATE stake_rewards
        SET status = 'paid', paid_timestamp = %s, last_error = NULL
        WHERE stake_id = %s::uuid
        """,
        (paid_timestamp, stake_id),
    )


def mark_reward_error(stake_id: str, error_message: str, attempt_timestamp: int) -> int:
    return run_execute(
        """
        UPDATE stake_rewards
        SET last_error = %s,
            last_attempt_timestamp = %s,
            attempt_count = COALESCE(attempt_count, 0) + 1
        WHERE stake_id = %s::uuid
        """,
        (error_message, attempt_timestamp, stake_id),
    )


def list_payout_stake_ids() -> set[str]:
    rows = run_query("SELECT stake_id FROM stake_payouts")
    return {str(row["stake_id"]) for row in rows}


def create_payout(payout: dict[str, Any]) -> int:
    return run_execute(
        """
        INSERT INTO stake_payouts (
            payout_id, stake_id, user_id, wallet, amount, asset, status,
            created_timestamp, paid_timestamp, source, reward_record_timestamp,
            transfer_tx_id, don_api, idempotency_key, support_note
        )
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stake_id) DO NOTHING
        """,
        (
            payout["payout_id"],
            payout["stake_id"],
            payout["user_id"],
            payout.get("wallet"),
            float(payout["amount"]),
            payout["asset"],
            payout["status"],
            int(payout["created_timestamp"]),
            int(payout["paid_timestamp"]),
            payout.get("source"),
            payout.get("reward_record_timestamp"),
            payout.get("transfer_tx_id"),
            Json(payout.get("don_api") or {}),
            payout.get("idempotency_key"),
            payout.get("support_note"),
        ),
    )