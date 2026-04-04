import json
import os
import time

# Importar el manejador de base de datos del staking
import staking_data

# Archivo donde se guardarán las recompensas generadas
RECOMPENSAS_PATH = "/app/staking_recompensa.json"

# Asegurar que el archivo existe
if not os.path.exists(RECOMPENSAS_PATH):
    with open(RECOMPENSAS_PATH, "w") as f:
        json.dump([], f)


def load_recompensas():
    """Carga el archivo de recompensas."""
    with open(RECOMPENSAS_PATH, "r") as f:
        return json.load(f)


def save_recompensas(data):
    """Guarda el archivo de recompensas."""
    with open(RECOMPENSAS_PATH, "w") as f:
        json.dump(data, f, indent=4)


def procesar_recompensas():
    ahora = int(time.time())

    activos = staking_data.list_activos()
    recompensas = load_recompensas()

    for stake in activos:
        if stake["end_timestamp"] <= ahora:
            stake_id = stake["stake_id"]

            # Mover a completados usando staking_data
            staking_data.move_to_completed(stake_id)

            # Registrar recompensa
            recompensa = {
                "stake_id": stake["stake_id"],
                "user_id": stake["user_id"],
                "wallet": stake["wallet"],
                "reward_don": stake["reward_don"],
                "timestamp": ahora,
                "status": "pending"  # luego tu sistema de DON lo procesará
            }

            recompensas.append(recompensa)

            print(f"[OK] Staking finalizado: {stake_id} → recompensa generada")

    # Guardar recompensas actualizadas
    save_recompensas(recompensas)

    print("Proceso de recompensas completado.")


if __name__ == "__main__":
    procesar_recompensas()
