import uuid
from datetime import datetime, timedelta
from staking import load_staking, save_staking, move_to_history


# ---------------------------------------------------------
#   GENERAR ID ÚNICO
# ---------------------------------------------------------
def generate_stake_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------
#   TABLA DE RECOMPENSAS FIJAS EN DON
# ---------------------------------------------------------
def get_total_don_reward(days, amount):
    reward_table = {
        30: 6.6,
        60: 15,
        90: 25,
        180: 55,
        365: 120
    }

    base_reward = reward_table.get(days, 0)

    # Recompensa proporcional al monto
    return (amount / 1000) * base_reward


# ---------------------------------------------------------
#   CALCULAR RECOMPENSA DIARIA (DON / días)
# ---------------------------------------------------------
def calculate_daily_reward(total_reward, days):
    return round(total_reward / days, 8)


# ---------------------------------------------------------
#   TOTAL GLOBAL STAKEADO
# ---------------------------------------------------------
def get_total_staked():
    staking = load_staking()
    total = sum(float(s["amount"]) for s in staking["stakes"] if s["status"] == "locked")
    return total


# ---------------------------------------------------------
#   GENERAR STAKE COMPLETO
# ---------------------------------------------------------
def generar_stake_completo(user_id, amount, days):

    # 🔥 1. Verificar límite global de 10.000 BEND
    total_actual = get_total_staked()
    if total_actual + amount > 10000:
        return {"error": "Límite global de 10.000 BENDICIÓN en staking alcanzado"}

    # 🔥 2. Fechas
    start = datetime.utcnow()
    end = start + timedelta(days=days)

    # 🔥 3. Recompensas
    total_reward = get_total_don_reward(days, amount)
    reward_daily = calculate_daily_reward(total_reward, days)

    # 🔥 4. Crear stake
    stake = {
        "stake_id": generate_stake_id(),
        "user_id": user_id,
        "amount": amount,
        "days": days,
        "total_reward": total_reward,
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
