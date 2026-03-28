import uuid
from datetime import datetime, timedelta
from staking import load_staking, save_staking, move_to_history
from staking import load_history, save_history


# ---------------------------------------------------------
#   GENERAR ID ÚNICO
# ---------------------------------------------------------
def generate_stake_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------
#   CALCULAR APR SEGÚN DÍAS
# ---------------------------------------------------------
def get_apr(days):
    if days == 30:
        return 5
    elif days == 60:
        return 12
    elif days == 90:
        return 20
    return 5  # default


# ---------------------------------------------------------
#   CALCULAR RECOMPENSA DIARIA
# ---------------------------------------------------------
def calculate_daily_reward(amount, apr):
    return round(amount * (apr / 100) / 365, 8)


# ---------------------------------------------------------
#   GENERAR STAKE COMPLETO
# ---------------------------------------------------------
def generar_stake_completo(user_id, amount, days):
    apr = get_apr(days)
    start = datetime.utcnow()
    end = start + timedelta(days=days)

    reward_daily = calculate_daily_reward(amount, apr)

    stake = {
        "stake_id": generate_stake_id(),
        "user_id": user_id,
        "amount": amount,
        "days": days,
        "apr": apr,
        "reward_daily": reward_daily,
        "reward_acumulada": 0.0,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "last_reward_date": start.isoformat(),
        "status": "locked"
    }

    return stake


# ---------------------------------------------------------
#   PROCESAR RECOMPENSAS DIARIAS
# ---------------------------------------------------------
def process_daily_rewards():
    staking = load_staking()
    now = datetime.utcnow()

    for stake in staking["stakes"]:
        if stake["status"] != "locked":
            continue

        last = datetime.fromisoformat(stake["last_reward_date"])

        # Si ya pasó 1 día, pagar recompensa
        if (now - last).days >= 1:
            stake["reward_acumulada"] += stake["reward_daily"]
            stake["last_reward_date"] = now.isoformat()

    save_staking(staking)


# ---------------------------------------------------------
#   LIBERAR STAKES COMPLETADOS
# ---------------------------------------------------------
def release_finished_stakes():
    staking = load_staking()
    now = datetime.utcnow()

    for stake in staking["stakes"]:
        if stake["status"] != "locked":
            continue

        end = datetime.fromisoformat(stake["end_date"])

        if now >= end:
            stake["status"] = "completed"
            move_to_history(stake["stake_id"], reason="completed")

    save_staking(staking)


# ---------------------------------------------------------
#   CANCELAR STAKE (RETIRO ANTICIPADO)
# ---------------------------------------------------------
def cancel_stake(stake_id):
    staking = load_staking()

    stake = next((s for s in staking["stakes"] if s["stake_id"] == stake_id), None)
    if not stake:
        return {"error": "Stake no encontrado"}

    # Penalización: perder recompensas
    stake["reward_acumulada"] = 0.0
    stake["status"] = "cancelled"

    move_to_history(stake_id, reason="cancelled")

    save_staking(staking)
    return {"success": True}


# ---------------------------------------------------------
#   CRON JOB AUTOMÁTICO
# ---------------------------------------------------------
def cron_job():
    """
    Esta función debe ejecutarse cada X minutos.
    - Paga recompensas diarias
    - Libera stakes completados
    """
    process_daily_rewards()
    release_finished_stakes()

    return {"cron": "ok"}
