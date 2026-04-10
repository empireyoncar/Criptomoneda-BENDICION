import time

from staking_db import ensure_schema, run_execute, run_query, run_query_one


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
    return True


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
