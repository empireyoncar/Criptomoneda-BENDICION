"""Input and transaction validation utilities with lightweight fraud checks."""

from __future__ import annotations

import math
import re
import threading
import time
from collections import defaultdict, deque
from typing import Any

from email_validator import EmailNotValidError, validate_email

_USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")

# In-memory anti-fraud windowing.
_FRAUD_WINDOW_SECONDS = 300
_FRAUD_MAX_EVENTS = 25
_IP_SPREAD_LIMIT = 8
_fraud_lock = threading.Lock()
_user_ip_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_ip_user_events: dict[str, deque[tuple[float, str]]] = defaultdict(deque)


def validar_email(email: str) -> bool:
    """Validate email format using RFC-aware validator."""
    if not isinstance(email, str) or not email.strip():
        return False

    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def validar_usuario(user_id: str) -> bool:
    """Validate user identifier pattern used by project services."""
    if not isinstance(user_id, str):
        return False
    return bool(_USER_RE.fullmatch(user_id.strip()))


def validar_cantidad(amount: float) -> bool:
    """Validate monetary amount: finite, positive and within safe system limits."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return False

    if not math.isfinite(value):
        return False
    return 0.0 < value <= 1_000_000_000_000.0


def validar_transaccion(tx_data: dict[str, Any]) -> dict[str, Any]:
    """Validate required transaction fields and produce actionable errors."""
    if not isinstance(tx_data, dict):
        return {"valida": False, "errores": ["tx_data debe ser un diccionario"]}

    errors: list[str] = []

    from_user = tx_data.get("from_user")
    to_user = tx_data.get("to_user")
    amount = tx_data.get("amount")

    if not validar_usuario(str(from_user or "")):
        errors.append("from_user invalido")
    if not validar_usuario(str(to_user or "")):
        errors.append("to_user invalido")
    if from_user == to_user and from_user is not None:
        errors.append("from_user y to_user no pueden ser iguales")

    try:
        parsed_amount = float(amount)
    except (TypeError, ValueError):
        parsed_amount = -1.0

    if not validar_cantidad(parsed_amount):
        errors.append("amount invalido")

    tx_type = tx_data.get("tx_type")
    if tx_type is not None and tx_type not in {"transfer", "mint", "burn", "stake", "unstake"}:
        errors.append("tx_type no permitido")

    return {"valida": len(errors) == 0, "errores": errors}


def detectar_fraude(user_id: str, ip: str) -> bool:
    """Flag suspicious activity based on velocity and IP spread heuristics."""
    if not validar_usuario(user_id):
        return True
    if not isinstance(ip, str) or not ip.strip():
        return True

    now = time.time()
    key = (user_id, ip)

    with _fraud_lock:
        pair_events = _user_ip_events[key]
        pair_events.append(now)

        # Remove old timestamps outside sliding window.
        while pair_events and now - pair_events[0] > _FRAUD_WINDOW_SECONDS:
            pair_events.popleft()

        ip_events = _ip_user_events[ip]
        ip_events.append((now, user_id))
        while ip_events and now - ip_events[0][0] > _FRAUD_WINDOW_SECONDS:
            ip_events.popleft()

        # Rule 1: too many operations for one user from one IP in short time.
        if len(pair_events) > _FRAUD_MAX_EVENTS:
            return True

        # Rule 2: one IP touching too many users in short time.
        unique_users = {u for _, u in ip_events}
        if len(unique_users) > _IP_SPREAD_LIMIT:
            return True

    return False
