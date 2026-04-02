# staking_manager.py
import requests
from staking_data import load_staking, save_staking
from staking_recompensa import generar_stake_completo

# ============================================================
#   FUNCIONES PARA COMUNICARSE CON WALLET
# ============================================================
def load_wallets():
    try:
        r = requests.get("http://wallet_api:5002/get_wallets")
        return r.json()
    except:
        return {"wallets": []}

# ============================================================
#   FUNCIONES PARA COMUNICARSE CON BLOCKCHAIN
# ============================================================
def get_balance(address):
    r = requests.get(f"http://blockchain_api:5004/get_balance/{address}")
    return r.json().get("balance", 0)

def get_locked(address):
    r = requests.get(f"http://blockchain_api:5004/get_locked/{address}")
    return r.json().get("locked", 0)

def lock_balance(address, amount):
    r = requests.post("http://blockchain_api:5004/lock_balance", json={
        "address": address,
        "amount": amount
    })
    return r.json().get("success", False)

# ============================================================
#   VALIDAR USUARIO + WALLET + SALDO REAL
# ============================================================
def get_user_staking_info(user_id):
    if not user_id:
        return {"error": "Usuario no autenticado"}

    wallets = load_wallets()
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "El usuario no tiene wallet asociada"}

    address = wallet["address"]

    balance = get_balance(address)
    locked = get_locked(address)
    available = balance - locked

    return {
        "user_id": user_id,
        "wallet_address": address,
        "balance": balance,
        "locked": locked,
        "available": available
    }

# ============================================================
#   CREAR STAKE
# ============================================================
def create_stake(user_id, amount, days):
    try:
        amount = float(amount)
        days = int(days)
    except:
        return {"error": "Parámetros inválidos"}

    wallets = load_wallets()
    wallet = next((w for w in wallets["wallets"] if w["user_id"] == user_id), None)

    if wallet is None:
        return {"error": "Wallet no encontrada"}

    address = wallet["address"]

    balance = get_balance(address)
    locked = get_locked(address)
    available = balance - locked

    if available < amount:
        return {"error": "Saldo insuficiente"}

    # Bloquear saldo en blockchain
    if not lock_balance(address, amount):
        return {"error": "No se pudo bloquear el saldo"}

    # Generar stake completo
    stake_data = generar_stake_completo(user_id, amount, days)

    # Guardar stake
    staking = load_staking()
    staking["stakes"].append(stake_data)
    save_staking(staking)

    return {"success": True, "stake": stake_data}
