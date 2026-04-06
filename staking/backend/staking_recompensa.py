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
    if not os.path.exists(RECOMPENSAS_PATH):
        return []

    with open(RECOMPENSAS_PATH, "r") as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []


def save_recompensas(data):
    with open(RECOMPENSAS_PATH, "w") as f:
        json.dump(data, f, indent=4)


def procesar_recompensas():
    ahora = int(time.time())

    activos = staking_data.list_activos()
    recompensas = load_recompensas()
    recompensas_existentes = {
        r.get("stake_id") for r in recompensas if r.get("stake_id")
    }
    nuevos_registros = 0

    for stake in activos:
        stake_id = stake.get("stake_id")
        end_timestamp = stake.get("end_timestamp")

        if not stake_id or end_timestamp is None:
            continue

        if int(end_timestamp) > ahora:
            continue

        if stake_id in recompensas_existentes:
            # Ya existe recompensa (pending o paid), no volver a generar.
            continue

        moved = staking_data.move_to_completed(stake_id)
        if not moved:
            print(f"[WARN] No se pudo mover a completados: {stake_id}")
            continue

        recompensa = {
            "stake_id": stake_id,
            "user_id": stake.get("user_id"),
            "wallet": stake.get("wallet"),
            "reward_don": stake.get("reward_don", 0),
            "transfer_tx_id": stake.get("transfer_tx_id"),
            "timestamp": ahora,
            "status": "pending"
        }

        recompensas.append(recompensa)
        recompensas_existentes.add(stake_id)
        nuevos_registros += 1
        print(f"[OK] Staking finalizado: {stake_id} -> recompensa generada")

    if nuevos_registros > 0:
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
