from __future__ import annotations

import p2p_repository as repo
from p2p_common import is_admin_user, require_non_empty


def send_chat_message(order_id: str, sender_user_id: str, message: str, message_type: str = "text") -> dict:
    order_id = require_non_empty(order_id, "order_id")
    sender_user_id = require_non_empty(sender_user_id, "sender_user_id")
    message = require_non_empty(message, "message")

    if len(message) > 2000:
        raise ValueError("Mensaje demasiado largo")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    if sender_user_id not in {order["buyer_id"], order["seller_id"]} and not is_admin_user(sender_user_id):
        raise PermissionError("No tienes acceso al chat de esta orden")

    return repo.add_chat_message(order_id, sender_user_id, message, message_type)


def list_chat_messages(order_id: str, requester_user_id: str, limit: int = 200) -> list[dict]:
    order_id = require_non_empty(order_id, "order_id")
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    if requester_user_id not in {order["buyer_id"], order["seller_id"]} and not is_admin_user(requester_user_id):
        raise PermissionError("No tienes acceso al chat de esta orden")

    return repo.get_chat_messages(order_id, limit)
