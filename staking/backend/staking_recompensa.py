import json
import os
import time

import staking_data
import staking_payout  # ← Import directo, sin subprocess

RECOMPENSAS_PATH = "/app/backend/staking_recompensa.json"

if not os.path.exists(RECOMPENSAS_PATH):
    with open(RECOMPENSAS_PATH, "w") as f:
        json.dump([], f)


def load_recompensas():
    with open(RECOMPENSAS_PATH, "r") as f:
        return json.load(f)


def save_recompensas(data):
    with open(RECOMPENSAS_PATH, "w") as f:
        json.dump(data, f, indent=4)


def procesar_recompensas():
    ahora = int(time.time())

    activos = staking_data.list_activos()
    recompensas = load_recompensas()

    for stake in activos:
        if stake["end_timestamp"] <= ahora:
            stake_id = stake["stake_id"]
            stake["status"] = "finished"

            staking_data.move_to_completed(stake_id)

            recompensa = {
                "stake_id": stake["stake_id"],
                "user_id": stake["user_id"],
                "wallet": stake["wallet"],
                "reward_don": stake["reward_don"],
                "timestamp": ahora,
                "status": "pending"
            }

            recompensas.append(recompensa)
            print(f"[OK] Staking finalizado: {stake_id} → recompensa generada")

    save_recompensas(recompensas)
    print("Proceso de recompensas completado.")

    # 🔥 EJECUTAR payout de forma segura
    try:
        print("Ejecutando payout...")
        staking_payout.process_payouts()
        print("Payout ejecutado correctamente.")
    except Exception as e:
        print("Error ejecutando payout:", e)


if __name__ == "__main__":
    while True:
        print("Ejecutando proceso de recompensas...")
        procesar_recompensas()
        print("Proceso completado. Próxima ejecución en 12 horas.")
        time.sleep(43200)
