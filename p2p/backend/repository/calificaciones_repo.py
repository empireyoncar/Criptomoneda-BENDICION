"""Repository for P2P rating (calificaciones) operations."""

from __future__ import annotations

from typing import Any

from p2p_db import run_query


def add_rating(order_id: str, from_user_id: str, to_user_id: str, score: int, comment: str) -> dict[str, Any]:
    """Add a rating from one user to another for an order."""
    rows = run_query(
        """
        INSERT INTO p2p_ratings (order_id, from_user_id, to_user_id, score, comment)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (order_id, from_user_id, to_user_id, score, comment),
    )
    return rows[0]


def get_order_rating_by_user(order_id: str, from_user_id: str) -> dict[str, Any] | None:
    """Get a specific rating given by a user for an order."""
    rows = run_query(
        """
        SELECT *
        FROM p2p_ratings
        WHERE order_id = %s AND from_user_id = %s
        LIMIT 1
        """,
        (order_id, from_user_id),
    )
    return rows[0] if rows else None


def count_order_ratings(order_id: str) -> int:
    """Count total ratings submitted for an order."""
    rows = run_query(
        """
        SELECT COUNT(*)::INT AS total
        FROM p2p_ratings
        WHERE order_id = %s
        """,
        (order_id,),
    )
    return int(rows[0]["total"]) if rows else 0
