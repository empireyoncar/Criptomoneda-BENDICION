import json
from wallet_manager import load_wallets, save_wallets
from staking import register_stake
from staking_calculo import generar_stake_completo   # este genera ID, fechas, APR, etc.


# ---------------------------------------------------------
#   STAKE TOKENS (LÓGICA DE NEGOCIO)
# ---------------------------------------------------------
def stake_tokens(user_id, amount, days):
    """
    Conecta la wallet con el sistema de staking.
    - Verifica saldo
    - Resta saldo
    - Genera stake completo (ID, fechas, APR, etc.)
    - Registra stake en staking.json
    """

    try:
        amount = float(amount)
        days = int(days)
    except:
        return {"error": "Parámetros inválidos"}

    # Cargar wallets
    wallets = load_wallets()

    # Buscar wallet del usuario
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "Wallet no encontrada"}

    # Asegurar que tenga balance
    if "balance" not in wallet:
        wallet["balance"] = 0.0

    # Verificar saldo suficiente
    if wallet["balance"] < amount:
        return {"error": "Saldo insuficiente"}

    # Restar saldo
    wallet["balance"] -= amount
    save_wallets(wallets)

    # Generar stake completo (ID, fechas, APR, reward diario, etc.)
    stake_data = generar_stake_completo(user_id, amount, days)

    # Registrar stake en staking.json
    stake_registrado = register_stake(stake_data)

    return {
        "success": True,
        "stake": stake_registrado
    }
