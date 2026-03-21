import json
import os
from wallet_manager import load_wallets, save_wallets
from staking import create_stake   # tu motor de staking

def stake_tokens(user_id, amount, days):
    amount = float(amount)

    wallets = load_wallets()

    # Buscar wallet del usuario
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "Wallet no encontrada"}

    # Si no existe balance, lo inicializamos
    if "balance" not in wallet:
        wallet["balance"] = 0.0

    # Verificar saldo
    if wallet["balance"] < amount:
        return {"error": "Saldo insuficiente"}

    # Restar saldo
    wallet["balance"] -= amount
    save_wallets(wallets)

    # Registrar staking
    stake = create_stake(user_id, amount, days)

    return {"success": True, "stake": stake}
