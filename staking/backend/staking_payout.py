# staking/backend/staking_payout.py

from staking.backend.staking_data import load_staking, save_staking, move_to_history
from wallet.backend.wallet_manager import load_wallets
import requests

# URL del microservicio DON (nombre del servicio en docker-compose)
DON_URL = "http://don_api:5008"

def don_add(user_id, amount):
    """Llama al microservicio DON para crear tokens (mint)."""
    try:
        requests.post(f"{DON_URL}/don/add", json={
            "user_id": user_id,
            "amount": amount
        })
    except Exception as e:
        print(f"❌ Error llamando a DON: {e}")


def pay_completed_stakes():
    """
    - Busca stakes completados
    - Crea DON como recompensa (vía API DON)
    - Mueve stake al historial
    """

    staking = load_staking()
    wallets = load_wallets()

    pagados = 0

    for stake in staking["stakes"]:
        if stake["status"] != "completed":
            continue

        user_id = stake["user_id"]
        reward = float(stake["reward_acumulada"])

        # Verificar que el usuario tiene wallet
        wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)
        if wallet is None:
            print(f"⚠ No se encontró wallet para user_id {user_id}")
            continue

        # Crear DON (mint) vía API DON
        don_add(user_id, reward)

        # Marcar stake como pagado
        stake["status"] = "paid"

        # Mover al historial
        move_to_history(stake["stake_id"], reason="reward_paid")

        pagados += 1

    save_staking(staking)

    return {
        "status": "ok",
        "pagados": pagados
    }
