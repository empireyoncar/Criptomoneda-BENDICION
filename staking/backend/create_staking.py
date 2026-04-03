import requests
import uuid
import time

from staking_data import add_staking

BLOCKCHAIN_SERVER = "http://blockchain_api:5004"
STAKING_POOL = "STAKING_POOL"

# Tabla de recompensas según días
REWARD_TABLE = {
    30: 6.6,
    60: 15,
    90: 25,
    180: 55,
    365: 120
}


def bloquear_tokens(wallet_address, amount):
    tx = {
        "from": wallet_address,
        "to": STAKING_POOL,
        "amount": amount
    }

    res = requests.post(
        f"{BLOCKCHAIN_SERVER}/send_tx",
        json={
            "tx": tx,
            "public_key": "0" * 64,
            "signature": "0" * 128
        }
    )

    if res.status_code != 200:
        raise Exception("Error al bloquear tokens en blockchain")

    return True


def confirmar_bloqueo():
    res = requests.post(f"{BLOCKCHAIN_SERVER}/commit")

    if res.status_code != 200:
        raise Exception("Error al confirmar el bloqueo en blockchain")

    return True


def crear_staking(user_id, wallet_address, amount, days):
    """
    1. Bloquea tokens
    2. Confirma bloqueo
    3. Crea registro del staking con recompensa fija
    """

    # 1. BLOQUEAR TOKENS
    bloquear_tokens(wallet_address, amount)

    # 2. CONFIRMAR BLOQUEO
    confirmar_bloqueo()

    # 3. CALCULAR RECOMPENSA TOTAL
    don_base = REWARD_TABLE.get(int(days), 0)
    reward_total = (amount / 1000) * don_base

    # 4. CREAR REGISTRO DEL STAKING
    stake_id = str(uuid.uuid4())
    timestamp = int(time.time())
    end_timestamp = timestamp + (int(days) * 24 * 3600)

    new_stake = {
        "stake_id": stake_id,
        "user_id": user_id,
        "wallet": wallet_address,
        "amount": amount,
        "days": int(days),
        "reward_total": reward_total,
        "reward_claimed": False,
        "timestamp": timestamp,
        "end_timestamp": end_timestamp,
        "status": "active"
    }

    add_staking(new_stake)

    return {
        "status": "success",
        "stake_id": stake_id,
        "reward_total": reward_total,
        "message": "Staking creado correctamente"
    }
