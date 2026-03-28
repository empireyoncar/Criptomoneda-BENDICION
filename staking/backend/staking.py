import json
import os
from datetime import datetime

# Rutas de los archivos
DB_DIR = "/app/db"
STAKING_FILE = os.path.join(DB_DIR, "staking.json")
HISTORY_FILE = os.path.join(DB_DIR, "staking_history.json")


# ---------------------------------------------------------
#   CREAR BASES DE DATOS SI NO EXISTEN
# ---------------------------------------------------------
def create_staking_db():
    """Crea los archivos staking.json y staking_history.json si no existen."""
    os.makedirs(DB_DIR, exist_ok=True)

    if not os.path.exists(STAKING_FILE):
        with open(STAKING_FILE, "w") as f:
            json.dump({"stakes": []}, f, indent=4)

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump({"history": []}, f, indent=4)


# ---------------------------------------------------------
#   FUNCIONES DE CARGA Y GUARDADO
# ---------------------------------------------------------
def load_staking():
    with open(STAKING_FILE, "r") as f:
        return json.load(f)


def save_staking(data):
    with open(STAKING_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_history():
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
#   REGISTRAR NUEVO STAKE (NO CALCULA NADA)
# ---------------------------------------------------------
def register_stake(stake_data):
    """
    Recibe un diccionario con los datos del stake ya calculados
    por staking_calculo.py y lo guarda en staking.json.
    """
    staking = load_staking()
    staking["stakes"].append(stake_data)
    save_staking(staking)
    return stake_data


# ---------------------------------------------------------
#   MOVER STAKE AL HISTORIAL
# ---------------------------------------------------------
def move_to_history(stake_id, reason="completed"):
    """
    Mueve un stake desde staking.json hacia staking_history.json.
    Esto se usa cuando:
    - el stake termina
    - el usuario cancela
    - se aplica penalización
    """

    staking = load_staking()
    history = load_history()

    # Buscar stake
    stake = next((s for s in staking["stakes"] if s["stake_id"] == stake_id), None)

    if not stake:
        return {"error": "Stake no encontrado"}

    # Remover de activos
    staking["stakes"] = [s for s in staking["stakes"] if s["stake_id"] != stake_id]
    save_staking(staking)

    # Agregar al historial
    stake["moved_at"] = datetime.utcnow().isoformat()
    stake["reason"] = reason
    history["history"].append(stake)
    save_history(history)

    return {"success": True, "stake": stake}
