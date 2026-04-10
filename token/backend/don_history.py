import json
import time
import uuid
from datetime import datetime

from don_db import ensure_schema, fetch_all, transaction


def get_transactions(limit=None, user_id=None):
    ensure_schema()
    query = """
        SELECT tx_id, tx_type, user_from, user_to, amount, timestamp, datetime, metadata_json
        FROM don_transactions
    """
    params = []

    if user_id:
        query += " WHERE user_from = %s OR user_to = %s"
        params.extend([user_id, user_id])

    query += " ORDER BY timestamp DESC"
    if isinstance(limit, int) and limit > 0:
        query += " LIMIT %s"
        params.append(limit)

    rows = fetch_all(query, tuple(params))
    transactions = []
    for row in rows:
        metadata_raw = row.get("metadata_json")
        metadata = {}
        if metadata_raw:
            try:
                metadata = json.loads(metadata_raw)
            except (TypeError, ValueError):
                metadata = {}

        transactions.append({
            "tx_id": row.get("tx_id"),
            "type": row.get("tx_type"),
            "user_from": row.get("user_from"),
            "user_to": row.get("user_to"),
            "amount": float(row.get("amount") or 0),
            "timestamp": int(row.get("timestamp") or 0),
            "datetime": row.get("datetime"),
            "metadata": metadata,
        })

    return transactions

def _generate_tx_id():
    return f"don_{uuid.uuid4().hex}"

def log_transaction(tx_type, user_from, user_to, amount, metadata=None):
    ensure_schema()
    tx_id = _generate_tx_id()
    now_ts = int(time.time())
    with transaction() as conn:
        with conn.cursor() as cur:
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
