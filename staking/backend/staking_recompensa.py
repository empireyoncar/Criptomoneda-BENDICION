import json
import os
import time
import subprocess

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
                "status": "pending"  # staking_payout.py lo cambiará a "paid"
            }

            recompensas.append(recompensa)

            print(f"[OK] Staking finalizado: {stake_id} → recompensa generada")

    # Guardar recompensas actualizadas
    save_recompensas(recompensas)

    print("Proceso de recompensas completado.")

    # 🔥 EJECUTAR staking_payout.py AUTOMÁTICAMENTE
    try:
        print("Ejecutando staking_payout.py...")
        subprocess.run(["python3", "/app/backend/staking_payout.py"], check=True)
        print("staking_payout.py ejecutado correctamente.")
    except Exception as e:
        print("Error ejecutando staking_payout.py:", e)


if __name__ == "__main__":
    while True:
        print("Ejecutando proceso de recompensas...")
        procesar_recompensas()
        print("Proceso completado. Próxima ejecución en 12 horas.")
        
        time.sleep(43200)  # 12 horas = 2 veces al día
