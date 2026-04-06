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

    tx_id = str(uuid.uuid4())
    tx = {
        "from": wallet_address,
        "to": ADMIN_WALLET,
        "amount": amount,
        "tx_id": tx_id,
        "metadata": {
            "type": "staking_lock"
        }
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

    return tx_id


def rollback_transfer(wallet_address, amount, original_tx_id):
    """
    Si falla la persistencia del staking después del commit,
    devuelve los BEND desde admin al usuario.
    """
    rollback_tx = {
        "from": ADMIN_WALLET,
        "to": wallet_address,
        "amount": amount,
        "tx_id": f"rollback-{original_tx_id}",
        "metadata": {
            "type": "staking_rollback",
            "original_tx_id": original_tx_id
        }
    }

    res = requests.post(
        f"{BLOCKCHAIN_SERVER}/send_tx",
        json={
            "tx": rollback_tx,
            "public_key": "0" * 64,
            "signature": "0" * 128
        }
    )

    if res.status_code != 200:
        raise Exception("No se pudo crear la transacción de rollback")

    confirmar_transaccion()
    return rollback_tx["tx_id"]


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

    if int(days) not in REWARD_TABLE:
        raise ValueError("Días inválidos. Solo se permiten: 30, 60, 90, 180, 365")

    if float(amount) <= 0:
        raise ValueError("Monto inválido. Debe ser mayor que 0")

    # 1. TRANSFERIR BENDICIÓN (BEND) DEL USUARIO AL ADMIN
    transfer_tx_id = restar_bendicion(wallet_address, amount)

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
        "transfer_tx_id": transfer_tx_id,
        "timestamp": timestamp,
        "end_timestamp": end_timestamp,
        "status": "active"
    }

    try:
        add_staking(new_stake)
    except Exception as e:
        rollback_tx_id = rollback_transfer(wallet_address, amount, transfer_tx_id)
        raise Exception(
            f"Error guardando staking. Se ejecutó rollback automático. "
            f"transfer_tx_id={transfer_tx_id}, rollback_tx_id={rollback_tx_id}. Detalle: {e}"
        )

    return {
        "status": "success",
        "stake_id": stake_id,
        "transfer_tx_id": transfer_tx_id,
        "reward_don": reward_total,
        "message": "Staking creado correctamente"
    }
