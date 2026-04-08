"""Repository layer for the P2P domain.

This module isolates SQL access by domain entity: offers, orders, disputes,
chat, and ratings.
"""

from __future__ import annotations

import json
from typing import Any

from p2p_db import db_transaction, run_query


def create_offer(data: dict[str, Any]) -> dict[str, Any]:
    rows = run_query(
        """
        INSERT INTO p2p_offers (
                    user_id, country, side, asset, fiat_currency, payment_method,
                    payment_provider, account_reference, account_holder,
                    price, amount_total, amount_available, min_limit, max_limit, terms, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        RETURNING *
        """,
        (
            data["user_id"],
                        data.get("country", "N/A"),
            data["side"],
            data.get("asset", "BEN"),
            data.get("fiat_currency", "USD"),
            data["payment_method"],
                        data.get("payment_provider", ""),
                        data.get("account_reference", ""),
                        data.get("account_holder", ""),
            data["price"],
            data["amount_total"],
            data["amount_total"],
            data.get("min_limit", 0),
            data.get("max_limit", 0),
            data.get("terms", ""),
        ),
    )
    return rows[0]


def list_active_offers(side: str | None, asset: str | None, limit: int) -> list[dict[str, Any]]:
    filters = ["status = 'active'"]
    params: list[Any] = []

    if side:
        filters.append("side = %s")
        params.append(side)
    if asset:
        filters.append("asset = %s")
        params.append(asset)

    params.append(limit)

    query = f"""
    SELECT *
    FROM p2p_offers
    WHERE {' AND '.join(filters)}
    ORDER BY created_at DESC
    LIMIT %s
    """
    return run_query(query, tuple(params))


def take_offer(offer_id: str, taker_user_id: str, amount: float) -> dict[str, Any]:
    """Atomically lock offer, create order and append escrow hold event."""
    with db_transaction() as cur:
        cur.execute(
            """
            SELECT *
            FROM p2p_offers
            WHERE id = %s
            FOR UPDATE
            """,
            (offer_id,),
        )
        offer = cur.fetchone()
        if not offer:
            raise ValueError("Oferta no encontrada")

        if offer["status"] != "active":
            raise ValueError("La oferta no esta activa")

        if offer["user_id"] == taker_user_id:
            raise ValueError("No puedes tomar tu propia oferta")

        if float(offer["amount_available"]) < amount:
            raise ValueError("Cantidad insuficiente en oferta")

        if offer["side"] == "sell":
            seller_id = offer["user_id"]
            buyer_id = taker_user_id
        else:
            seller_id = taker_user_id
            buyer_id = offer["user_id"]

        unit_price = float(offer["price"])
        total_fiat = unit_price * amount

        cur.execute(
            """
            INSERT INTO p2p_orders (
              offer_id, buyer_id, seller_id, amount,
              unit_price, total_fiat, status
            ) VALUES (%s, %s, %s, %s, %s, %s, 'pending_payment')
            RETURNING *
            """,
            (offer_id, buyer_id, seller_id, amount, unit_price, total_fiat),
        )
        order = cur.fetchone()

        new_available = float(offer["amount_available"]) - amount
        new_status = "filled" if new_available <= 0 else "active"

        cur.execute(
            """
            UPDATE p2p_offers
            SET amount_available = %s,
                status = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (max(new_available, 0), new_status, offer_id),
        )

        cur.execute(
            """
            INSERT INTO p2p_escrow_events (order_id, event_type, actor_user_id, details)
            VALUES (%s, 'hold', %s, %s::jsonb)
            """,
            (
                order["id"],
                taker_user_id,
                json.dumps({"amount": amount, "offer_id": offer_id}),
            ),
        )

        return dict(order)


def get_order(order_id: str) -> dict[str, Any] | None:
    rows = run_query("SELECT * FROM p2p_orders WHERE id = %s", (order_id,))
    return rows[0] if rows else None


def get_order_detail(order_id: str) -> dict[str, Any] | None:
    rows = run_query(
        """
        SELECT
          o.id,
          o.offer_id,
          o.buyer_id,
          o.seller_id,
          o.amount,
          o.unit_price,
          o.total_fiat,
          o.payment_proof_url,
          o.status,
          o.created_at,
          f.country,
          f.payment_method,
          f.payment_provider,
          f.account_reference,
          f.account_holder,
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


def update_order_status(order_id: str, status: str, proof_url: str | None = None) -> dict[str, Any]:
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
    run_query(
        """
        INSERT INTO p2p_escrow_events (order_id, event_type, actor_user_id, details)
        VALUES (%s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (order_id, event_type, actor_user_id, json.dumps(details)),
    )


def create_dispute(order_id: str, opened_by_user_id: str, reason: str, evidence: list[str]) -> dict[str, Any]:
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


def add_rating(order_id: str, from_user_id: str, to_user_id: str, score: int, comment: str) -> dict[str, Any]:
    rows = run_query(
        """
        INSERT INTO p2p_ratings (order_id, from_user_id, to_user_id, score, comment)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (order_id, from_user_id, to_user_id, score, comment),
    )
    return rows[0]


def get_user_reputation(user_id: str) -> dict[str, Any]:
    rows = run_query(
        """
        SELECT
          to_user_id AS user_id,
          COUNT(*)::INT AS total_ratings,
          COALESCE(ROUND(AVG(score)::numeric, 2), 0) AS average_score
        FROM p2p_ratings
        WHERE to_user_id = %s
        GROUP BY to_user_id
        """,
        (user_id,),
    )
    if not rows:
        return {"user_id": user_id, "total_ratings": 0, "average_score": 0.0}
    return rows[0]


def add_chat_message(order_id: str, sender_user_id: str, message: str, message_type: str = "text") -> dict[str, Any]:
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
