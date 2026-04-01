from flask import Flask, request, jsonify
from staking_manager import stake_tokens
from staking_dashboard import (
    get_balance, get_stakes, get_history,
    get_rewards, release_stake, cancel_stake_api
)
from staking_recompensa import cron_job

app = Flask(__name__)


# ---------------------------------------------------------
#   STATUS DEL SERVIDOR
# ---------------------------------------------------------
@app.get("/")
def home():
    return jsonify({"status": "staking server online"})


# ---------------------------------------------------------
#   CREAR NUEVO STAKE
# ---------------------------------------------------------
@app.post("/stake")
def api_stake():
    data = request.json

    user_id = data.get("user_id")
    amount = data.get("amount")
    days = data.get("days")

    if not user_id or not amount or not days:
        return jsonify({"error": "Faltan parámetros"}), 400

    result = stake_tokens(user_id, amount, days)
    return jsonify(result)


# ---------------------------------------------------------
#   ENDPOINTS DEL DASHBOARD
# ---------------------------------------------------------
@app.get("/dashboard/balance/<user_id>")
def api_balance(user_id):
    return get_balance(user_id)


@app.get("/dashboard/stakes/<user_id>")
def api_stakes(user_id):
    return get_stakes(user_id)


@app.get("/dashboard/history/<user_id>")
def api_history(user_id):
    return get_history(user_id)


@app.get("/dashboard/rewards/<user_id>")
def api_rewards(user_id):
    return get_rewards(user_id)


@app.post("/dashboard/release/<stake_id>")
def api_release(stake_id):
    return release_stake(stake_id)


@app.post("/dashboard/cancel/<stake_id>")
def api_cancel(stake_id):
    return cancel_stake_api(stake_id)


# ---------------------------------------------------------
#   CRON JOB AUTOMÁTICO
# ---------------------------------------------------------
@app.get("/cron")
def api_cron():
    """
    Este endpoint puede ser llamado por:
    - un cron real del servidor
    - UptimeRobot
    - Cron-job.org
    - Tu propio script
    """
    result = cron_job()
    return jsonify(result)
def get_total_staked():
    staking = load_staking()
    total = sum(float(s["amount"]) for s in staking["stakes"] if s["status"] == "locked")
    return total


# ---------------------------------------------------------
#   INICIAR SERVIDOR
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)
