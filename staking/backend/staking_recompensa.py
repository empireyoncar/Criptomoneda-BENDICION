import time
import json
import os
from staking_data import load_file, save_file, move_to_completed

BASE_PATH = "/app"

# Archivos principales
RECOMPENSA_LOG = os.path.join(BASE_PATH, "staking_recompensa.json")
ACTIVOS_FILE = os.path.join(BASE_PATH, "stakingactivos.json")

# Límites recomendados
MAX_RECOMPENSA_MB = 5 * 1024 * 1024     # 5 MB
MAX_STAKING_ACTIVOS = 5000              # 5000 staking por archivo


# ---------------------------------------------------------
# ROTACIÓN DE ARCHIVOS
# ---------------------------------------------------------

def rotar_archivo_recompensa():
    """Rota staking_recompensa.json cuando supera 5 MB."""
    if not os.path.exists(RECOMPENSA_LOG):
        return

    if os.path.getsize(RECOMPENSA_LOG) < MAX_RECOMPENSA_MB:
        return

    # Buscar siguiente número disponible
    i = 1
    while True:
        nuevo = os.path.join(BASE_PATH, f"staking_recompensa_{i}.json")
        if not os.path.exists(nuevo):
            os.rename(RECOMPENSA_LOG, nuevo)
            break
        i += 1

    # Crear archivo nuevo vacío
    with open(RECOMPENSA_LOG, "w") as f:
        json.dump([], f)


def rotar_archivo_activos():
    """Rota stakingactivos.json cuando supera 5000 staking."""
    activos = load_file("activos")

    if len(activos) < MAX_STAKING_ACTIVOS:
        return

    # Buscar siguiente número disponible
    i = 1
    while True:
        nuevo = os.path.join(BASE_PATH, f"stakingactivos_{i}.json")
        if not os.path.exists(nuevo):
            with open(nuevo, "w") as f:
                json.dump(activos, f, indent=4)
            break
        i += 1

    # Vaciar archivo principal
    with open(ACTIVOS_FILE, "w") as f:
        json.dump([], f)


# ---------------------------------------------------------
# LOG GLOBAL DE RECOMPENSAS
# ---------------------------------------------------------

def log_recompensa(entry):
    """Guarda un registro global de recompensas diarias."""

    # Rotar si es necesario
    rotar_archivo_recompensa()

    # Cargar archivo actual
    with open(RECOMPENSA_LOG, "r") as f:
        data = json.load(f)

    data.append(entry)

    with open(RECOMPENSA_LOG, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
# PROCESAR RECOMPENSAS DIARIAS
# ---------------------------------------------------------

def procesar_recompensas():
    """
    - Recorre todos los staking activos
    - Genera recompensa diaria
    - Actualiza reward_history
    - Mueve a completados si terminó
    - Rota archivos si es necesario
    """
    activos = load_file("activos")
    ahora = int(time.time())
    cambios = False

    for stake in activos:
        stake_id = stake["stake_id"]
        days = stake["days"]
        reward_total = stake["reward_total"]
        reward_daily = reward_total / days

        if "reward_history" not in stake:
            stake["reward_history"] = []

        # Si terminó → mover a completados
        if ahora >= stake["end_timestamp"]:
            move_to_completed(stake_id)
            cambios = True
            continue

        # Ver si ya pasó 1 día
        last_calc = stake.get("last_reward_calc", stake["timestamp"])
        if ahora - last_calc < 24 * 3600:
            continue

        # Registrar recompensa diaria
        stake["reward_history"].append({
            "timestamp": ahora,
            "reward": reward_daily
        })

        stake["reward_accumulated"] = stake.get("reward_accumulated", 0) + reward_daily
        stake["last_reward_calc"] = ahora

        # Log global
        log_recompensa({
            "stake_id": stake_id,
            "timestamp": ahora,
            "reward": reward_daily
        })

        cambios = True

    if cambios:
        save_file("activos", activos)

    # Rotar archivo de staking activos si es necesario
    rotar_archivo_activos()

    return {"status": "ok", "updated": cambios}
