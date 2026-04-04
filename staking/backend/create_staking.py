import requests
import uuid
import time

from staking_data import add_staking

BLOCKCHAIN_SERVER = "http://blockchain_api:5004"

# Wallet del administrador donde se guardan los tokens stakeados
ADMIN_WALLET = "bc1caf7ddb9d0f14e32e5806582efc561fa554661e5ac96235c52634b3b48c80"

# Tabla de recompensas según días
REWARD_TABLE = {
    30: 6.6,
    60: 15,
    90: 25,
    180: 55,
    365: 120
}


def restar_bendicion(wallet_address, amount):
    """
    Resta criptomoneda Bendición (BEND) del usuario
    enviándola a la wallet del administrador.
    """

    tx = {
        "from": wallet_address,
        "to": ADMIN_WALLET,
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
        raise Exception("Error al transferir Bendición en la blockchain")

    return True


def confirmar_transaccion():
    """
    Confirma la transacción en la blockchain.
    """
    res = requests.post(f"{BLOCKCHAIN_SERVER}/commit")

    if res.status_code != 200:
        raise Exception("Error al confirmar la transacción en blockchain")

    return True


def crear_staking(user_id, wallet_address, amount, days):
    """
    1. Resta Bendición al usuario (envía al admin)
    2. Confirma la transacción
    3. Calcula recompensa DON
    4. Crea registro del staking
    """

    # 1. RESTAR BENDICIÓN (BEND)
    restar_bendicion(wallet_address, amount)

    # 2. CONFIRMAR TRANSACCIÓN
    confirmar_transaccion()

    # 3. CALCULAR RECOMPENSA DON
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
        "amount_bend": amount,
        "days": int(days),
        "reward_don": reward_total,
        "reward_claimed": False,
        "timestamp": timestamp,
        "end_timestamp": end_timestamp,
        "status": "active"
    }

    add_staking(new_stake)

    return {
        "status": "success",
        "stake_id": stake_id,
        "reward_don": reward_total,
        "message": "Staking creado correctamente"
    }
