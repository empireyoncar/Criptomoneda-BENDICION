"""Repository for P2P order operations."""

from __future__ import annotations

import json
from typing import Any

from p2p_db import run_query


def get_order(order_id: str) -> dict[str, Any] | None:
    """Get basic order info."""
    rows = run_query("SELECT * FROM p2p_orders WHERE id = %s", (order_id,))
    return rows[0] if rows else None


def get_order_detail(order_id: str) -> dict[str, Any] | None:
    """Get detailed order info with offer details."""
    rows = run_query(
        """
        SELECT
          o.id,
          o.offer_id,
          o.buyer_id,
                    o.buyer_wallet,
          o.seller_id,
                    o.seller_wallet,
          o.amount,
          o.unit_price,
          o.total_fiat,
          o.payment_proof_url,
          o.status,
          o.created_at,
          o.expires_at,
          f.country,
          f.payment_method,
          f.payment_provider,
          f.account_reference,
          f.account_holder,
          f.min_limit,
          f.max_limit,
          f.completion_time_minutes,
          f.fiat_currency,
          f.asset,
          f.terms
        FROM p2p_orders o
        JOIN p2p_offers f ON f.id = o.offer_id
        WHERE o.id = %s
        """,
        (order_id,),
    )
    return rows[0] if rows else None


def list_user_orders(user_id: str, role: str = "participant", limit: int = 100) -> list[dict[str, Any]]:
    """List orders for a user (buyer, seller, or both)."""
    if role == "seller":
        where_clause = "o.seller_id = %s"
    elif role == "buyer":
        where_clause = "o.buyer_id = %s"
    else:
        where_clause = "(o.buyer_id = %s OR o.seller_id = %s)"

    if role == "participant":
        params: tuple[Any, ...] = (user_id, user_id, limit)
    else:
        params = (user_id, limit)

    return run_query(
        f"""
        SELECT
            o.id,
            o.offer_id,
            o.buyer_id,
            o.seller_id,
            o.amount,
            o.unit_price,
            o.total_fiat,
            o.status,
            o.created_at,
            o.expires_at,
            f.country,
            f.payment_method,
            f.payment_provider,
            f.account_reference,
            f.account_holder,
            f.completion_time_minutes,
            f.fiat_currency,
            f.asset
        FROM p2p_orders o
        JOIN p2p_offers f ON f.id = o.offer_id
        WHERE {where_clause}
        ORDER BY o.created_at DESC
        LIMIT %s
        """,
        params,
    )


def update_order_status(order_id: str, status: str, proof_url: str | None = None) -> dict[str, Any]:
    """Update order status and optionally payment proof URL."""
    if proof_url is None:
        rows = run_query(
            """
            UPDATE p2p_orders
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (status, order_id),
        )
    else:
        rows = run_query(
            """
            UPDATE p2p_orders
            SET status = %s, payment_proof_url = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (status, proof_url, order_id),
        )
    return rows[0]


def add_escrow_event(order_id: str, event_type: str, actor_user_id: str, details: dict[str, Any]) -> None:
    """Record an escrow event for an order."""
    run_query(
        """
        INSERT INTO p2p_escrow_events (order_id, event_type, actor_user_id, details)
        VALUES (%s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (order_id, event_type, actor_user_id, json.dumps(details)),
    )
