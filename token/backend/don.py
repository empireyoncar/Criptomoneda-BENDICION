import json
import os
from threading import Lock

# ============================================================
# Archivo donde se guardan los balances y el supply
# Se monta desde docker-compose:
# ./token/backend/don_ledger.json:/app/don_ledger.json
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


def add(user_id: str, amount: float) -> None:
    """Generar DON (mint) y sumarlo al usuario."""
    amount = float(amount)
    if amount <= 0:
        return

    with _lock:
        data = _load()
        users = data["users"]

        users[user_id] = float(users.get(user_id, 0.0)) + amount
        data["total_supply"] = float(data.get("total_supply", 0.0)) + amount

        _save(data)


def subtract(user_id: str, amount: float) -> bool:
    """Restar DON al usuario (pago/uso)."""
    amount = float(amount)
    if amount <= 0:
        return False

    with _lock:
        data = _load()
        users = data["users"]

        current = float(users.get(user_id, 0.0))
        if current < amount:
            return False

        users[user_id] = current - amount
        _save(data)
        return True


def transfer(from_user: str, to_user: str, amount: float) -> bool:
    """Transferir DON entre usuarios."""
    amount = float(amount)
    if amount <= 0:
        return False

    with _lock:
        data = _load()
        users = data["users"]

        current_from = float(users.get(from_user, 0.0))
        if current_from < amount:
            return False

        users[from_user] = current_from - amount
        users[to_user] = float(users.get(to_user, 0.0)) + amount

        _save(data)
        return True


def burn(user_id: str, amount: float) -> bool:
    """Quemar DON del usuario (eliminar del sistema)."""
    amount = float(amount)
    if amount <= 0:
        return False

    with _lock:
        data = _load()
        users = data["users"]

        current = float(users.get(user_id, 0.0))
        if current < amount:
            return False

        users[user_id] = current - amount
        data["total_supply"] = float(data.get("total_supply", 0.0)) - amount

        _save(data)
        return True
