# wallet_manager.py
import json
import os
from wallet import generate_wallet

WALLETS_FILE = os.path.join("/app/db", "wallets.json")
DB_FILE = os.path.join("/app/db", "database.json")

# Crear wallets.json si no existe
if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump({"wallets": []}, f, indent=4)

def load_wallets():
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(data):
    with open(WALLETS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_wallet_for_user(user_id):
    # Generar wallet real
    wallet = generate_wallet()

    # Guardar en wallets.json
    wallets = load_wallets()
    wallets["wallets"].append({
        "user_id": user_id,
        "private_key": wallet["private_key"],
        "public_key": wallet["public_key"],
        "address": wallet["address"]
    })
    save_wallets(wallets)

    # Guardar address en database.json
    db = load_db()
    for u in db["users"]:
        if u["id"] == user_id:
            u["wallets"].append(wallet["address"])
            break
    save_db(db)

    return wallet
