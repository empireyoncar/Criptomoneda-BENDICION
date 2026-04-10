import time

from flask import Flask, request, jsonify
from create_staking import crear_staking   # <--- IMPORTAMOS TU FUNCIÓN
from staking_data import list_user_activos, list_user_history

app = Flask(__name__)


def _serialize_active_stake(stake):
    start_ts = int(stake["timestamp"])
    end_ts = int(stake["end_timestamp"])
    now_ts = int(time.time())
    total_seconds = max(1, end_ts - start_ts)
    elapsed_seconds = max(0, min(now_ts - start_ts, total_seconds))
    progress_percent = round((elapsed_seconds / total_seconds) * 100, 2)
    reward_total = float(stake.get("reward_don", 0))
    reward_accumulated = round(reward_total * (elapsed_seconds / total_seconds), 8)

    return {
        "stake_id": stake["stake_id"],
        "wallet": stake["wallet"],
        "amount": int(stake["amount_bend"]),
        "days": int(stake["days"]),
        "reward_total": reward_total,
        "reward_acumulada": reward_accumulated,
        "progress_percent": progress_percent,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "start_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_ts)),
        "end_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_ts)),
        "status": stake["status"],
        "transfer_tx_id": stake.get("transfer_tx_id"),
    }


def _serialize_history_stake(stake):
    final_timestamp = stake.get("finished_timestamp") or stake.get("cancelled_timestamp") or stake.get("end_timestamp")
    return {
        "stake_id": stake["stake_id"],
        "wallet": stake["wallet"],
        "amount": int(stake["amount_bend"]),
        "days": int(stake["days"]),
        "total_reward": float(stake.get("reward_don", 0)),
        "status": stake["status"],
        "start_timestamp": int(stake["timestamp"]),
        "end_timestamp": int(stake["end_timestamp"]),
        "final_timestamp": int(final_timestamp) if final_timestamp else None,
        "start_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(stake["timestamp"]))),
        "end_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(stake["end_timestamp"]))),
        "final_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(final_timestamp))) if final_timestamp else None,
        "transfer_tx_id": stake.get("transfer_tx_id"),
    }

# ---------------------------------------------------------
#   CREAR STAKING (USADO POR EL FRONTEND)
# ---------------------------------------------------------
@app.post("/Staking/create")
def api_create_staking():
    data = request.json

    required = ["user_id", "wallet", "amount", "days", "transfer_tx_id"]
    if not all(k in data for k in required):
        return jsonify({"error": "Faltan parámetros"}), 400

    try:
        result = crear_staking(
            user_id=data["user_id"],
            wallet_address=data["wallet"],
            amount=float(data["amount"]),
            days=int(data["days"]),
            transfer_tx_id=data["transfer_tx_id"]
        )
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/Staking/user/<user_id>")
def api_user_active_stakes(user_id):
    stakes = [_serialize_active_stake(stake) for stake in list_user_activos(user_id)]
    return jsonify({"stakes": stakes})


@app.get("/Staking/history/<user_id>")
def api_user_staking_history(user_id):
    history = [_serialize_history_stake(stake) for stake in list_user_history(user_id)]
    return jsonify({"history": history})


# ---------------------------------------------------------
#   INICIAR SERVIDOR
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)
