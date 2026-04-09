from __future__ import annotations

from datetime import datetime, timezone

import p2p_repository as repo
from p2p_common import is_admin_user, parse_dt, require_non_empty, require_order_participant
from ordenes import add_escrow_event


def open_dispute(order_id: str, opened_by_user_id: str, reason: str, evidence: list[str] | None = None) -> dict:
    order_id = require_non_empty(order_id, "order_id")
    opened_by_user_id = require_non_empty(opened_by_user_id, "opened_by_user_id")
    reason = require_non_empty(reason, "reason")
    evidence = evidence or []

    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Orden no encontrada")
    require_order_participant(order, opened_by_user_id)

    if order["status"] == "pending_payment":
        expires_at = parse_dt(order.get("expires_at"))
        if expires_at and datetime.now(timezone.utc) < expires_at:
            raise ValueError("La disputa se habilita cuando termine el cronometro")

    repo.update_order_status(order_id, "disputed")
    dispute = repo.create_dispute(order_id, opened_by_user_id, reason, evidence)
    add_escrow_event(order_id, "dispute_open", opened_by_user_id, {"reason": reason})
    return dispute


def resolve_dispute(order_id: str, admin_id: str, resolution: str, note: str) -> dict:
    order_id = require_non_empty(order_id, "order_id")
    admin_id = require_non_empty(admin_id, "admin_id")
    resolution = require_non_empty(resolution, "resolution")

    if not is_admin_user(admin_id):
        raise PermissionError("Solo admin puede resolver disputas")

    if resolution not in {"resolved_buyer", "resolved_seller", "rejected"}:
        raise ValueError("resolution invalida")

    dispute = repo.resolve_dispute(order_id, admin_id, resolution, note)

    if resolution == "resolved_buyer":
        repo.update_order_status(order_id, "refunded")
        add_escrow_event(order_id, "refund", admin_id, {"source": "dispute"})
    elif resolution == "resolved_seller":
        repo.update_order_status(order_id, "released")
        add_escrow_event(order_id, "release", admin_id, {"source": "dispute"})

    add_escrow_event(order_id, "dispute_resolve", admin_id, {"resolution": resolution})
    return dispute


def list_disputes(requester_user_id: str, status: str = "open", limit: int = 100) -> list[dict]:
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")
    if not is_admin_user(requester_user_id):
        raise PermissionError("Solo admin puede ver disputas")
    return repo.list_disputes(status=status, limit=limit)


def get_dispute_detail(order_id: str, requester_user_id: str) -> dict:
    requester_user_id = require_non_empty(requester_user_id, "requester_user_id")
    if not is_admin_user(requester_user_id):
        raise PermissionError("Solo admin puede ver disputas")
    dispute = repo.get_dispute_detail(order_id)
    if not dispute:
        raise ValueError("Disputa no encontrada")
    return dispute
