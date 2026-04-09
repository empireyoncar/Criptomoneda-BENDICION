"""Repository for P2P offer operations."""

from __future__ import annotations

import json
from typing import Any

from p2p_db import db_transaction, run_query


def get_offer(offer_id: str) -> dict[str, Any] | None:
    """Get an offer by id."""
    rows = run_query("SELECT * FROM p2p_offers WHERE id = %s", (offer_id,))
    return rows[0] if rows else None


def create_offer(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new P2P offer."""
    rows = run_query(
        """
        INSERT INTO p2p_offers (
                    user_id, country, side, asset, fiat_currency, payment_method,
                    payment_provider, account_reference, account_holder,
                    price, amount_total, amount_available, min_limit, max_limit,
                    completion_time_minutes, terms, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
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
            data.get("completion_time_minutes", 15),
            data.get("terms", ""),
        ),
    )
    return rows[0]


def list_active_offers(side: str | None, asset: str | None, limit: int) -> list[dict[str, Any]]:
    """List active offers with user stats and ratings."""
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
        SELECT
            o.*,
            COALESCE(stats.total_orders, 0) AS total_orders,
            COALESCE(stats.completed_orders, 0) AS completed_orders,
            COALESCE(stats.completion_rate, 0) AS completion_rate,
            COALESCE(rating.average_score, 0) AS average_score,
            COALESCE(rating.total_ratings, 0) AS total_ratings
        FROM p2p_offers o
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::INT AS total_orders,
                COUNT(*) FILTER (WHERE status IN ('released', 'completed'))::INT AS completed_orders,
                COALESCE(
                    ROUND(
                        (
                            COUNT(*) FILTER (WHERE status IN ('released', 'completed'))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100,
                        0
                    ),
                    0
                )::INT AS completion_rate
            FROM p2p_orders po
            WHERE po.buyer_id = o.user_id OR po.seller_id = o.user_id
        ) AS stats ON TRUE
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::INT AS total_ratings,
                COALESCE(ROUND(AVG(score)::numeric, 2), 0) AS average_score
            FROM p2p_ratings pr
            WHERE pr.to_user_id = o.user_id
        ) AS rating ON TRUE
        WHERE {' AND '.join(f'o.{part}' for part in filters)}
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
                            unit_price, total_fiat, status, expires_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, 'pending_payment',
                            NOW() + make_interval(mins => %s)
                        )
            RETURNING *
            """,
            (
                offer_id,
                buyer_id,
                seller_id,
                amount,
                unit_price,
                total_fiat,
                int(offer.get("completion_time_minutes") or 15),
            ),
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


def cancel_offer(offer_id: str, requester_user_id: str) -> dict[str, Any]:
    """Cancel an offer if user is the creator."""
    with db_transaction() as cur:
        cur.execute(
            """
            SELECT * FROM p2p_offers WHERE id = %s FOR UPDATE
            """,
            (offer_id,),
        )
        offer = cur.fetchone()
        if not offer:
            raise ValueError("Oferta no encontrada")
        if offer["user_id"] != requester_user_id:
            raise PermissionError("Solo el creador puede cancelar la oferta")
        if offer["status"] != "active":
            raise ValueError("La oferta no puede ser cancelada en estado " + offer["status"])

        cur.execute(
            """
            UPDATE p2p_offers
            SET status = 'cancelled', updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (offer_id,),
        )
        return dict(cur.fetchone())
