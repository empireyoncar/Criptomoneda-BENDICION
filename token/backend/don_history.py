import json
import os
import time
from datetime import datetime
from threading import Lock

HISTORY_DIR = "/app/don_history"
MAX_TX_PER_FILE = 1000

_lock = Lock()

def _ensure_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def _get_latest_file():
    _ensure_dir()
    files = [f for f in os.listdir(HISTORY_DIR) if f.startswith("don_history_")]
    if not files:
        return os.path.join(HISTORY_DIR, "don_history_1.json")

    files.sort()
    return os.path.join(HISTORY_DIR, files[-1])

def _load_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def _save_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def _get_history_files():
    _ensure_dir()
    files = [f for f in os.listdir(HISTORY_DIR) if f.startswith("don_history_") and f.endswith(".json")]

    def sort_key(filename):
        try:
            return int(filename.split("_")[-1].split(".")[0])
        except ValueError:
            return 0

    files.sort(key=sort_key)
    return [os.path.join(HISTORY_DIR, filename) for filename in files]


def get_transactions(limit=None, user_id=None):
    transactions = []

    for path in _get_history_files():
        try:
            transactions.extend(_load_file(path))
        except (OSError, json.JSONDecodeError):
            continue

    if user_id:
        transactions = [
            tx for tx in transactions
            if tx.get("user_from") == user_id or tx.get("user_to") == user_id
        ]

    transactions.sort(key=lambda tx: tx.get("timestamp", 0), reverse=True)

    if isinstance(limit, int) and limit > 0:
        return transactions[:limit]

    return transactions

def _generate_tx_id():
    return f"don_{int(time.time())}"

def log_transaction(tx_type, user_from, user_to, amount, metadata=None):
    with _lock:
        path = _get_latest_file()
        data = _load_file(path)

        # Rotar archivo si está lleno
        if len(data) >= MAX_TX_PER_FILE:
            number = int(path.split("_")[-1].split(".")[0]) + 1
            path = os.path.join(HISTORY_DIR, f"don_history_{number}.json")
            data = []

        tx = {
            "tx_id": _generate_tx_id(),
            "type": tx_type,
            "user_from": user_from,
            "user_to": user_to,
            "amount": amount,
            "timestamp": int(time.time()),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata or {}
        }

        data.append(tx)
        _save_file(path, data)

        return tx["tx_id"]
