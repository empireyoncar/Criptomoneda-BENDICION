from flask import jsonify

# IMPORTS CORRECTOS SEGÚN TU ESTRUCTURA REAL
from wallet.backend.wallet_manager import load_wallets
from staking.backend.staking_data import load_staking, load_history
from staking.backend.staking_recompensa import release_finished_stakes, cancel_stake


# ============================================================
#   OBTENER BALANCE DEL USUARIO
# ============================================================
def get_balance(user_id):
    wallets = load_wallets()

    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return jsonify({"error": "Wallet no encontrada"}), 404

    balance = wallet.get("balance", 0.0)

    return jsonify({
        "user_id": user_id,
        "balance": balance
    })


# ============================================================
#   OBTENER STAKES ACTIVOS DEL USUARIO
# ============================================================
def get_stakes(user_id):
    staking = load_staking()

    stakes_user = [s for s in staking["stakes"] if s["user_id"] == user_id]

    return jsonify({
        "user_id": user_id,
        "stakes": stakes_user
    })


# ============================================================
#   OBTENER HISTORIAL DEL USUARIO
# ============================================================
def get_history(user_id):
    history = load_history()

    history_user = [h for h in history["history"] if h["user_id"] == user_id]

    return jsonify({
        "user_id": user_id,
        "history": history_user
    })


# ============================================================
#   OBTENER RECOMPENSAS ACUMULADAS
# ============================================================
def get_rewards(user_id):
    staking = load_staking()

    total_rewards = sum(
        s.get("reward_acumulada", 0.0)
        for s in staking["stakes"]
        if s["user_id"] == user_id
    )

    return jsonify({
        "user_id": user_id,
        "rewards": round(total_rewards, 8)
    })


# ============================================================
#   LIBERAR STAKE MANUALMENTE
# ============================================================
def release_stake(stake_id):
    """
    Llama a release_finished_stakes() para procesar automáticamente,
    pero también permite liberar manualmente un stake si ya cumplió.
    """
    release_finished_stakes()
    return jsonify({"success": True, "message": "Stake liberado si estaba listo"})


# ============================================================
#   CANCELAR STAKE (RETIRO ANTICIPADO)
# ============================================================
def cancel_stake_api(stake_id):
    result = cancel_stake(stake_id)

    if "error" in result:
        return jsonify(result), 400

    return jsonify({"success": True, "message": "Stake cancelado correctamente"})
