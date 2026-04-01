import json
import os
from datetime import datetime

STAKING_FILE = "staking.json"
HISTORY_FILE = "staking_history.json"


# ---------------------------------------------------------
#   Cargar archivo staking.json (stakes activos)
# ---------------------------------------------------------
def load_staking():
    if not os.path.exists(STAKING_FILE):
        return {"stakes": []}

    with open(STAKING_FILE, "r") as f:
        return json.load(f)


# ---------------------------------------------------------
#   Guardar archivo staking.json
# ---------------------------------------------------------
def save_staking(data):
    with open(STAKING_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
#   Cargar historial (stakes terminados/cancelados)
# ---------------------------------------------------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"history": []}

    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


# ---------------------------------------------------------
#   Guardar historial
# ---------------------------------------------------------
def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------
#   Mover stake al historial
# ---------------------------------------------------------
def move_to_history(stake_id, reason="completed"):
    staking = load_staking()
    history = load_history()

    stake = next((s for s in staking["stakes"] if s["stake_id"] == stake_id), None)
    if not stake:
        return False

    # Actualizar estado y fecha final
    stake["status"] = reason
    stake["finalized_at"] = datetime.utcnow().isoformat()

    # Guardar en historial
    history["history"].append(stake)
    save_history(history)

    # Eliminar de stakes activos
    staking["stakes"] = [s for s in staking["stakes"] if s["stake_id"] != stake_id]
    save_staking(staking)

    return True
