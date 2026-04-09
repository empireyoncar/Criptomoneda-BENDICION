"""Repository for P2P dispute operations."""

from __future__ import annotations

import json
from typing import Any

from p2p_db import run_query


def create_dispute(order_id: str, opened_by_user_id: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    """Create or update a dispute for an order."""
    rows = run_query(
        """
        INSERT INTO p2p_disputes (order_id, opened_by_user_id, reason, evidence, status)
        VALUES (%s, %s, %s, %s::jsonb, 'open')
        ON CONFLICT (order_id) DO UPDATE
        SET reason = EXCLUDED.reason,
            evidence = EXCLUDED.evidence,
            status = 'open'
        RETURNING *
        """,
        (order_id, opened_by_user_id, reason, json.dumps(evidence)),
    )
    return rows[0]


def resolve_dispute(order_id: str, admin_id: str, status: str, note: str) -> dict[str, Any]:
    """Resolve a dispute with admin decision and note."""
    rows = run_query(
        """
        UPDATE p2p_disputes
        SET status = %s,
            admin_id = %s,
            resolution_note = %s,
            resolved_at = NOW()
        WHERE order_id = %s
        RETURNING *
        """,
        (status, admin_id, note, order_id),
    )
    return rows[0]


def list_disputes(status: str = "open", limit: int = 100) -> list[dict[str, Any]]:
    """List disputes optionally filtered by status."""
    return run_query(
        """
        SELECT
            d.id,
            d.order_id,
            d.opened_by_user_id,
            d.reason,
            d.evidence,
            d.status,
            d.admin_id,
            d.resolution_note,
            d.created_at,
            d.resolved_at,
            o.buyer_id,
            o.seller_id,
            o.amount,
            o.total_fiat,
            o.status AS order_status,
            o.expires_at
        FROM p2p_disputes d
        JOIN p2p_orders o ON o.id = d.order_id
        WHERE (%s = '' OR d.status = %s)
        ORDER BY d.created_at DESC
        LIMIT %s
        """,
        (status, status, limit),
    )


def get_dispute_detail(order_id: str) -> dict[str, Any] | None:
    """Get detailed info for a dispute."""
    rows = run_query(
        """
        SELECT
            d.id,
            d.order_id,
            d.opened_by_user_id,
            d.reason,
            d.evidence,
            d.status,
            d.admin_id,
            d.resolution_note,
            d.created_at,
            d.resolved_at,
            o.buyer_id,
            o.seller_id,
            o.amount,
            o.unit_price,
            o.total_fiat,
            o.status AS order_status,
            o.expires_at
        FROM p2p_disputes d
        JOIN p2p_orders o ON o.id = d.order_id
        WHERE d.order_id = %s
        """,
        (order_id,),
    )
    return rows[0] if rows else None
