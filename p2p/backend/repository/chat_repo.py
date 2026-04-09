"""Repository for P2P chat message operations."""

from __future__ import annotations

from typing import Any

from p2p_db import run_query


def add_chat_message(order_id: str, sender_user_id: str, message: str, message_type: str = "text") -> dict[str, Any]:
    """Add a chat message to an order conversation."""
    rows = run_query(
        """
        INSERT INTO p2p_chat_messages (order_id, sender_user_id, message, message_type)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        (order_id, sender_user_id, message, message_type),
    )
    return rows[0]


def get_chat_messages(order_id: str, limit: int = 200) -> list[dict[str, Any]]:
    """Get chat messages for an order ordered chronologically."""
    return run_query(
        """
        SELECT *
        FROM p2p_chat_messages
        WHERE order_id = %s
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (order_id, limit),
    )
