from __future__ import annotations

import p2p_repository as repo
from p2p_common import require_non_empty


def submit_rating(order_id: str, from_user_id: str, score: int, comment: str = "") -> dict:
    order_id = require_non_empty(order_id, "order_id")
    from_user_id = require_non_empty(from_user_id, "from_user_id")

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

    existing = repo.get_order_rating_by_user(order_id, from_user_id)
    if existing:
        raise ValueError("Ya calificaste esta orden")

    if from_user_id == order["buyer_id"]:
        to_user_id = order["seller_id"]
    elif from_user_id == order["seller_id"]:
        to_user_id = order["buyer_id"]
    else:
        raise PermissionError("No participaste en esta orden")

    rating = repo.add_rating(order_id, from_user_id, to_user_id, score_int, comment)
    if order["status"] != "completed":
        repo.update_order_status(order_id, "completed")

    return rating
