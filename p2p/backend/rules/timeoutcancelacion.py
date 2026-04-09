from __future__ import annotations

from datetime import datetime, timezone

import p2p_repository as repo
from p2p_common import parse_dt, require_non_empty, require_order_participant
from .ordenes import add_escrow_event


def get_timeout_status(order_id: str, requester_user_id: str) -> dict:
    order_id = require_non_empty(order_id, "order_id")
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    require_order_participant(order, requester_user_id)

    expires_at = parse_dt(order.get("expires_at"))
    now = datetime.now(timezone.utc)
    expired = bool(expires_at and now >= expires_at)
    votes = repo.get_timeout_votes(order_id)
    vote_map = {row["user_id"]: bool(row["cancel_requested"]) for row in votes}
    participants = [order["buyer_id"], order["seller_id"]]
    both_voted = all(user in vote_map for user in participants)
    both_cancel = both_voted and all(vote_map[user] for user in participants)
    any_keep = any((user in vote_map and not vote_map[user]) for user in participants)

    dispute_unlocked = expired and (order["status"] == "pending_payment") and (any_keep or not both_cancel)
    return {
        "order_id": order_id,
        "status": order["status"],
        "expired": expired,
        "expires_at": order.get("expires_at"),
        "votes": votes,
        "both_voted": both_voted,
        "both_cancel": both_cancel,
        "dispute_unlocked": dispute_unlocked,
    }


def submit_timeout_vote(order_id: str, user_id: str, cancel_requested: bool) -> dict:
    order_id = require_non_empty(order_id, "order_id")
    user_id = require_non_empty(user_id, "user_id")

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    require_order_participant(order, user_id)
    if order["status"] != "pending_payment":
        raise ValueError("Solo aplica en ordenes pending_payment")

    expires_at = parse_dt(order.get("expires_at"))
    if not expires_at or datetime.now(timezone.utc) < expires_at:
        raise ValueError("El cronometro aun no ha finalizado")

    repo.upsert_timeout_vote(order_id, user_id, bool(cancel_requested))
    status = get_timeout_status(order_id, user_id)
    if status["both_cancel"]:
        repo.update_order_status(order_id, "cancelled")
        add_escrow_event(order_id, "timeout", user_id, {"decision": "cancelled_by_both"})
        status["status"] = "cancelled"
        status["dispute_unlocked"] = True
    return status
