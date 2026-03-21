import json
import os
from wallet_manager import load_wallets, save_wallets, load_db, save_db

STAKING_FILE = os.path.join("/app/db", "staking.json")

# Crear archivo si no existe
if not os.path.exists(STAKING_FILE):
    with open(STAKING_FILE, "w") as f:
        json.dump({"stakes": []}, f, indent=4)

def load_staking():
    with open(STAKING_FILE, "r") as f:
        return json.load(f)

def save_staking(data):
    with open(STAKING_FILE, "w") as f:
        json.dump(data, f, indent=4)

def create_stake(user_id, amount, days):
    staking = load_staking()

    stake = {
        "user_id": user_id,
        "amount": float(amount),
        "days": int(days),
        "status": "locked"
    }

    staking["stakes"].append(stake)
    save_staking(staking)

    return stake
