"""Repository for P2P order timeout voting operations."""

from __future__ import annotations

from typing import Any

from p2p_db import run_query


def upsert_timeout_vote(order_id: str, user_id: str, cancel_requested: bool) -> dict[str, Any]:
    """Record or update a timeout vote from a user."""
    rows = run_query(
        """
        INSERT INTO p2p_order_timeout_votes (order_id, user_id, cancel_requested)
        VALUES (%s, %s, %s)
        ON CONFLICT (order_id, user_id) DO UPDATE
        SET cancel_requested = EXCLUDED.cancel_requested,
            created_at = NOW()
        RETURNING order_id, user_id, cancel_requested, created_at
        """,
        (order_id, user_id, cancel_requested),
    )
    return rows[0]


def get_timeout_votes(order_id: str) -> list[dict[str, Any]]:
    """Get all timeout votes for an order."""
    return run_query(
        """
        SELECT order_id, user_id, cancel_requested, created_at
        FROM p2p_order_timeout_votes
        WHERE order_id = %s
        ORDER BY created_at ASC
        """,
        (order_id,),
    )
