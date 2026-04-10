import uuid
import time

from staking_data import add_staking

# Tabla de recompensas según días
REWARD_TABLE = {
    30: 6.6,
    60: 15,
    90: 25,
    180: 55,
    365: 120
}
def crear_staking(user_id, wallet_address, amount, days, transfer_tx_id):
    """
    1. Recibe un transfer_tx_id ya confirmado en blockchain
    2. Calcula recompensa DON
    3. Crea registro del staking
    """

    if int(days) not in REWARD_TABLE:
        raise ValueError("Días inválidos. Solo se permiten: 30, 60, 90, 180, 365")

    if float(amount) <= 0:
        raise ValueError("Monto inválido. Debe ser mayor que 0")
    if not transfer_tx_id:
        raise ValueError("Falta transfer_tx_id de la transacción blockchain")

    # 2. CALCULAR RECOMPENSA DON
    don_base = REWARD_TABLE.get(int(days), 0)
    reward_total = (amount / 1000) * don_base

    # 3. CREAR REGISTRO DEL STAKING
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

    add_staking(new_stake)

    return {
        "status": "success",
        "stake_id": stake_id,
        "transfer_tx_id": transfer_tx_id,
        "reward_don": reward_total,
        "message": "Staking creado correctamente"
    }
