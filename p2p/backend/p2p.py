"""Business logic for the P2P marketplace."""

from __future__ import annotations

from typing import Any

import p2p_repository as repo

_ALLOWED_ORDER_STATUSES = {
    "pending_payment",
    "paid",
    "released",
    "refunded",
    "disputed",
    "cancelled",
    "completed",
}

ASSET_CODE = "BEN"
ASSET_NAME = "BENDICION"
ALLOWED_COMPLETION_MINUTES = {10, 15, 30, 60}


def _require_non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} es requerido")
    return value.strip()


def _require_positive(value: float, name: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} debe ser numerico") from None
    if n <= 0:
        raise ValueError(f"{name} debe ser mayor que cero")
    return n


def create_offer(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = _require_non_empty(payload.get("user_id", ""), "user_id")
    side = _require_non_empty(payload.get("side", ""), "side").lower()
    if side not in {"buy", "sell"}:
        raise ValueError("side debe ser buy o sell")

    amount_total = _require_positive(payload.get("amount_total"), "amount_total")
    price = _require_positive(payload.get("price"), "price")

    min_limit = float(payload.get("min_limit") or 0)
    max_limit = float(payload.get("max_limit") or 0)
    if min_limit < 0 or max_limit < 0:
        raise ValueError("min_limit y max_limit no pueden ser negativos")
    if max_limit > 0 and min_limit > max_limit:
        raise ValueError("min_limit no puede ser mayor que max_limit")

    completion_time_minutes = int(payload.get("completion_time_minutes") or 15)
    if completion_time_minutes not in ALLOWED_COMPLETION_MINUTES:
        raise ValueError("completion_time_minutes debe ser 10, 15, 30 o 60")

    data = {
        "user_id": user_id,
        "country": _require_non_empty(payload.get("country", ""), "country"),
        "side": side,
        "asset": _require_non_empty(payload.get("asset", ASSET_CODE), "asset").upper(),
        "fiat_currency": _require_non_empty(payload.get("fiat_currency", "USD"), "fiat_currency").upper(),
        "payment_method": _require_non_empty(payload.get("payment_method", "TRANSFER"), "payment_method"),
        "payment_provider": _require_non_empty(payload.get("payment_provider", ""), "payment_provider"),
        "account_reference": _require_non_empty(payload.get("account_reference", ""), "account_reference"),
        "account_holder": _require_non_empty(payload.get("account_holder", ""), "account_holder"),
        "price": price,
        "amount_total": amount_total,
        "min_limit": min_limit,
        "max_limit": max_limit,
        "completion_time_minutes": completion_time_minutes,
        "terms": str(payload.get("terms") or "").strip(),
    }

    if data["asset"] != ASSET_CODE:
        raise ValueError(f"Solo se permite {ASSET_NAME} ({ASSET_CODE}) en este mercado")

    return repo.create_offer(data)


def list_offers(side: str | None = None, asset: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200

    norm_side = side.lower() if isinstance(side, str) and side else None
    norm_asset = ASSET_CODE
    if isinstance(asset, str) and asset and asset.upper() != ASSET_CODE:
        return []
    return repo.list_active_offers(norm_side, norm_asset, limit)


def take_offer(offer_id: str, taker_user_id: str, amount: float) -> dict[str, Any]:
    offer_id = _require_non_empty(offer_id, "offer_id")
    taker_user_id = _require_non_empty(taker_user_id, "taker_user_id")
    amount = _require_positive(amount, "amount")
    return repo.take_offer(offer_id, taker_user_id, amount)


def get_order_detail(order_id: str) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    detail = repo.get_order_detail(order_id)
    if not detail:
        raise ValueError("Orden no encontrada")
    return detail


def _require_order_participant(order: dict[str, Any], user_id: str) -> None:
    if user_id not in {order["buyer_id"], order["seller_id"]}:
        raise PermissionError("No tienes permiso sobre esta orden")


def is_order_participant(order_id: str, user_id: str) -> bool:
    order = repo.get_order(order_id)
    if not order:
        return False
    return user_id in {order["buyer_id"], order["seller_id"]}


def mark_paid(order_id: str, buyer_id: str, payment_proof_url: str | None = None) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    buyer_id = _require_non_empty(buyer_id, "buyer_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    if order["buyer_id"] != buyer_id:
        raise PermissionError("Solo el comprador puede marcar pago")
    if order["status"] != "pending_payment":
        raise ValueError("La orden no esta en estado pending_payment")

    updated = repo.update_order_status(order_id, "paid", payment_proof_url)
    repo.add_escrow_event(order_id, "paid", buyer_id, {"payment_proof_url": payment_proof_url})
    return updated


def release_order(order_id: str, seller_id: str) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    seller_id = _require_non_empty(seller_id, "seller_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    if order["seller_id"] != seller_id:
        raise PermissionError("Solo el vendedor puede liberar")
    if order["status"] != "paid":
        raise ValueError("La orden debe estar pagada para liberar")

    updated = repo.update_order_status(order_id, "released")
    repo.add_escrow_event(order_id, "release", seller_id, {})
    return updated


def refund_order(order_id: str, actor_user_id: str) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    actor_user_id = _require_non_empty(actor_user_id, "actor_user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    _require_order_participant(order, actor_user_id)
    if order["status"] not in {"pending_payment", "paid", "disputed"}:
        raise ValueError("Estado de orden invalido para reembolso")

    updated = repo.update_order_status(order_id, "refunded")
    repo.add_escrow_event(order_id, "refund", actor_user_id, {})
    return updated


def open_dispute(order_id: str, opened_by_user_id: str, reason: str, evidence: list[str] | None = None) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    opened_by_user_id = _require_non_empty(opened_by_user_id, "opened_by_user_id")
    reason = _require_non_empty(reason, "reason")
    evidence = evidence or []

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    _require_order_participant(order, opened_by_user_id)

    repo.update_order_status(order_id, "disputed")
    dispute = repo.create_dispute(order_id, opened_by_user_id, reason, evidence)
    repo.add_escrow_event(order_id, "dispute_open", opened_by_user_id, {"reason": reason})
    return dispute


def resolve_dispute(order_id: str, admin_id: str, resolution: str, note: str) -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    admin_id = _require_non_empty(admin_id, "admin_id")
    resolution = _require_non_empty(resolution, "resolution")

    if resolution not in {"resolved_buyer", "resolved_seller", "rejected"}:
        raise ValueError("resolution invalida")

    dispute = repo.resolve_dispute(order_id, admin_id, resolution, note)

    if resolution == "resolved_buyer":
        repo.update_order_status(order_id, "refunded")
        repo.add_escrow_event(order_id, "refund", admin_id, {"source": "dispute"})
    elif resolution == "resolved_seller":
        repo.update_order_status(order_id, "released")
        repo.add_escrow_event(order_id, "release", admin_id, {"source": "dispute"})

    repo.add_escrow_event(order_id, "dispute_resolve", admin_id, {"resolution": resolution})
    return dispute


def send_chat_message(order_id: str, sender_user_id: str, message: str, message_type: str = "text") -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    sender_user_id = _require_non_empty(sender_user_id, "sender_user_id")
    message = _require_non_empty(message, "message")

    if len(message) > 2000:
        raise ValueError("Mensaje demasiado largo")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    # Allow admin users too when handling disputes.
    if sender_user_id not in {order["buyer_id"], order["seller_id"]} and not sender_user_id.startswith("admin"):
        raise PermissionError("No tienes acceso al chat de esta orden")

    return repo.add_chat_message(order_id, sender_user_id, message, message_type)


def list_chat_messages(order_id: str, requester_user_id: str, limit: int = 200) -> list[dict[str, Any]]:
    order_id = _require_non_empty(order_id, "order_id")
    requester_user_id = _require_non_empty(requester_user_id, "requester_user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    if requester_user_id not in {order["buyer_id"], order["seller_id"]} and not requester_user_id.startswith("admin"):
        raise PermissionError("No tienes acceso al chat de esta orden")

    return repo.get_chat_messages(order_id, limit)


def submit_rating(order_id: str, from_user_id: str, score: int, comment: str = "") -> dict[str, Any]:
    order_id = _require_non_empty(order_id, "order_id")
    from_user_id = _require_non_empty(from_user_id, "from_user_id")

    try:
        score_int = int(score)
    except (TypeError, ValueError):
        raise ValueError("score invalido") from None

    if score_int < 1 or score_int > 5:
        raise ValueError("score debe estar entre 1 y 5")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    if order["status"] not in {"released", "refunded", "completed"}:
        raise ValueError("Solo se puede calificar una orden finalizada")

    if from_user_id == order["buyer_id"]:
        to_user_id = order["seller_id"]
    elif from_user_id == order["seller_id"]:
        to_user_id = order["buyer_id"]
    else:
        raise PermissionError("No participaste en esta orden")

    return repo.add_rating(order_id, from_user_id, to_user_id, score_int, comment)


def get_reputation(user_id: str) -> dict[str, Any]:
    user_id = _require_non_empty(user_id, "user_id")
    return repo.get_user_reputation(user_id)


def update_profile(user_id: str, actor_user_id: str, bio: str) -> dict[str, Any]:
    user_id = _require_non_empty(user_id, "user_id")
    actor_user_id = _require_non_empty(actor_user_id, "actor_user_id")
    if user_id != actor_user_id:
        raise PermissionError("Solo el propietario puede editar su biografia")

    bio = str(bio or "").strip()
    if len(bio) > 300:
        raise ValueError("La biografia no puede superar 300 caracteres")
    return repo.upsert_user_profile(user_id, bio)


def validate_order_status(status: str) -> bool:
    return status in _ALLOWED_ORDER_STATUSES
