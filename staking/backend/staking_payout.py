import json
import requests
import os

HISTORY_FILE = "/app/stakingcompletados_history.json"
PAYOUT_FILE = "/app/staking_payout.json"
DON_API_URL = "http://don_api:5008/don/add"


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except:
            return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def process_payouts():
    history = load_json(HISTORY_FILE)
    payouts = load_json(PAYOUT_FILE)

    # evitar pagos duplicados
    pagados = {p["staking_id"] for p in payouts}

    nuevos_pagos = []

    for item in history:
        staking_id = item.get("staking_id")
        if staking_id in pagados:
            continue

        user_id = item.get("user_id")
        reward = item.get("reward")

        if not user_id or reward is None:
            continue

        # pagar DON
        try:
            requests.post(DON_API_URL, json={
                "user_id": user_id,
                "amount": reward
            })
        except:
            continue

        # registrar pago
        nuevos_pagos.append({
            "staking_id": staking_id,
            "user_id": user_id,
            "amount": reward
        })

    if nuevos_pagos:
        payouts.extend(nuevos_pagos)
        save_json(PAYOUT_FILE, payouts)


if __name__ == "__main__":
    process_payouts()
