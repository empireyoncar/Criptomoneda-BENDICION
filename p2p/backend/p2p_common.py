from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def is_admin_user(user_id: str) -> bool:
    return user_id.startswith("admin") or user_id == "001"


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def require_non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} es requerido")
    return value.strip()


def require_positive(value: float, name: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} debe ser numerico") from None
    if n <= 0:
        raise ValueError(f"{name} debe ser mayor que cero")
    return n


def require_order_participant(order: dict[str, Any], user_id: str) -> None:
    if user_id not in {order["buyer_id"], order["seller_id"]}:
        raise PermissionError("No tienes permiso sobre esta orden")
