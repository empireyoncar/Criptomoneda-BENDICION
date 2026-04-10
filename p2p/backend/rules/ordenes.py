from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from blockchain_client import BlockchainError, refund_from_escrow, release_from_escrow
import p2p_repository as repo
from p2p_common import require_non_empty, require_order_participant

_ALLOWED_ORDER_STATUSES = {
    "pending_payment",
    "paid",
    "released",
    "refunded",
    "disputed",
    "cancelled",
    "completed",
}


def get_order_detail(order_id: str) -> dict[str, Any]:
    order_id = require_non_empty(order_id, "order_id")
    detail = repo.get_order_detail(order_id)
    if not detail:
        raise ValueError("Orden no encontrada")
    return detail


def is_order_participant(order_id: str, user_id: str) -> bool:
    order = repo.get_order(order_id)
    if not order:
        return False
    return user_id in {order["buyer_id"], order["seller_id"]}


def add_escrow_event(order_id: str, event_type: str, actor_user_id: str, details: dict[str, Any]) -> None:
    repo.add_escrow_event(order_id, event_type, actor_user_id, details)


def mark_paid(order_id: str, buyer_id: str, payment_proof_url: str | None = None) -> dict[str, Any]:
    order_id = require_non_empty(order_id, "order_id")
    buyer_id = require_non_empty(buyer_id, "buyer_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    if order["buyer_id"] != buyer_id:
        raise PermissionError("Solo el comprador puede marcar pago")
    if order["status"] != "pending_payment":
        raise ValueError("La orden no esta en estado pending_payment")

    updated = repo.update_order_status(order_id, "paid", payment_proof_url)
    add_escrow_event(order_id, "paid", buyer_id, {"payment_proof_url": payment_proof_url})
    return updated


def release_order(order_id: str, seller_id: str) -> dict[str, Any]:
    order_id = require_non_empty(order_id, "order_id")
    seller_id = require_non_empty(seller_id, "seller_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    if order["seller_id"] != seller_id:
        raise PermissionError("Solo el vendedor puede liberar")
    if order["status"] != "paid":
        raise ValueError("La orden debe estar pagada para liberar")

    release_metadata = {
        "source": "p2p_release_order",
        "order_id": order_id,
        "seller_id": seller_id,
        "buyer_id": order["buyer_id"],
        "amount": float(order["amount"]),
    }
    release_tx_id = sha256(json.dumps(release_metadata, sort_keys=True).encode()).hexdigest()
    try:
        release_from_escrow(
            to_wallet=order["buyer_wallet"],
            amount=float(order["amount"]),
            tx_id=release_tx_id,
            metadata=release_metadata,
        )
    except BlockchainError as exc:
        raise ValueError(f"No se pudo liberar fondos en blockchain: {exc}") from exc

    updated = repo.update_order_status(order_id, "released")
    add_escrow_event(order_id, "release", seller_id, {})
    return updated


def refund_order(order_id: str, actor_user_id: str) -> dict[str, Any]:
    order_id = require_non_empty(order_id, "order_id")
    actor_user_id = require_non_empty(actor_user_id, "actor_user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    require_order_participant(order, actor_user_id)
    if order["status"] not in {"pending_payment", "paid", "disputed"}:
        raise ValueError("Estado de orden invalido para reembolso")

    refund_metadata = {
        "source": "p2p_refund_order",
        "order_id": order_id,
        "actor_user_id": actor_user_id,
        "seller_id": order["seller_id"],
        "amount": float(order["amount"]),
    }
    refund_tx_id = sha256(json.dumps(refund_metadata, sort_keys=True).encode()).hexdigest()
    try:
        refund_from_escrow(
            to_wallet=order["seller_wallet"],
            amount=float(order["amount"]),
            tx_id=refund_tx_id,
            metadata=refund_metadata,
        )
    except BlockchainError as exc:
        raise ValueError(f"No se pudo reembolsar fondos en blockchain: {exc}") from exc

    updated = repo.update_order_status(order_id, "refunded")
    add_escrow_event(order_id, "refund", actor_user_id, {})
    return updated


def validate_order_status(status: str) -> bool:
    return status in _ALLOWED_ORDER_STATUSES


def list_user_orders(user_id: str, role: str = "participant", limit: int = 100) -> list[dict[str, Any]]:
    user_id = require_non_empty(user_id, "user_id")
    if role not in {"participant", "seller", "buyer"}:
        raise ValueError("role invalido")
    return repo.list_user_orders(user_id=user_id, role=role, limit=limit)
