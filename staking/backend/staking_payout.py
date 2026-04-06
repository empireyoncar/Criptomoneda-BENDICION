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
    pagados = {p.get("stake_id") for p in payouts if p.get("stake_id")}

    nuevos_pagos = []
    cambios_recompensas = False

    for item in recompensas:
        if item.get("status") != "pending":
            continue

        stake_id = item.get("stake_id")
        if not stake_id:
            continue

        if stake_id in pagados:
            # Si por alguna razón quedó pending pero ya existe en payouts,
            # sincronizamos estado para mantener consistencia.
            item["status"] = "paid"
            item["paid_timestamp"] = item.get("paid_timestamp", int(time.time()))
            cambios_recompensas = True
            continue

        user_id = item.get("user_id")
        reward = item.get("reward_don")
        if reward is None:
            reward = item.get("reward")

        if not user_id or reward is None:
            continue

        try:
            reward = float(reward)
        except (TypeError, ValueError):
            item["last_error"] = "reward_invalido"
            item["last_attempt_timestamp"] = int(time.time())
            item["attempt_count"] = int(item.get("attempt_count", 0)) + 1
            cambios_recompensas = True
            continue

        if reward <= 0:
            item["last_error"] = "reward_no_positivo"
            item["last_attempt_timestamp"] = int(time.time())
            item["attempt_count"] = int(item.get("attempt_count", 0)) + 1
            cambios_recompensas = True
            continue

        # PAGAR DON
        try:
            res = requests.post(DON_API_URL, json={
                "user_id": user_id,
                "amount": reward,
                "metadata": {
                    "source": "staking_recompensa",
                    "stake_id": stake_id,
                    "reward_timestamp": item.get("timestamp")
                }
            }, timeout=15)
            res.raise_for_status()
            try:
                api_response = res.json()
            except ValueError:
                api_response = {"raw": res.text}
        except Exception as e:
            print("Error pagando DON:", e)
            item["last_error"] = str(e)
            item["last_attempt_timestamp"] = int(time.time())
            item["attempt_count"] = int(item.get("attempt_count", 0)) + 1
            cambios_recompensas = True
            continue

        # CAMBIAR ESTADO A PAID
        item["status"] = "paid"
        item["paid_timestamp"] = int(time.time())
        cambios_recompensas = True

        # REGISTRAR LOG DE PAGO
        nuevos_pagos.append({
            "payout_id": str(uuid.uuid4()),
            "stake_id": stake_id,
            "user_id": user_id,
            "wallet": item.get("wallet"),
            "amount": reward,
            "asset": "DON",
            "status": "paid",
            "created_timestamp": int(item.get("timestamp", time.time())),
            "paid_timestamp": int(time.time()),
            "source": "staking_recompensa",
            "reward_record_timestamp": item.get("timestamp"),
            "transfer_tx_id": item.get("transfer_tx_id"),
            "don_api": {
                "http_status": "OK",
                "response_body": api_response,
                "tx_id": api_response.get("tx_id") if isinstance(api_response, dict) else None
            },
            "idempotency_key": f"stake:{stake_id}",
            "support_note": "Pago automatico por vencimiento de staking"
        })

    # GUARDAR CAMBIOS
    if nuevos_pagos:
        payouts.extend(nuevos_pagos)
        save_json(PAYOUT_FILE, payouts)

    if cambios_recompensas:
        save_json(RECOMPENSAS_FILE, recompensas)


if __name__ == "__main__":
    process_payouts()
