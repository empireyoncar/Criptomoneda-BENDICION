import json
import os
from threading import Lock
from don_history import log_transaction   # ← INTEGRACIÓN

# ============================================================
# Archivo donde se guardan los balances y el supply
# ============================================================
DON_FILE = "/app/don_ledger.json"

_lock = Lock()


def _init_file():
    """Crea el archivo don_ledger.json si no existe."""
    if not os.path.exists(DON_FILE):
        data = {
            "total_supply": 0.0,
            "users": {}
        }
        with open(DON_FILE, "w") as f:
            json.dump(data, f, indent=4)


def _load():
    """Carga el ledger desde el archivo."""
    _init_file()
    with open(DON_FILE, "r") as f:
        return json.load(f)


def _save(data):
    """Guarda el ledger en el archivo."""
    with open(DON_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
#   FUNCIONES PÚBLICAS
# ============================================================

def get_balance(user_id: str) -> float:
    with _lock:
        data = _load()
        return float(data["users"].get(user_id, 0.0))


def get_total_supply() -> float:
    with _lock:
        data = _load()
        return float(data.get("total_supply", 0.0))


def add(user_id: str, amount: float, metadata=None):
    """Generar DON (mint) y sumarlo al usuario."""
    amount = float(amount)
    if amount <= 0:
        return None

    with _lock:
        data = _load()
        users = data["users"]

        users[user_id] = float(users.get(user_id, 0.0)) + amount
        data["total_supply"] = float(data.get("total_supply", 0.0)) + amount

        _save(data)

        # HISTORIAL
        return log_transaction("mint", None, user_id, amount, metadata=metadata)


def transfer(from_user: str, to_user: str, amount: float, metadata=None):
    """Transferir DON entre usuarios."""
    amount = float(amount)
    if amount <= 0:
        return False, None

    with _lock:
        data = _load()
        users = data["users"]

        current_from = float(users.get(from_user, 0.0))
        if current_from < amount:
            return False, None

        users[from_user] = current_from - amount
        users[to_user] = float(users.get(to_user, 0.0)) + amount

        _save(data)

        # HISTORIAL
        tx_id = log_transaction("transfer", from_user, to_user, amount, metadata=metadata)

        return True, tx_id


def burn(user_id: str, amount: float, metadata=None):
    """Quemar DON del usuario (eliminar del sistema)."""
    amount = float(amount)
    if amount <= 0:
        return False, None

    with _lock:
        data = _load()
        users = data["users"]

        current = float(users.get(user_id, 0.0))
        if current < amount:
            return False, None

        users[user_id] = current - amount
        data["total_supply"] = float(data.get("total_supply", 0.0)) - amount

        _save(data)

        # HISTORIAL
        tx_id = log_transaction("burn", user_id, None, amount, metadata=metadata)

        return True, tx_id
