import json
import time
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from don_db import ensure_schema, fetch_one, transaction


DECIMAL_QUANT = Decimal("0.00000001")


def _as_decimal(value):
    try:
        amount = Decimal(str(value)).quantize(DECIMAL_QUANT, rounding=ROUND_DOWN)
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount


def _create_tx_id():
    return f"don_{uuid.uuid4().hex}"


def _save_transaction(cur, tx_type, user_from, user_to, amount, metadata=None):
    tx_id = _create_tx_id()
    now_ts = int(time.time())
    cur.execute(
        """
        INSERT INTO don_transactions (
            tx_id, tx_type, user_from, user_to, amount, timestamp, datetime, metadata_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            tx_id,
            tx_type,
            user_from,
            user_to,
            amount,
            now_ts,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            json.dumps(metadata or {}, separators=(",", ":")),
        ),
    )
    return tx_id


def _lock_and_get_balance(cur, user_id):
    cur.execute(
        "SELECT balance FROM don_accounts WHERE user_id = %s FOR UPDATE",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return Decimal("0")
    return Decimal(str(row[0]))


def _upsert_balance(cur, user_id, balance):
    cur.execute(
        """
        INSERT INTO don_accounts (user_id, balance, updated_timestamp)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET balance = EXCLUDED.balance,
            updated_timestamp = EXCLUDED.updated_timestamp
        """,
        (user_id, balance, int(time.time())),
    )


# ============================================================
#   FUNCIONES PÚBLICAS
# ============================================================

def get_balance(user_id: str) -> float:
    ensure_schema()
    row = fetch_one("SELECT balance FROM don_accounts WHERE user_id = %s", (user_id,))
    if not row:
        return 0.0
    return float(row["balance"])


def get_total_supply() -> float:
    ensure_schema()
    row = fetch_one("SELECT COALESCE(SUM(balance), 0) AS total_supply FROM don_accounts")
    return float(row["total_supply"]) if row else 0.0


def add(user_id: str, amount: float, metadata=None):
    """Generar DON (mint) y sumarlo al usuario."""
    ensure_schema()
    amount_decimal = _as_decimal(amount)
    if amount_decimal is None or amount_decimal <= 0:
        return None

    with transaction() as conn:
        with conn.cursor() as cur:
            current = _lock_and_get_balance(cur, user_id)
            _upsert_balance(cur, user_id, current + amount_decimal)
            return _save_transaction(cur, "mint", None, user_id, amount_decimal, metadata=metadata)


def transfer(from_user: str, to_user: str, amount: float, metadata=None):
    """Transferir DON entre usuarios."""
    ensure_schema()
    amount_decimal = _as_decimal(amount)
    if amount_decimal is None or amount_decimal <= 0:
        return False, None

    with transaction() as conn:
        with conn.cursor() as cur:
            ordered = sorted([from_user, to_user])
            for user_id in ordered:
                _lock_and_get_balance(cur, user_id)

            current_from = _lock_and_get_balance(cur, from_user)
            current_to = _lock_and_get_balance(cur, to_user)
            if current_from < amount_decimal:
                return False, None

            _upsert_balance(cur, from_user, current_from - amount_decimal)
            _upsert_balance(cur, to_user, current_to + amount_decimal)
            tx_id = _save_transaction(cur, "transfer", from_user, to_user, amount_decimal, metadata=metadata)
            return True, tx_id


def burn(user_id: str, amount: float, metadata=None):
    """Quemar DON del usuario (eliminar del sistema)."""
    ensure_schema()
    amount_decimal = _as_decimal(amount)
    if amount_decimal is None or amount_decimal <= 0:
        return False, None

    with transaction() as conn:
        with conn.cursor() as cur:
            current = _lock_and_get_balance(cur, user_id)
            if current < amount_decimal:
                return False, None

            _upsert_balance(cur, user_id, current - amount_decimal)
            tx_id = _save_transaction(cur, "burn", user_id, None, amount_decimal, metadata=metadata)
            return True, tx_id
