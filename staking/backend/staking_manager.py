# staking_manager.py
from wallet.backend.wallet_manager import load_wallets
from Blockchain.bakend.blockchain import Blockchain
from staking.backend.staking_data import load_staking, save_staking
from staking.backend.staking_recompensa import generar_stake_completo

# ============================================================
#   VALIDAR USUARIO + WALLET + SALDO REAL
# ============================================================
def get_user_staking_info(user_id):
    """
    Devuelve al frontend:
    - wallet del usuario
    - saldo real en blockchain
    - saldo bloqueado
    - saldo disponible
    """

    if not user_id:
        return {"error": "Usuario no autenticado"}

    # Buscar wallet asociada al usuario
    wallets = load_wallets()
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "El usuario no tiene wallet asociada"}

    address = wallet["address"]

    # Obtener saldo real desde la blockchain
    bc = Blockchain()
    balance = bc.get_balance(address)
    locked = bc._get_locked_balance(address)
    available = balance - locked

    return {
        "user_id": user_id,
        "wallet_address": address,
        "balance": balance,
        "locked": locked,
        "available": available
    }


# ============================================================
#   CREAR STAKE (RESTA SALDO + BLOQUEA SALDO)
# ============================================================
def create_stake(user_id, amount, days):
    """
    - Valida saldo real en blockchain
    - Bloquea BEND para staking
    - Resta saldo real (commit)
    - Genera stake completo
    - Guarda stake en staking.json
    """

    try:
        amount = float(amount)
        days = int(days)
    except:
        return {"error": "Parámetros inválidos"}

    # Obtener wallet del usuario
    wallets = load_wallets()
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "Wallet no encontrada"}

    address = wallet["address"]

    # 1. Validar saldo real
    bc = Blockchain()
    balance = bc.get_balance(address)
    locked = bc._get_locked_balance(address)
    available = balance - locked

    if available < amount:
        return {"error": "Saldo insuficiente"}

    # 2. Bloquear saldo (transacción pendiente)
    ok = bc.add_transaction(address, "STAKING_LOCK", amount)
    if not ok:
        return {"error": "No se pudo bloquear el saldo"}

    # 3. Confirmar transacción (resta saldo real)
    bc.commit_pending_transactions()

    # 4. Generar stake completo
    stake_data = generar_stake_completo(user_id, amount, days)

    # 5. Guardar stake en staking.json
    staking = load_staking()
    staking["stakes"].append(stake_data)
    save_staking(staking)

    return {
        "success": True,
        "stake": stake_data
    }
