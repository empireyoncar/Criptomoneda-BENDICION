import json
import requests
import os
import time
import uuid

PAYOUT_FILE = "/app/backend/staking_payout.json"
RECOMPENSAS_FILE = "/app/backend/staking_recompensa.json"

# MISMO ENDPOINT QUE USA EL FRONTEND
DON_API_URL = "https://empireyoncar.duckdns.org/CriptoBendicion/don_api/don/add"


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def process_payouts():
    recompensas = load_json(RECOMPENSAS_FILE)
    payouts = load_json(PAYOUT_FILE)

    # evitar pagos duplicados
    pagados = {p["stake_id"] for p in payouts}

    nuevos_pagos = []
    cambios_recompensas = False

    for item in recompensas:
        if item.get("status") != "pending":
            continue

        stake_id = item.get("stake_id")
        if stake_id in pagados:
            continue

        user_id = item.get("user_id")
        reward = item.get("reward_don") or item.get("reward")

        if not user_id or reward is None:
            continue

        # PAGAR DON
        try:
            res = requests.post(DON_API_URL, json={
                "user_id": user_id,
                "amount": reward
            })
            res.raise_for_status()
            api_response = res.text
        except Exception as e:
            print("Error pagando DON:", e)
            continue

        # CAMBIAR ESTADO A PAID
        item["status"] = "paid"
        item["paid_timestamp"] = int(time.time())
        cambios_recompensas = True

        # REGISTRAR LOG DE PAGO
        nuevos_pagos.append({
            "stake_id": stake_id,
            "user_id": user_id,
            "amount": reward,
            "status": "paid",
            "timestamp": int(time.time()),
            "tx_id": str(uuid.uuid4()),
            "source": "staking_recompensa",
            "don_api_response": api_response
        })

    # GUARDAR CAMBIOS
    if nuevos_pagos:
        payouts.extend(nuevos_pagos)
        save_json(PAYOUT_FILE, payouts)

    if cambios_recompensas:
        save_json(RECOMPENSAS_FILE, recompensas)


if __name__ == "__main__":
    process_payouts()
