"""Compatibility facade for P2P business logic modules.

This file keeps the same public API that existing servers import,
while the implementation is now split by domain.
"""

from __future__ import annotations

from rules.calificaciones import submit_rating
from rules.chat import list_chat_messages, send_chat_message
from rules.disputas import get_dispute_detail, list_disputes, open_dispute, resolve_dispute
from rules.ofertas import cancel_offer, create_offer, list_offers, take_offer
from rules.ordenes import (
    add_escrow_event,
    get_order_detail,
    is_order_participant,
    list_user_orders,
    mark_paid,
    refund_order,
    release_order,
    validate_order_status,
)
from rules.reputacionperfil import get_reputation, update_profile
from rules.timeoutcancelacion import get_timeout_status, submit_timeout_vote

__all__ = [
    "add_escrow_event",
    "cancel_offer",
    "create_offer",
    "get_dispute_detail",
    "get_order_detail",
    "get_reputation",
    "get_timeout_status",
    "is_order_participant",
    "list_chat_messages",
    "list_disputes",
    "list_offers",
    "list_user_orders",
    "mark_paid",
    "open_dispute",
    "refund_order",
    "release_order",
    "resolve_dispute",
    "send_chat_message",
    "submit_rating",
    "submit_timeout_vote",
    "take_offer",
    "update_profile",
    "validate_order_status",
]
