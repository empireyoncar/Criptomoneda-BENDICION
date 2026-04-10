import glob
import json
import os
import time

from staking_db import ensure_schema, run_execute, run_query, run_query_one

BASE_PATH = "/app/backend"
ARCHIVE_PATH = os.path.join(BASE_PATH, "archive")
CHUNK_SIZE = 100
COMPLETED_CHUNK_PATTERN = os.path.join(ARCHIVE_PATH, "stakingcompletados_*.json")

LEGACY_FILES = {
    "activos": os.path.join(BASE_PATH, "stakingactivos.json"),
    "cancelados": os.path.join(BASE_PATH, "stakingcancelados_history.json")
}


def get_chunk_threshold(path):
    name = os.path.basename(path)
    number = name.split("_")[-1].split(".")[0]
    try:
        return int(number)
    except ValueError:
        return 0


def get_completed_chunk_path():
    os.makedirs(ARCHIVE_PATH, exist_ok=True)
    chunk_files = glob.glob(COMPLETED_CHUNK_PATTERN)
    if not chunk_files:
        return os.path.join(ARCHIVE_PATH, f"stakingcompletados_{CHUNK_SIZE}.json")

    chunk_files.sort(key=get_chunk_threshold)
    latest = chunk_files[-1]
    with open(latest, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    if len(data) < CHUNK_SIZE:
        return latest

    next_threshold = get_chunk_threshold(latest) + CHUNK_SIZE
    return os.path.join(ARCHIVE_PATH, f"stakingcompletados_{next_threshold}.json")


def _load_json_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _ensure_legacy_files():
    os.makedirs(ARCHIVE_PATH, exist_ok=True)
    for path in LEGACY_FILES.values():
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fp:
                json.dump([], fp)


def _save_legacy_file(name, data):
    _save_json_file(LEGACY_FILES[name], data)


def _append_to_completed_chunk(stake):
    path = get_completed_chunk_path()
    data = _load_json_file(path)
    data.append(stake)
    _save_json_file(path, data)


def _sync_legacy_activos(rows):
    _save_legacy_file("activos", rows)


def _sync_legacy_cancelled_append(stake):
    cancelados = _load_json_file(LEGACY_FILES["cancelados"])
    cancelados.append(stake)
    _save_legacy_file("cancelados", cancelados)


def _stake_row_to_dict(row):
    return {
        "stake_id": str(row["stake_id"]),
        "user_id": row["user_id"],
        "wallet": row["wallet"],
        "amount_bend": int(row["amount_bend"]),
        "days": int(row["days"]),
        "reward_don": float(row["reward_don"]),
        "transfer_tx_id": row["transfer_tx_id"],
        "timestamp": int(row["timestamp"]),
        "end_timestamp": int(row["end_timestamp"]),
        "status": row["status"],
        "finished_timestamp": row.get("finished_timestamp"),
        "cancelled_timestamp": row.get("cancelled_timestamp"),
    }


ensure_schema()
_ensure_legacy_files()


# ---------------------------------------------------------
# AGREGAR NUEVO STAKING
# ---------------------------------------------------------
def add_staking(stake):
    run_execute(
        """
        INSERT INTO stakes (
            stake_id, user_id, wallet, amount_bend, days, reward_don,
            transfer_tx_id, timestamp, end_timestamp, status,
            finished_timestamp, cancelled_timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            stake["stake_id"],
            stake["user_id"],
            stake["wallet"],
            int(stake["amount_bend"]),
            int(stake["days"]),
            float(stake["reward_don"]),
            stake["transfer_tx_id"],
            int(stake["timestamp"]),
            int(stake["end_timestamp"]),
            stake.get("status", "active"),
            stake.get("finished_timestamp"),
            stake.get("cancelled_timestamp"),
        ),
    )
    _sync_legacy_activos(list_activos())


# ---------------------------------------------------------
# MOVER A COMPLETADOS
# ---------------------------------------------------------
def move_to_completed(stake_id):
    stake = get_stake(stake_id)
    if not stake or stake.get("status") != "active":
        return False

    finished_timestamp = int(time.time())
    updated = run_execute(
        """
        UPDATE stakes
        SET status = 'finished', finished_timestamp = %s
        WHERE stake_id = %s::uuid AND status = 'active'
        """,
        (finished_timestamp, stake_id),
    )
    if not updated:
        return False

    stake["status"] = "finished"
    stake["finished_timestamp"] = finished_timestamp
    _sync_legacy_activos(list_activos())
    _append_to_completed_chunk(stake)
    return True


# ---------------------------------------------------------
# MOVER A CANCELADOS
# ---------------------------------------------------------
def move_to_cancelled(stake_id):
    stake = get_stake(stake_id)
    if not stake or stake.get("status") != "active":
        return False

    cancelled_timestamp = int(time.time())
    updated = run_execute(
        """
        UPDATE stakes
        SET status = 'cancelled', cancelled_timestamp = %s
        WHERE stake_id = %s::uuid AND status = 'active'
        """,
        (cancelled_timestamp, stake_id),
    )
    if not updated:
        return False

    stake["status"] = "cancelled"
    stake["cancelled_timestamp"] = cancelled_timestamp
    _sync_legacy_activos(list_activos())
    _sync_legacy_cancelled_append(stake)
    return True


# ---------------------------------------------------------
# OBTENER STAKING POR ID
# ---------------------------------------------------------
def get_stake(stake_id):
    row = run_query_one(
        """
        SELECT stake_id, user_id, wallet, amount_bend, days, reward_don,
               transfer_tx_id, timestamp, end_timestamp, status,
               finished_timestamp, cancelled_timestamp
        FROM stakes
        WHERE stake_id = %s::uuid
        LIMIT 1
        """,
        (stake_id,),
    )
    return _stake_row_to_dict(row) if row else None


# ---------------------------------------------------------
# LISTAR TODOS LOS STAKINGS ACTIVOS
# ---------------------------------------------------------
def list_activos():
    rows = run_query(
        """
        SELECT stake_id, user_id, wallet, amount_bend, days, reward_don,
               transfer_tx_id, timestamp, end_timestamp, status,
               finished_timestamp, cancelled_timestamp
        FROM stakes
        WHERE status = 'active'
        ORDER BY timestamp ASC, stake_id ASC
        """
    )
    return [_stake_row_to_dict(row) for row in rows]


def list_user_activos(user_id):
    rows = run_query(
        """
        SELECT stake_id, user_id, wallet, amount_bend, days, reward_don,
               transfer_tx_id, timestamp, end_timestamp, status,
               finished_timestamp, cancelled_timestamp
        FROM stakes
        WHERE user_id = %s AND status = 'active'
        ORDER BY timestamp DESC, stake_id ASC
        """,
        (str(user_id),),
    )
    return [_stake_row_to_dict(row) for row in rows]


def list_user_history(user_id):
    rows = run_query(
        """
        SELECT stake_id, user_id, wallet, amount_bend, days, reward_don,
               transfer_tx_id, timestamp, end_timestamp, status,
               finished_timestamp, cancelled_timestamp
        FROM stakes
        WHERE user_id = %s AND status IN ('finished', 'cancelled')
        ORDER BY COALESCE(finished_timestamp, cancelled_timestamp, end_timestamp) DESC, stake_id ASC
        """,
        (str(user_id),),
    )
    return [_stake_row_to_dict(row) for row in rows]
